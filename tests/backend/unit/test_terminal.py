"""Tests for the terminal console session."""

import asyncio
import os
import sys
from collections.abc import AsyncIterator

import psutil
import pytest

from pysrc import terminal
from pysrc.terminal import TerminalSession, resolve_shell, shutdown_terminals

pytestmark = pytest.mark.skipif(
    terminal.IS_WINDOWS,
    reason="POSIX pty behaviour; Windows uses the pipe fallback.",
)


async def _drain(session: TerminalSession, quiet_after: float = 3.0) -> str:
    """Collect output until the stream goes quiet."""
    chunks: list[str] = []
    try:
        while True:
            chunk = await asyncio.wait_for(session.next_chunk(), quiet_after)
            if chunk is None:
                break
            chunks.append(chunk)
    except TimeoutError:
        pass
    return "".join(chunks)


@pytest.fixture
async def session() -> AsyncIterator[TerminalSession]:
    """Provide a started session that is always cleaned up.

    Async because TerminalSession captures the running event loop on
    construction in order to hand data back from its reader thread.
    """
    created = TerminalSession()
    created.start()
    try:
        yield created
    finally:
        created.close()


def test_resolve_shell_uses_login_shell(monkeypatch: pytest.MonkeyPatch) -> None:
    """A login shell is required so the GUI inherits the user's PATH."""
    monkeypatch.setenv("SHELL", "/bin/zsh")

    assert resolve_shell() == ["/bin/zsh", "-l"]


def test_resolve_shell_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    """A missing SHELL must not stop the terminal from opening."""
    monkeypatch.delenv("SHELL", raising=False)

    assert resolve_shell() == ["/bin/sh", "-l"]


async def test_session_runs_a_command(session: TerminalSession) -> None:
    """The shell executes input and streams its output back."""
    await _drain(session, quiet_after=1.5)

    session.write("echo terminal_probe_$((6*7))\n")
    output = await _drain(session, quiet_after=3.0)

    assert "terminal_probe_42" in output


async def test_session_registers_and_deregisters() -> None:
    """Sessions must be reachable from the global shutdown path."""
    created = TerminalSession()
    created.start()
    assert created in terminal._active_terminals  # noqa: SLF001

    created.close()
    assert created not in terminal._active_terminals  # noqa: SLF001


async def test_close_is_idempotent() -> None:
    """Both the connection handler and shutdown call close()."""
    created = TerminalSession()
    created.start()

    created.close()
    created.close()

    assert created.process is not None
    assert created.process.poll() is not None


async def test_close_reaps_background_grandchildren() -> None:
    """Killing only the shell would orphan whatever it started.

    An interactive shell applies job control, so a backgrounded command gets its
    own process group and survives a killpg aimed at the shell. A survivor holds
    the pty slave open and wedges the reader thread, so the tree has to be
    walked explicitly.
    """
    created = TerminalSession()
    created.start()
    assert created.process is not None
    # The shell must own its session, otherwise close() would signal the
    # application's own process group.
    assert os.getpgid(created.process.pid) != os.getpgid(os.getpid())

    created.write("sleep 47 &\n")
    await asyncio.sleep(1.5)
    background = [
        child
        for child in psutil.Process(created.process.pid).children(recursive=True)
        if "sleep" in child.name()
    ]
    assert background, "background job did not start"

    created.close()

    assert created.process.poll() is not None
    psutil.wait_procs(background, timeout=3)
    assert not [child for child in background if child.is_running()]


async def test_shutdown_terminals_closes_everything() -> None:
    """Application shutdown must not leave a shell running."""
    first, second = TerminalSession(), TerminalSession()
    first.start()
    second.start()

    shutdown_terminals()

    assert first.process is not None
    assert second.process is not None
    assert first.process.poll() is not None
    assert second.process.poll() is not None
    assert not terminal._active_terminals  # noqa: SLF001


async def test_write_after_close_is_ignored() -> None:
    """A late frame from a closing socket must not raise."""
    created = TerminalSession()
    created.start()
    created.close()

    created.write("echo late\n")


async def test_resize_survives_a_dead_terminal() -> None:
    """Resize races with shutdown and must stay silent."""
    created = TerminalSession()
    created.start()
    created.close()

    created.resize(120, 40)


async def test_output_queue_is_bounded(
    session: TerminalSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Runaway output is dropped rather than allowed to exhaust memory.

    The reader thread only schedules queue puts, so the limit has to be tracked
    independently of the queue's own size.
    """
    monkeypatch.setattr(terminal, "MAX_PENDING_CHUNKS", 4)
    for _ in range(50):
        session._push("noise")  # noqa: SLF001
    await asyncio.sleep(0.05)

    assert session.output_queue.qsize() <= terminal.MAX_PENDING_CHUNKS
    # Draining must free capacity again, otherwise the terminal would go mute
    # after the first burst.
    assert await session.next_chunk() == "noise"
    session._push("after-drain")  # noqa: SLF001
    await asyncio.sleep(0.05)
    assert session.output_queue.qsize() == terminal.MAX_PENDING_CHUNKS


async def test_child_env_requests_unbuffered_output(
    session: TerminalSession,
) -> None:
    """Pipes make child stdio fully buffered, hiding interactive prompts."""
    env = session._child_env()  # noqa: SLF001

    assert env["PYTHONUNBUFFERED"] == "1"
    assert env["TERM"] == "xterm-256color"


def test_module_imports_cleanly_on_this_platform() -> None:
    """The pty imports are platform guarded; catch a regression early."""
    assert "pysrc.terminal" in sys.modules
    assert terminal.IS_WINDOWS is False
