import json
import platform
import shlex
import subprocess
import time
from pathlib import Path

import psutil
from loguru import logger

from .config import config, config_p, merge_meta
from .config_meta import config_meta
from .judge import cph2testcase, task_checker
from .langs import lang_compilers, lang_runners, langs, type_mp
from .user_data import user_data_dir
from .utils import format as fmt
from .watch import Watcher


class Api:
    def __init__(
        self,
    ) -> None:
        self.cwd_save_path = user_data_dir / "cwd.txt"
        self.cwd = Path.cwd()
        if self.cwd_save_path.exists():
            p = Path(self.cwd_save_path.read_text(encoding="utf-8"))
            if p.is_dir():
                self.cwd = p

        self.opened_file: Path = self.cwd / ".tie.temp.txt"
        if self.opened_file.exists():
            self.opened_file.unlink()

        self.opened_testcase_file = None
        self.watcher: Watcher = Watcher(self._callback)

    def _callback(self, path: str) -> None:
        logger.debug(f"File modified: {path}")

        if Path(path) != self.opened_file:
            return
        if not Path(path).exists():
            return
        from .web import window

        j = json.dumps({"detail": self.opened_file.read_text(encoding="utf-8")})
        window.run_js(
            f"""window.dispatchEvent(
                    new CustomEvent(
                        'file-changed', {j}
                    )
                );
            """
        )
        logger.debug("File change event dispatched.")

    def format_code(self) -> str:
        code = self.get_code()
        lang = code.get("type", None)
        if lang not in config.get("programmingLanguages", {}):
            raise ValueError(f"Language {lang} is not supported.")
        formatter_cfg = config["programmingLanguages"][lang].get("formatter", {})
        if not formatter_cfg.get("active", False):
            raise ValueError(f"Formatter for language {lang} is not active.")
        if not (cmd := formatter_cfg.get("command", "")).strip():
            raise ValueError(f"Formatter command for language {lang} is empty.")
        cmd_list=[]
        for c in shlex.split(cmd):
            cmd_list.append(fmt(c, file_path=self.opened_file))
        return subprocess.check_output(
            cmd_list,
            creationflags=subprocess.CREATE_NO_WINDOW
            if platform.system() == "Windows"
            else 0,
            shell=True if platform.system() == "Windows" else False,
            cwd=self.opened_file.parent,
            text=True,
        )

    def focus(self) -> None:
        # window.show()
        ...  # todo: how?

    def get_cpu_count(self) -> tuple[int, int]:
        return psutil.cpu_count(logical=False), psutil.cpu_count(logical=True)

    def save_scoll(self, scroll: int) -> None:
        scroll_p = user_data_dir / "scroll.txt"
        scroll_p.write_text(str(int(scroll)), encoding="utf-8")

    def get_scoll(self) -> int:
        scroll_p = user_data_dir / "scroll.txt"
        if scroll_p.exists():
            return int(scroll_p.read_text(encoding="utf-8"))
        return 0

    def run_task(self, task_id: int, memory_limit: int = 256, timeout: int = 1) -> dict:
        code = self.get_code()
        lang = code.get("type", None)
        if lang not in lang_runners:
            raise ValueError(f"Language {lang} is not supported.")
        task = self.get_testcase().get("tests", [{}])[task_id - 1]
        inp = task.get("input", "")
        output, status, time, memory = lang_runners[lang](
            self.opened_file, inp, memory_limit=memory_limit, timeout=timeout
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

    def get_config(self) -> dict:
        return merge_meta(config_meta, config)

    def compile(self) -> str:
        lang_info = self.get_code().get("type", None)
        if lang_info not in lang_compilers:
            logger.warning(f"Language {lang_info} is not supported for compilation.")
            return "success"
        compile_func = lang_compilers[lang_info]
        try:
            compile_func(self.opened_file)
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

    def save_testcase(self, testcase: dict) -> None:
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

    def set_config(self, id_str: str, value: str | bool | float) -> None:
        logger.info(f"Setting config: {id_str} = {value}")
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

    def get_config_path(self) -> str:
        return str(config_p)

    def get_langs(self) -> dict:
        return langs

    def get_port(self) -> int:
        from .web import port

        return port

    def get_code(self) -> dict:
        if self.opened_file is None:
            return {"code": "", "type": "text"}
        if not self.opened_file.exists():
            self.opened_file.parent.mkdir(parents=True, exist_ok=True)
            self.opened_file.touch()
        alias = type_mp.get(self.opened_file.suffix.lower(), {}).get("alias", [])
        if id_ := type_mp.get(self.opened_file.suffix.lower(), {}).get("id"):
            alias.append(id_)
        alias = list(set(alias))  # deduplicate
        return {
            "code": self.opened_file.read_text(encoding="utf-8"),
            "type": type_mp.get(self.opened_file.suffix.lower(), {}).get("id", "text"),
            "alias": alias,
        }

    def save_code(self, code: str) -> None:
        if self.opened_file is None:
            raise ValueError("No file is opened.")
        if not self.opened_file.exists():
            self.opened_file.parent.mkdir(parents=True, exist_ok=True)
            self.opened_file.touch()
        if not self.opened_file.is_file():
            raise ValueError(f"{self.opened_file} is not a file.")
        self.opened_file.write_text(code, encoding="utf-8")

    def set_opened_file(self, path: str) -> None:
        p = Path(path)
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.touch()
        if not p.is_file():
            raise ValueError(f"{p} is not a file.")
        self.watcher.create_observer(str(p.parent))
        self.opened_file = p
        self.opened_testcase_file = None
        self.bin_path = None

    def get_opened_file(self) -> str | None:
        if self.opened_file is None:
            return None
        return str(self.opened_file)

    def set_cwd(self, path: str) -> None:
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

    def path_to_uri(self, path: str) -> str:
        p = Path(path)
        if not p.is_absolute():
            raise ValueError(f"{p} is not an absolute path.")
        return f"file://{p.as_posix()}"

    def path_ls(self, path: None | str) -> dict:
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

    def path_join(self, *args: str) -> str:
        return str(Path(*args))

    def path_parent(self, path: str) -> str:
        return str(Path(path).parent)

    def path_get_info(self, path: str) -> dict:
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

    def path_get_text(self, path: str) -> str:
        p = Path(path)
        if not p.is_file():
            raise ValueError(f"{p} is not a file.")
        return p.read_text(encoding="utf-8")

    def path_touch(self, path: str) -> dict:
        p = Path(path)
        if p.exists():
            return {"status": "warning", "message": f"{p} already exists."}
        if not p.parent.exists():
            p.parent.mkdir(parents=True, exist_ok=True)

        p.touch()
        return {"status": "success", "message": f"{p} created."}

    def path_mkdir(self, path: str) -> dict:
        p = Path(path)
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            return {"status": "success", "message": f"{p} created."}
        else:
            return {"status": "warning", "message": f"{p} already exists."}
