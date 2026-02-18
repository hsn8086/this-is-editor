/**
 * Editor Composables
 * 
 * 此目录包含与 Ace Editor 相关的可复用逻辑：
 * - useAceEditor: 编辑器实例管理
 * - useEditorTheme: 主题管理
 */

export { useAceEditor, type UseAceEditorOptions, type UseAceEditorReturn } from './useAceEditor'
export { useEditorTheme, type UseEditorThemeOptions, type UseEditorThemeReturn, type AceTheme } from './useEditorTheme'
