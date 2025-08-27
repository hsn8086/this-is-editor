import asyncio
import json
import threading
from pydantic import BaseModel
import webview
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from a2wsgi import ASGIMiddleware
from pathlib import Path
import time
import appdirs
import webview.state
from runner import compile_c_cpp_builder, run_c_cpp, run_python
import subprocess
from functools import partial
import psutil
import platform

app = FastAPI()
should_exit = False


@app.websocket("/lsp/{lang:str}")
async def websocket_endpoint(websocket: WebSocket, lang: str):
    if should_exit:
        await websocket.close()
        return
    # 使用 await 获取 Process 对象
    p = subprocess.Popen(
        type_mp.get(lang, {}).get("lsp", []),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    await websocket.accept()
    print(f"WebSocket connection established for language: {lang}")

    async def ws_handler():
        try:
            while True:
                data = (await websocket.receive_text()).encode("utf-8")
                # p.stdin.write(f"Content-Length: {len(data)}\r\n\r\n".encode("utf-8"))
                await asyncio.to_thread(
                    p.stdin.write,
                    f"Content-Length: {len(data)}\r\n\r\n".encode("utf-8"),
                )
                # p.stdin.write(data)
                await asyncio.to_thread(p.stdin.write, data)
                await asyncio.to_thread(p.stdin.flush)
        except Exception as e:
            print(f"WebSocket handler error: {e}")
            # 确保 WebSocket 关闭时不会重复调用
            if not websocket.client_state.name == "DISCONNECTED":
                await websocket.close()

    async def p_handler():
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

    async def p_err_handler():
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


app.mount("/", StaticFiles(directory="web", html=True), name="web")

app_prob_recver = FastAPI()


class Problem(BaseModel):
    name: str
    group: str | None
    url: str | None
    interactive: bool | None
    memoryLimit: int | None
    timeLimit: int | None
    tests: list[dict] = []
    testType: str | None
    input: dict | None
    output: dict | None
    languages: dict | None
    batch: dict | None


@app_prob_recver.post("/")
async def receive_problem(problem: Problem):
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
        f"window.dispatchEvent(new CustomEvent('problem-received', {{ detail: {json.dumps({'name': problem.name, 'tests': tests})} }}));"
    )

    return {"status": "success", "message": f"Problem {problem.name} received."}


# py_lsp=["ruff","server"]
# py_lsp = ["uv", "run", "pylsp"]
langs = [
    {
        "id": "python",
        "display": "Python Source",
        "lsp": ["uv", "run", "pylsp"],
        # "lsp": ["ruff", "server"],
        # "lsp": ["uv", "run", "pyright-langserver", "--stdio"],
        "suffix": [".py"],
        "alias": ["py", "Python", "python3"],
    },
    {
        "id": "cpp",
        "display": "C++ Source",
        "lsp": ["clangd"],
        "suffix": [".cpp", ".cxx", ".cc", ".c++", ".hpp"],
        "alias": ["C++", "c++", "c_cpp"],
    },
]
lang_runners = {
    "python": partial(run_python, version="python"),
    "cpp": partial(run_c_cpp),
    "c": partial(
        run_c_cpp,
    ),
}
lang_compilers = {
    "cpp": compile_c_cpp_builder("gnu++23", "c++", ["-O2", "-Wall", "-Wextra"]),
    "c": compile_c_cpp_builder("gcc", "c", ["-O2", "-Wall", "-Wextra"]),
}
type_mp = {
    # ".py": {"display": "Python Source", "id": "python", "lsp": py_lsp},
    # "python": {
    #     "display": "Python Source",
    #     "id": "python",
    #     "lsp": py_lsp,
    # },
}

for lang in langs:
    for key in lang["suffix"] + lang.get("alias", []):
        type_mp[key] = lang
    type_mp[lang["id"]] = lang


class ConfigItem(BaseModel):
    display: str
    value: str | bool | int | float


"""
  fixedWidthGutter: true,
  fadeFoldWidgets: true,
  displayIndentGuides: false,
  highlightIndentGuides: true,
  highlightGutterLine: true,
  highlightActiveLine: true,
  highlightSelectedWord: true,
  cursorStyle: "smooth",
  tabSize: 4,
  tooltipFollowsMouse: true,
  foldStyle: "markbeginend",
"""

