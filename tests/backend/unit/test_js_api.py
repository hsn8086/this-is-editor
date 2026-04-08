"""Unit tests for the js_api module.

This module contains P0 level tests for the Api class, focusing on:
- get_code/save_code functionality
- get_config/set_config functionality
- path_* operations
- run_task/compile functionality
- Exception handling
"""

import json
from collections.abc import Callable, Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pysrc.js_api import Api


class StubWatcher:
    """A lightweight stub for Watcher to avoid file system operations in tests."""

    def __init__(self, callback: Callable[[str], None] | None = None) -> None:
        """Initialize the StubWatcher.

        Args:
            callback: Optional callback function for file change events.

        """
        self._callback = callback

    def create_observer(self, path: str) -> None:
        """Stub method - does nothing."""


@pytest.fixture
def api_with_tmp_path(tmp_path: Path) -> Generator[Api, None, None]:
    """Create an Api instance with tmp_path for user_data and cwd."""
    user_data = tmp_path / "data"
    user_data.mkdir(parents=True, exist_ok=True)

    # Create a dummy cwd.txt to prevent reading non-existent file
    cwd_file = user_data / "cwd.txt"
    cwd_file.write_text(str(tmp_path), encoding="utf-8")

    with patch("pysrc.js_api.user_data_dir", user_data):
        with patch("pysrc.js_api.Watcher", StubWatcher):
            # Patch Path.cwd to return tmp_path
            with patch("pysrc.js_api.Path.cwd", return_value=tmp_path):
                api = Api()
                api.cwd = tmp_path
                yield api


@pytest.fixture
def api_with_file(tmp_path: Path, api_with_tmp_path: Api) -> Api:
    """Create an Api with a test file already opened."""
    test_file = tmp_path / "test.py"
    test_file.write_text("print('hello')", encoding="utf-8")
    api_with_tmp_path.opened_file = test_file
    return api_with_tmp_path


class TestApiGetCode:
    """Tests for the get_code method."""

    def test_get_code_with_existing_file(self, api_with_file: Api) -> None:
        """Test get_code returns correct data for existing file."""
        result = api_with_file.get_code()

        assert result["code"] == "print('hello')"
        assert result["type"] == "python"

    def test_get_code_with_nonexistent_file(
        self,
        tmp_path: Path,
        api_with_tmp_path: Api,
    ) -> None:
        """Test get_code creates file if it doesn't exist."""
        test_file = tmp_path / "new_file.py"
        api_with_tmp_path.opened_file = test_file

        # File doesn't exist, get_code should create it
        result = api_with_tmp_path.get_code()

        # Check file was created
        assert test_file.exists()
        assert result["code"] == ""
        assert result["type"] == "python"

    def test_get_code_with_none_opened_file(self, api_with_tmp_path: Api) -> None:
        """Test get_code returns default values when no file is opened."""
        api_with_tmp_path.opened_file = None  # type: ignore[assignment]
        result = api_with_tmp_path.get_code()

        assert result["code"] == ""
        assert result["type"] == "text"


class TestApiSaveCode:
    """Tests for the save_code method."""

    def test_save_code_success(self, tmp_path: Path, api_with_tmp_path: Api) -> None:
        """Test save_code writes content to file."""
        test_file = tmp_path / "test.py"
        test_code = "print('saved')"

        api_with_tmp_path.opened_file = test_file
        api_with_tmp_path.save_code(test_code)

        assert test_file.read_text() == test_code

    def test_save_code_with_none_opened_file(self, api_with_tmp_path: Api) -> None:
        """Test save_code raises ValueError when no file is opened."""
        api_with_tmp_path.opened_file = None  # type: ignore[assignment]

        with pytest.raises(ValueError, match="No file is opened"):
            api_with_tmp_path.save_code("some code")

    def test_save_code_with_non_file_path(
        self,
        tmp_path: Path,
        api_with_tmp_path: Api,
    ) -> None:
        """Test save_code raises ValueError when path is not a file."""
        test_dir = tmp_path / "not_a_file"
        test_dir.mkdir()

        api_with_tmp_path.opened_file = test_dir

        with pytest.raises(ValueError, match="is not a file"):
            api_with_tmp_path.save_code("some code")


