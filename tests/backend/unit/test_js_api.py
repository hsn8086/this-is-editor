"""Unit tests for the js_api module.

This module contains P0 level tests for the Api class, focusing on:
- get_code/save_code functionality
- get_config/set_config functionality
- path_* operations
- run_task/compile functionality
- Exception handling
"""

from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import pytest


class TestApiGetCode:
    """Tests for the get_code method."""

    def test_get_code_with_existing_file(self, tmp_path: Path) -> None:
        """Test get_code returns correct data for existing file."""
        test_file = tmp_path / "test.py"
        test_code = "print('hello world')"
        test_file.write_text(test_code, encoding="utf-8")

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    mock_opened_file = MagicMock()
                    mock_opened_file.exists.return_value = True
                    mock_opened_file.read_text.return_value = test_code
                    mock_opened_file.suffix.lower.return_value = ".py"

                    with patch("pysrc.js_api.Watcher"):
                        with patch("pysrc.js_api.type_mp", {".py": {"id": "python"}}):
                            from pysrc.js_api import Api

                            api = Api()
                            api.opened_file = test_file
                            result = api.get_code()

        assert result["code"] == test_code
        assert result["type"] == "python"

    def test_get_code_with_nonexistent_file(self, tmp_path: Path) -> None:
        """Test get_code creates file if it doesn't exist."""
        test_file = tmp_path / "new_file.py"

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    mock_opened_file = MagicMock()
                    mock_opened_file.exists.return_value = False
                    mock_opened_file.suffix.lower.return_value = ".py"
                    mock_opened_file.parent.mkdir = MagicMock()

                    with patch("pysrc.js_api.Watcher"):
                        with patch("pysrc.js_api.type_mp", {}):
                            from pysrc.js_api import Api

                            api = Api()
                            api.opened_file = test_file
                            api.get_code()

        mock_opened_file.parent.mkdir.assert_called()

    def test_get_code_with_none_opened_file(self, tmp_path: Path) -> None:
        """Test get_code returns default values when no file is opened."""
        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        from pysrc.js_api import Api

                        api = Api()
                        api.opened_file = cast("Path", None)
                        result = api.get_code()

        assert result["code"] == ""
        assert result["type"] == "text"


class TestApiSaveCode:
    """Tests for the save_code method."""

    def test_save_code_success(self, tmp_path: Path) -> None:
        """Test save_code writes content to file."""
        test_file = tmp_path / "test.py"
        test_code = "print('saved')"

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        from pysrc.js_api import Api

                        api = Api()
                        api.opened_file = test_file
                        api.save_code(test_code)

        assert test_file.read_text() == test_code

    def test_save_code_with_none_opened_file(self, tmp_path: Path) -> None:
        """Test save_code raises ValueError when no file is opened."""
        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        from pysrc.js_api import Api

                        api = Api()
                        api.opened_file = cast("Path", None)

                        with pytest.raises(ValueError, match="No file is opened"):
                            api.save_code("some code")

    def test_save_code_with_non_file_path(self, tmp_path: Path) -> None:
        """Test save_code raises ValueError when path is not a file."""
        test_path = tmp_path / "not_a_file"

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=True):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        from pysrc.js_api import Api

                        api = Api()
                        api.opened_file = test_path

                        with pytest.raises(ValueError, match="is not a file"):
                            api.save_code("some code")


class TestApiConfig:
    """Tests for get_config and set_config methods."""

    def test_get_config_returns_merged(self, tmp_path: Path) -> None:
        """Test get_config returns merged configuration."""
        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        with patch("pysrc.js_api.merge_meta") as mock_merge:
                            with patch("pysrc.js_api.config_meta") as mock_meta:
                                with patch("pysrc.js_api.config") as mock_config:
                                    mock_merge.return_value = {"key": "value"}

                                    from pysrc.js_api import Api

                                    api = Api()
                                    result = api.get_config()

        assert result == {"key": "value"}
        mock_merge.assert_called_once_with(mock_meta, mock_config)

    def test_set_config_simple_key(self, tmp_path: Path) -> None:
        """Test set_config with simple key."""
        config_file = tmp_path / "config.json"

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        with patch("pysrc.js_api.config_p", config_file):
                            with patch("pysrc.js_api.config", {}):
                                from pysrc.js_api import Api

                                api = Api()
                                api.set_config("testKey", "testValue")

        assert config_file.exists()

    def test_set_config_nested_key(self, tmp_path: Path) -> None:
        """Test set_config with nested key using dot notation."""
        test_config: dict = {"outer": {"inner": "original"}}
        config_file = tmp_path / "config.json"

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        with patch("pysrc.js_api.config_p", config_file):
                            with patch("pysrc.js_api.config", test_config):
                                from pysrc.js_api import Api

                                api = Api()
                                api.set_config("outer.inner", "newValue")

        assert test_config["outer"]["inner"] == "newValue"


