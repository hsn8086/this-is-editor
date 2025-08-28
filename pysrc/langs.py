from functools import partial

from pysrc.runner import compile_c_cpp_builder, run_c_cpp, run_python

langs = [
    {
        "id": "python",
        "display": "Python Source",
        "lsp": ["uv", "run", "pylsp"],
        # "lsp": ["ruff", "server"],
        # "lsp": ["uv", "run", "pyright-langserver", "--stdio"],
        "suffix": [".py"],
        "alias": ["py", "Python", "python3"],
    },
    {
        "id": "cpp",
        "display": "C++ Source",
        "lsp": ["clangd"],
        "suffix": [".cpp", ".cxx", ".cc", ".c++", ".hpp"],
        "alias": ["C++", "c++", "c_cpp"],
    },
]
lang_runners = {
    "python": partial(run_python, version="python"),
    "cpp": partial(run_c_cpp),
    "c": partial(
        run_c_cpp,
    ),
}
lang_compilers = {
    "cpp": compile_c_cpp_builder("gnu++23", "c++", ["-O2", "-Wall", "-Wextra"]),
    "c": compile_c_cpp_builder("gcc", "c", ["-O2", "-Wall", "-Wextra"]),
}
type_mp = {}
for lang in langs:
    for key in lang["suffix"] + lang.get("alias", []):
        type_mp[key] = lang
    type_mp[lang["id"]] = lang