class TestApiConfig:
    """Tests for get_config and set_config methods."""

    def test_get_config_returns_merged(self, api_with_tmp_path: Api) -> None:
        """Test get_config returns merged configuration."""
        with patch("pysrc.js_api.merge_meta") as mock_merge:
            with patch("pysrc.js_api.config_meta") as mock_meta:
                with patch("pysrc.js_api.config") as mock_config:
                    mock_merge.return_value = {"key": "value"}

                    result = api_with_tmp_path.get_config()

        assert result == {"key": "value"}
        mock_merge.assert_called_once_with(mock_meta, mock_config)

    def test_set_config_simple_key(
        self,
        tmp_path: Path,
        api_with_tmp_path: Api,
    ) -> None:
        """Test set_config with simple key."""
        config_file = tmp_path / "config.json"

        with patch("pysrc.js_api.config_p", config_file):
            with patch("pysrc.js_api.config", {}):
                api_with_tmp_path.set_config("testKey", "testValue")

        assert config_file.exists()

    def test_set_config_nested_key(
        self,
        tmp_path: Path,
        api_with_tmp_path: Api,
    ) -> None:
        """Test set_config with nested key using dot notation."""
        test_config: dict = {"outer": {"inner": "original"}}
        config_file = tmp_path / "config.json"

        with patch("pysrc.js_api.config_p", config_file):
            with patch("pysrc.js_api.config", test_config):
                api_with_tmp_path.set_config("outer.inner", "newValue")

        assert test_config["outer"]["inner"] == "newValue"


