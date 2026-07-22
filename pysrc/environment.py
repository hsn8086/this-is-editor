"""Discover the local competitive-programming toolchain."""

import json
import os
import platform
import re
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypedDict

from .config import config, config_p
from .user_data import user_data_dir

type ToolStatus = Literal["ready", "missing", "error"]
type CandidateStatus = Literal["ready", "error"]
type ToolSource = Literal["configured", "managed", "path"]


class EnvironmentCandidate(TypedDict):
    """One discovered executable for an environment tool."""

    path: str
    version: str | None
    source: ToolSource
    status: CandidateStatus
    message: str | None


class EnvironmentTool(TypedDict):
    """Serializable result for one environment tool."""

    id: str
    name: str
    toolchain: Literal["python", "cpp"]
    role: Literal["runtime", "analysis", "format"]
    required: bool
    status: ToolStatus
    path: str | None
    version: str | None
    source: ToolSource | None
    message: str | None
    candidates: list[EnvironmentCandidate]


@dataclass(frozen=True)
class ToolSpec:
    """Static discovery information for an environment tool."""

    id: str
    name: str
    toolchain: Literal["python", "cpp"]
    role: Literal["runtime", "analysis", "format"]
    required: bool
    commands: tuple[str, ...]
    config_path: tuple[str, ...]


TOOL_SPECS = (
    ToolSpec(
        id="python",
        name="Python",
        toolchain="python",
        role="runtime",
        required=True,
        commands=("python3", "python"),
        config_path=("programmingLanguages", "python", "executable"),
    ),
    ToolSpec(
        id="ty",
        name="ty",
        toolchain="python",
        role="analysis",
        required=False,
        commands=("ty",),
        config_path=("programmingLanguages", "python", "lsp", "command"),
    ),
    ToolSpec(
        id="ruff",
        name="Ruff",
        toolchain="python",
        role="format",
        required=False,
        commands=("ruff",),
        config_path=("programmingLanguages", "python", "formatter", "command"),
    ),
    ToolSpec(
        id="cpp",
        name="G++",
        toolchain="cpp",
        role="runtime",
        required=True,
        commands=("g++",),
        config_path=("programmingLanguages", "cpp", "executable"),
    ),
    ToolSpec(
        id="clangd",
        name="clangd",
        toolchain="cpp",
        role="analysis",
        required=False,
        commands=("clangd",),
        config_path=("programmingLanguages", "cpp", "lsp", "command"),
    ),
    ToolSpec(
        id="clang-format",
        name="clang-format",
        toolchain="cpp",
        role="format",
        required=False,
        commands=("clang-format",),
        config_path=("programmingLanguages", "cpp", "formatter", "command"),
    ),
)


def _nested_config_value(path: tuple[str, ...]) -> str | list[str] | None:
    value: object = config
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value if isinstance(value, (str, list)) else None


def _command_name(command: str | list[str] | None) -> str | None:
    if isinstance(command, list):
        return command[0] if command else None
    if not command:
        return None
    try:
        parts = shlex.split(command, posix=platform.system() != "Windows")
    except ValueError:
        return None
    return parts[0].strip('"') if parts else None


def _matches_tool_name(spec: ToolSpec, path: Path) -> bool:
    name = path.name.casefold().removesuffix(".exe")
    patterns = {
        "python": r"python(?:\d+(?:\.\d+)*)?",
        "cpp": r"g\+\+(?:-\d+(?:\.\d+)*)?",
        "clangd": r"clangd(?:-\d+(?:\.\d+)*)?",
        "clang-format": r"clang-format(?:-\d+(?:\.\d+)*)?",
    }
    pattern = patterns.get(spec.id)
    if pattern:
        return re.fullmatch(pattern, name) is not None
    return name in spec.commands


def _managed_executables(spec: ToolSpec, managed_root: Path) -> list[Path]:
    if not managed_root.is_dir():
        return []
    try:
        return sorted(
            candidate.resolve()
            for candidate in managed_root.rglob("*")
            if candidate.is_file() and _matches_tool_name(spec, candidate)
        )
    except OSError:
        return []


def _path_executables(
    spec: ToolSpec,
    command_names: tuple[str, ...],
    search_path: str | None,
) -> list[Path]:
    if not search_path:
        return []

    results: list[Path] = []
    directories = list(
        dict.fromkeys(entry for entry in search_path.split(os.pathsep) if entry),
    )
    for command_name in command_names:
        if Path(command_name).is_absolute():
            continue
        results.extend(
            Path(executable).resolve()
            for directory in directories
            if (executable := shutil.which(command_name, path=directory))
        )

    for directory in directories:
        try:
            entries = sorted(Path(directory).iterdir())
        except OSError:
            continue
        results.extend(
            Path(executable).resolve()
            for entry in entries
            if entry.is_file()
            and _matches_tool_name(spec, entry)
            and (executable := shutil.which(entry.name, path=directory))
        )
    return results


