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
    }
}
config = {
    "editor": {
        "aceMain": {
            "fontSize": 14,
            "fontFamily": "Fira Code, monospace",
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
}
