import asyncio
import json
import platform
import subprocess
import sys
import threading
import time
from pathlib import Path

import uvicorn
import webview
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles

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
    # 使用 await 获取 Process 对象

    p = subprocess.Popen(
        type_mp.get(lang, {}).get("lsp", []),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW
        if platform.system() == "Windows"
        else 0,
        shell=True if platform.system() == "Windows"
        else 0,
    )

    time.sleep(0.1)
    if p.poll() is not None:
        print(f"Failed to start LSP for language: {lang}")
        print(p.stderr.read().decode("utf-8"))  
        await websocket.close()
        return
    await websocket.accept()
    print(f"WebSocket connection established for language: {lang}")

    async def ws_handler() -> None:
        try:
            while True:
                data = (await websocket.receive_text()).encode("utf-8")
                # p.stdin.write(f"Content-Length: {len(data)}\r\n\r\n".encode("utf-8"))
                await asyncio.to_thread(
                    p.stdin.write,
                    f"Content-Length: {len(data)}\r\n\r\n".encode(),
                )
                # p.stdin.write(data)
                await asyncio.to_thread(p.stdin.write, data)
                await asyncio.to_thread(p.stdin.flush)
        except Exception as e:
            print(f"WebSocket handler error: {e}")
            # 确保 WebSocket 关闭时不会重复调用
            if not websocket.client_state.name == "DISCONNECTED":
                await websocket.close()

    async def p_handler() -> None:
        buffer = b""
        try:
            while True:
                # chunk = await p.stdout.read(1024)
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
                buffer = buffer[header_end + 4 :]  # 跳过头部
                while len(buffer) < content_length:
                    # chunk = await p.stdout.read(content_length - len(buffer))
                    chunk = await asyncio.to_thread(
                        p.stdout.read, content_length - len(buffer)
                    )
                    buffer += chunk

                content = buffer[:content_length]
                buffer = buffer[content_length:]  # 保留剩余数据
                # check content
                if not content:
                    continue
                await websocket.send_text(content.decode("utf-8"))

        except Exception as e:
            print(f"WebSocket handler error: {e}")
            # 确保 WebSocket 关闭时不会重复调用
            if not websocket.client_state.name == "DISCONNECTED":
                await websocket.close()

    async def p_err_handler() -> None:
        try:
            while True:
                # error_chunk = await p.stderr.read(1024)
                error_chunk = await asyncio.to_thread(p.stderr.readline)
                if not error_chunk:
                    break
                print(f"Error from LSP: {error_chunk.decode('utf-8')}")
        except Exception as e:
            print(f"Error handler error: {e}")

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
                print(f"WebSocket connection closed for language: {lang}")
                return
            if task_p.done() or task_ws.done() or task_perr.done():
                return


if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    res_path = Path(sys._MEIPASS)
else:
    res_path = Path.cwd()

app.mount("/", StaticFiles(directory=res_path / "web", html=True), name="web")

app_prob_recver = FastAPI()


@app_prob_recver.post("/")
async def receive_problem(problem: Problem) -> dict:
    print(f"Received problem: {problem.name} with {len(problem.tests)} tests.")
    print(problem)
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
        "window.dispatchEvent(new CustomEvent('problem-received', "
        f"{{ detail: {json.dumps({'name': problem.name, 'tests': tests})} }}));"
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

    print(f"Starting server on port {port}...")
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
