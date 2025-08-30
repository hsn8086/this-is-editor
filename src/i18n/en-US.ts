export default {

    settingPage: {
        title: "Settings",
        search: "Search settings...",
        group: {
            editor: "Editor",
            programmingLanguages: "Programming Languages",
            tie: "Tie",
            keyboardShortcuts: "Keyboard Shortcuts"
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
                ...genProgrammingLanguages([
                    ["python", "Python"],
                    ["cpp", "C++"],
                    ["json", "JSON"],
                ])
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

function genProgrammingLanguages(langMP: [string, string][]) {
    const res: { [key: string]: any } = {};
    for (const [lang, display] of langMP) {
        res[lang] = commonProgrammingLanguage(display);
    }
    return res;
}

function commonProgrammingLanguage(langId: string) {
    return {
        executable: `${langId}: Executable File`,
        compileCommand: `${langId}: Compile Command`,
        runCommand: `${langId}: Run Command`,
        fileExtensions: `${langId}: File Extensions`,
        alias: `${langId}: Alias`,
        lsp: {
            command: `${langId}: LSP Command`
        },
        formatter: {
            active: `${langId}: Formatter Enabled`,
            command: `${langId}: Formatter Command`,
            action: `${langId}: Post-Format Action`,
        },
        enableCheckerPanel: `${langId}: Enable Checker Panel`
    };
}