import { ref, type Ref } from 'vue'
import type { Ace } from 'ace-builds'
import { HashHandler } from 'ace-code/src/keyboard/hash_handler'

export interface KeyboardShortcut {
  bindKey: string
  name: string
  exec: () => void
}

export interface UseEditorKeyboardOptions {
  /** Ace Editor 实例 Ref */
  editor: Ref<Ace.Editor | undefined>
  /** 键盘快捷键配置 */
  keyboardShortcuts: Ref<{
    formatCode: { value: string | boolean | number }
    runJudge: { value: string | boolean | number }
  }>
  /** 格式化代码回调 */
  onFormat: () => void
  /** 运行评测回调 */
  onRunJudge: () => void
  /** 剪切回调 */
  onCut: () => void
  /** 复制回调 */
  onCopy: () => void
}

export interface UseEditorKeyboardReturn {
  /** 是否已绑定键盘处理器 */
  isBound: Ref<boolean>
  /** 当前键盘处理器 */
  handler: Ref<InstanceType<typeof HashHandler> | undefined>
  /** 绑定键盘快捷键 */
  bindKeyboard: () => void
  /** 解绑键盘快捷键 */
  unbindKeyboard: () => void
}

/**
 * 编辑器键盘快捷键 Composable
 *
 * 负责：
 * - 初始化 HashHandler 并绑定快捷键
 * - 支持 format、runJudge、cut、copy 操作
 * - 提供绑定/解绑方法
 *
 * 注意：editor 未初始化时无法绑定
 */
export function useEditorKeyboard(options: UseEditorKeyboardOptions): UseEditorKeyboardReturn {
  const { editor, keyboardShortcuts, onFormat, onRunJudge, onCut, onCopy } = options

  const isBound = ref(false)
  const handler = ref<InstanceType<typeof HashHandler> | undefined>(undefined)

  /**
   * 创建键盘处理器
   */
  function createHandler(): InstanceType<typeof HashHandler> {
    const shortcuts: KeyboardShortcut[] = [
      {
        bindKey: keyboardShortcuts.value.formatCode.value as string,
        name: 'format',
        exec: () => {
          console.log('[useEditorKeyboard] Format command triggered')
          onFormat()
        },
      },
      {
        bindKey: 'Ctrl-X',
        name: 'cut',
        exec: onCut,
      },
      {
        bindKey: 'Ctrl-C',
        name: 'copy',
        exec: onCopy,
      },
      {
        bindKey: keyboardShortcuts.value.runJudge.value as string,
        name: 'runJudge',
        exec: () => {
          console.log('[useEditorKeyboard] Run judge command triggered')
          onRunJudge()
        },
      },
    ]

    return new HashHandler(shortcuts)
  }

  /**
   * 绑定键盘快捷键
   */
  function bindKeyboard(): void {
    const ed = editor.value
    if (!ed) {
      console.warn('[useEditorKeyboard] Cannot bind: editor not initialized')
      return
    }

    if (isBound.value) {
      console.warn('[useEditorKeyboard] Keyboard already bound, skipping')
      return
    }

    try {
      handler.value = createHandler()
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ed.setKeyboardHandler(handler.value as any)
      isBound.value = true
      console.log('[useEditorKeyboard] Keyboard shortcuts bound successfully')
    } catch (err) {
      console.error('[useEditorKeyboard] Failed to bind keyboard:', err)
      isBound.value = false
    }
  }

  /**
   * 解绑键盘快捷键
   */
  function unbindKeyboard(): void {
    const ed = editor.value
    if (!ed) {
      console.warn('[useEditorKeyboard] Cannot unbind: editor not initialized')
      return
    }

    if (!isBound.value) {
      return
    }

    try {
      // 重置为默认键盘处理器
      ed.setKeyboardHandler(null)
      handler.value = undefined
      isBound.value = false
      console.log('[useEditorKeyboard] Keyboard shortcuts unbound successfully')
    } catch (err) {
      console.error('[useEditorKeyboard] Failed to unbind keyboard:', err)
    }
  }

  return {
    isBound,
    handler,
    bindKeyboard,
    unbindKeyboard,
  }
}

export default useEditorKeyboard
