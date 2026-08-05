"""Back a terminal console with a real shell process.

Streams shell output to the frontend and feeds keystrokes back to its input.

On POSIX the shell runs behind a pseudo-terminal from the standard library, so
it prints a prompt, keeps line editing, and stays line buffered. Windows has no
stdlib ConPTY binding, so it falls back to pipes: still usable, but without a
prompt from the shell itself.

The threading model mirrors ``LspBridge`` in ``pysrc.web``: blocking reads live
on daemon threads and hand data to the event loop through
``loop.call_soon_threadsafe``.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import platform
import signal
import subprocess
import threading
from typing import TYPE_CHECKING

import psutil
from loguru import logger

if TYPE_CHECKING:
    from pathlib import Path

IS_WINDOWS = platform.system() == "Windows"

if not IS_WINDOWS:
    import fcntl
    import pty
    import struct
    import termios

# Guards against a runaway process (``while (1) printf(...)``) filling memory
# faster than the frontend drains the socket.
MAX_PENDING_CHUNKS = 2048
READ_SIZE = 4096
DEFAULT_COLS = 80
DEFAULT_ROWS = 24

_active_terminals: set[TerminalSession] = set()


def resolve_shell() -> list[str]:
    """Return the command line for the user's interactive shell.

    POSIX shells are started as login shells. A GUI application on macOS
    inherits a minimal PATH that lacks Homebrew and other user directories, and
    a login shell re-reads the user's profile to restore it.

    Returns:
        list[str]: Executable and arguments for the shell process.

    """
    if IS_WINDOWS:
        return [os.environ.get("COMSPEC") or "cmd.exe"]
    return [os.environ.get("SHELL") or "/bin/sh", "-l"]


class TerminalSession:
    """Own a shell process and pump its I/O between threads and asyncio."""

    def __init__(self, cwd: Path | None = None) -> None:
        """Prepare a session; call :meth:`start` to spawn the shell.

        Args:
            cwd (Path | None): Working directory for the shell.

        """
        self.cwd = cwd
        self.loop = asyncio.get_running_loop()
        self.output_queue: asyncio.Queue[str | None] = asyncio.Queue()
        self.stop_event = threading.Event()
        self.threads: list[threading.Thread] = []
        self.process: subprocess.Popen | None = None
        self._master_fd: int | None = None
        self._dropped = 0
        # Counted here rather than via output_queue.qsize(): the reader thread
        # hands items over with call_soon_threadsafe, which only *schedules* the
        # put. While the loop is behind, qsize() stays stale and would never
        # trip the limit, exactly when backpressure is needed most.
        self._pending = 0
        self._pending_lock = threading.Lock()

    @property
    def pid(self) -> int | None:
        """Process id of the shell, or None before start / after cleanup."""
        return self.process.pid if self.process else None

    def start(self) -> None:
        """Spawn the shell and begin streaming its output.

        Raises:
            OSError: If the shell process cannot be started.

        """
        command = resolve_shell()
        cwd = str(self.cwd) if self.cwd else None
        logger.info(f"Starting terminal shell: {command} (cwd={cwd})")

        if IS_WINDOWS:
            self._start_windows(command, cwd)
        else:
            self._start_posix(command, cwd)

        _active_terminals.add(self)
        reader = threading.Thread(target=self._read_worker, daemon=True)
        self.threads.append(reader)
        reader.start()

    def _start_posix(self, command: list[str], cwd: str | None) -> None:
        master_fd, slave_fd = pty.openpty()
        self._master_fd = master_fd
        try:
            self.process = subprocess.Popen(
                command,
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                cwd=cwd,
                # Its own session makes the pty the controlling terminal and
                # lets the whole process group be signalled on close.
                start_new_session=True,
                close_fds=True,
                env=self._child_env(),
            )
        finally:
            # The child owns the slave end now; holding it open here would keep
            # reads from ever reporting EOF.
            os.close(slave_fd)
        self.resize(DEFAULT_COLS, DEFAULT_ROWS)

    def _start_windows(self, command: list[str], cwd: str | None) -> None:
        # Fetched dynamically: these constants only exist on Windows, and the
        # type checker resolves this module against the host platform.
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        creationflags |= getattr(subprocess, "CREATE_NO_WINDOW", 0)
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=cwd,
            creationflags=creationflags,
            close_fds=True,
            env=self._child_env(),
        )

    def _child_env(self) -> dict[str, str]:
        env = dict(os.environ)
        # Nudge child programs away from full buffering so prompts written
        # without a trailing newline still reach the panel.
        env["PYTHONUNBUFFERED"] = "1"
        if not IS_WINDOWS:
            env.setdefault("TERM", "xterm-256color")
        return env

    def write(self, data: str) -> None:
        """Send keystrokes to the shell.

        Args:
            data (str): Raw text to write to the shell input.

        """
        if self.stop_event.is_set():
            return
        payload = data.encode("utf-8", errors="replace")
        with contextlib.suppress(OSError, ValueError):
            if self._master_fd is not None:
                os.write(self._master_fd, payload)
            elif self.process and self.process.stdin:
                self.process.stdin.write(payload)
                self.process.stdin.flush()

    def resize(self, cols: int, rows: int) -> None:
        """Tell the shell how wide its terminal is.

        No-op on Windows, which has no pty to resize.

        Args:
            cols (int): Column count.
            rows (int): Row count.

        """
        if IS_WINDOWS or self._master_fd is None:
            return
        size = struct.pack("HHHH", max(rows, 1), max(cols, 1), 0, 0)
        with contextlib.suppress(OSError, ValueError):
            fcntl.ioctl(self._master_fd, termios.TIOCSWINSZ, size)

    def interrupt(self) -> None:
        """Deliver an interrupt to the foreground program, like Ctrl-C."""
        process = self.process
        if not process or process.poll() is not None:
            return
        with contextlib.suppress(OSError, ValueError, ProcessLookupError):
            if IS_WINDOWS:
                process.send_signal(getattr(signal, "CTRL_BREAK_EVENT", signal.SIGTERM))
            else:
                os.killpg(os.getpgid(process.pid), signal.SIGINT)

    def close(self) -> None:
        """Stop the shell, its descendants, and the reader thread.

        Safe to call repeatedly: both the connection handler and the global
        shutdown path invoke it.
        """
        if self.stop_event.is_set():
            return
        self.stop_event.set()
        _active_terminals.discard(self)

        self._terminate_process()

        if self._master_fd is not None:
            with contextlib.suppress(OSError):
                os.close(self._master_fd)
            self._master_fd = None

        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1)

        self._push(None)

    def _terminate_process(self) -> None:
        process = self.process
        if not process or process.poll() is not None:
            return

        # Snapshot the tree first: once the shell dies its children are
        # reparented and can no longer be found from this pid.
        descendants = self._descendants(process.pid)

        # A shell forks children; signalling only the shell would orphan them.
        for send, wait in (
            (self._signal_group_term, 1.0),
            (self._signal_group_kill, 1.0),
        ):
            send(process)
            with contextlib.suppress(subprocess.TimeoutExpired, OSError):
                process.wait(timeout=wait)
            if process.poll() is not None:
                break

        # An interactive shell runs job control, so `sleep 30 &` lands in its
        # own process group and the killpg above never reaches it. A survivor
        # keeps the pty slave open, which blocks the reader thread forever.
        self._kill_survivors(descendants)

    def _descendants(self, pid: int) -> list[psutil.Process]:
        try:
            return psutil.Process(pid).children(recursive=True)
        except (psutil.Error, OSError):
            return []

    def _kill_survivors(self, processes: list[psutil.Process]) -> None:
        for child in processes:
            with contextlib.suppress(psutil.Error, OSError):
                if child.is_running():
                    child.kill()
        if processes:
            with contextlib.suppress(psutil.Error, OSError):
                psutil.wait_procs(processes, timeout=1)

    def _signal_group_term(self, process: subprocess.Popen) -> None:
        with contextlib.suppress(OSError, ValueError, ProcessLookupError):
            if IS_WINDOWS:
                process.terminate()
            else:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)

    def _signal_group_kill(self, process: subprocess.Popen) -> None:
        with contextlib.suppress(OSError, ValueError, ProcessLookupError):
            if IS_WINDOWS:
                process.kill()
            else:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)

    async def next_chunk(self) -> str | None:
        """Await the next output chunk, or None once the stream ends.

        Returns:
            str | None: Decoded output, or None at end of stream.

        """
        item = await self.output_queue.get()
        if item is not None:
            with self._pending_lock:
                self._pending -= 1
        return item

    def _push(self, item: str | None) -> None:
        if item is not None:
            with self._pending_lock:
                if self._pending >= MAX_PENDING_CHUNKS:
                    self._dropped += 1
                    return
                self._pending += 1
        with contextlib.suppress(RuntimeError):
            self.loop.call_soon_threadsafe(self.output_queue.put_nowait, item)

    def _read_chunk(self) -> bytes:
        if self._master_fd is not None:
            return os.read(self._master_fd, READ_SIZE)
        stdout = self.process.stdout if self.process else None
        if stdout is None:
            return b""
        reader = getattr(stdout, "read1", None)
        if callable(reader):
            return reader(READ_SIZE)
        return stdout.read(READ_SIZE)

    def _read_worker(self) -> None:
        try:
            while not self.stop_event.is_set():
                chunk = self._read_chunk()
                if not chunk:
                    break
                self._push(chunk.decode("utf-8", errors="replace"))
        except OSError:
            # A closed pty reports EIO rather than EOF once the child is gone.
            pass
        except (ValueError, RuntimeError) as e:
            if not self.stop_event.is_set():
                logger.opt(exception=e).error("Terminal reader failed")
        finally:
            if self._dropped:
                logger.warning(f"Terminal dropped {self._dropped} output chunks")
            self._push(None)


def shutdown_terminals() -> None:
    """Close every live terminal session during application shutdown."""
    for session in tuple(_active_terminals):
        session.close()
