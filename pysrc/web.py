"""Provides the backend implementation for a web-based application.

It includes WebSocket handling, Language Server Protocol (LSP) integration,
problem reception, and server management using FastAPI and Uvicorn.
"""

import asyncio
import contextlib
import json
import platform
import queue
import shlex
import socket
import subprocess
import threading
from pathlib import Path
from typing import IO, cast

import uvicorn
import webview
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from loguru import logger
from starlette.websockets import WebSocketDisconnect

from .js_api import Api
from .langs import type_mp
from .models import Problem
from .terminal import TerminalSession, shutdown_terminals


def get_free_port() -> int:
    """Find and return a free port on the local machine.

    Returns:
        int: An available port number.

    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


port = get_free_port()

app = FastAPI()
should_exit: bool = False
_active_bridges: set["LspBridge"] = set()


class LspBridge:
    """Bridge a blocking stdio LSP process into asyncio-friendly queues."""

    def __init__(self, process: subprocess.Popen) -> None:
        """Initialize the bridge for a spawned LSP process."""
        self.process = process
        self.loop = asyncio.get_running_loop()
        self.stdout_queue: asyncio.Queue[str | None] = asyncio.Queue()
        self.stderr_queue: asyncio.Queue[str | None] = asyncio.Queue()
        self.stdin_queue: queue.Queue[bytes | None] = queue.Queue()
        self.stop_event = threading.Event()
        self.threads: list[threading.Thread] = []

    def start(self) -> None:
        """Start background worker threads for process I/O."""
        workers = [
            threading.Thread(target=self._stdout_worker, daemon=True),
            threading.Thread(target=self._stderr_worker, daemon=True),
            threading.Thread(target=self._stdin_worker, daemon=True),
        ]
        self.threads.extend(workers)
        for worker in workers:
            worker.start()

    def submit(self, message: str) -> None:
        """Queue a JSON-RPC payload for the LSP stdin worker."""
        self.stdin_queue.put_nowait(message.encode("utf-8"))

    def close(self) -> None:
        """Stop background workers and terminate the process if needed."""
        if self.stop_event.is_set():
            return
        self.stop_event.set()
        _active_bridges.discard(self)
        self.stdin_queue.put_nowait(None)
        if self.process.poll() is None:
            with contextlib.suppress(OSError):
                self.process.terminate()
            with contextlib.suppress(subprocess.TimeoutExpired, OSError):
                self.process.wait(timeout=1)
            if self.process.poll() is None:
                with contextlib.suppress(OSError):
                    self.process.kill()
                with contextlib.suppress(subprocess.TimeoutExpired, OSError):
                    self.process.wait(timeout=1)

        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1)

    def _push_async(
        self,
        target: asyncio.Queue[str | None],
        item: str | None,
    ) -> None:
        with contextlib.suppress(RuntimeError):
            self.loop.call_soon_threadsafe(target.put_nowait, item)

    def _read_available(
        self,
        stream: IO[bytes],
        size: int = 4096,
    ) -> bytes:
        reader = getattr(stream, "read1", None)
        if callable(reader):
            return reader(size)
        return stream.read(size)

    def _stdout_worker(self) -> None:  # noqa: C901, PLR0912
        stdout = self.process.stdout
        if stdout is None:
            self._push_async(self.stdout_queue, None)
            return

        buffer = bytearray()
        expected_length: int | None = None
        try:
            while not self.stop_event.is_set():
                chunk = self._read_available(stdout)
                if not chunk:
                    break
                buffer.extend(chunk)

                while True:
                    if expected_length is None:
                        header_end = buffer.find(b"\r\n\r\n")
                        if header_end == -1:
                            break
                        headers = buffer[:header_end].decode("ascii", errors="replace")
                        expected_length = None
                        for header in headers.split("\r\n"):
                            if header.lower().startswith("content-length:"):
                                expected_length = int(header.split(":", 1)[1].strip())
                                break
                        if expected_length is None:
                            msg = "Missing Content-Length header"
                            raise ValueError(msg)  # noqa: TRY301
                        del buffer[: header_end + 4]

                    if len(buffer) < expected_length:
                        break

                    content = bytes(buffer[:expected_length])
                    del buffer[:expected_length]
                    expected_length = None
                    if content:
                        self._push_async(
                            self.stdout_queue,
                            content.decode("utf-8", errors="replace"),
                        )
        except (OSError, ValueError, RuntimeError) as e:
            logger.opt(exception=e).error("LSP stdout worker error")
        finally:
            self._push_async(self.stdout_queue, None)

    def _stderr_worker(self) -> None:
        stderr = self.process.stderr
        if stderr is None:
            self._push_async(self.stderr_queue, None)
            return
        try:
            while not self.stop_event.is_set():
                error_chunk = stderr.readline()
                if not error_chunk:
                    break
                self._push_async(
                    self.stderr_queue,
                    error_chunk.decode("utf-8", errors="replace").strip(),
                )
        except (OSError, RuntimeError) as e:
            logger.opt(exception=e).error("LSP stderr worker error")
        finally:
            self._push_async(self.stderr_queue, None)

    def _stdin_worker(self) -> None:
        stdin = self.process.stdin
        if stdin is None:
            return
        try:
            while not self.stop_event.is_set():
                data = self.stdin_queue.get()
                if data is None:
                    break
                stdin.write(f"Content-Length: {len(data)}\r\n\r\n".encode("ascii"))
                stdin.write(data)
                stdin.flush()
        except (BrokenPipeError, OSError, RuntimeError) as e:
            if not self.stop_event.is_set():
                logger.opt(exception=e).error("LSP stdin worker error")


@app.websocket("/lsp/{lang:str}")
async def websocket_endpoint(websocket: WebSocket, lang: str) -> None:
    """Handle LSP WebSocket connections for a given language.

    Args:
        websocket (WebSocket): The WebSocket connection.
        lang (str): The language identifier.

    Returns:
        None

    """
    if should_exit:
        await websocket.close()
        return

    try:
        workspace_path = resolve_workspace_path(
            websocket.query_params.get("workspace"),
        )
    except ValueError as e:
        logger.warning(str(e))
        await websocket.close(code=1008)
        return

    bridge = await start_lsp_process(websocket, lang, workspace_path)
    if not bridge:
        return

    await websocket.accept()
    logger.info(f"WebSocket connection established for language: {lang}")

    async with asyncio.TaskGroup() as tg:
        task_ws = tg.create_task(handle_websocket(websocket, bridge, lang))
        task_p = tg.create_task(handle_process_output(websocket, bridge, lang))
        task_perr = tg.create_task(handle_process_error(bridge, lang))
        await monitor_tasks(lang, bridge, [task_ws, task_p, task_perr])


def resolve_workspace_path(raw_path: str | None) -> Path | None:
    """Validate and resolve an optional LSP workspace directory."""
    if raw_path is None:
        return None

    workspace_path = Path(raw_path).expanduser()
    if not workspace_path.is_absolute():
        msg = f"LSP workspace path must be absolute: {raw_path}"
        raise ValueError(msg)

    try:
        workspace_path = workspace_path.resolve(strict=True)
    except (OSError, RuntimeError) as e:
        msg = f"LSP workspace path cannot be resolved: {raw_path}"
        raise ValueError(msg) from e

    if not workspace_path.is_dir():
        msg = f"LSP workspace path is not a directory: {raw_path}"
        raise ValueError(msg)
    return workspace_path


async def start_lsp_process(
    websocket: WebSocket,
    lang: str,
    workspace_path: Path | None = None,
) -> LspBridge | None:
    """Start the Language Server Protocol (LSP) process for the specified language.

    Args:
        websocket (WebSocket): The WebSocket connection.
        lang (str): The language identifier.
        workspace_path (Path | None): Working directory for the LSP process.

    Returns:
        LspBridge | None: The running bridge if started successfully, else None.

    """
    raw_cmd = type_mp.get(lang, {}).get("lsp", {}).get("command", "")
    if not raw_cmd:
        logger.error(f"No LSP command found for language: {lang}")
        await websocket.close()
        return None

    is_windows = platform.system() == "Windows"
    cmd: str | list[str]
    cmd_display: str
    if isinstance(raw_cmd, str):
        cmd_display = raw_cmd
        cmd = raw_cmd if is_windows else shlex.split(raw_cmd)
    else:
        cmd_display = " ".join(raw_cmd)
        cmd = subprocess.list2cmdline(raw_cmd) if is_windows else raw_cmd

    creationflags = 0
    if is_windows:
        creationflags = cast("int", getattr(subprocess, "CREATE_NO_WINDOW", 0))
    try:
        p = subprocess.Popen(  # noqa: ASYNC220
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=workspace_path,
            creationflags=creationflags,
            shell=is_windows,
        )
    except (FileNotFoundError, PermissionError, OSError) as e:
        logger.error(f"Failed to start LSP for language: {lang}")
        logger.opt(exception=e).error(f"Command: {cmd_display}")
        await websocket.close()
        return None

    await asyncio.sleep(0.1)
    if p.poll() is not None:
        logger.error(f"Failed to start LSP for language: {lang}")
        if p.stderr is not None:
            logger.error(p.stderr.read().decode("utf-8", errors="replace"))
        await websocket.close()
        return None

    bridge = LspBridge(p)
    bridge.start()
    _active_bridges.add(bridge)
    return bridge


async def handle_websocket(
    websocket: WebSocket,
    bridge: LspBridge,
    lang: str,
) -> None:
    """Forward messages from the WebSocket to the LSP process.

    Args:
        websocket (WebSocket): The WebSocket connection.
        bridge (LspBridge): The LSP bridge.
        lang (str): The language identifier.

    Returns:
        None

    """
    try:
        while True:
            bridge.submit(await websocket.receive_text())
    except (asyncio.CancelledError, ConnectionError) as e:
        if not should_exit:
            logger.opt(exception=e).error(f"{lang} LS websocket error")
    except WebSocketDisconnect as e:
        if not should_exit:
            logger.opt(exception=e).error(f"{lang} LS websocket disconnected")
    finally:
        bridge.close()
        if websocket.client_state.name != "DISCONNECTED":
            await websocket.close()


async def handle_process_output(
    websocket: WebSocket,
    bridge: LspBridge,
    lang: str,
) -> None:
    """Read output from the LSP process and send it to the WebSocket client.

    Args:
        websocket (WebSocket): The WebSocket connection.
        bridge (LspBridge): The LSP bridge.
        lang (str): The language identifier.

    Returns:
        None

    """
    try:
        while True:
            content = await bridge.stdout_queue.get()
            if content is None:
                return
            await websocket.send_text(content)

    except (ValueError, RuntimeError) as e:
        if not should_exit:
            logger.opt(exception=e).error(f"{lang} LS process error")

    except asyncio.exceptions.CancelledError:
        ...
    finally:
        bridge.close()
        if websocket.client_state.name != "DISCONNECTED":
            await websocket.close()


async def handle_process_error(bridge: LspBridge, lang: str) -> None:
    """Read and log error output from the LSP process.

    Args:
        bridge (LspBridge): The LSP bridge.
        lang (str): The language identifier.

    Returns:
        None

    """
    try:
        while True:
            error_chunk = await bridge.stderr_queue.get()
            if error_chunk is None:
                break
            logger.error(f"{lang} LSP stderr: {error_chunk}")
    except (OSError, RuntimeError) as e:
        if not should_exit:
            logger.opt(exception=e).error(f"{lang} LS process stderr error")


async def monitor_tasks(
    lang: str,
    bridge: LspBridge,
    tasks: list[asyncio.Task],
) -> None:
    """Monitor background tasks and handle server exit or task completion.

    Args:
        lang (str): The language identifier.
        bridge (LspBridge): The LSP bridge.
        tasks (list[asyncio.Task]): List of asyncio tasks to monitor.

    Returns:
        None

    """
    while True:
        await asyncio.sleep(1)
        if should_exit:
            for task in tasks:
                task.cancel()
            bridge.close()
            with contextlib.suppress(subprocess.TimeoutExpired):
                await asyncio.to_thread(bridge.process.wait, 3)
            logger.info(f"WebSocket connection closed for language: {lang}")
            return
        if bridge.process.poll() is not None:
            bridge.close()
            for task in tasks:
                task.cancel()
            return
        if all(task.done() for task in tasks):
            bridge.close()
            return


@app.websocket("/terminal")
async def terminal_endpoint(websocket: WebSocket) -> None:
    """Stream a shell session over a WebSocket.

    Client frames are JSON: ``{"type": "stdin", "data": str}``,
    ``{"type": "resize", "cols": int, "rows": int}``, ``{"type": "interrupt"}``.
    Server frames are ``{"type": "output", "data": str}`` and
    ``{"type": "exit", "code": int | None}``.

    Args:
        websocket (WebSocket): The WebSocket connection.

    """
    if should_exit:
        await websocket.close()
        return

    session = TerminalSession(cwd=_js_api.cwd)
    try:
        session.start()
    except OSError as e:
        logger.opt(exception=e).error("Failed to start terminal shell")
        await websocket.close(code=1011)
        return

    await websocket.accept()
    logger.info(f"Terminal session started (pid={session.pid})")

    async with asyncio.TaskGroup() as tg:
        task_in = tg.create_task(handle_terminal_input(websocket, session))
        task_out = tg.create_task(handle_terminal_output(websocket, session))
        await monitor_terminal(session, [task_in, task_out])


async def handle_terminal_input(
    websocket: WebSocket,
    session: TerminalSession,
) -> None:
    """Forward client frames to the shell until the socket closes.

    Args:
        websocket (WebSocket): The WebSocket connection.
        session (TerminalSession): The shell session to feed.

    """
    try:
        while not should_exit:
            raw = await websocket.receive_text()
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                logger.warning("Discarding malformed terminal frame")
                continue

            kind = message.get("type")
            if kind == "stdin":
                session.write(str(message.get("data", "")))
            elif kind == "resize":
                session.resize(
                    int(message.get("cols", 80)),
                    int(message.get("rows", 24)),
                )
            elif kind == "interrupt":
                session.interrupt()
    except WebSocketDisconnect:
        logger.info("Terminal WebSocket disconnected")
    except (OSError, RuntimeError, ValueError) as e:
        if not should_exit:
            logger.opt(exception=e).error("Terminal input handler failed")


async def handle_terminal_output(
    websocket: WebSocket,
    session: TerminalSession,
) -> None:
    """Relay shell output to the client until the stream ends.

    Args:
        websocket (WebSocket): The WebSocket connection.
        session (TerminalSession): The shell session to read from.

    """
    try:
        while True:
            chunk = await session.next_chunk()
            if chunk is None:
                break
            await websocket.send_text(
                json.dumps({"type": "output", "data": chunk}),
            )
        process = session.process
        await websocket.send_text(
            json.dumps(
                {"type": "exit", "code": process.poll() if process else None},
            ),
        )
    except WebSocketDisconnect:
        pass
    except (OSError, RuntimeError, ValueError) as e:
        if not should_exit:
            logger.opt(exception=e).error("Terminal output handler failed")


async def monitor_terminal(
    session: TerminalSession,
    tasks: list[asyncio.Task],
) -> None:
    """Cancel terminal tasks once the shell or the application stops.

    Without this watchdog a live session would keep uvicorn from draining and
    the process would hang on shutdown.

    Args:
        session (TerminalSession): The shell session being monitored.
        tasks (list[asyncio.Task]): Tasks to cancel when the session ends.

    """
    while True:
        await asyncio.sleep(1)
        if should_exit:
            for task in tasks:
                task.cancel()
            session.close()
            logger.info("Terminal session closed for shutdown")
            return

        process = session.process
        if process is not None and process.poll() is not None:
            session.close()
            for task in tasks:
                task.cancel()
            return

        # `any`, not `all`: the output task blocks until the shell exits, so
        # waiting for both would keep a shell running after the client hangs up.
        if any(task.done() for task in tasks):
            session.close()
            for task in tasks:
                task.cancel()
            return


web_dir = Path(__file__).parent.parent / "web"
# Registered last on purpose: Starlette matches in order and Mount("/") also
# claims websocket scopes, so any route added below would be unreachable.
app.mount(
    "/",
    StaticFiles(directory=web_dir, html=True),
    name="web",
)

app_prob_recver = FastAPI()


@app_prob_recver.post("/")
async def receive_problem(problem: Problem) -> dict:
    """Receive a problem from the client and dispatch it to the frontend.

    Args:
        problem (Problem): The problem object containing name and tests.

    Returns:
        dict: Status and message about the received problem.

    """
    logger.info(f"Received problem: {problem.name} with {len(problem.tests)} tests.")
    tests = []
    for i, test in enumerate(problem.tests, start=1):
        tests.append(
            {
                "id": i,
                "input": test.get("input", ""),
                "answer": test.get("output", ""),
            },
        )

    if window is not None:
        window.run_js(
            f"""
            window.dispatchEvent(
                new CustomEvent(
                    'problem-received', 
                    {{ detail: {json.dumps({"name": problem.name, "tests": tests})} }}
                )
            );
            """,
        )

    return {"status": "success", "message": f"Problem {problem.name} received."}


_js_api = Api()
window = webview.create_window(
    "TIE",
    f"http://127.0.0.1:{port}",
    js_api=_js_api,
    width=800,
    height=600,
)


def start_server() -> tuple[
    uvicorn.Server,
    threading.Thread,
    uvicorn.Server,
    threading.Thread,
]:
    """Start the main FastAPI server and the problem receiver server.

    Returns:
        tuple: (main server, main thread, receiver server, receiver thread)

    """
    logger.info(f"Starting server on port {port}")
    conf = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="info", workers=8)
    server = uvicorn.Server(conf)
    conf_recver = uvicorn.Config(
        app_prob_recver,
        host="127.0.0.1",
        port=10043,
        log_level="info",
        workers=1,
    )
    server_recver = uvicorn.Server(conf_recver)
    thread = threading.Thread(target=server.run, daemon=True)
    thread_recver = threading.Thread(target=server_recver.run, daemon=True)
    thread_recver.start()
    thread.start()
    return server, thread, server_recver, thread_recver


def shutdown_lsp_bridges() -> None:
    """Close all active LSP bridges before process shutdown."""
    for bridge in tuple(_active_bridges):
        bridge.close()


def shutdown_runtime() -> None:
    """Shut down runtime background resources before server teardown."""
    shutdown_lsp_bridges()
    shutdown_terminals()
    _js_api.shutdown()
