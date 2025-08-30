import asyncio
import json
import platform
import shlex
import subprocess
import sys
import threading
import time
from pathlib import Path

import uvicorn
import webview
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from loguru import logger

from .js_api import Api
from .langs import type_mp
from .models import Problem


def get_free_port() -> int:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


port = get_free_port()

app = FastAPI()
should_exit = False


@app.websocket("/lsp/{lang:str}")
async def websocket_endpoint(websocket: WebSocket, lang: str) -> None:
    if should_exit:
        await websocket.close()
        return
    cmd = type_mp.get(lang, {}).get("lsp", {}).get("command", "")
    if not cmd:
        logger.error(f"No LSP command found for language: {lang}")
        await websocket.close()
        return
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    try:
        p = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
            if platform.system() == "Windows"
            else 0,
            shell=True if platform.system() == "Windows" else 0,
        )
    except Exception as e:
        logger.error(f"Failed to start LSP for language: {lang}")
        logger.opt(exception=e).error(f"Command: {' '.join(cmd)}")
        await websocket.close()
        return

    time.sleep(0.1)
    if p.poll() is not None:
        logger.error(f"Failed to start LSP for language: {lang}")
        logger.error(p.stderr.read().decode("utf-8"))
        await websocket.close()
        return

    await websocket.accept()
    logger.info(f"WebSocket connection established for language: {lang}")

    async def ws_handler() -> None:
        try:
            while True:
                data = (await websocket.receive_text()).encode("utf-8")
                await asyncio.to_thread(
                    p.stdin.write,
                    f"Content-Length: {len(data)}\r\n\r\n".encode(),
                )
                await asyncio.to_thread(p.stdin.write, data)
                await asyncio.to_thread(p.stdin.flush)
        except Exception as e:
            logger.opt(exception=e).error(f"{lang} LS websocket error")
            if not websocket.client_state.name == "DISCONNECTED":
                await websocket.close()

    async def p_handler() -> None:
        buffer = b""
        try:
            while True:
                # 你就说他是不是能跑!
                await asyncio.to_thread(p.stdout.read, 16)
                while b"\r\n\r\n" not in buffer:
                    buffer += p.stdout.read(1)

                header_end = buffer.find(b"\r\n\r\n")

                if header_end == -1:
                    continue

                content_length = int(
                    buffer[:header_end].strip().split(b"\n")[0].strip().split()[-1]
                )
                buffer = buffer[header_end + 4 :]  # skip \r\n\r\n
                while len(buffer) < content_length:
                    chunk = await asyncio.to_thread(
                        p.stdout.read, content_length - len(buffer)
                    )
                    buffer += chunk

                content = buffer[:content_length]
                buffer = buffer[content_length:]  # keep remaining data for next
                # check content
                if not content:
                    continue
                await websocket.send_text(content.decode("utf-8"))

        except Exception as e:
            logger.opt(exception=e).error(f"{lang} LS process error")
            # make sure websocket is closed
            if not websocket.client_state.name == "DISCONNECTED":
                await websocket.close()

    async def p_err_handler() -> None:
        try:
            while True:
                error_chunk = await asyncio.to_thread(p.stderr.readline)
                if not error_chunk:
                    break
                logger.error(
                    f"{lang} LSP stderr: {error_chunk.decode('utf-8').strip()}"
                )
        except Exception as e:
            logger.opt(exception=e).error(f"{lang} LS process stderr error")

    async with asyncio.TaskGroup() as tg:
        task_ws = tg.create_task(ws_handler())
        task_p = tg.create_task(p_handler())
        task_perr = tg.create_task(p_err_handler())

        while True:
            await asyncio.sleep(1)
            if should_exit:
                task_p.cancel()
                task_ws.cancel()
                task_perr.cancel()
                p.terminate()
                p.wait()
                logger.info(f"WebSocket connection closed for language: {lang}")
                return
            if task_p.done() or task_ws.done() or task_perr.done():
                return


app.mount("/", StaticFiles(directory=Path(__file__).parent / "web", html=True), name="web")

app_prob_recver = FastAPI()


@app_prob_recver.post("/")
async def receive_problem(problem: Problem) -> dict:
    logger.info(f"Received problem: {problem.name} with {len(problem.tests)} tests.")
    tests = []
    for i, test in enumerate(problem.tests, start=1):
        tests.append(
            {
                "id": i,
                "input": test.get("input", ""),
                "answer": test.get("output", ""),
            }
        )
        print(tests[-1])

    window.run_js(
        f"""
        window.dispatchEvent(
            new CustomEvent(
                'problem-received', 
                {{ detail: {json.dumps({"name": problem.name, "tests": tests})} }}
            )
        );
        """
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
    uvicorn.Server, threading.Thread, uvicorn.Server, threading.Thread
]:
    import uvicorn

    logger.info(f"Starting server on port {port}")
    conf = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="info", workers=8)
    server = uvicorn.Server(conf)
    conf_recver = uvicorn.Config(
        app_prob_recver, host="127.0.0.1", port=10043, log_level="info", workers=1
    )
    server_recver = uvicorn.Server(conf_recver)
    thread = threading.Thread(target=server.run, daemon=True)
    thread_recver = threading.Thread(target=server_recver.run, daemon=True)
    thread_recver.start()
    thread.start()
    return server, thread, server_recver, thread_recver
