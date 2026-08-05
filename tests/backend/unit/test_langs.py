"""Tests for derived programming-language configuration."""

from unittest.mock import patch

from pysrc import langs


def test_refresh_language_config_updates_runtime_and_lsp_settings() -> None:
    """Tool selections are reflected without restarting the backend."""
    original_config = langs.config
    selected_config = {
        "programmingLanguages": {
            "python": {
                "executable": "/opt/python",
                "runCommand": "{executable} {file}",
                "compileCommand": "{executable} -m compileall {file}",
                "fileExtensions": [".py"],
                "alias": ["python3"],
                "lsp": {"command": "/opt/ty server"},
            },
        },
    }

    try:
        with patch.object(langs, "config", selected_config):
            langs.refresh_language_config()

            assert langs.langs[0]["executable"] == "/opt/python"
            assert langs.langs[0]["lsp"]["command"] == "/opt/ty server"
            assert langs.lang_runners["python"].keywords["executable"] == "/opt/python"
            assert langs.type_mp[".py"]["id"] == "python"
    finally:
        with patch.object(langs, "config", original_config):
            langs.refresh_language_config()
