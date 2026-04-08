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
 * - useEditorFileSync: 文件同步与自动保存（Phase 2.4）
 *   - 单次 debounce（500ms）保存
 *   - 输入变更时立即更新 lastModified（用于 1000ms 冷却判断）
 *   - 基础函数无副作用，事件监听在 useEditorFileSyncWithListener 中管理
 */

export { useAceEditor, type UseAceEditorOptions, type UseAceEditorReturn } from './useAceEditor'
export { useEditorClipboard, type UseEditorClipboardOptions, type UseEditorClipboardReturn } from './useEditorClipboard'
export { useEditorContextMenu, type UseEditorContextMenuOptions, type UseEditorContextMenuReturn } from './useEditorContextMenu'
export {
  useEditorFileSync,
  type UseEditorFileSyncOptions,
  type UseEditorFileSyncReturn,
  useEditorFileSyncWithListener,
  type UseEditorFileSyncWithListenerOptions,
  type UseEditorFileSyncWithListenerReturn,
} from './useEditorFileSync'
export { type FormatAction, type FormatterConfig, useEditorFormat, type UseEditorFormatOptions, type UseEditorFormatReturn } from './useEditorFormat'
export { type KeyboardShortcut, useEditorKeyboard, type UseEditorKeyboardOptions, type UseEditorKeyboardReturn } from './useEditorKeyboard'
export { useEditorLsp, type UseEditorLspOptions, type UseEditorLspReturn } from './useEditorLsp'
export { useEditorScreenshot, type UseEditorScreenshotOptions, type UseEditorScreenshotReturn } from './useEditorScreenshot'
export { type AceTheme, useEditorTheme, type UseEditorThemeOptions, type UseEditorThemeReturn } from './useEditorTheme'