class TestApiPathOperations:
    """Tests for path_* methods."""

    def test_path_ls(self, tmp_path: Path) -> None:
        """Test path_ls lists directory contents."""
        (tmp_path / "file1.txt").touch()
        (tmp_path / "file2.py").touch()
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        with patch("pysrc.js_api.type_mp", {}):
                            from pysrc.js_api import Api

                            api = Api()
                            api.cwd = tmp_path
                            result = api.path_ls(None)

        assert result["now_path"] == str(tmp_path)
        assert len(result["files"]) == 3

    def test_path_join(self, tmp_path: Path) -> None:
        """Test path_join joins path components."""
        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        from pysrc.js_api import Api

                        api = Api()
                        result = api.path_join("dir", "subdir", "file.txt")

        assert result == str(Path("dir") / "subdir" / "file.txt")

    def test_path_parent(self, tmp_path: Path) -> None:
        """Test path_parent returns parent directory."""
        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        from pysrc.js_api import Api

                        api = Api()
                        result = api.path_parent("/home/user/file.txt")

        assert result == "/home/user"

    def test_path_get_info(self, tmp_path: Path) -> None:
        """Test path_get_info returns file metadata."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')", encoding="utf-8")

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        with patch("pysrc.js_api.type_mp", {}):
                            from pysrc.js_api import Api

                            api = Api()
                            result = api.path_get_info(str(test_file))

        assert result["name"] == "test.py"
        assert result["stem"] == "test"
        assert result["is_file"] is True

    def test_path_get_info_raises_on_nonexistent(self, tmp_path: Path) -> None:
        """Test path_get_info raises FileNotFoundError for nonexistent path."""
        nonexistent = tmp_path / "nonexistent.txt"

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        from pysrc.js_api import Api

                        api = Api()

                        with pytest.raises(FileNotFoundError):
                            api.path_get_info(str(nonexistent))

    def test_path_get_text(self, tmp_path: Path) -> None:
        """Test path_get_text returns file content."""
        test_file = tmp_path / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content, encoding="utf-8")

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        from pysrc.js_api import Api

                        api = Api()
                        result = api.path_get_text(str(test_file))

        assert result == test_content

    def test_path_get_text_raises_on_directory(self, tmp_path: Path) -> None:
        """Test path_get_text raises ValueError for directory."""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        from pysrc.js_api import Api

                        api = Api()

                        with pytest.raises(ValueError, match="is not a file"):
                            api.path_get_text(str(test_dir))

    def test_path_to_uri(self, tmp_path: Path) -> None:
        """Test path_to_uri converts path to URI."""
        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path
                    mock_path_cls.return_value.is_absolute.return_value = True
                    mock_path_cls.return_value.as_posix.return_value = (
                        "/home/user/file.txt"
                    )

                    with patch("pysrc.js_api.Watcher"):
                        from pysrc.js_api import Api

                        api = Api()
                        result = api.path_to_uri("/home/user/file.txt")

        assert result == "file:///home/user/file.txt"

    def test_path_to_uri_raises_on_relative(self, tmp_path: Path) -> None:
        """Test path_to_uri raises ValueError for relative path."""
        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path
                    mock_path_cls.return_value.is_absolute.return_value = False

                    with patch("pysrc.js_api.Watcher"):
                        from pysrc.js_api import Api

                        api = Api()

                        with pytest.raises(ValueError, match="is not an absolute path"):
                            api.path_to_uri("relative/path.txt")

    def test_path_touch(self, tmp_path: Path) -> None:
        """Test path_touch creates empty file."""
        new_file = tmp_path / "new_file.txt"

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        from pysrc.js_api import Api

                        api = Api()
                        result = api.path_touch(str(new_file))

        assert result["status"] == "success"
        assert new_file.exists()

    def test_path_touch_existing_file(self, tmp_path: Path) -> None:
        """Test path_touch returns warning for existing file."""
        existing_file = tmp_path / "existing.txt"
        existing_file.touch()

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=True):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        from pysrc.js_api import Api

                        api = Api()
                        result = api.path_touch(str(existing_file))

        assert result["status"] == "warning"

    def test_path_mkdir(self, tmp_path: Path) -> None:
        """Test path_mkdir creates directory."""
        new_dir = tmp_path / "new_dir"

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        from pysrc.js_api import Api

                        api = Api()
                        result = api.path_mkdir(str(new_dir))

        assert result["status"] == "success"
        assert new_dir.exists()


class TestApiCompile:
    """Tests for compile method."""

    def test_compile_success(self, tmp_path: Path) -> None:
        """Test compile returns success."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')", encoding="utf-8")

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        with patch(
                            "pysrc.js_api.lang_compilers", {"python": MagicMock()}
                        ):
                            with patch(
                                "pysrc.js_api.type_mp", {".py": {"id": "python"}}
                            ):
                                from pysrc.js_api import Api

                                api = Api()
                                api.opened_file = test_file
                                result = api.compile()

        assert result == "success"

    def test_compile_unsupported_language(self, tmp_path: Path) -> None:
        """Test compile returns success for unsupported language."""
        test_file = tmp_path / "test.xyz"
        test_file.write_text("some content", encoding="utf-8")

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        with patch("pysrc.js_api.lang_compilers", {}):
                            with patch("pysrc.js_api.type_mp", {".xyz": {"id": "xyz"}}):
                                from pysrc.js_api import Api

                                api = Api()
                                api.opened_file = test_file
                                result = api.compile()

        assert result == "success"

    def test_compile_error(self, tmp_path: Path) -> None:
        """Test compile returns error message on failure."""

        def mock_compile(path: Path) -> None:
            raise FileNotFoundError("Compilation failed")

        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')", encoding="utf-8")

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        with patch(
                            "pysrc.js_api.lang_compilers", {"python": mock_compile}
                        ):
                            with patch(
                                "pysrc.js_api.type_mp", {".py": {"id": "python"}}
                            ):
                                from pysrc.js_api import Api

                                api = Api()
                                api.opened_file = test_file
                                result = api.compile()

        assert "Compilation failed" in result


