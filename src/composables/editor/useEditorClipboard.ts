import { ref, type Ref } from 'vue'
import type { Ace } from 'ace-builds'

export interface UseEditorClipboardOptions {
  /** Ace Editor 实例 Ref */
  editor: Ref<Ace.Editor | undefined>
}

export interface UseEditorClipboardReturn {
  /** 是否正在执行剪贴板操作 */
  isProcessing: Ref<boolean>
  /** 剪切：优先选区，否则当前行 */
  cut: () => Promise<void>
  /** 复制：优先选区，否则当前行 */
  copy: () => Promise<void>
  /** 复制全部内容 */
  copyAll: () => Promise<void>
  /** 粘贴：读取剪贴板并插入光标位置 */
  paste: () => Promise<void>
}

/**
 * 编辑器剪贴板操作 Composable
 * 
 * 负责：
 * - cut: 优先选区，否则当前行
 * - copy: 优先选区，否则当前行
 * - copyAll: 复制全部内容
 * - paste: 读取剪贴板并插入
 * 
 * 注意：所有操作都有 guard，editor 未初始化时不执行
 */
export function useEditorClipboard(options: UseEditorClipboardOptions): UseEditorClipboardReturn {
  const { editor } = options
  const isProcessing = ref(false)

  /**
   * 安全获取编辑器实例
   */
  function getEditor(): Ace.Editor | undefined {
    return editor.value
  }

  /**
   * 剪切操作
   * 优先选区，否则当前行
   */
  async function cut(): Promise<void> {
    const ed = getEditor()
    if (!ed) {
      console.warn('[useEditorClipboard] Cannot cut: editor not initialized')
      return
    }

    isProcessing.value = true
    try {
      const selectedText = ed.getSelectedText()
      
      if (selectedText) {
        // 有选区：复制选区并删除
        await navigator.clipboard.writeText(selectedText)
        ed.session.remove(ed.getSelectionRange())
      } else {
        // 无选区：复制当前行并删除该行
        const pos = ed.getCursorPosition()
        const lineContent = ed.session.getLine(pos.row)
        
        if (lineContent !== undefined) {
          await navigator.clipboard.writeText(lineContent.trim())
          ed.session.removeFullLines(pos.row, pos.row)
          ed.moveCursorTo(pos.row, 0)
        }
      }
    } catch (err) {
      console.error('[useEditorClipboard] Cut failed:', err)
    } finally {
      isProcessing.value = false
    }
  }

  /**
   * 复制操作
   * 优先选区，否则当前行
   */
  async function copy(): Promise<void> {
    const ed = getEditor()
    if (!ed) {
      console.warn('[useEditorClipboard] Cannot copy: editor not initialized')
      return
    }

    isProcessing.value = true
    try {
      const selectedText = ed.getSelectedText()
      
      if (selectedText) {
        // 有选区：复制选区
        await navigator.clipboard.writeText(selectedText)
      } else {
        // 无选区：复制当前行
        const pos = ed.getCursorPosition()
        const lineContent = ed.session.getLine(pos.row)
        
        if (lineContent !== undefined) {
          await navigator.clipboard.writeText(lineContent.trim())
        }
      }
    } catch (err) {
      console.error('[useEditorClipboard] Copy failed:', err)
    } finally {
      isProcessing.value = false
    }
  }

  /**
   * 复制全部内容
   */
  async function copyAll(): Promise<void> {
    const ed = getEditor()
    if (!ed) {
      console.warn('[useEditorClipboard] Cannot copyAll: editor not initialized')
      return
    }

    isProcessing.value = true
    try {
      const allContent = ed.getValue()
      await navigator.clipboard.writeText(allContent)
    } catch (err) {
      console.error('[useEditorClipboard] CopyAll failed:', err)
    } finally {
      isProcessing.value = false
    }
  }

  /**
   * 粘贴操作
   * 读取剪贴板并插入光标位置
   */
  async function paste(): Promise<void> {
    const ed = getEditor()
    if (!ed) {
      console.warn('[useEditorClipboard] Cannot paste: editor not initialized')
      return
    }

    isProcessing.value = true
    try {
      const clipboardText = await navigator.clipboard.readText()
      ed.insert(clipboardText)
    } catch (err) {
      console.error('[useEditorClipboard] Paste failed:', err)
    } finally {
      isProcessing.value = false
    }
  }

  return {
    isProcessing,
    cut,
    copy,
    copyAll,
    paste,
  }
}

export default useEditorClipboard
