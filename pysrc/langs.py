"""Language configuration and runner/compilation utilities for TIE.

Defines language metadata, runners, compilers, and type mapping.
"""

from functools import partial

from .config import config
from .runner import run, run_compilation

lang_config = config["programmingLanguages"]
lang_cfg_python = lang_config["python"]
lang_cfg_cpp = lang_config["cpp"]
langs: list[dict] = []
lang_runners: dict = {}
lang_compilers: dict = {}
type_mp: dict = {}


def refresh_language_config() -> None:
    """Refresh derived language metadata after runtime configuration changes."""
    current_languages = config["programmingLanguages"]
    langs.clear()
    langs.extend(
        {
            "id": key,
            "suffix": value.get("fileExtensions", []),
            "alias": value.get("alias", []),
            "display": value.get("display", key),
            "runCommand": value.get("runCommand", ""),
            "compileCommand": value.get("compileCommand", ""),
            "executable": value.get("executable", ""),
            "lsp": value.get("lsp", {}),
        }
        for key, value in current_languages.items()
    )

    lang_runners.clear()
    lang_runners.update(
        {
            key: partial(
                run,
                cmd=value.get("runCommand", ""),
                executable=value.get("executable", ""),
            )
            for key, value in current_languages.items()
        },
    )
    lang_compilers.clear()
    lang_compilers.update(
        {
            key: partial(
                run_compilation,
                cmd=value.get("compileCommand", ""),
                executable=value.get("executable", ""),
            )
            for key, value in current_languages.items()
        },
    )

    type_mp.clear()
    for lang in langs:
        for key in lang["suffix"] + lang.get("alias", []):
            type_mp[key] = lang
        type_mp[lang["id"]] = lang


refresh_language_config()