class TestApiRunTask:
    """Tests for run_task method."""

    def test_run_task_success(self, tmp_path: Path) -> None:
        """Test run_task executes and returns result."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print(input())", encoding="utf-8")

        mock_runner = MagicMock(return_value=("output", "success", 0.1, 10))

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        with patch(
                            "pysrc.js_api.lang_runners", {"python": mock_runner}
                        ):
                            with patch(
                                "pysrc.js_api.type_mp", {".py": {"id": "python"}}
                            ):
                                with patch(
                                    "pysrc.js_api.task_checker", return_value=True
                                ):
                                    from pysrc.js_api import Api

                                    api = Api()
                                    api.opened_file = test_file
                                    api.opened_testcase_file = MagicMock()

                                    with patch.object(
                                        api, "get_code", return_value={"type": "python"}
                                    ):
                                        with patch.object(
                                            api,
                                            "get_testcase",
                                            return_value={
                                                "tests": [
                                                    {
                                                        "input": "test input",
                                                        "answer": "test output",
                                                    }
                                                ]
                                            },
                                        ):
                                            result = api.run_task(1)

        assert result["status"] == "success"
        assert result["result"] == "output"

    def test_run_task_unsupported_language(self, tmp_path: Path) -> None:
        """Test run_task raises ValueError for unsupported language."""
        test_file = tmp_path / "test.xyz"
        test_file.write_text("content", encoding="utf-8")

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        with patch("pysrc.js_api.lang_runners", {}):
                            with patch("pysrc.js_api.type_mp", {".xyz": {"id": "xyz"}}):
                                from pysrc.js_api import Api

                                api = Api()
                                api.opened_file = test_file

                                with patch.object(
                                    api, "get_code", return_value={"type": "xyz"}
                                ):
                                    with pytest.raises(
                                        ValueError, match="is not supported"
                                    ):
                                        api.run_task(1)


class TestApiOtherMethods:
    """Tests for other Api methods."""

    def test_get_langs(self, tmp_path: Path) -> None:
        """Test get_langs returns language metadata."""
        mock_langs = {"python": {"id": "python"}, "cpp": {"id": "cpp"}}

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        with patch("pysrc.js_api.langs", mock_langs):
                            from pysrc.js_api import Api

                            api = Api()
                            result = api.get_langs()

        assert result == mock_langs

    def test_get_cpu_count(self, tmp_path: Path) -> None:
        """Test get_cpu_count returns CPU core counts."""
        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        with patch("pysrc.psutil.cpu_count") as mock_cpu:
                            mock_cpu.return_value = 4

                            from pysrc.js_api import Api

                            api = Api()
                            result = api.get_cpu_count()

        assert result == (4, 4)

    def test_get_disks(self, tmp_path: Path) -> None:
        """Test get_disks returns available disks."""
        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        with patch(
                            "pysrc.js_api.platform.system", return_value="Linux"
                        ):
                            with patch(
                                "pysrc.js_api.Path.home", return_value=tmp_path / "home"
                            ):
                                from pysrc.js_api import Api

                                api = Api()
                                result = api.get_disks()

        assert len(result) == 2
        assert result[0]["name"] == "/"
        assert result[1]["name"] == "home"

    def test_get_config_path(self, tmp_path: Path) -> None:
        """Test get_config_path returns config file path."""
        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        with patch("pysrc.js_api.config_p", tmp_path / "config.json"):
                            from pysrc.js_api import Api

                            api = Api()
                            result = api.get_config_path()

        assert str(tmp_path / "config.json") in result


class TestApiSetOpenedFile:
    """Tests for set_opened_file method."""

    def test_set_opened_file_success(self, tmp_path: Path) -> None:
        """Test set_opened_file sets the opened file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')", encoding="utf-8")

        mock_watcher = MagicMock()

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=True):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher", return_value=mock_watcher):
                        from pysrc.js_api import Api

                        api = Api()
                        api.set_opened_file(str(test_file))

        assert api.opened_file == test_file
        mock_watcher.create_observer.assert_called_once()

    def test_set_opened_file_raises_for_directory(self, tmp_path: Path) -> None:
        """Test set_opened_file raises ValueError for directory."""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=True):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        from pysrc.js_api import Api

                        api = Api()

                        with pytest.raises(ValueError, match="is not a file"):
                            api.set_opened_file(str(test_dir))


