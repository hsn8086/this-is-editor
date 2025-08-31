"""Language configuration and runner/compilation utilities for TIE.

Defines language metadata, runners, compilers, and type mapping.
"""

from functools import partial

from .config import config
from .runner import run, run_compilation

lang_config = config["programmingLanguages"]
lang_cfg_python = lang_config["python"]
lang_cfg_cpp = lang_config["cpp"]
langs = [
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
    for key, value in lang_config.items()
]
lang_runners = {
    key: partial(
        run,
        cmd=value.get("runCommand", ""),
        executable=value.get("executable", ""),
    )
    for key, value in lang_config.items()
}
lang_compilers = {
    key: partial(
        run_compilation,
        cmd=value.get("compileCommand", ""),
        executable=value.get("executable", ""),
    )
    for key, value in lang_config.items()
}
type_mp = {}
for lang in langs:
    for key in lang["suffix"] + lang.get("alias", []):
        type_mp[key] = lang
    type_mp[lang["id"]] = lang
