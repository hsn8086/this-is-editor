"""Tests for the Nuitka build command wrapper."""

import subprocess
from unittest.mock import patch

from tools import builder


def test_build_command_configures_windows_release() -> None:
    """Windows release builds should be one-file GUI executables."""
    args = builder.parse_args(["--mode", "onefile"])

    command = builder.build_command(args, system="Windows")

    assert "--onefile" in command
    assert "--windows-disable-console" in command
    assert "--debugger" not in command


def test_build_command_configures_debug_directory() -> None:
    """Debug directory builds should disable LTO and retain a console."""
    args = builder.parse_args(["--mode", "dir", "--debug"])

    command = builder.build_command(args, system="Windows")

    assert "--onefile" not in command
    assert "--windows-disable-console" not in command
    assert "--lto=no" in command
    assert "--debugger" in command


def test_main_propagates_nuitka_failure() -> None:
    """A failed compiler process must fail the calling CI step."""
    error = subprocess.CalledProcessError(7, ["uv", "run", "nuitka"])

    with patch("tools.builder.subprocess.run", side_effect=error):
        exit_code = builder.main([])

    assert exit_code == 7


def test_main_returns_zero_after_success() -> None:
    """A successful compiler process should return zero."""
    with patch("tools.builder.subprocess.run") as run:
        exit_code = builder.main([])

    assert exit_code == 0
    run.assert_called_once_with(
        builder.build_command(builder.parse_args([])),
        check=True,
    )