class TestApiSetCwd:
    """Tests for set_cwd and get_cwd methods."""

    def test_set_cwd_success(self, tmp_path: Path) -> None:
        """Test set_cwd sets current working directory."""
        new_dir = tmp_path / "new_dir"
        new_dir.mkdir()

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path
                    mock_path_cls.return_value.is_dir.return_value = True
                    mock_path_cls.return_value.exists.return_value = True

                    with patch("pysrc.js_api.Watcher"):
                        from pysrc.js_api import Api

                        api = Api()
                        api.set_cwd(str(new_dir))

        assert api.cwd == new_dir

    def test_set_cwd_raises_for_nonexistent(self, tmp_path: Path) -> None:
        """Test set_cwd raises FileNotFoundError for nonexistent path."""
        nonexistent = tmp_path / "nonexistent"

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path
                    mock_path_cls.return_value.is_dir.return_value = False
                    mock_path_cls.return_value.exists.return_value = False

                    with patch("pysrc.js_api.Watcher"):
                        from pysrc.js_api import Api

                        api = Api()

                        with pytest.raises(FileNotFoundError):
                            api.set_cwd(str(nonexistent))

    def test_set_cwd_raises_for_file(self, tmp_path: Path) -> None:
        """Test set_cwd raises ValueError when path is a file."""
        test_file = tmp_path / "file.txt"
        test_file.touch()

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path
                    mock_path_cls.return_value.is_dir.return_value = False
                    mock_path_cls.return_value.exists.return_value = True

                    with patch("pysrc.js_api.Watcher"):
                        from pysrc.js_api import Api

                        api = Api()

                        with pytest.raises(ValueError, match="is not a directory"):
                            api.set_cwd(str(test_file))

    def test_get_cwd(self, tmp_path: Path) -> None:
        """Test get_cwd returns current working directory."""
        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        from pysrc.js_api import Api

                        api = Api()
                        api.cwd = tmp_path
                        result = api.get_cwd()

        assert result == str(tmp_path)


