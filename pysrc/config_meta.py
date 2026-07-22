"""Contains configuration metadata and default settings for the editor.

- `config_meta`: Metadata for configuration options.
- `config`: Default configuration values for the editor.
"""

config_meta = {
    "editor": {
        "aceMain": {
            "fontSize": {
                "display": "Font Size",
                "i18n": "setting.editor.aceMain.fontSize",
                "requiresRestart": True,
            },
            "fontFamily": {
                "display": "Font Family",
                "i18n": "setting.editor.aceMain.fontFamily",
                "requiresRestart": True,
            },
            "enableBasicAutocompletion": {
                "display": "Autocompletion",
                "i18n": "setting.editor.aceMain.enableBasicAutocompletion",
                "requiresRestart": True,
            },
            "enableSnippets": {
                "display": "Enable Snippets",
                "i18n": "setting.editor.aceMain.enableSnippets",
                "requiresRestart": True,
            },
            "enableLiveAutocompletion": {
                "display": "Live Autocompletion",
                "i18n": "setting.editor.aceMain.enableLiveAutocompletion",
                "requiresRestart": True,
            },
            "animatedScroll": {
                "display": "Animated Scroll",
                "i18n": "setting.editor.aceMain.animatedScroll",
                "requiresRestart": True,
            },
            "scrollPastEnd": {
                "display": "Scroll Past End",
                "i18n": "setting.editor.aceMain.scrollPastEnd",
                "requiresRestart": True,
            },
            "showPrintMargin": {
                "display": "Show Print Margin",
                "i18n": "setting.editor.aceMain.showPrintMargin",
                "requiresRestart": True,
            },
            "fixedWidthGutter": {
                "display": "Fixed Width Gutter",
                "i18n": "setting.editor.aceMain.fixedWidthGutter",
                "requiresRestart": True,
            },
            "fadeFoldWidgets": {
                "display": "Fade Fold Widgets",
                "i18n": "setting.editor.aceMain.fadeFoldWidgets",
                "requiresRestart": True,
            },
            "displayIndentGuides": {
                "display": "Display Indent Guides",
                "i18n": "setting.editor.aceMain.displayIndentGuides",
                "requiresRestart": True,
            },
            "highlightIndentGuides": {
                "display": "Highlight Indent Guides",
                "i18n": "setting.editor.aceMain.highlightIndentGuides",
                "requiresRestart": True,
            },
            "highlightGutterLine": {
                "display": "Highlight Gutter Line",
                "i18n": "setting.editor.aceMain.highlightGutterLine",
                "requiresRestart": True,
            },
            "highlightActiveLine": {
                "display": "Highlight Active Line",
                "i18n": "setting.editor.aceMain.highlightActiveLine",
                "requiresRestart": True,
            },
            "highlightSelectedWord": {
                "display": "Highlight Selected Word",
                "i18n": "setting.editor.aceMain.highlightSelectedWord",
                "requiresRestart": True,
            },
            "cursorStyle": {
                "display": "Cursor Style",
                "i18n": "setting.editor.aceMain.cursorStyle",
                "enum": ["smooth", "slim", "wide", "ace", "smoothwide"],
                "requiresRestart": True,
            },
            "tabSize": {
                "display": "Tab Size",
                "i18n": "setting.editor.aceMain.tabSize",
                "requiresRestart": True,
            },
            "tooltipFollowsMouse": {
                "display": "Tooltip Follows Mouse",
                "i18n": "setting.editor.aceMain.tooltipFollowsMouse",
                "requiresRestart": True,
            },
            "foldStyle": {
                "display": "Fold Style",
                "i18n": "setting.editor.aceMain.foldStyle",
                "enum": ["markbeginend", "manual", "markbegin"],
                "requiresRestart": True,
            },
        },
        "tie": {
            "theme": {
                "display": "Theme",
                "i18n": "setting.editor.tie.theme",
                "enum": ["light", "dark", "system"],
            },
            "language": {
                "display": "Language",
                "i18n": "setting.editor.tie.language",
                "enum": ["en-US", "zh-Hans"],
            },
        },
    },
    "programmingLanguages": {
        "python": {
            "executable": {
                "display": "Python: Executable",
                "i18n": "setting.programmingLanguages.python.executable",
                "requiresRestart": True,
            },
            "compileCommand": {
                "display": "Python: Compile Command",
                "i18n": "setting.programmingLanguages.python.compileCommand",
                "requiresRestart": True,
            },
            "runCommand": {
                "display": "Python: Run Command",
                "i18n": "setting.programmingLanguages.python.runCommand",
                "requiresRestart": True,
            },
            "fileExtensions": {
                "display": "Python: File Extensions",
                "i18n": "setting.programmingLanguages.python.fileExtensions",
                "requiresRestart": True,
            },
            "alias": {
                "display": "Python: Alias",
                "i18n": "setting.programmingLanguages.python.alias",
                "requiresRestart": True,
            },
            "lsp": {
                "command": {
                    "display": "Python: LSP Command",
                    "i18n": "setting.programmingLanguages.python.lsp.command",
                    "requiresRestart": True,
                },
            },
            "formatter": {
                "command": {
                    "display": "Python: Formatter Command",
                    "i18n": "setting.programmingLanguages.python.formatter.command",
                },
                "action": {
                    "display": "Python: Formatter Action",
                    "i18n": "setting.programmingLanguages.python.formatter.action",
                    "enum": ["reload", "stdout", "skip"],
                },
                "active": {
                    "display": "Python: Formatter Active",
                    "i18n": "setting.programmingLanguages.python.formatter.active",
                },
            },
            "enableCheckerPanel": {
                "display": "Python: Enable Checker Panel",
                "i18n": "setting.programmingLanguages.python.enableCheckerPanel",
            },
        },
        "cpp": {
            "executable": {
                "display": "C++: Executable",
                "i18n": "setting.programmingLanguages.cpp.executable",
                "requiresRestart": True,
            },
            "compileCommand": {
                "display": "C++: Compile Command",
                "i18n": "setting.programmingLanguages.cpp.compileCommand",
                "requiresRestart": True,
            },
            "runCommand": {
                "display": "C++: Run Command",
                "i18n": "setting.programmingLanguages.cpp.runCommand",
                "requiresRestart": True,
            },
            "fileExtensions": {
                "display": "C++: File Extensions",
                "i18n": "setting.programmingLanguages.cpp.fileExtensions",
                "requiresRestart": True,
            },
            "alias": {
                "display": "C++: Alias",
                "i18n": "setting.programmingLanguages.cpp.alias",
                "requiresRestart": True,
            },
            "lsp": {
                "command": {
                    "display": "C++: LSP Command",
                    "i18n": "setting.programmingLanguages.cpp.lsp.command",
                    "requiresRestart": True,
                },
            },
            "formatter": {
                "command": {
                    "display": "C++: Formatter Command",
                    "i18n": "setting.programmingLanguages.cpp.formatter.command",
                },
                "action": {
                    "display": "C++: Formatter Action",
                    "i18n": "setting.programmingLanguages.cpp.formatter.action",
                    "enum": ["reload", "stdout", "skip"],
                },
                "active": {
                    "display": "C++: Formatter Active",
                    "i18n": "setting.programmingLanguages.cpp.formatter.active",
                },
            },
            "enableCheckerPanel": {
                "display": "C++: Enable Checker Panel",
                "i18n": "setting.programmingLanguages.cpp.enableCheckerPanel",
            },
        },
        "json": {
            "alias": {
                "display": "JSON: Alias",
                "i18n": "setting.programmingLanguages.json.alias",
                "requiresRestart": True,
            },
            "fileExtensions": {
                "display": "JSON: File Extensions",
                "i18n": "setting.programmingLanguages.json.fileExtensions",
                "requiresRestart": True,
            },
        },
    },
    "keyboardShortcuts": {
        "runJudge": {
            "display": "Run Judge",
            "i18n": "setting.keyboardShortcuts.runJudge",
            "requiresRestart": True,
        },
        "formatCode": {
            "display": "Format Code",
            "i18n": "setting.keyboardShortcuts.formatCode",
            "requiresRestart": True,
        },
    },
}
config = {
    "editor": {
        "aceMain": {
            "fontSize": 14,
            "fontFamily": "Maple Mono, Maple Mono NF CN, Fira Code, monospace",
            "enableBasicAutocompletion": True,
            "enableSnippets": True,
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
        "tie": {"theme": "system", "language": "en-US"},
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
                "command": "ty server",
            },
            "formatter": {
                "active": True,
                "command": "ruff format {file}",
                "action": "reload",
            },
            "enableCheckerPanel": True,
        },
        "cpp": {
            "executable": "g++",
            "compileCommand": "{executable} {file} "
            "-O2 -Wall -Wextra -std=c++20 -o {fileStem}.out",
            "runCommand": "{fileWithoutExt}.out",
            "fileExtensions": [".cpp", ".cc", ".cxx", ".c++", ".C"],
            "alias": ["cpp", "Cpp", "CPP", "c++", "C++", "c_cpp"],
            "display": "C++ Source",
            "lsp": {
                "command": "clangd",
            },
            "formatter": {
                "active": True,
                "command": "clang-format -style=file -i {file}",
                "action": "reload",
            },
            "enableCheckerPanel": True,
        },
        "json": {
            "alias": ["json", "JSON", "Json", "json5", "JSON5", "Json5"],
            "fileExtensions": [".json", ".json5"],
            "display": "JSON File",
        },
    },
    "keyboardShortcuts": {
        "runJudge": "F5",
        "formatCode": "Ctrl-Alt-L",
    },
}