class TestApiPathOperations:
    """Tests for path_* methods."""

    def test_path_ls(self, tmp_path: Path, api_with_tmp_path: Api) -> None:
        """Test path_ls lists directory contents."""
        (tmp_path / "file1.txt").touch()
        (tmp_path / "file2.py").touch()
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        result = api_with_tmp_path.path_ls(None)

        assert result["now_path"] == str(tmp_path)
        # Contains: data (from fixture), subdir, file1.txt, file2.py
        assert len(result["files"]) == 4

    def test_path_join(self, api_with_tmp_path: Api) -> None:
        """Test path_join joins path components."""
        result = api_with_tmp_path.path_join("dir", "subdir", "file.txt")

        assert result == str(Path("dir") / "subdir" / "file.txt")

    def test_path_parent(self, api_with_tmp_path: Api) -> None:
        """Test path_parent returns parent directory."""
        result = api_with_tmp_path.path_parent("/home/user/file.txt")

        assert result == "/home/user"

    def test_path_get_info(self, tmp_path: Path, api_with_tmp_path: Api) -> None:
        """Test path_get_info returns file metadata."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')", encoding="utf-8")

        result = api_with_tmp_path.path_get_info(str(test_file))

        assert result["name"] == "test.py"
        assert result["stem"] == "test"
        assert result["is_file"] is True

    def test_path_get_info_raises_on_nonexistent(
        self,
        tmp_path: Path,
        api_with_tmp_path: Api,
    ) -> None:
        """Test path_get_info raises FileNotFoundError for nonexistent path."""
        nonexistent = tmp_path / "nonexistent.txt"

        with pytest.raises(FileNotFoundError):
            api_with_tmp_path.path_get_info(str(nonexistent))

    def test_path_get_text(self, tmp_path: Path, api_with_tmp_path: Api) -> None:
        """Test path_get_text returns file content."""
        test_file = tmp_path / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content, encoding="utf-8")

        result = api_with_tmp_path.path_get_text(str(test_file))

        assert result == test_content

    def test_path_get_text_raises_on_directory(
        self,
        tmp_path: Path,
        api_with_tmp_path: Api,
    ) -> None:
        """Test path_get_text raises ValueError for directory."""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()

        with pytest.raises(ValueError, match="is not a file"):
            api_with_tmp_path.path_get_text(str(test_dir))

    def test_path_to_uri(self, api_with_tmp_path: Api) -> None:
        """Test path_to_uri converts path to URI."""
        result = api_with_tmp_path.path_to_uri("/home/user/file.txt")

        assert result == "file:///home/user/file.txt"

    def test_path_to_uri_raises_on_relative(self, api_with_tmp_path: Api) -> None:
        """Test path_to_uri raises ValueError for relative path."""
        with pytest.raises(ValueError, match="is not an absolute path"):
            api_with_tmp_path.path_to_uri("relative/path.txt")

    def test_path_touch(self, tmp_path: Path, api_with_tmp_path: Api) -> None:
        """Test path_touch creates empty file."""
        new_file = tmp_path / "new_file.txt"

        result = api_with_tmp_path.path_touch(str(new_file))

        assert result["status"] == "success"
        assert new_file.exists()

    def test_path_touch_existing_file(
        self,
        tmp_path: Path,
        api_with_tmp_path: Api,
    ) -> None:
        """Test path_touch returns warning for existing file."""
        existing_file = tmp_path / "existing.txt"
        existing_file.touch()

        result = api_with_tmp_path.path_touch(str(existing_file))

        assert result["status"] == "warning"

    def test_path_mkdir(self, tmp_path: Path, api_with_tmp_path: Api) -> None:
        """Test path_mkdir creates directory."""
        new_dir = tmp_path / "new_dir"

        result = api_with_tmp_path.path_mkdir(str(new_dir))

        assert result["status"] == "success"
        assert new_dir.exists()

    def test_path_rename_file_moves_related_testcase(
        self,
        tmp_path: Path,
        api_with_tmp_path: Api,
    ) -> None:
        """Test path_rename migrates testcase data for renamed files."""
        source = tmp_path / "old.py"
        source.write_text("print('old')", encoding="utf-8")
        cph_file = tmp_path / ".cph" / ".old.py.prob"
        cph_file.parent.mkdir(parents=True, exist_ok=True)
        cph_file.write_text(
            json.dumps(
                {
                    "name": "old.py",
                    "tests": [],
                    "memoryLimit": 1000,
                    "timeLimit": 1000,
                    "srcPath": "old.py",
                    "url": str(source),
                },
            ),
            encoding="utf-8",
        )

        result = api_with_tmp_path.path_rename(
            str(source),
            str(tmp_path / "new.py"),
        )

        migrated = tmp_path / ".cph" / ".new.py.prob"
        assert result["status"] == "success"
        assert not source.exists()
        assert migrated.exists()
        migrated_data = json.loads(migrated.read_text(encoding="utf-8"))
        assert migrated_data["name"] == "new.py"
        assert migrated_data["srcPath"] == "new.py"
        assert migrated_data["url"] == str(tmp_path / "new.py")

    def test_path_delete_file_removes_related_testcase(
        self,
        tmp_path: Path,
        api_with_tmp_path: Api,
    ) -> None:
        """Test path_delete removes testcase data for deleted files."""
        source = tmp_path / "old.py"
        source.write_text("print('old')", encoding="utf-8")
        cph_file = tmp_path / ".cph" / ".old.py.prob"
        cph_file.parent.mkdir(parents=True, exist_ok=True)
        cph_file.write_text("{}", encoding="utf-8")

        result = api_with_tmp_path.path_delete(str(source))

        assert result["status"] == "success"
        assert not source.exists()
        assert not cph_file.exists()

    def test_path_save_text_success(
        self,
        tmp_path: Path,
        api_with_tmp_path: Api,
    ) -> None:
        """Test path_save_text writes content to file."""
        test_file = tmp_path / "test.txt"
        test_content = "Hello, World!"

        api_with_tmp_path.path_save_text(str(test_file), test_content)

        assert test_file.read_text(encoding="utf-8") == test_content

    def test_path_save_text_raises_on_directory(
        self,
        tmp_path: Path,
        api_with_tmp_path: Api,
    ) -> None:
        """Test path_save_text raises ValueError for directory path."""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()

        with pytest.raises(ValueError, match="is a directory"):
            api_with_tmp_path.path_save_text(str(test_dir), "some text")

    def test_path_save_text_creates_parent_directories(
        self,
        tmp_path: Path,
        api_with_tmp_path: Api,
    ) -> None:
        """Test path_save_text creates parent directories if they don't exist."""
        test_file = tmp_path / "subdir1" / "subdir2" / "test.txt"
        test_content = "nested content"

        api_with_tmp_path.path_save_text(str(test_file), test_content)

        assert test_file.exists()
        assert test_file.read_text(encoding="utf-8") == test_content

    def test_path_save_text_overwrites_existing(
        self,
        tmp_path: Path,
        api_with_tmp_path: Api,
    ) -> None:
        """Test path_save_text overwrites existing file."""
        test_file = tmp_path / "existing.txt"
        test_file.write_text("old content", encoding="utf-8")
        new_content = "new content"

        api_with_tmp_path.path_save_text(str(test_file), new_content)

        assert test_file.read_text(encoding="utf-8") == new_content


