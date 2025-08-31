"""Provide the Api class for frontend-backend communication and file/code operations.

Include methods for managing files, directories, configurations, and test cases, as well
as utilities for interacting with the system and running tasks.
"""

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
from .utils import formatter as fmt
from .watch import Watcher


class Api:
    """JS API bridge for frontend-backend communication and file/code operations."""

    def __init__(
        self,
    ) -> None:
        """Initialize the Api instance."""
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
        """Handle file change events.

        Args:
            path (str): Path of the modified file.

        """
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
            """,
        )
        logger.debug("File change event dispatched.")

    def get_pinned_files(self) -> list[str]:
        """Get a list of pinned files with metadata.

        Returns:
            list[str]: List of pinned file metadata dictionaries.

        """
        pinned_p = user_data_dir / "pinned.txt"
        if not pinned_p.exists():
            return []
        rst = []
        for line in pinned_p.read_text(encoding="utf-8").splitlines():
            stripped_line = line.strip()
            if stripped_line and (path := Path(stripped_line)).exists():
                rst.append(
                    {
                        "name": path.name,
                        "stem": path.stem,
                        "path": str(path),
                        "is_dir": path.is_dir(),
                        "is_file": path.is_file(),
                        "is_symlink": path.is_symlink(),
                        "size": path.stat().st_size,
                        "last_modified": time.strftime(
                            "%Y-%m-%d %H:%M:%S",
                            time.localtime(path.stat().st_mtime),
                        ),
                        "type": "Directory"
                        if path.is_dir()
                        else type_mp.get(path.suffix.lower(), {}).get(
                            "display",
                            "File",
                        ),
                    },
                )
        return rst

    def add_pinned_file(self, path: str) -> None:
        """Add a file to the pinned files list.

        Args:
            path (str): Path to the file to pin.

        """
        pinned_p = user_data_dir / "pinned.txt"
        pinned_files = []
        for line in pinned_p.read_text(encoding="utf-8").splitlines():
            stripped_line = line.strip()
            if stripped_line:
                pinned_files.append(stripped_line)
        if path in pinned_files:
            return
        pinned_files.append(path)
        pinned_p.write_text("\n".join(pinned_files), encoding="utf-8")

    def remove_pinned_file(self, path: str) -> None:
        """Remove a file from the pinned files list.

        Args:
            path (str): Path to the file to unpin.

        """
        pinned_p = user_data_dir / "pinned.txt"
        pinned_files = []
        for line in pinned_p.read_text(encoding="utf-8").splitlines():
            stripped_line = line.strip()
            if stripped_line:
                pinned_files.append(stripped_line)
        if path not in pinned_files:
            return
        pinned_files.remove(path)
        pinned_p.write_text("\n".join(pinned_files), encoding="utf-8")

    def get_disks(self) -> list[dict]:
        """Get a list of available disks or root directories.

        Returns:
            list[dict]: List of disk metadata dictionaries.

        """
        if platform.system() != "Windows":
            return [
                {
                    "name": "/",
                    "stem": "/",
                    "path": "/",
                    "is_dir": True,
                    "is_file": False,
                    "is_symlink": False,
                    "size": 0,
                    "last_modified": "",
                    "type": "Drive",
                },
                {
                    "name": "home",
                    "stem": "home",
                    "path": str(Path.home()),
                    "is_dir": True,
                    "is_file": False,
                    "is_symlink": False,
                    "size": 0,
                    "last_modified": "",
                    "type": "Drive",
                },
            ]
        import ctypes
        import string

        drives = []
        bitmask = ctypes.cdll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drives.append(
                    {
                        "name": letter + ":\\",
                        "stem": letter,
                        "path": letter + ":\\",
                        "is_dir": True,
                        "is_file": False,
                        "is_symlink": False,
                        "size": 0,
                        "last_modified": "",
                        "type": "Drive",
                    },
                )
            bitmask >>= 1
        return drives

    def format_code(self) -> str:
        """Format the currently opened code file using the configured formatter.

        Returns:
            str: The formatted code.

        Raises:
            ValueError: If language or formatter is not supported or active.

        """
        code = self.get_code()
        lang = code.get("type", None)
        if lang not in config.get("programmingLanguages", {}):
            msg = f"Language {lang} is not supported."
            raise ValueError(msg)
        formatter_cfg = config["programmingLanguages"][lang].get("formatter", {})
        if not formatter_cfg.get("active", False):
            msg = f"Formatter for language {lang} is not active."
            raise ValueError(msg)
        if not (cmd := formatter_cfg.get("command", "")).strip():
            msg = f"Formatter command for language {lang} is empty."
            raise ValueError(msg)
        cmd_list = [fmt(c, file_path=self.opened_file) for c in shlex.split(cmd)]
        return subprocess.check_output(
            cmd_list,
            creationflags=subprocess.CREATE_NO_WINDOW
            if platform.system() == "Windows"
            else 0,
            shell=platform.system() == "Windows",
            cwd=self.opened_file.parent,
            text=True,
        )

    def focus(
        self,
    ) -> None:
        """Focus the application window (not implemented)."""
        # TODO(hsn8086): how?

    def get_cpu_count(self) -> tuple[int, int]:
        """Get the number of physical and logical CPU cores.

        Returns:
            tuple[int, int]: (physical cores, logical cores)

        """
        return psutil.cpu_count(logical=False), psutil.cpu_count(logical=True)

    def save_scoll(self, scroll: int) -> None:
        """Save the scroll position.

        Args:
            scroll (int): Scroll position value.

        """
        scroll_p = user_data_dir / "scroll.txt"
        scroll_p.write_text(str(int(scroll)), encoding="utf-8")

    def get_scoll(self) -> int:
        """Get the saved scroll position.

        Returns:
            int: Scroll position value.

        """
        scroll_p = user_data_dir / "scroll.txt"
        if scroll_p.exists():
            return int(scroll_p.read_text(encoding="utf-8"))
        return 0

    def run_task(self, task_id: int, memory_limit: int = 256, timeout: int = 1) -> dict:
        """Run a test case for the opened code file.

        Args:
            task_id (int): The test case ID (1-based).
            memory_limit (int): Memory limit in MB.
            timeout (int): Timeout in seconds.

        Returns:
            dict: Result dictionary with output, status, time, and memory.

        """
        code = self.get_code()
        lang = code.get("type", None)
        if lang not in lang_runners:
            msg = f"Language {lang} is not supported."
            raise ValueError(msg)
        task = self.get_testcase().get("tests", [{}])[task_id - 1]
        inp = task.get("input", "")
        output, status, time, memory = lang_runners[lang](
            self.opened_file,
            inp,
            memory_limit=memory_limit,
            timeout=timeout,
        )
        answer = task.get("answer", "")
        if status == "success":
            status = "success" if task_checker(output, answer) else "failed"
        return {
            "result": output,
            "status": status,
            "time": time,
            "memory": memory,
        }

    def get_config(self) -> dict:
        """Get the merged configuration.

        Returns:
            dict: Merged configuration dictionary.

        """
        return merge_meta(config_meta, config)

    def compile(self) -> str:
        """Compile the currently opened code file.

        Returns:
            str: Compilation result ("success" or error message).

        """
        lang_info = self.get_code().get("type", None)
        if lang_info not in lang_compilers:
            logger.warning(f"Language {lang_info} is not supported for compilation.")
            return "success"
        compile_func = lang_compilers[lang_info]
        try:
            compile_func(self.opened_file)
        except (FileNotFoundError, ValueError) as e:
            return str(e)
        return "success"

    def get_testcase(self) -> dict:
        """Get the test cases for the currently opened file.

        Returns:
            dict: Test case dictionary.

        """
        none_testcase = {
            "name": self.opened_file.name,
            "tests": [],
            "memoryLimit": 1024,
            "timeLimit": 3,
        }
        if self.opened_testcase_file is not None:
            return cph2testcase(
                json.loads(Path(self.opened_testcase_file).read_text(encoding="utf-8")),
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
        """Save the given test case to the appropriate file.

        Args:
            testcase (dict): Test case dictionary.

        """
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
                },
            )
        p.write_text(json.dumps(j, indent=4), encoding="utf-8")

    def set_config(self, id_str: str, value: str | bool | float) -> None:
        """Set a configuration value.

        Args:
            id_str (str): Configuration key (dot-separated for nested).
            value (str | bool | float): Value to set.

        """
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
        """Get the path to the configuration file.

        Returns:
            str: Configuration file path.

        """
        return str(config_p)

    def get_langs(self) -> dict:
        """Get the list of supported languages.

        Returns:
            dict: Language metadata.

        """
        return langs

    def get_port(self) -> int:
        """Get the server port.

        Returns:
            int: Server port number.

        """
        from .web import port

        return port

    def get_code(self) -> dict:
        """Get the code and language info for the opened file.

        Returns:
            dict: Code and language metadata.

        """
        if self.opened_file is None:
            return {"code": "", "type": "text"}
        if not self.opened_file.exists():
            self.opened_file.parent.mkdir(parents=True, exist_ok=True)
            self.opened_file.touch()
        alias = type_mp.get(self.opened_file.suffix.lower(), {}).get("alias", [])
        if id_ := type_mp.get(self.opened_file.suffix.lower(), {}).get("id"):
            alias = [id_, *alias]
        alias = list(set(alias))  # deduplicate
        return {
            "code": self.opened_file.read_text(encoding="utf-8"),
            "type": type_mp.get(self.opened_file.suffix.lower(), {}).get("id", "text"),
            "alias": alias,
        }

    def save_code(self, code: str) -> None:
        """Save code to the currently opened file.

        Args:
            code (str): Code content to save.

        """
        if self.opened_file is None:
            msg = "No file is opened."
            raise ValueError(msg)
        if not self.opened_file.exists():
            self.opened_file.parent.mkdir(parents=True, exist_ok=True)
            self.opened_file.touch()
        if not self.opened_file.is_file():
            msg = f"{self.opened_file} is not a file."
            raise ValueError(msg)
        self.opened_file.write_text(code, encoding="utf-8")

    def set_opened_file(self, path: str) -> None:
        """Set the currently opened file.

        Args:
            path (str): Path to the file to open.

        """
        p = Path(path)
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.touch()
        if not p.is_file():
            msg = f"{p} is not a file."
            raise ValueError(msg)
        self.watcher.create_observer(str(p.parent))
        self.opened_file = p
        self.opened_testcase_file = None
        self.bin_path = None

    def get_opened_file(self) -> str | None:
        """Get the path of the currently opened file.

        Returns:
            str | None: Path to the opened file or None.

        """
        if self.opened_file is None:
            return None
        return str(self.opened_file)

    def set_cwd(self, path: str) -> None:
        """Set the current working directory.

        Args:
            path (str): Path to the directory.

        """
        p = Path(path)
        if not p.is_dir():
            msg = f"{p} is not a directory."
            raise ValueError(msg)
        if not p.exists():
            msg = f"{p} does not exist."
            raise FileNotFoundError(msg)
        self.cwd = p
        if not self.cwd_save_path.exists():
            self.cwd_save_path.parent.mkdir(parents=True, exist_ok=True)
            self.cwd_save_path.touch()
        self.cwd_save_path.write_text(str(self.cwd), encoding="utf-8")

    def get_cwd(self) -> str:
        """Get the current working directory.

        Returns:
            str: Path to the current working directory.

        """
        return str(self.cwd)

    def path_to_uri(self, path: str) -> str:
        """Convert a file path to a URI.

        Args:
            path (str): Absolute file path.

        Returns:
            str: URI string.

        """
        p = Path(path)
        if not p.is_absolute():
            msg = f"{p} is not an absolute path."
            raise ValueError(msg)
        return f"file://{p.as_posix()}"

    def path_ls(self, path: None | str) -> dict:
        """List files in a directory.

        Args:
            path (None | str): Directory path or None for cwd.

        Returns:
            dict: Directory listing and metadata.

        """
        p = Path(path) if path else self.cwd
        rst = []
        for f in p.iterdir():
            try:
                rst.append(self.path_get_info(str(f)))
            except (FileNotFoundError, PermissionError) as e:
                logger.opt(exception=e).warning(f"Failed to get info for {f}: {e}")
        rst.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        return {
            "now_path": str(p),
            "files": rst,
        }

    def path_join(self, *args: str) -> str:
        """Join multiple path components.

        Args:
            *args (str): Path components.

        Returns:
            str: Joined path.

        """
        return str(Path(*args))

    def path_parent(self, path: str) -> str:
        """Get the parent directory of a path.

        Args:
            path (str): File or directory path.

        Returns:
            str: Parent directory path.

        """
        return str(Path(path).parent)

    def path_get_info(self, path: str) -> dict:
        """Get metadata for a file or directory.

        Args:
            path (str): Path to the file or directory.

        Returns:
            dict: Metadata dictionary.

        """
        if not Path(path).exists():
            msg = f"{path} does not exist."
            raise FileNotFoundError(msg)
        p = Path(path)
        return {
            "name": p.name,
            "stem": p.stem,
            "path": str(p),
            "is_dir": p.is_dir(),
            "is_file": p.is_file(),
            "is_symlink": p.is_symlink(),
            "size": p.stat().st_size,
            "last_modified": time.strftime(
                "%Y-%m-%d %H:%M:%S",
                time.localtime(p.stat().st_mtime),
            ),
            "type": "Directory"
            if p.is_dir()
            else type_mp.get(p.suffix.lower(), {}).get("display", "File"),
        }

    def path_get_text(self, path: str) -> str:
        """Get the text content of a file.

        Args:
            path (str): Path to the file.

        Returns:
            str: File content.

        """
        p = Path(path)
        if not p.is_file():
            msg = f"{p} is not a file."
            raise ValueError(msg)
        return p.read_text(encoding="utf-8")

    def path_touch(self, path: str) -> dict:
        """Create an empty file at the given path.

        Args:
            path (str): Path to the file.

        Returns:
            dict: Status and message.

        """
        p = Path(path)
        if p.exists():
            return {"status": "warning", "message": f"{p} already exists."}
        if not p.parent.exists():
            p.parent.mkdir(parents=True, exist_ok=True)

        p.touch()
        return {"status": "success", "message": f"{p} created."}

    def path_mkdir(self, path: str) -> dict:
        """Create a directory at the given path.

        Args:
            path (str): Path to the directory.

        Returns:
            dict: Status and message.

        """
        p = Path(path)
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            return {"status": "success", "message": f"{p} created."}
        return {"status": "warning", "message": f"{p} already exists."}
