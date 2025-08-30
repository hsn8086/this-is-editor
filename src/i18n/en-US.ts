export default {

    settingPage: {
        title: "Settings",
        search: "Search settings...",
        group: {
            editor: "Editor",
            programmingLanguages: "Programming Languages",
            tie: "Tie"
        },
        openConfigFile: "Open config file to edit",
        advance: "Advance",
        about: "About",
        licenses: "Licenses",
        setting: {
            editor: {
                aceMain: {
                    fontSize: "Font Size",
                    fontFamily: "Font Family",
                    enableBasicAutocompletion: "Autocompletion",
                    enableSnippets: "Enable Snippets",
                    enableLiveAutocompletion: "Live Autocompletion",
                    animatedScroll: "Animated Scroll",
                    scrollPastEnd: "Scroll Past End",
                    showPrintMargin: "Show Print Margin",
                    fixedWidthGutter: "Fixed Width Gutter",
                    fadeFoldWidgets: "Fade Fold Widgets",
                    displayIndentGuides: "Display Indent Guides",
                    highlightIndentGuides: "Highlight Indent Guides",
                    highlightGutterLine: "Highlight Gutter Line",
                    highlightActiveLine: "Highlight Active Line",
                    highlightSelectedWord: "Highlight Selected Word",
                    cursorStyle: "Cursor Style",
                    tabSize: "Tab Size",
                    tooltipFollowsMouse: "Tooltip Follows Mouse",
                    foldStyle: "Fold Style"
                },
                tie: {
                    theme: "Theme",
                    language: "Language"
                }
            },
            programmingLanguages: {
                python: {
                    executable: "Python: Executable",
                    compileCommand: "Python: Compile Command",
                    runCommand: "Python: Run Command",
                    fileExtensions: "Python: File Extensions",
                    alias: "Python: Alias",
                    lsp: {
                        command: "Python: LSP Command"
                    },
                    formatter: {
                        active: "Python: Formatter Active",
                        command: "Python: Formatter Command",
                        action: "Python: Formatter Action",
                    }
                },
                cpp: {
                    executable: "C++: Executable",
                    compileCommand: "C++: Compile Command",
                    runCommand: "C++: Run Command",
                    fileExtensions: "C++: File Extensions",
                    alias: "C++: Alias",
                    lsp: {
                        command: "C++: LSP Command"
                    },
                    formatter: {
                        active: "C++: Formatter Active",
                        command: "C++: Formatter Command",
                        action: "C++: Formatter Action",
                    }
                }
            },
            keyboardShortcuts: {
                runJudge: "Run Judge",
                formatCode: "Format Code",
            }
        }
    },
    checkerPanel: {
        runAllStatus: "Run All | Compiling... | Running... | All Done",
        deleteTask: "Delete Task",
        clearAllTasks: "Clear All Tasks",
        addTask: "Add Task",
        input: "Input",
        answer: "Answer",
        output: "Output",
        copyAll: "Copy All",
        copied: "Copied to clipboard!",
        pasteFromClipboard: "Paste from Clipboard",
        pasteError: "Failed to paste tasks! Please ensure the clipboard contains valid task data."
    }
}