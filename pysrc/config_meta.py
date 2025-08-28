config_meta = {
    "editor": {
        "aceMain": {
            "fontSize": {"display": "Font Size"},
            "fontFamily": {"display": "Font Family"},
            "enableBasicAutocompletion": {"display": "Autocompletion"},
            "enableSnippets": {"display": "Enable Snippets"},
            "enableLiveAutocompletion": {"display": "Live Autocompletion"},
            "animatedScroll": {"display": "Animated Scroll"},
            "scrollPastEnd": {"display": "Scroll Past End"},
            "showPrintMargin": {"display": "Show Print Margin"},
            "fixedWidthGutter": {"display": "Fixed Width Gutter"},
            "fadeFoldWidgets": {"display": "Fade Fold Widgets"},
            "displayIndentGuides": {"display": "Display Indent Guides"},
            "highlightIndentGuides": {"display": "Highlight Indent Guides"},
            "highlightGutterLine": {"display": "Highlight Gutter Line"},
            "highlightActiveLine": {"display": "Highlight Active Line"},
            "highlightSelectedWord": {"display": "Highlight Selected Word"},
            "cursorStyle": {
                "display": "Cursor Style",
                "enum": ["smooth", "slim", "wide", "ace", "smoothwide"],
            },
            "tabSize": {"display": "Tab Size"},
            "tooltipFollowsMouse": {"display": "Tooltip Follows Mouse"},
            "foldStyle": {
                "display": "Fold Style",
                "enum": ["markbeginend", "manual", "markbegin"],
            },
        },
        "tie": {
            "theme": {"display": "Theme", "enum": ["light", "dark", "system"]},
        },
    },
    "programmingLanguages": {
        "python": {
            "executable": {"display": "Python: Executable"},
            "compileCommand": {"display": "Python: Compile Command"},
            "runCommand": {"display": "Python: Run Command"},
            "fileExtensions": {"display": "Python: File Extensions"},
            "alias": {"display": "Python: Alias"},
            "lsp": {
                "command": {"display": "Python: LSP Command"},
            },
        },
        "cpp": {
            "executable": {"display": "C++: Executable"},
            "compileCommand": {"display": "C++: Compile Command"},
            "runCommand": {"display": "C++: Run Command"},
            "fileExtensions": {"display": "C++: File Extensions"},
            "alias": {"display": "C++: Alias"},
            "lsp": {
                "command": {"display": "C++: LSP Command"},
            },
        },
    },
}
config = {
    "editor": {
        "aceMain": {
            "fontSize": 14,
            "fontFamily": "Maple Mono, Maple Mono NF CN, Fira Code, monospace",
            "enableBasicAutocompletion": True,
            "enableSnippets": False,
            "enableLiveAutocompletion": True,
            "animatedScroll": True,
            "scrollPastEnd": True,
            "showPrintMargin": False,
            "fixedWidthGutter": True,
            "fadeFoldWidgets": True,
            "displayIndentGuides": False,
            "highlightIndentGuides": True,
            "highlightGutterLine": True,
            "highlightActiveLine": True,
            "highlightSelectedWord": True,
            "cursorStyle": "smooth",
            "tabSize": 4,
            "tooltipFollowsMouse": True,
            "foldStyle": "markbeginend",
        },
        "tie": {"theme": "system"},
    },
    "programmingLanguages": {
        "python": {
            "executable": "python3",
            "compileCommand": "{executable} -m compileall -o 2 -b {file}",
            "runCommand": "{executable} {fileStem}.pyc",
            "fileExtensions": [".py"],
            "alias": ["py", "python", "Python", "python3", "Python3"],
            "display": "Python Source",
            "lsp": {
                "command": "pylsp",
            },
        },
        "cpp": {
            "executable": "g++",
            "compileCommand": "{executable} {file} "
            "-O 2 -Wall -Wextra -std=c++20 -o {fileStem}",
            "runCommand": "{fileStem}",
            "fileExtensions": [".cpp", ".cc", ".cxx", ".c++", ".C"],
            "alias": ["cpp", "Cpp", "CPP", "c++", "C++", "c_cpp"],
            "display": "C++ Source",
            "lsp": {
                "command": "clangd",
            },
        },
    },
}