class TestApiCompile:
    """Tests for compile method."""

    def test_compile_success(self, tmp_path: Path, api_with_tmp_path: Api) -> None:
        """Test compile returns success."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')", encoding="utf-8")
        api_with_tmp_path.opened_file = test_file

        with patch("pysrc.js_api.lang_compilers", {"python": MagicMock()}):
            with patch("pysrc.js_api.type_mp", {".py": {"id": "python"}}):
                result = api_with_tmp_path.compile()

        assert result == "success"

    def test_compile_unsupported_language(
        self,
        tmp_path: Path,
        api_with_tmp_path: Api,
    ) -> None:
        """Test compile returns success for unsupported language."""
        test_file = tmp_path / "test.xyz"
        test_file.write_text("some content", encoding="utf-8")
        api_with_tmp_path.opened_file = test_file

        with patch("pysrc.js_api.lang_runners", {}):
            with patch("pysrc.js_api.type_mp", {".xyz": {"id": "xyz"}}):
                result = api_with_tmp_path.compile()

        assert result == "success"

    def test_compile_error(self, tmp_path: Path, api_with_tmp_path: Api) -> None:
        """Test compile returns error message on failure."""

        def mock_compile(path: Path) -> None:
            raise FileNotFoundError("Compilation failed")

        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')", encoding="utf-8")
        api_with_tmp_path.opened_file = test_file

        with patch("pysrc.js_api.lang_compilers", {"python": mock_compile}):
            with patch("pysrc.js_api.type_mp", {".py": {"id": "python"}}):
                result = api_with_tmp_path.compile()

        assert "Compilation failed" in result


class TestApiRunTask:
    """Tests for run_task method."""

    def test_run_task_success(self, tmp_path: Path, api_with_tmp_path: Api) -> None:
        """Test run_task executes and returns result."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print(input())", encoding="utf-8")
        api_with_tmp_path.opened_file = test_file
        api_with_tmp_path.opened_testcase_file = MagicMock()

        mock_runner = MagicMock(return_value=("output", "", "success", 0.1, 10))

        with patch("pysrc.js_api.lang_runners", {"python": mock_runner}):
            with patch("pysrc.js_api.type_mp", {".py": {"id": "python"}}):
                with patch("pysrc.js_api.task_checker", return_value=True):
                    with patch.object(
                        api_with_tmp_path,
                        "get_code",
                        return_value={"type": "python"},
                    ):
                        with patch.object(
                            api_with_tmp_path,
                            "get_testcase",
                            return_value={
                                "tests": [
                                    {
                                        "input": "test input",
                                        "answer": "test output",
                                    },
                                ],
                            },
                        ):
                            result = api_with_tmp_path.run_task(1)

        assert result["status"] == "success"
        assert result["result"] == "output"
        assert result["stderr"] == ""

    def test_run_task_returns_stderr_without_affecting_stdout_judgement(
        self,
        tmp_path: Path,
        api_with_tmp_path: Api,
    ) -> None:
        """Test run_task returns stderr separately and judges by stdout only."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')", encoding="utf-8")
        api_with_tmp_path.opened_file = test_file

        mock_runner = MagicMock(
            return_value=("", "stderr output", "runtime_error", 0.1, 10),
        )

        with patch("pysrc.js_api.lang_runners", {"python": mock_runner}):
            with patch("pysrc.js_api.type_mp", {".py": {"id": "python"}}):
                with patch.object(
                    api_with_tmp_path,
                    "get_code",
                    return_value={"type": "python"},
                ):
                    with patch.object(
                        api_with_tmp_path,
                        "get_testcase",
                        return_value={
                            "tests": [
                                {
                                    "input": "test input",
                                    "answer": "test output",
                                },
                            ],
                        },
                    ):
                        result = api_with_tmp_path.run_task(1)

        assert result["status"] == "runtime_error"
        assert result["result"] == ""
        assert result["stderr"] == "stderr output"

    def test_run_task_unsupported_language(
        self,
        tmp_path: Path,
        api_with_tmp_path: Api,
    ) -> None:
        """Test run_task raises ValueError for unsupported language."""
        test_file = tmp_path / "test.xyz"
        test_file.write_text("content", encoding="utf-8")
        api_with_tmp_path.opened_file = test_file

        with patch("pysrc.js_api.lang_runners", {}):
            with patch("pysrc.js_api.type_mp", {".xyz": {"id": "xyz"}}):
                with patch.object(
                    api_with_tmp_path,
                    "get_code",
                    return_value={"type": "xyz"},
                ):
                    with pytest.raises(ValueError, match="is not supported"):
                        api_with_tmp_path.run_task(1)

    def test_run_task_cleans_compiled_artifact_after_run(
        self,
        tmp_path: Path,
        api_with_tmp_path: Api,
    ) -> None:
        """Test cleanup_compiled_artifact removes the compiled artifact."""
        test_file = tmp_path / "test.cpp"
        artifact = tmp_path / "test.out"
        test_file.write_text("int main() { return 0; }", encoding="utf-8")
        artifact.write_text("binary", encoding="utf-8")
        api_with_tmp_path.opened_file = test_file

        with patch(
            "pysrc.js_api.lang_runners",
            {"cpp": MagicMock(return_value=("ok", "", "success", 0.1, 4))},
        ):
            with patch("pysrc.js_api.type_mp", {".cpp": {"id": "cpp"}}):
                with patch("pysrc.js_api.task_checker", return_value=True):
                    with patch.object(
                        api_with_tmp_path,
                        "get_code",
                        return_value={"type": "cpp"},
                    ):
                        with patch.object(
                            api_with_tmp_path,
                            "get_testcase",
                            return_value={
                                "tests": [
                                    {
                                        "input": "",
                                        "answer": "ok",
                                    },
                                ],
                            },
                        ):
                            result = api_with_tmp_path.run_task(1)

        assert result["status"] == "success"
        assert artifact.exists()

        api_with_tmp_path.cleanup_compiled_artifact("cpp")

        assert not artifact.exists()

    def test_run_task_cleans_artifact_using_run_command_path(
        self,
        tmp_path: Path,
        api_with_tmp_path: Api,
    ) -> None:
        """Test run_task falls back to the run command path when cleaning artifacts."""
        test_file = tmp_path / "test.cpp"
        artifact = tmp_path / "custom-test.out"
        test_file.write_text("int main() { return 0; }", encoding="utf-8")
        artifact.write_text("binary", encoding="utf-8")
        api_with_tmp_path.opened_file = test_file

        with patch(
            "pysrc.js_api.config",
            {
                "programmingLanguages": {
                    "cpp": {
                        "compileCommand": "g++ {file} -o {fileStem}.out",
                        "runCommand": "{fileParent}/custom-{fileStem}.out",
                    },
                },
            },
        ):
            with patch(
                "pysrc.js_api.lang_runners",
                {"cpp": MagicMock(return_value=("ok", "", "success", 0.1, 4))},
            ):
                with patch("pysrc.js_api.type_mp", {".cpp": {"id": "cpp"}}):
                    with patch("pysrc.js_api.task_checker", return_value=True):
                        with patch.object(
                            api_with_tmp_path,
                            "get_code",
                            return_value={"type": "cpp"},
                        ):
                            with patch.object(
                                api_with_tmp_path,
                                "get_testcase",
                                return_value={
                                    "tests": [
                                        {
                                            "input": "",
                                            "answer": "ok",
                                        },
                                    ],
                                },
                            ):
                                result = api_with_tmp_path.run_task(1)

            assert result["status"] == "success"
            assert artifact.exists()

            api_with_tmp_path.cleanup_compiled_artifact("cpp")

        assert not artifact.exists()

    def test_run_task_cleans_python_pyc_artifact(
        self,
        tmp_path: Path,
        api_with_tmp_path: Api,
    ) -> None:
        """Test run_task removes the compiled Python bytecode artifact."""
        test_file = tmp_path / "test.py"
        artifact = tmp_path / "test.pyc"
        test_file.write_text("print('ok')", encoding="utf-8")
        artifact.write_text("bytecode", encoding="utf-8")
        api_with_tmp_path.opened_file = test_file

        with patch(
            "pysrc.js_api.lang_runners",
            {"python": MagicMock(return_value=("ok", "", "success", 0.1, 4))},
        ):
            with patch("pysrc.js_api.type_mp", {".py": {"id": "python"}}):
                with patch("pysrc.js_api.task_checker", return_value=True):
                    with patch.object(
                        api_with_tmp_path,
                        "get_code",
                        return_value={"type": "python"},
                    ):
                        with patch.object(
                            api_with_tmp_path,
                            "get_testcase",
                            return_value={
                                "tests": [
                                    {
                                        "input": "",
                                        "answer": "ok",
                                    },
                                ],
                            },
                        ):
                            result = api_with_tmp_path.run_task(1)

        assert result["status"] == "success"
        assert artifact.exists()

        api_with_tmp_path.cleanup_compiled_artifact("python")

        assert not artifact.exists()


class TestApiOtherMethods:
    """Tests for other Api methods."""

    def test_get_langs(self, api_with_tmp_path: Api) -> None:
        """Test get_langs returns language metadata."""
        mock_langs = {"python": {"id": "python"}, "cpp": {"id": "cpp"}}

        with patch("pysrc.js_api.langs", mock_langs):
            result = api_with_tmp_path.get_langs()

        assert result == mock_langs

    def test_get_cpu_count(self, api_with_tmp_path: Api) -> None:
        """Test get_cpu_count returns CPU core counts."""
        import psutil

        with patch.object(psutil, "cpu_count") as mock_cpu_count:
            # cpu_count can be called with logical=False or logical=True
            mock_cpu_count.side_effect = lambda logical=True: 4 if logical else 2
            result = api_with_tmp_path.get_cpu_count()

        assert result == (2, 4)

    def test_get_disks(self, api_with_tmp_path: Api) -> None:
        """Test get_disks returns available disks."""
        with patch("pysrc.js_api.platform.system", return_value="Linux"):
            with patch("pysrc.js_api.Path.home", return_value=Path("/home")):
                result = api_with_tmp_path.get_disks()

        assert len(result) == 2
        assert result[0]["name"] == "/"
        assert result[1]["name"] == "home"

    def test_get_config_path(self, tmp_path: Path, api_with_tmp_path: Api) -> None:
        """Test get_config_path returns config file path."""
        config_file = tmp_path / "config.json"

        with patch("pysrc.js_api.config_p", config_file):
            result = api_with_tmp_path.get_config_path()

        assert str(config_file) in result


class TestApiSetOpenedFile:
    """Tests for set_opened_file method."""

    def test_set_opened_file_success(
        self,
        tmp_path: Path,
        api_with_tmp_path: Api,
    ) -> None:
        """Test set_opened_file sets the opened file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')", encoding="utf-8")

        # Mock the watcher's create_observer method
        with patch.object(
            api_with_tmp_path.watcher,
            "create_observer",
            create=True,
        ) as mock_observer:
            api_with_tmp_path.set_opened_file(str(test_file))

        assert api_with_tmp_path.opened_file == test_file
        mock_observer.assert_called_once()

    def test_set_opened_file_raises_for_directory(
        self,
        tmp_path: Path,
        api_with_tmp_path: Api,
    ) -> None:
        """Test set_opened_file raises ValueError for directory."""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()

        with pytest.raises(ValueError, match="is not a file"):
            api_with_tmp_path.set_opened_file(str(test_dir))


