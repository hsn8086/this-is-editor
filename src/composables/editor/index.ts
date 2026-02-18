/**
 * Editor Composables
 * 
 * 此目录包含与 Ace Editor 相关的可复用逻辑：
 * - useAceEditor: 编辑器实例管理
 * - useEditorTheme: 主题管理
 * - useEditorClipboard: 剪贴板操作（cut/copy/copyAll/paste）
 * - useEditorContextMenu: 右键菜单控制
 * - useEditorKeyboard: 键盘快捷键管理（Phase 2.1）
 * - useEditorFormat: 代码格式化（Phase 2.1）
 * - useEditorLsp: LSP 集成管理（Phase 2.2）
 * - useEditorScreenshot: 代码截图（Phase 2.3）
 */

export { useAceEditor, type UseAceEditorOptions, type UseAceEditorReturn } from './useAceEditor'
export { useEditorTheme, type UseEditorThemeOptions, type UseEditorThemeReturn, type AceTheme } from './useEditorTheme'
export { useEditorClipboard, type UseEditorClipboardOptions, type UseEditorClipboardReturn } from './useEditorClipboard'
export { useEditorContextMenu, type UseEditorContextMenuOptions, type UseEditorContextMenuReturn } from './useEditorContextMenu'
export { useEditorKeyboard, type UseEditorKeyboardOptions, type UseEditorKeyboardReturn, type KeyboardShortcut } from './useEditorKeyboard'
export { useEditorFormat, type UseEditorFormatOptions, type UseEditorFormatReturn, type FormatAction, type FormatterConfig } from './useEditorFormat'
export { useEditorLsp, type UseEditorLspOptions, type UseEditorLspReturn } from './useEditorLsp'
export { useEditorScreenshot, type UseEditorScreenshotOptions, type UseEditorScreenshotReturn } from './useEditorScreenshot'