def _find_executables(
    spec: ToolSpec,
    *,
    managed_root: Path,
    search_path: str | None,
) -> list[tuple[Path, ToolSource]]:
    found: list[tuple[Path, ToolSource]] = []
    seen: set[str] = set()

    def add(path: Path, source: ToolSource) -> None:
        resolved = path.resolve()
        key = os.path.normcase(str(resolved))
        if key not in seen:
            seen.add(key)
            found.append((resolved, source))

    configured_name = _command_name(_nested_config_value(spec.config_path))
    if configured_name:
        configured_path = Path(configured_name).expanduser()
        if (
            configured_path.is_absolute()
            and configured_path.is_file()
            and _matches_tool_name(spec, configured_path)
        ):
            add(configured_path, "configured")

    for managed in _managed_executables(spec, managed_root):
        add(managed, "managed")

    configured_command = (
        configured_name
        if configured_name and _matches_tool_name(spec, Path(configured_name))
        else None
    )
    command_names = tuple(
        command_name
        for command_name in dict.fromkeys((configured_command, *spec.commands))
        if command_name
    )
    for executable in _path_executables(spec, command_names, search_path):
        add(executable, "path")
    return found


def _tool_version(executable: Path) -> tuple[CandidateStatus, str | None, str | None]:
    creationflags = 0
    if platform.system() == "Windows":
        creationflags = int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
    try:
        result = subprocess.run(
            [str(executable), "--version"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
            creationflags=creationflags,
        )
    except (OSError, subprocess.SubprocessError) as e:
        return "error", None, str(e)

    output = (result.stdout.strip() or result.stderr.strip()).splitlines()
    version = output[0] if output else None
    if result.returncode != 0:
        return "error", version, f"Exited with code {result.returncode}"
    return "ready", version, None


def scan_environment(
    *,
    managed_root: Path | None = None,
    search_path: str | None = None,
) -> list[EnvironmentTool]:
    """Scan managed tools and PATH, then verify each discovered executable."""
    root = managed_root if managed_root is not None else user_data_dir / "tools"
    path_value = search_path if search_path is not None else os.environ.get("PATH")
    results: list[EnvironmentTool] = []

    for spec in TOOL_SPECS:
        found = _find_executables(spec, managed_root=root, search_path=path_value)
        candidates = []
        for executable, source in found:
            status, version, message = _tool_version(executable)
            candidates.append(
                EnvironmentCandidate(
                    path=str(executable),
                    version=version,
                    source=source,
                    status=status,
                    message=message,
                ),
            )

        if not candidates:
            results.append(
                EnvironmentTool(
                    id=spec.id,
                    name=spec.name,
                    toolchain=spec.toolchain,
                    role=spec.role,
                    required=spec.required,
                    status="missing",
                    path=None,
                    version=None,
                    source=None,
                    message=None,
                    candidates=[],
                ),
            )
            continue

        active = candidates[0]
        results.append(
            EnvironmentTool(
                id=spec.id,
                name=spec.name,
                toolchain=spec.toolchain,
                role=spec.role,
                required=spec.required,
                status=active["status"],
                path=active["path"],
                version=active["version"],
                source=active["source"],
                message=active["message"],
                candidates=candidates,
            ),
        )
    return results


def _replace_command_executable(
    command: str | list[str] | None,
    executable: Path,
) -> str | list[str]:
    parts: list[str]
    if isinstance(command, list):
        parts = command.copy()
    elif command:
        parts = shlex.split(command, posix=platform.system() != "Windows")
    else:
        parts = []

    updated = [str(executable), *parts[1:]] if parts else [str(executable)]
    if isinstance(command, list):
        return updated
    if platform.system() == "Windows":
        return subprocess.list2cmdline(updated)
    return shlex.join(updated)


def select_environment_tool(
    tool_id: str,
    executable_path: str,
    *,
    managed_root: Path | None = None,
    search_path: str | None = None,
) -> list[EnvironmentTool]:
    """Select one discovered executable and persist it in language settings."""
    spec = next((item for item in TOOL_SPECS if item.id == tool_id), None)
    if spec is None:
        msg = f"Unknown environment tool: {tool_id}"
        raise ValueError(msg)

    selected = Path(executable_path).expanduser().resolve(strict=True)
    results = scan_environment(managed_root=managed_root, search_path=search_path)
    tool = next(item for item in results if item["id"] == tool_id)
    candidate = next(
        (item for item in tool["candidates"] if Path(item["path"]) == selected),
        None,
    )
    if candidate is None or candidate["status"] != "ready":
        msg = f"Executable is not an available {spec.name} environment: {selected}"
        raise ValueError(msg)

    target: dict = config
    for key in spec.config_path[:-1]:
        target = target[key]
    config_key = spec.config_path[-1]
    target[config_key] = _replace_command_executable(target.get(config_key), selected)
    config_p.write_text(json.dumps(config, indent=4), encoding="utf-8")
    return scan_environment(managed_root=managed_root, search_path=search_path)


def environment_setup_path() -> Path:
    """Return the marker used to skip first-run environment setup."""
    return user_data_dir / "environment-setup-complete"


def is_environment_setup_complete() -> bool:
    """Return whether the first-run environment screen was completed."""
    return environment_setup_path().is_file()


def complete_environment_setup() -> None:
    """Persist completion of the first-run environment screen."""
    marker = environment_setup_path()
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("complete\n", encoding="utf-8")
