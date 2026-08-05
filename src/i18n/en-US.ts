export default {

  environmentPage: {
    eyebrow: 'Toolchain check',
    title: 'Development environment',
    summary: '{ready} of {total} tools ready',
    scanning: 'Scanning installed tools...',
    rescan: 'Scan again',
    continue: 'Continue to editor',
    backToSettings: 'Back to settings',
    required: 'Required',
    guidance: 'Every environment can be skipped. Required only marks a recommended dependency for that language and never blocks the editor. Choose the default tool here when multiple versions are found.',
    scanFailed: 'The environment scan could not be completed.',
    selectionFailed: 'The selected environment could not be saved.',
    role: {
      runtime: 'Runtime / compiler',
      analysis: 'Code analysis',
      format: 'Formatting',
    },
    status: {
      ready: 'Ready',
      missing: 'Not found',
      error: 'Could not run',
    },
  },

  settingPage: {
    title: 'Settings',
    search: 'Search settings...',
    restartRequired: 'Takes effect after restart',
    group: {
      editor: 'Editor',
      programmingLanguages: 'Programming Languages',
      tie: 'Tie',
      keyboardShortcuts: 'Keyboard Shortcuts',
    },
    openConfigFile: 'Open config file to edit',
    environmentDiagnostics: 'Environment diagnostics',
    advance: 'Advance',
    about: 'About',
    licenses: 'Licenses',
    setting: {
      editor: {
        aceMain: {
          fontSize: 'Font Size',
          fontFamily: 'Font Family',
          enableBasicAutocompletion: 'Autocompletion',
          enableSnippets: 'Snippet Autocompletion',
          enableLiveAutocompletion: 'Live Autocompletion',
          animatedScroll: 'Animated Scroll',
          scrollPastEnd: 'Scroll Past End',
          showPrintMargin: 'Show Print Margin',
          fixedWidthGutter: 'Fixed Width Gutter',
          fadeFoldWidgets: 'Fade Fold Widgets',
          displayIndentGuides: 'Display Indent Guides',
          highlightIndentGuides: 'Highlight Indent Guides',
          highlightGutterLine: 'Highlight Gutter Line',
          highlightActiveLine: 'Highlight Active Line',
          highlightSelectedWord: 'Highlight Selected Word',
          cursorStyle: 'Cursor Style',
          tabSize: 'Tab Size',
          tooltipFollowsMouse: 'Tooltip Follows Mouse',
          foldStyle: 'Fold Style',
        },
        tie: {
          theme: 'Theme',
          language: 'Language',
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
        runJudge: 'Run Judge',
        formatCode: 'Format Code',
      },
    },
  },
  checkerPanel: {
    runAllStatus: 'Run All | Compiling... | Running... | All Done',
    deleteTask: 'Delete Task',
    clearAllTasks: 'Clear All Tasks',
    addTask: 'Add Task',
    input: 'Input',
    answer: 'Answer',
    output: 'Output',
    copyAll: 'Copy All',
    copied: 'Copied to clipboard!',
    pasteFromClipboard: 'Paste from Clipboard',
    pasteError: 'Failed to paste tasks! Please ensure the clipboard contains valid task data.',
  },
  terminalPanel: {
    title: 'Terminal',
    toggle: 'Toggle Terminal',
    clear: 'Clear',
    interrupt: 'Interrupt (Ctrl-C)',
    hide: 'Hide Terminal',
    resize: 'Drag to resize',
    exited: 'exited {code}',
  },
  editorPage: {
    menu: {
      cut: 'Cut',
      copy: 'Copy',
      copyAll: 'Copy All',
      paste: 'Paste',
      undo: 'Undo',
      redo: 'Redo',
      selectAll: 'Select All',
      formatCode: 'Format Code',
      find: 'Find',
      replace: 'Replace',
      goToLine: 'Go to Line...',
      toggleComment: 'Toggle Comment',
      runTest: 'Run Test',
      screenshot: 'Take Screenshot',
      toggleTerminal: 'Toggle Terminal',
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
    executable: `${langId}: Executable File`,
    compileCommand: `${langId}: Compile Command`,
    runCommand: `${langId}: Run Command`,
    fileExtensions: `${langId}: File Extensions`,
    alias: `${langId}: Alias`,
    lsp: {
      command: `${langId}: LSP Command`,
    },
    formatter: {
      active: `${langId}: Formatter Enabled`,
      command: `${langId}: Formatter Command`,
      action: `${langId}: Post-Format Action`,
    },
    enableCheckerPanel: `${langId}: Enable Checker Panel`,
  }
}
