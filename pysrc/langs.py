from functools import partial

from .config import config
from .runner import compile, run

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
        compile,
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