config_meta = {
    "editor": {
        "aceMain": {
            "fontSize": {"display": "Font Size"},
            "fontFamily": {"display": "Font Family"},
            "enableBasicAutocompletion": {"display": "Autocompletion"},
            "enableSnippets": {"display": "Enable Snippets"},
            "enableLiveAutocompletion": {"display": "Live Autocompletion"},
            "animatedScroll": {"display": "Animated Scroll"},
            "scrollPastEnd": {"display": "Scroll Past End"},
            "showPrintMargin": {"display": "Show Print Margin"},
            "fixedWidthGutter": {"display": "Fixed Width Gutter"},
            "fadeFoldWidgets": {"display": "Fade Fold Widgets"},
            "displayIndentGuides": {"display": "Display Indent Guides"},
            "highlightIndentGuides": {"display": "Highlight Indent Guides"},
            "highlightGutterLine": {"display": "Highlight Gutter Line"},
            "highlightActiveLine": {"display": "Highlight Active Line"},
            "highlightSelectedWord": {"display": "Highlight Selected Word"},
            "cursorStyle": {
                "display": "Cursor Style",
                "enum": ["smooth", "slim", "wide", "ace", "smoothwide"],
            },
            "tabSize": {"display": "Tab Size"},
            "tooltipFollowsMouse": {"display": "Tooltip Follows Mouse"},
            "foldStyle": {
                "display": "Fold Style",
                "enum": ["markbeginend", "manual", "markbegin"],
            },
        },
        "tie": {
            "theme": {"display": "Theme", "enum": ["light", "dark", "system"]},
        },
    }
}
config = {
    "editor": {
        "aceMain": {
            "fontSize": 14,
            "fontFamily": "Fira Code, monospace",
            "enableBasicAutocompletion": True,
            "enableSnippets": False,
            "enableLiveAutocompletion": True,
            "animatedScroll": True,
            "scrollPastEnd": True,
            "showPrintMargin": False,
            "fixedWidthGutter": True,
            "fadeFoldWidgets": True,
            "displayIndentGuides": False,
            "highlightIndentGuides": True,
            "highlightGutterLine": True,
            "highlightActiveLine": True,
            "highlightSelectedWord": True,
            "cursorStyle": "smooth",
            "tabSize": 4,
            "tooltipFollowsMouse": True,
            "foldStyle": "markbeginend",
        },
        "tie": {"theme": "system"},
    },
}


def merge(a: dict, b: dict) -> dict:
    for key, value in b.items():
        if isinstance(value, dict) and key in a and isinstance(a[key], dict):
            a[key] = merge(a[key], value)
        else:
            a[key] = value
    return a


def merge_meta(cfg_meta: dict, config: dict) -> dict:
    merged = {}
    for key, value in cfg_meta.items():
        if "display" in value:
            merged[key] = {"value": config.get(key, None)}
            merged[key].update(value)
        else:
            merged[key] = merge_meta(value, config.get(key, {}))
    return merged


user_config_dir = Path(appdirs.user_config_dir("this_is_editor", "small-hsn"))
user_data_dir = Path(appdirs.user_data_dir("this_is_editor", "small-hsn"))
if not Path(user_config_dir).exists():
    Path(user_config_dir).mkdir(parents=True, exist_ok=True)
config_p = user_config_dir / "config.json"
if not config_p.exists():
    config_p.write_text(json.dumps(config, indent=4), encoding="utf-8")

config = merge(config, json.loads(config_p.read_text(encoding="utf-8")))


def task_checker(ouput: str, answer: str):
    oup = filter(bool, ouput.split())
    ans = filter(bool, answer.split())
    for i, j in zip(oup, ans):
        if i.strip() != j.strip():
            return False
    return True


def cph2testcase(cph_json: dict) -> dict:
    tests = []
    for i, v in enumerate(cph_json.get("tests", []), start=1):
        tests.append(
            {
                "id": i,
                "input": v.get("input", ""),
                "answer": v.get("output", ""),
            }
        )
    return {
        "name": cph_json.get("name", "Unnamed"),
        "tests": tests,
        "memoryLimit": cph_json.get("memoryLimit", 1024),
        "timeLimit": cph_json.get("timeLimit", 3000) / 1000,
    }


