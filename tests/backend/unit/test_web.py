"""Unit tests for LSP workspace handling in the web server."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pysrc import web


def test_window_does_not_seed_private_pywebview_state() -> None:
    """Application data is not written through pywebview's private state bridge."""
    assert web.window is not None
    assert "_hash" not in web.window.state


class TestResolveWorkspacePath:
    """Tests for workspace validation before an LSP process is started."""

    def test_none_keeps_legacy_process_cwd(self) -> None:
        """An omitted workspace preserves the process default cwd."""
        assert web.resolve_workspace_path(None) is None

    def test_resolves_existing_directory(self, tmp_path: Path) -> None:
        """An existing absolute directory is resolved."""
        assert web.resolve_workspace_path(str(tmp_path)) == tmp_path.resolve()

    def test_rejects_relative_path(self) -> None:
        """Relative workspace paths are rejected."""
        with pytest.raises(ValueError, match="must be absolute"):
            web.resolve_workspace_path("relative/project")

    def test_rejects_missing_path(self, tmp_path: Path) -> None:
        """Missing workspace paths are rejected."""
        with pytest.raises(ValueError, match="cannot be resolved"):
            web.resolve_workspace_path(str(tmp_path / "missing"))

    def test_rejects_file(self, tmp_path: Path) -> None:
        """A workspace must be a directory rather than a file."""
        source_file = tmp_path / "main.py"
        source_file.touch()

        with pytest.raises(ValueError, match="not a directory"):
            web.resolve_workspace_path(str(source_file))


class TestStartLspProcess:
    """Tests for passing the workspace to the language server process."""

    @pytest.mark.asyncio
    async def test_starts_process_in_workspace(self, tmp_path: Path) -> None:
        """The validated workspace becomes the language server cwd."""
        websocket = AsyncMock()
        process = MagicMock()
        process.poll.return_value = None

        with (
            patch.object(
                web,
                "type_mp",
                {"python": {"lsp": {"command": "ty server"}}},
            ),
            patch.object(web.subprocess, "Popen", return_value=process) as popen,
            patch.object(web.LspBridge, "start"),
        ):
            bridge = await web.start_lsp_process(websocket, "python", tmp_path)

        assert bridge is not None
        popen.assert_called_once()
        assert popen.call_args.kwargs["cwd"] == tmp_path
        assert popen.call_args.args[0] == ["ty", "server"]
        bridge.close()