class TestApiSetCwd:
    """Tests for set_cwd and get_cwd methods."""

    def test_set_cwd_success(self, tmp_path: Path, api_with_tmp_path: Api) -> None:
        """Test set_cwd sets current working directory."""
        new_dir = tmp_path / "new_dir"
        new_dir.mkdir()

        api_with_tmp_path.set_cwd(str(new_dir))

        assert api_with_tmp_path.cwd == new_dir

    def test_set_cwd_raises_for_nonexistent(
        self,
        tmp_path: Path,
        api_with_tmp_path: Api,
    ) -> None:
        """Test set_cwd raises FileNotFoundError for nonexistent path.

        Note: set_cwd checks is_dir() first, which returns False for nonexistent
        paths, so it raises ValueError before reaching the exists() check.
        """
        nonexistent = tmp_path / "nonexistent"

        # First checks is_dir() which returns False for nonexistent paths
        with pytest.raises(ValueError, match="is not a directory"):
            api_with_tmp_path.set_cwd(str(nonexistent))

    def test_set_cwd_raises_for_file(
        self,
        tmp_path: Path,
        api_with_tmp_path: Api,
    ) -> None:
        """Test set_cwd raises ValueError when path is a file."""
        test_file = tmp_path / "file.txt"
        test_file.touch()

        with pytest.raises(ValueError, match="is not a directory"):
            api_with_tmp_path.set_cwd(str(test_file))

    def test_get_cwd(self, tmp_path: Path, api_with_tmp_path: Api) -> None:
        """Test get_cwd returns current working directory."""
        api_with_tmp_path.cwd = tmp_path
        result = api_with_tmp_path.get_cwd()

        assert result == str(tmp_path)


