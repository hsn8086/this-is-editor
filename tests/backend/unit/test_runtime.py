"""Tests for development runtime path overrides."""

import os
from pathlib import Path

import pytest

import main
from pysrc.runtime import DEV_USER_DATA_DIR_ENV, configure_dev_user_data_dir
from pysrc.user_data import ensure_user_directories, resolve_user_directories


def test_parse_dev_user_data_dir(tmp_path: Path) -> None:
    """The CLI resolves the isolated user-data root to an absolute path."""
    requested_path = tmp_path / "tie-user"

    args = main.parse_args(["--debug", "--dev-user-data-dir", str(requested_path)])

    assert args.debug is True
    assert args.dev_user_data_dir == requested_path.resolve()


def test_dev_user_data_dir_isolates_all_application_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The override derives and creates isolated data, config, and log paths."""
    monkeypatch.delenv(DEV_USER_DATA_DIR_ENV, raising=False)
    dev_root = tmp_path / "scan-fixture"

    configure_dev_user_data_dir(dev_root)
    directories = resolve_user_directories(os.environ[DEV_USER_DATA_DIR_ENV])
    ensure_user_directories(directories)

    assert directories.data == dev_root / "data"
    assert directories.config == dev_root / "config"
    assert directories.log == dev_root / "log"
    assert all(
        path.is_dir()
        for path in (directories.data, directories.config, directories.log)
    )
