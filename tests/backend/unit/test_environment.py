"""Tests for development-tool environment discovery."""

import copy
import shlex
from pathlib import Path
from unittest.mock import patch

from pysrc import environment


def _tool(
    results: list[environment.EnvironmentTool],
    tool_id: str,
) -> environment.EnvironmentTool:
    return next(result for result in results if result["id"] == tool_id)


def test_scan_finds_tool_in_managed_user_directory(tmp_path: Path) -> None:
    """Managed tools are discovered before system PATH entries."""
    managed_root = tmp_path / "tools"
    managed_ty = managed_root / "python" / "bin" / "ty"
    managed_ty.parent.mkdir(parents=True)
    managed_ty.touch()

    with patch.object(
        environment,
        "_tool_version",
        return_value=("ready", "ty 0.0.test", None),
    ):
        results = environment.scan_environment(
            managed_root=managed_root,
            search_path="",
        )

    ty_result = _tool(results, "ty")
    assert ty_result["status"] == "ready"
    assert ty_result["source"] == "managed"
    assert ty_result["path"] == str(managed_ty.resolve())
    assert ty_result["candidates"] == [
        {
            "path": str(managed_ty.resolve()),
            "version": "ty 0.0.test",
            "source": "managed",
            "status": "ready",
            "message": None,
        },
    ]
    assert _tool(results, "clangd")["status"] == "missing"


def test_scan_reports_executable_failure(tmp_path: Path) -> None:
    """A discovered executable that cannot run is reported as an error."""
    managed_root = tmp_path / "tools"
    managed_ruff = managed_root / "ruff"
    managed_root.mkdir()
    managed_ruff.touch()

    with patch.object(
        environment,
        "_tool_version",
        return_value=("error", None, "permission denied"),
    ):
        results = environment.scan_environment(
            managed_root=managed_root,
            search_path="",
        )

    ruff_result = _tool(results, "ruff")
    assert ruff_result["status"] == "error"
    assert ruff_result["message"] == "permission denied"


def test_scan_returns_all_path_environments_in_priority_order(tmp_path: Path) -> None:
    """Multiple PATH installations are exposed without duplicate paths."""
    first_bin = tmp_path / "first" / "bin"
    second_bin = tmp_path / "second" / "bin"
    first_python = first_bin / "python3"
    second_python = second_bin / "python3"
    for executable in (first_python, second_python):
        executable.parent.mkdir(parents=True)
        executable.touch(mode=0o755)

    with patch.object(
        environment,
        "_tool_version",
        return_value=("ready", "Python 3.12", None),
    ):
        results = environment.scan_environment(
            managed_root=tmp_path / "managed",
            search_path=f"{first_bin}:{second_bin}:{first_bin}",
        )

    python = _tool(results, "python")
    assert python["path"] == str(first_python.resolve())
    assert [candidate["path"] for candidate in python["candidates"]] == [
        str(first_python.resolve()),
        str(second_python.resolve()),
    ]


def test_scan_survives_unreadable_path_entry(tmp_path: Path) -> None:
    """An entry whose stat() raises EACCES must not abort the whole scan.

    macOS keeps SIP-protected binaries such as /usr/sbin/weakpass_edit on PATH,
    and Path.is_file() propagates PermissionError instead of swallowing it.
    """
    path_bin = tmp_path / "bin"
    path_bin.mkdir(parents=True)
    (path_bin / "python3").touch(mode=0o755)
    protected = path_bin / "weakpass_edit"
    protected.touch(mode=0o755)

    real_is_file = Path.is_file

    def fake_is_file(self: Path) -> bool:
        if self.name == "weakpass_edit":
            raise PermissionError(13, "Permission denied")
        return real_is_file(self)

    with (
        patch.object(Path, "is_file", fake_is_file),
        patch.object(
            environment,
            "_tool_version",
            return_value=("ready", "Python 3.12", None),
        ),
    ):
        results = environment.scan_environment(
            managed_root=tmp_path / "managed",
            search_path=str(path_bin),
        )

    assert _tool(results, "python")["status"] == "ready"


def test_scan_ignores_configured_executable_for_a_different_tool(
    tmp_path: Path,
) -> None:
    """An old pylsp command must not be reported as a ty installation."""
    pylsp = tmp_path / "pylsp"
    ty = tmp_path / "ty"
    pylsp.touch(mode=0o755)
    ty.touch(mode=0o755)
    test_config = copy.deepcopy(environment.config)
    test_config["programmingLanguages"]["python"]["lsp"]["command"] = "pylsp"

    with (
        patch.object(environment, "config", test_config),
        patch.object(
            environment,
            "_tool_version",
            return_value=("ready", "ty 1.0", None),
        ),
    ):
        results = environment.scan_environment(
            managed_root=tmp_path / "managed",
            search_path=str(tmp_path),
        )

    ty_result = _tool(results, "ty")
    assert ty_result["path"] == str(ty.resolve())
    assert [candidate["path"] for candidate in ty_result["candidates"]] == [
        str(ty.resolve()),
    ]


def test_select_environment_preserves_command_arguments(tmp_path: Path) -> None:
    """Selecting another executable changes only the command executable."""
    first_bin = tmp_path / "first"
    second_bin = tmp_path / "second"
    first_ruff = first_bin / "ruff"
    second_ruff = second_bin / "ruff"
    for executable in (first_ruff, second_ruff):
        executable.parent.mkdir()
        executable.touch(mode=0o755)

    test_config = copy.deepcopy(environment.config)
    config_file = tmp_path / "config.json"
    with (
        patch.object(environment, "config", test_config),
        patch.object(environment, "config_p", config_file),
        patch.object(
            environment,
            "_tool_version",
            return_value=("ready", "ruff 1.0", None),
        ),
    ):
        results = environment.select_environment_tool(
            "ruff",
            str(second_ruff),
            managed_root=tmp_path / "managed",
            search_path=f"{first_bin}:{second_bin}",
        )

    command = test_config["programmingLanguages"]["python"]["formatter"]["command"]
    assert shlex.split(command) == [str(second_ruff.resolve()), "format", "{file}"]
    assert _tool(results, "ruff")["source"] == "configured"


def test_environment_completion_marker_is_isolated(tmp_path: Path) -> None:
    """First-run completion is persisted in the selected TIE data directory."""
    with patch.object(environment, "user_data_dir", tmp_path):
        assert environment.is_environment_setup_complete() is False
        environment.complete_environment_setup()
        assert environment.is_environment_setup_complete() is True
        assert environment.environment_setup_path().parent == tmp_path
