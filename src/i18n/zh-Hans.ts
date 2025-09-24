export default {
    settingPage: {
        title: "设置",
        search: "搜索设置...",
        group: {
            editor: "编辑器",
            programmingLanguages: "编程语言",
            tie: "Tie",
            keyboardShortcuts: "快捷键"
        },
        openConfigFile: "打开配置文件进行编辑",
        advance: "高级",
        about: "关于",
        licenses: "许可证",
        setting: {
            editor: {
                aceMain: {
                    fontSize: "字体大小",
                    fontFamily: "字体",
                    enableBasicAutocompletion: "自动补全",
                    enableSnippets: "启用代码片段",
                    enableLiveAutocompletion: "实时自动补全",
                    animatedScroll: "动画滚动",
                    scrollPastEnd: "滚动至末尾后继续",
                    showPrintMargin: "显示打印边距",
                    fixedWidthGutter: "固定宽度边栏",
                    fadeFoldWidgets: "折叠控件淡化",
                    displayIndentGuides: "显示缩进指示线",
                    highlightIndentGuides: "高亮缩进指示线",
                    highlightGutterLine: "高亮边栏行",
                    highlightActiveLine: "高亮当前行",
                    highlightSelectedWord: "高亮选中词",
                    cursorStyle: "光标样式",
                    tabSize: "Tab宽度",
                    tooltipFollowsMouse: "工具提示跟随鼠标",
                    foldStyle: "折叠样式"
                },
                tie: {
                    language: "语言",
                    theme: "主题"
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
                runJudge: "运行评测",
                formatCode: "格式化代码",
            }
        }
    },
    checkerPanel: {
        runAll: "运行全部",
        runAllStatus: "运行全部 | 编译中... | 运行中... | 全部完成",
        deleteTask: "删除测试点",
        clearAllTasks: "清空所有测试点",
        addTask: "添加测试点",
        input: "输入",
        answer: "答案",
        output: "输出",
        copyAll: "复制全部",
        copied: "已复制到剪贴板！",
        pasteFromClipboard: "从剪贴板粘贴",
        pasteError: "粘贴任务失败！请确保剪贴板内容为有效的任务数据。"
    },
    editorPage: {
        menu: {
            cut: "剪切",
            copy: "复制",
            paste: "粘贴",
            undo: "撤销",
            redo: "重做",
            selectAll: "全选",
            formatCode: "格式化代码",
            find: "查找",
            replace: "替换",
            goToLine: "跳转到行...",
            toggleComment: "切换注释",
            runTest: "运行测试",
            screenshot: "截图",
        },
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
        executable: `${langId}: 可执行文件`,
        compileCommand: `${langId}: 编译命令`,
        runCommand: `${langId}: 运行命令`,
        fileExtensions: `${langId}: 文件扩展名`,
        alias: `${langId}: 别名`,
        lsp: {
            command: `${langId}: LSP命令`
        },
        formatter: {
            active: `${langId}: 格式化工具启用`,
            command: `${langId}: 格式化工具命令`,
            action: `${langId}: 格式化后操作`,
        },
        enableCheckerPanel: `${langId}: 启用评测面板`
    };
}