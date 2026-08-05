"""Tests for pywebview path hash data.

These tests ensure path hash metadata is included in API responses
that the frontend consumes for pywebview state and file navigation.
"""

from collections.abc import Callable, Generator
from pathlib import Path
from unittest.mock import patch

import pytest

from pysrc.js_api import Api


class StubWatcher:
    """A lightweight stub for Watcher to avoid file system operations in tests."""

    def __init__(self, callback: Callable[[str], None]) -> None:
        """Store the callback without touching the filesystem."""
        self._callback = callback

    def create_observer(self, path: str) -> None:
        """Pretend to create an observer for the given path."""


@pytest.fixture
def api_with_tmp_path(tmp_path: Path) -> Generator[Api, None, None]:
    """Create an Api instance with tmp_path for user_data and cwd."""
    user_data = tmp_path / "data"
    user_data.mkdir(parents=True, exist_ok=True)

    cwd_file = user_data / "cwd.txt"
    cwd_file.write_text(str(tmp_path), encoding="utf-8")

    with patch("pysrc.js_api.user_data_dir", user_data):
        with patch("pysrc.js_api.Watcher", StubWatcher):
            with patch("pysrc.js_api.Path.cwd", return_value=tmp_path):
                api = Api()
                api.cwd = tmp_path
                yield api


def test_get_code_includes_path_hashes(api_with_tmp_path: Api) -> None:
    """Ensure get_code returns path hash metadata."""
    result = api_with_tmp_path.get_code()
    assert "_hash" in result
    assert isinstance(result["_hash"], dict)
    assert result["_hash"]


def test_path_ls_includes_path_hashes(api_with_tmp_path: Api) -> None:
    """Ensure path_ls returns path hash metadata."""
    result = api_with_tmp_path.path_ls(None)
    assert "_hash" in result
    assert isinstance(result["_hash"], dict)
    assert result["_hash"]
