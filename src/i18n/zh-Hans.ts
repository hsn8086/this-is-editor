export default {
  environmentPage: {
    eyebrow: '工具链检查',
    title: '开发环境',
    summary: '已就绪 {ready}/{total} 项工具',
    scanning: '正在扫描已安装工具...',
    rescan: '重新扫描',
    continue: '进入编辑器',
    backToSettings: '返回设置',
    required: '必需',
    guidance: '所有环境均可跳过；“必需”仅表示对应语言功能的建议依赖，不会阻止进入编辑器。检测到多个版本时可在此选择默认工具。',
    scanFailed: '无法完成环境扫描。',
    selectionFailed: '无法保存所选环境。',
    role: {
      runtime: '运行时 / 编译器',
      analysis: '代码分析',
      format: '代码格式化',
    },
    status: {
      ready: '已就绪',
      missing: '未找到',
      error: '无法运行',
    },
  },
  settingPage: {
    title: '设置',
    search: '搜索设置...',
    restartRequired: '重启后生效',
    group: {
      editor: '编辑器',
      programmingLanguages: '编程语言',
      tie: 'Tie',
      keyboardShortcuts: '快捷键',
    },
    openConfigFile: '打开配置文件进行编辑',
    environmentDiagnostics: '环境诊断',
    advance: '高级',
    about: '关于',
    licenses: '许可证',
    setting: {
      editor: {
        aceMain: {
          fontSize: '字体大小',
          fontFamily: '字体',
          enableBasicAutocompletion: '自动补全',
          enableSnippets: '代码片段自动补全',
          enableLiveAutocompletion: '实时自动补全',
          animatedScroll: '动画滚动',
          scrollPastEnd: '滚动至末尾后继续',
          showPrintMargin: '显示打印边距',
          fixedWidthGutter: '固定宽度边栏',
          fadeFoldWidgets: '折叠控件淡化',
          displayIndentGuides: '显示缩进指示线',
          highlightIndentGuides: '高亮缩进指示线',
          highlightGutterLine: '高亮边栏行',
          highlightActiveLine: '高亮当前行',
          highlightSelectedWord: '高亮选中词',
          cursorStyle: '光标样式',
          tabSize: 'Tab宽度',
          tooltipFollowsMouse: '工具提示跟随鼠标',
          foldStyle: '折叠样式',
        },
        tie: {
          language: '语言',
          theme: '主题',
        },
      },
      programmingLanguages: {
        ...genProgrammingLanguages([
          ['python', 'Python'],
          ['cpp', 'C++'],
          ['json', 'JSON'],
        ]),
      },
      keyboardShortcuts: {
        runJudge: '运行评测',
        formatCode: '格式化代码',
      },
    },
  },
  checkerPanel: {
    runAll: '运行全部',
    runAllStatus: '运行全部 | 编译中... | 运行中... | 全部完成',
    deleteTask: '删除测试点',
    clearAllTasks: '清空所有测试点',
    addTask: '添加测试点',
    input: '输入',
    answer: '答案',
    output: '输出',
    copyAll: '复制全部',
    copied: '已复制到剪贴板！',
    pasteFromClipboard: '从剪贴板粘贴',
    pasteError: '粘贴任务失败！请确保剪贴板内容为有效的任务数据。',
  },
  terminalPanel: {
    title: '终端',
    toggle: '切换终端',
    clear: '清屏',
    interrupt: '中断 (Ctrl-C)',
    hide: '隐藏终端',
    resize: '拖动调整高度',
    exited: '已退出 {code}',
  },
  editorPage: {
    menu: {
      cut: '剪切',
      copy: '复制',
      copyAll: '复制全部',
      paste: '粘贴',
      undo: '撤销',
      redo: '重做',
      selectAll: '全选',
      formatCode: '格式化代码',
      find: '查找',
      replace: '替换',
      goToLine: '跳转到行...',
      toggleComment: '切换注释',
      runTest: '运行测试',
      screenshot: '截图',
      toggleTerminal: '切换终端',
    },
  },
}

function genProgrammingLanguages (langMP: [string, string][]) {
  const res: { [key: string]: any } = {}
  for (const [lang, display] of langMP) {
    res[lang] = commonProgrammingLanguage(display)
  }
  return res
}

function commonProgrammingLanguage (langId: string) {
  return {
    executable: `${langId}: 可执行文件`,
    compileCommand: `${langId}: 编译命令`,
    runCommand: `${langId}: 运行命令`,
    fileExtensions: `${langId}: 文件扩展名`,
    alias: `${langId}: 别名`,
    lsp: {
      command: `${langId}: LSP命令`,
    },
    formatter: {
      active: `${langId}: 格式化工具启用`,
      command: `${langId}: 格式化工具命令`,
      action: `${langId}: 格式化后操作`,
    },
    enableCheckerPanel: `${langId}: 启用评测面板`,
  }
}