class TestApiGetOpenedFile:
    """Tests for get_opened_file method."""

    def test_get_opened_file_returns_path(self, tmp_path: Path) -> None:
        """Test get_opened_file returns file path."""
        test_file = tmp_path / "test.py"

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        from pysrc.js_api import Api

                        api = Api()
                        api.opened_file = test_file
                        result = api.get_opened_file()

        assert result == str(test_file)

    def test_get_opened_file_returns_none(self, tmp_path: Path) -> None:
        """Test get_opened_file returns None when no file is opened."""
        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        from pysrc.js_api import Api

                        api = Api()
                        api.opened_file = cast("Path", None)
                        result = api.get_opened_file()

        assert result is None


class TestApiPinnedFiles:
    """Tests for pinned files methods."""

    def test_get_pinned_files_empty(self, tmp_path: Path) -> None:
        """Test get_pinned_files returns empty list when no pinned files."""
        pinned_file = tmp_path / "data" / "pinned.txt"

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path
                    mock_path_cls.return_value.exists.return_value = False

                    with patch("pysrc.js_api.Watcher"):
                        from pysrc.js_api import Api

                        api = Api()
                        result = api.get_pinned_files()

        assert result == []

    def test_add_pinned_file(self, tmp_path: Path) -> None:
        """Test add_pinned_file adds file to pinned list."""
        pinned_file = tmp_path / "data" / "pinned.txt"
        pinned_file.parent.mkdir(parents=True, exist_ok=True)
        pinned_file.write_text("file1.py\n", encoding="utf-8")

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path
                    mock_path_cls.return_value.exists.return_value = True
                    mock_path_cls.return_value.is_dir.return_value = False

                    with patch("pysrc.js_api.Watcher"):
                        from pysrc.js_api import Api

                        api = Api()
                        api.add_pinned_file("file2.py")

        content = pinned_file.read_text(encoding="utf-8")
        assert "file2.py" in content

    def test_remove_pinned_file(self, tmp_path: Path) -> None:
        """Test remove_pinned_file removes file from pinned list."""
        pinned_file = tmp_path / "data" / "pinned.txt"
        pinned_file.parent.mkdir(parents=True, exist_ok=True)
        pinned_file.write_text("file1.py\nfile2.py\n", encoding="utf-8")

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path
                    mock_path_cls.return_value.exists.return_value = True
                    mock_path_cls.return_value.is_dir.return_value = False

                    with patch("pysrc.js_api.Watcher"):
                        from pysrc.js_api import Api

                        api = Api()
                        api.remove_pinned_file("file1.py")

        content = pinned_file.read_text(encoding="utf-8")
        assert "file1.py" not in content


class TestApiScroll:
    """Tests for scroll position methods."""

    def test_save_and_get_scroll(self, tmp_path: Path) -> None:
        """Test save_scoll and get_scoll."""
        scroll_file = tmp_path / "data" / "scroll.txt"

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        from pysrc.js_api import Api

                        api = Api()
                        api.save_scoll(100)

        assert scroll_file.read_text() == "100"

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        from pysrc.js_api import Api

                        api = Api()
                        result = api.get_scoll()

        assert result == 100


class TestApiTestcase:
    """Tests for testcase methods."""

    def test_get_testcase_empty(self, tmp_path: Path) -> None:
        """Test get_testcase returns empty testcase."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')", encoding="utf-8")

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        with patch(
                            "pysrc.js_api.cph2testcase", side_effect=lambda x: x
                        ):
                            from pysrc.js_api import Api

                            api = Api()
                            api.opened_file = test_file
                            result = api.get_testcase()

        assert result["tests"] == []
        assert result["name"] == "test.py"

    def test_save_testcase(self, tmp_path: Path) -> None:
        """Test save_testcase saves testcase to file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')", encoding="utf-8")

        with patch("pysrc.js_api.user_data_dir", tmp_path / "data"):
            with patch.object(Path, "exists", return_value=False):
                with patch("pysrc.js_api.Path") as mock_path_cls:
                    mock_path_cls.cwd.return_value = tmp_path

                    with patch("pysrc.js_api.Watcher"):
                        from pysrc.js_api import Api

                        api = Api()
                        api.opened_file = test_file
                        api.opened_testcase_file = None

                        testcase = {
                            "name": "Test",
                            "memoryLimit": 256,
                            "timeLimit": 2,
                            "tests": [{"id": 1, "input": "a", "answer": "b"}],
                        }
                        api.save_testcase(testcase)

        cph_file = tmp_path / ".cph" / ".test.py.prob"
        assert cph_file.exists()
