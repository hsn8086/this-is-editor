config_meta = {
    "editor": {
        "aceMain": {
            "fontSize": {
                "display": "Font Size",
                "i18n": "setting.editor.aceMain.fontSize",
            },
            "fontFamily": {
                "display": "Font Family",
                "i18n": "setting.editor.aceMain.fontFamily",
            },
            "enableBasicAutocompletion": {
                "display": "Autocompletion",
                "i18n": "setting.editor.aceMain.enableBasicAutocompletion",
            },
            "enableSnippets": {
                "display": "Enable Snippets",
                "i18n": "setting.editor.aceMain.enableSnippets",
            },
            "enableLiveAutocompletion": {
                "display": "Live Autocompletion",
                "i18n": "setting.editor.aceMain.enableLiveAutocompletion",
            },
            "animatedScroll": {
                "display": "Animated Scroll",
                "i18n": "setting.editor.aceMain.animatedScroll",
            },
            "scrollPastEnd": {
                "display": "Scroll Past End",
                "i18n": "setting.editor.aceMain.scrollPastEnd",
            },
            "showPrintMargin": {
                "display": "Show Print Margin",
                "i18n": "setting.editor.aceMain.showPrintMargin",
            },
            "fixedWidthGutter": {
                "display": "Fixed Width Gutter",
                "i18n": "setting.editor.aceMain.fixedWidthGutter",
            },
            "fadeFoldWidgets": {
                "display": "Fade Fold Widgets",
                "i18n": "setting.editor.aceMain.fadeFoldWidgets",
            },
            "displayIndentGuides": {
                "display": "Display Indent Guides",
                "i18n": "setting.editor.aceMain.displayIndentGuides",
            },
            "highlightIndentGuides": {
                "display": "Highlight Indent Guides",
                "i18n": "setting.editor.aceMain.highlightIndentGuides",
            },
            "highlightGutterLine": {
                "display": "Highlight Gutter Line",
                "i18n": "setting.editor.aceMain.highlightGutterLine",
            },
            "highlightActiveLine": {
                "display": "Highlight Active Line",
                "i18n": "setting.editor.aceMain.highlightActiveLine",
            },
            "highlightSelectedWord": {
                "display": "Highlight Selected Word",
                "i18n": "setting.editor.aceMain.highlightSelectedWord",
            },
            "cursorStyle": {
                "display": "Cursor Style",
                "i18n": "setting.editor.aceMain.cursorStyle",
                "enum": ["smooth", "slim", "wide", "ace", "smoothwide"],
            },
            "tabSize": {
                "display": "Tab Size",
                "i18n": "setting.editor.aceMain.tabSize",
            },
            "tooltipFollowsMouse": {
                "display": "Tooltip Follows Mouse",
                "i18n": "setting.editor.aceMain.tooltipFollowsMouse",
            },
            "foldStyle": {
                "display": "Fold Style",
                "i18n": "setting.editor.aceMain.foldStyle",
                "enum": ["markbeginend", "manual", "markbegin"],
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
            },
            "compileCommand": {
                "display": "Python: Compile Command",
                "i18n": "setting.programmingLanguages.python.compileCommand",
            },
            "runCommand": {
                "display": "Python: Run Command",
                "i18n": "setting.programmingLanguages.python.runCommand",
            },
            "fileExtensions": {
                "display": "Python: File Extensions",
                "i18n": "setting.programmingLanguages.python.fileExtensions",
            },
            "alias": {
                "display": "Python: Alias",
                "i18n": "setting.programmingLanguages.python.alias",
            },
            "lsp": {
                "command": {
                    "display": "Python: LSP Command",
                    "i18n": "setting.programmingLanguages.python.lsp.command",
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
                    "enum": ["reload", "stdout", " none"],
                },
                "active": {
                    "display": "Python: Formatter Active",
                    "i18n": "setting.programmingLanguages.python.formatter.active",
                },
            },
        },
        "cpp": {
            "executable": {
                "display": "C++: Executable",
                "i18n": "setting.programmingLanguages.cpp.executable",
            },
            "compileCommand": {
                "display": "C++: Compile Command",
                "i18n": "setting.programmingLanguages.cpp.compileCommand",
            },
            "runCommand": {
                "display": "C++: Run Command",
                "i18n": "setting.programmingLanguages.cpp.runCommand",
            },
            "fileExtensions": {
                "display": "C++: File Extensions",
                "i18n": "setting.programmingLanguages.cpp.fileExtensions",
            },
            "alias": {
                "display": "C++: Alias",
                "i18n": "setting.programmingLanguages.cpp.alias",
            },
            "lsp": {
                "command": {
                    "display": "C++: LSP Command",
                    "i18n": "setting.programmingLanguages.cpp.lsp.command",
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
                    "enum": ["reload", "stdout", " none"],
                },
                "active": {
                    "display": "C++: Formatter Active",
                    "i18n": "setting.programmingLanguages.cpp.formatter.active",
                },
            },
        },
    },
    "keyboardShortcuts": {
        "runJudge": {
            "display": "Run Judge",
            "i18n": "setting.keyboardShortcuts.runJudge",
        },
        "formatCode": {
            "display": "Format Code",
            "i18n": "setting.keyboardShortcuts.formatCode",
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
                "command": "pylsp",
            },
            "formatter": {
                "active": True,
                "command": "ruff format {file}",
                "action": "reload",
            },
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
        },
    },
    "keyboardShortcuts": {
        "runJudge": "F5",
        "formatCode": "Ctrl-Alt-L",
    },
}