class TestApiGetOpenedFile:
    """Tests for get_opened_file method."""

    def test_get_opened_file_returns_path(
        self,
        tmp_path: Path,
        api_with_tmp_path: Api,
    ) -> None:
        """Test get_opened_file returns file path."""
        test_file = tmp_path / "test.py"
        api_with_tmp_path.opened_file = test_file
        result = api_with_tmp_path.get_opened_file()

        assert result == str(test_file)

    def test_get_opened_file_returns_none(self, api_with_tmp_path: Api) -> None:
        """Test get_opened_file returns None when no file is opened."""
        api_with_tmp_path.opened_file = None  # type: ignore[assignment]
        result = api_with_tmp_path.get_opened_file()

        assert result is None


class TestApiPinnedFiles:
    """Tests for pinned files methods."""

    def test_get_pinned_files_empty(self, api_with_tmp_path: Api) -> None:
        """Test get_pinned_files returns empty list when no pinned files."""
        result = api_with_tmp_path.get_pinned_files()

        assert result == []

    def test_add_pinned_file(self, tmp_path: Path, api_with_tmp_path: Api) -> None:
        """Test add_pinned_file adds file to pinned list."""
        pinned_file = tmp_path / "data" / "pinned.txt"

        api_with_tmp_path.add_pinned_file("file2.py")

        content = pinned_file.read_text(encoding="utf-8")
        assert "file2.py" in content

    def test_remove_pinned_file(self, tmp_path: Path, api_with_tmp_path: Api) -> None:
        """Test remove_pinned_file removes file from pinned list."""
        pinned_file = tmp_path / "data" / "pinned.txt"
        pinned_file.parent.mkdir(parents=True, exist_ok=True)
        pinned_file.write_text("file1.py\nfile2.py\n", encoding="utf-8")

        api_with_tmp_path.remove_pinned_file("file1.py")

        content = pinned_file.read_text(encoding="utf-8")
        assert "file1.py" not in content