class Api:
    def __init__(self):
        self.cwd_save_path = user_data_dir / "cwd.txt"
        if self.cwd_save_path.exists():
            self.cwd = Path(self.cwd_save_path.read_text(encoding="utf-8"))
        else:
            self.cwd = Path.cwd()
        if not self.cwd.is_dir():
            self.cwd = Path.cwd()

        self.opened_file: Path = self.cwd / ".tie.temp.txt"
        if self.opened_file.exists():
            self.opened_file.unlink()
        self.opened_testcase_file = None
        self.bin_path = None

    def focus(self):
        # window.show()
        ...  # todo: how?

    def get_cpu_count(self):
        return psutil.cpu_count(logical=False), psutil.cpu_count(logical=True)

    def save_scoll(self, scroll: int):
        scroll_p = user_data_dir / "scroll.txt"
        scroll_p.write_text(str(int(scroll)), encoding="utf-8")

    def get_scoll(self):
        scroll_p = user_data_dir / "scroll.txt"
        if scroll_p.exists():
            return int(scroll_p.read_text(encoding="utf-8"))
        return 0

    def run_task(self, task_id: int, memory_limit: int = 256, timeout: int = 1):
        if self.bin_path is None:
            oup = self.compile()
            if oup != "success":
                return {
                    "result": oup,
                    "status": "compile_error",
                    "time": 0,
                    "memory": 0,
                }
        code = self.get_code()
        lang = code.get("type", None)
        if lang not in lang_runners:
            raise ValueError(f"Language {lang} is not supported.")
        task = self.get_testcase().get("tests", [{}])[task_id - 1]
        inp = task.get("input", "")
        output, status, time, memory = lang_runners[lang](
            self.bin_path, inp, memory_limit=memory_limit, timeout=timeout
        )
        answer = task.get("answer", "")
        if status == "success":
            if task_checker(output, answer):
                status = "success"
            else:
                status = "failed"
        return {
            "result": output,
            "status": status,
            "time": time,
            "memory": memory,
        }

    def get_config(self):
        # print(merge_meta(config_meta, config))
        return merge_meta(config_meta, config)

    def compile(self):
        lang_info = self.get_code().get("type", None)
        if lang_info not in lang_compilers:
            print(f"Language {lang_info} is not supported for compilation.")
            self.bin_path = self.opened_file
            return "success"
        compile_func = lang_compilers[lang_info]
        try:
            self.bin_path = compile_func(self.opened_file)
        except Exception as e:
            return str(e)
        return "success"

    def get_testcase(self) -> dict:
        none_testcase = {
            "name": self.opened_file.name,
            "tests": [],
            "memoryLimit": 1024,
            "timeLimit": 3,
        }
        if self.opened_testcase_file is not None:
            return cph2testcase(
                json.loads(Path(self.opened_testcase_file).read_text(encoding="utf-8"))
            )
        cph_floder_p = self.opened_file.parent / ".cph"
        if not cph_floder_p.exists():
            return none_testcase
        for p in cph_floder_p.iterdir():
            if p.name.startswith("." + self.opened_file.name + "_") or p.name == (
                "." + self.opened_file.name + ".prob"
            ):
                self.opened_testcase_file = p
                return cph2testcase(json.loads(p.read_text(encoding="utf-8")))
        return none_testcase

    def save_testcase(self, testcase: dict):
        if self.opened_testcase_file is None:
            cph_floder_p = self.opened_file.parent / ".cph"
            cph_floder_p.mkdir(parents=True, exist_ok=True)
            self.opened_testcase_file = cph_floder_p / (
                "." + self.opened_file.name + ".prob"
            )
        p = self.opened_testcase_file
        j = {
            "name": testcase.get("name", self.opened_file.name),
            "memoryLimit": testcase.get("memoryLimit", 1024),
            "timeLimit": testcase.get("timeLimit", 3) * 1000,
            "tests": [],
            "local": True,
            "group": "local",
            "srcPath": self.opened_file.name,
            "url": str(self.opened_file),
            "interactive": False,
        }
        for test in testcase.get("tests", []):
            j["tests"].append(
                {
                    "id": test.get("id", int(time.time() * 1000)),
                    "input": test.get("input", ""),
                    "output": test.get("answer", ""),
                }
            )
        p.write_text(json.dumps(j, indent=4), encoding="utf-8")

    def set_config(self, id_str: str, value: str | bool | int | float):
        print(f"Setting config: {id_str} = {value}")
        id_str = id_str.strip()
        if "." in id_str:
            keys = id_str.split(".")
            cfg = config
            for key in keys[:-1]:
                cfg = cfg.get(key, {})
            cfg[keys[-1]] = value
        else:
            config[id_str] = value
        config_p.write_text(json.dumps(config, indent=4), encoding="utf-8")

    def get_langs(self):
        return langs

    def get_port(self):
        return port

    def get_code(self):
        if self.opened_file is None:
            return {"code": "", "type": "text"}
        if not self.opened_file.exists():
            self.opened_file.parent.mkdir(parents=True, exist_ok=True)
            self.opened_file.touch()
        print(type_mp.get(self.opened_file.suffix.lower(), {}).get("id", "text"))
        alias = type_mp.get(self.opened_file.suffix.lower(), {}).get("alias", [])
        if id_ := type_mp.get(self.opened_file.suffix.lower(), {}).get("id"):
            alias.append(id_)
        alias = list(set(alias))  # 去重
        return {
            "code": self.opened_file.read_text(encoding="utf-8"),
            "type": type_mp.get(self.opened_file.suffix.lower(), {}).get("id", "text"),
            "alias": alias,
        }

    def save_code(self, code: str):
        if self.opened_file is None:
            raise ValueError("No file is opened.")
        if not self.opened_file.exists():
            self.opened_file.parent.mkdir(parents=True, exist_ok=True)
            self.opened_file.touch()
        if not self.opened_file.is_file():
            raise ValueError(f"{self.opened_file} is not a file.")
        self.opened_file.write_text(code, encoding="utf-8")

    def set_opened_file(self, path: str):
        p = Path(path)
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.touch()
        if not p.is_file():
            raise ValueError(f"{p} is not a file.")

        self.opened_file = p
        self.opened_testcase_file = None
        self.bin_path = None

    def get_opened_file(self) -> str | None:
        if self.opened_file is None:
            return None
        return str(self.opened_file)

    def set_cwd(self, path: str):
        p = Path(path)
        if not p.is_dir():
            raise ValueError(f"{p} is not a directory.")
        if not p.exists():
            raise FileNotFoundError(f"{p} does not exist.")
        self.cwd = p
        if not self.cwd_save_path.exists():
            self.cwd_save_path.parent.mkdir(parents=True, exist_ok=True)
            self.cwd_save_path.touch()
        self.cwd_save_path.write_text(str(self.cwd), encoding="utf-8")

    def get_cwd(self) -> str:
        return str(self.cwd)

    def path_to_uri(self, path: str):
        p = Path(path)
        if not p.is_absolute():
            raise ValueError(f"{p} is not an absolute path.")
        return f"file://{p.as_posix()}"

    def path_ls(self, path: None | str):
        if path:
            p = Path(path)
        else:
            p = self.cwd
        rst = []
        for f in p.iterdir():
            rst.append(self.path_get_info(str(f)))
        rst.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        return {
            "now_path": str(p),
            "files": rst,
        }

    def path_join(self, *args):
        return str(Path(*args))

    def path_parent(self, path: str):
        return str(Path(path).parent)

    def path_get_info(self, path: str):
        p = Path(path)
        return {
            "name": p.name,
            "is_dir": p.is_dir(),
            "is_file": p.is_file(),
            "is_symlink": p.is_symlink(),
            "size": p.stat().st_size,
            "last_modified": time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(p.stat().st_mtime)
            ),
            "type": "Directory"
            if p.is_dir()
            else type_mp.get(p.suffix.lower(), {}).get("display", "File"),
        }

    def path_get_text(self, path: str):
        p = Path(path)
        if not p.is_file():
            raise ValueError(f"{p} is not a file.")
        return p.read_text(encoding="utf-8")

    def path_touch(self, path: str):
        p = Path(path)
        if p.exists():
            return {"status": "warning", "message": f"{p} already exists."}
        if not p.parent.exists():
            p.parent.mkdir(parents=True, exist_ok=True)

        p.touch()
        return {"status": "success", "message": f"{p} created."}

    def path_mkdir(self, path: str):
        p = Path(path)
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            return {"status": "success", "message": f"{p} created."}
        else:
            return {"status": "warning", "message": f"{p} already exists."}


def get_free_port():
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


port = get_free_port()


def start_server():
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


server, thread, server_recver, thread_recver = start_server()
window = webview.create_window(
    "TIE",
    f"http://127.0.0.1:{port}",
    js_api=Api(),
    width=800,
    height=600,
)

if platform.system() == "Windows":
    webview.start(window, gui="qt")
else:
    webview.start(window)

should_exit = True
server.should_exit = True
server_recver.should_exit = True

print("Shutting down server...")
thread.join()
thread_recver.join()
print("Server stopped.")
