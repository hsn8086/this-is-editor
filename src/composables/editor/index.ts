/**
 * Editor Composables
 * 
 * 此目录包含与 Ace Editor 相关的可复用逻辑：
 * - useAceEditor: 编辑器实例管理
 * - useEditorTheme: 主题管理
 * - useEditorClipboard: 剪贴板操作（cut/copy/copyAll/paste）
 * - useEditorContextMenu: 右键菜单控制
 */

export { useAceEditor, type UseAceEditorOptions, type UseAceEditorReturn } from './useAceEditor'
export { useEditorTheme, type UseEditorThemeOptions, type UseEditorThemeReturn, type AceTheme } from './useEditorTheme'
export { useEditorClipboard, type UseEditorClipboardOptions, type UseEditorClipboardReturn } from './useEditorClipboard'
export { useEditorContextMenu, type UseEditorContextMenuOptions, type UseEditorContextMenuReturn } from './useEditorContextMenu'
