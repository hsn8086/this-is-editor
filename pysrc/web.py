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
        self.stdin_queue.put_nowait(None)
        if self.process.poll() is None:
            with contextlib.suppress(OSError):
                self.process.terminate()

    def _push_async(
        self,
        target: asyncio.Queue[str | None],
        item: str | None,
    ) -> None:
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

    bridge = await start_lsp_process(websocket, lang)
    if not bridge:
        return

    await websocket.accept()
    logger.info(f"WebSocket connection established for language: {lang}")

    async with asyncio.TaskGroup() as tg:
        task_ws = tg.create_task(handle_websocket(websocket, bridge, lang))
        task_p = tg.create_task(handle_process_output(websocket, bridge, lang))
        task_perr = tg.create_task(handle_process_error(bridge, lang))
        await monitor_tasks(lang, bridge, [task_ws, task_p, task_perr])


async def start_lsp_process(websocket: WebSocket, lang: str) -> LspBridge | None:
    """Start the Language Server Protocol (LSP) process for the specified language.

    Args:
        websocket (WebSocket): The WebSocket connection.
        lang (str): The language identifier.

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


web_dir = Path(__file__).parent.parent / "web"
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
if window is not None:
    # pywebview state syncing relies on these internal members.
    window.state._hash = _js_api._path_hashes  # noqa: SLF001


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
