"""Provides the backend implementation for a web-based application.

It includes WebSocket handling, Language Server Protocol (LSP) integration,
problem reception, and server management using FastAPI and Uvicorn.
"""

import asyncio
import json
import platform
import shlex
import subprocess
import threading
from pathlib import Path

import starlette
import uvicorn
import webview
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from loguru import logger

from .js_api import Api
from .langs import type_mp
from .models import Problem


def get_free_port() -> int:
    """Find and return a free port on the local machine.

    Returns:
        int: An available port number.

    """
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


port = get_free_port()

app = FastAPI()
should_exit = False


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

    p = await start_lsp_process(websocket, lang)
    if not p:
        return

    await websocket.accept()
    logger.info(f"WebSocket connection established for language: {lang}")

    async with asyncio.TaskGroup() as tg:
        task_ws = tg.create_task(handle_websocket(websocket, p, lang))
        task_p = tg.create_task(handle_process_output(websocket, p, lang))
        task_perr = tg.create_task(handle_process_error(p, lang))
        await monitor_tasks(lang, p, [task_ws, task_p, task_perr])


async def start_lsp_process(websocket: WebSocket, lang: str) -> subprocess.Popen | None:
    """Start the Language Server Protocol (LSP) process for the specified language.

    Args:
        websocket (WebSocket): The WebSocket connection.
        lang (str): The language identifier.

    Returns:
        subprocess.Popen | None: The LSP process if started successfully, else None.

    """
    cmd = type_mp.get(lang, {}).get("lsp", {}).get("command", "")
    if not cmd:
        logger.error(f"No LSP command found for language: {lang}")
        await websocket.close()
        return None
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    try:
        p = subprocess.Popen(  # noqa: ASYNC220
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
            if platform.system() == "Windows"
            else 0,
            shell=True if platform.system() == "Windows" else 0,
        )
    except (FileNotFoundError, PermissionError, OSError) as e:
        logger.error(f"Failed to start LSP for language: {lang}")
        logger.opt(exception=e).error(f"Command: {' '.join(cmd)}")
        await websocket.close()
        return None

    await asyncio.sleep(0.1)
    if p.poll() is not None:
        logger.error(f"Failed to start LSP for language: {lang}")
        logger.error(p.stderr.read().decode("utf-8"))
        await websocket.close()
        return None

    return p


async def handle_websocket(
    websocket: WebSocket,
    p: subprocess.Popen,
    lang: str,
) -> None:
    """Forward messages from the WebSocket to the LSP process.

    Args:
        websocket (WebSocket): The WebSocket connection.
        p (subprocess.Popen): The LSP process.
        lang (str): The language identifier.

    Returns:
        None

    """
    try:
        while True:
            data = (await websocket.receive_text()).encode("utf-8")
            await asyncio.to_thread(
                p.stdin.write,
                f"Content-Length: {len(data)}\r\n\r\n".encode(),
            )
            await asyncio.to_thread(p.stdin.write, data)
            await asyncio.to_thread(p.stdin.flush)
    except (asyncio.CancelledError, ConnectionError) as e:
        logger.opt(exception=e).error(f"{lang} LS websocket error")
    except starlette.websockets.WebSocketDisconnect as e:
        if not should_exit:
            logger.opt(exception=e).error(f"{lang} LS websocket disconnected")
    finally:
        if websocket.client_state.name != "DISCONNECTED":
            await websocket.close()


async def handle_process_output(
    websocket: WebSocket,
    p: subprocess.Popen,
    lang: str,
) -> None:
    """Read output from the LSP process and send it to the WebSocket client.

    Args:
        websocket (WebSocket): The WebSocket connection.
        p (subprocess.Popen): The LSP process.
        lang (str): The language identifier.

    Returns:
        None

    """
    buffer = b""
    try:
        while True:
            await asyncio.to_thread(p.stdout.read, 16)
            while b"\r\n\r\n" not in buffer:
                buffer += p.stdout.read(1)

            header_end = buffer.find(b"\r\n\r\n")

            if header_end == -1:
                continue

            content_length = int(
                buffer[:header_end].strip().split(b"\n")[0].strip().split()[-1],
            )
            buffer = buffer[header_end + 4 :]  # skip \r\n\r\n
            while len(buffer) < content_length:
                chunk = await asyncio.to_thread(
                    p.stdout.read,
                    content_length - len(buffer),
                )
                buffer += chunk

            content = buffer[:content_length]
            buffer = buffer[content_length:]  # keep remaining data for next
            if not content:
                continue
            await websocket.send_text(content.decode("utf-8"))

    except (ValueError, RuntimeError) as e:
        logger.opt(exception=e).error(f"{lang} LS process error")

    except asyncio.exceptions.CancelledError:
        ...
    finally:
        if websocket.client_state.name != "DISCONNECTED":
            await websocket.close()


async def handle_process_error(p: subprocess.Popen, lang: str) -> None:
    """Read and log error output from the LSP process.

    Args:
        p (subprocess.Popen): The LSP process.
        lang (str): The language identifier.

    Returns:
        None

    """
    try:
        while True:
            error_chunk = await asyncio.to_thread(p.stderr.readline)
            if not error_chunk:
                break
            logger.error(
                f"{lang} LSP stderr: {error_chunk.decode('utf-8').strip()}",
            )
    except (OSError, RuntimeError) as e:
        logger.opt(exception=e).error(f"{lang} LS process stderr error")


async def monitor_tasks(
    lang: str,
    p: subprocess.Popen,
    tasks: list[asyncio.Task],
) -> None:
    """Monitor background tasks and handle server exit or task completion.

    Args:
        lang (str): The language identifier.
        p (subprocess.Popen): The LSP process.
        tasks (list[asyncio.Task]): List of asyncio tasks to monitor.

    Returns:
        None

    """
    while True:
        await asyncio.sleep(1)
        if should_exit:
            for task in tasks:
                task.cancel()
            p.terminate()
            p.wait()
            logger.info(f"WebSocket connection closed for language: {lang}")
            return
        if all(task.done() for task in tasks):
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


window = webview.create_window(
    "TIE",
    f"http://127.0.0.1:{port}",
    js_api=Api(),
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
    import uvicorn

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