class TestApiScroll:
    """Tests for scroll position methods."""

    def test_save_and_get_scroll(self, tmp_path: Path, api_with_tmp_path: Api) -> None:
        """Test save_scoll and get_scoll."""
        api_with_tmp_path.save_scoll(100)

        scroll_file = tmp_path / "data" / "scroll.txt"
        assert scroll_file.read_text() == "100"

        result = api_with_tmp_path.get_scoll()

        assert result == 100


class TestApiTestcase:
    """Tests for testcase methods."""

    def test_get_testcase_empty(self, tmp_path: Path, api_with_tmp_path: Api) -> None:
        """Test get_testcase returns empty testcase."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')", encoding="utf-8")
        api_with_tmp_path.opened_file = test_file

        with patch("pysrc.js_api.cph2testcase", side_effect=lambda x: x):
            result = api_with_tmp_path.get_testcase()

        assert result["tests"] == []
        assert result["name"] == "test.py"

    def test_save_testcase(self, tmp_path: Path, api_with_tmp_path: Api) -> None:
        """Test save_testcase saves testcase to file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')", encoding="utf-8")
        api_with_tmp_path.opened_file = test_file
        api_with_tmp_path.opened_testcase_file = None

        testcase = {
            "name": "Test",
            "memoryLimit": 256,
            "timeLimit": 2,
            "tests": [{"id": 1, "input": "a", "answer": "b"}],
        }
        api_with_tmp_path.save_testcase(testcase)

        cph_file = tmp_path / ".cph" / ".test.py.prob"
        assert cph_file.exists()
