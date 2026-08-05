import type { Ace } from 'ace-builds'
import type { VAceEditorInstance } from 'vue3-ace-editor/types'
import { computed, ref, type Ref } from 'vue'

export interface UseAceEditorOptions {
  /** 初始内容 */
  initialContent?: string
  /** 编辑器选项 */
  editorOptions?: Partial<Ace.EditorOptions> & { [key: string]: any }
}

export interface UseAceEditorReturn {
  /** Ace Editor 组件 ref */
  aceRef: Ref<VAceEditorInstance | undefined>
  /** Ace Editor 实例（需在 initEditor 后使用） */
  editor: Ref<Ace.Editor | undefined>
  /** 编辑器是否已就绪 */
  ready: Ref<boolean>
  /** 获取编辑器实例（封装检查） */
  getEditor: () => Ace.Editor | undefined
  /** 安全设置编辑器内容，保持光标位置 */
  setValue: (value: string, cursorPos?: number) => void
  /** 获取编辑器内容 */
  getValue: () => string
  /** 获取光标位置 */
  getCursorPosition: () => Ace.Point | undefined
  /** 移动光标到指定位置 */
  moveCursorToPosition: (pos: Ace.Point) => void
  /** 滚动到指定行 */
  scrollToLine: (row: number, center?: boolean) => void
  /** 获取选中的文本 */
  getSelectedText: () => string
  /** 设置编辑器模式 */
  setMode: (mode: string | Ace.SyntaxMode) => void
  /** 设置编辑器主题 */
  setTheme: (theme: string) => void
  /** 初始化编辑器（需在组件 mounted 后调用） */
  initEditor: () => Promise<Ace.Editor | undefined>
  /** 设置编辑器选项 */
  setOption: <K extends keyof Ace.EditorOptions>(key: K, value: Ace.EditorOptions[K]) => void
  /** 监听编辑器内容变化 */
  onChange: (callback: (e: Ace.Delta) => void) => void
  /** 销毁编辑器 */
  dispose: () => void
}

/**
 * Ace Editor 实例管理 Composable
 *
 * 负责：
 * - aceRef、editor 实例获取
 * - 初始化基本选项
 * - 暴露 setValue/getValue/ready 状态
 *
 * 注意：不涉及 LSP、快捷键、格式化、截图、右键菜单等逻辑
 */
export function useAceEditor (options: UseAceEditorOptions = {}): UseAceEditorReturn {
  const { initialContent = '', editorOptions = {} } = options

  // Refs
  const aceRef = ref<VAceEditorInstance>()
  const editor = ref<Ace.Editor>()
  const ready = ref(false)

  // 当前内容（内部状态，不直接绑定到 v-model）
  const currentContent = ref(initialContent)

  // Computed
  const isReady = computed(() => ready.value && !!editor.value)

  /**
   * 获取编辑器实例（带安全检查）
   */
  function getEditor (): Ace.Editor | undefined {
    return editor.value
  }

  /**
   * 初始化编辑器
   * 需在组件 mounted 后调用
   */
  async function initEditor (): Promise<Ace.Editor | undefined> {
    if (!aceRef.value) {
      console.warn('[useAceEditor] aceRef is not ready, cannot initialize editor')
      return undefined
    }

    // 获取 Ace 实例
    const aceInstance = aceRef.value.getAceInstance()
    if (!aceInstance) {
      console.warn('[useAceEditor] Failed to get ace instance')
      return undefined
    }

    editor.value = aceInstance

    // 应用基本编辑器选项
    for (const key in editorOptions) {
      aceInstance.setOption(
        key as keyof Ace.EditorOptions,
        editorOptions[key],
      )
    }

    // 设置初始内容
    if (initialContent) {
      aceInstance.setValue(initialContent, -1)
    }

    ready.value = true
    console.log('[useAceEditor] Editor initialized successfully')

    return aceInstance
  }

  /**
   * 安全设置编辑器内容，尝试保持光标位置
   * @param value 新内容
   * @param cursorPos 光标位置，-1 表示保持当前位置
   */
  function setValue (value: string, cursorPos = -1): void {
    const ed = editor.value
    if (!ed) {
      console.warn('[useAceEditor] Cannot setValue: editor not initialized')
      return
    }

    // 保存当前光标位置
    const savedPos = ed.getCursorPosition()

    // 设置内容
    ed.setValue(value, cursorPos)

    // 如果 cursorPos 为 -1，恢复光标位置（在有效范围内）
    if (cursorPos === -1) {
      const lineLen = ed.session.getLine(savedPos.row)?.length ?? 0
      const safeColumn = Math.min(savedPos.column, lineLen)
      ed.moveCursorToPosition({ row: savedPos.row, column: safeColumn })
    }

    currentContent.value = value
  }

  /**
   * 获取编辑器内容
   */
  function getValue (): string {
    const ed = editor.value
    if (!ed) {
      console.warn('[useAceEditor] Cannot getValue: editor not initialized')
      return ''
    }
    return ed.getValue()
  }

  /**
   * 获取光标位置
   */
  function getCursorPosition (): Ace.Point | undefined {
    return editor.value?.getCursorPosition()
  }

  /**
   * 移动光标到指定位置
   */
  function moveCursorToPosition (pos: Ace.Point): void {
    editor.value?.moveCursorToPosition(pos)
  }

  /**
   * 滚动到指定行
   */
  function scrollToLine (row: number, center = true): void {
    editor.value?.scrollToLine(row, center, true, () => {})
  }

  /**
   * 获取选中的文本
   */
  function getSelectedText (): string {
    return editor.value?.getSelectedText() ?? ''
  }

  /**
   * 设置编辑器模式（语言）
   */
  function setMode (mode: string | Ace.SyntaxMode): void {
    if (!editor.value) {
      console.warn('[useAceEditor] Cannot setMode: editor not initialized')
      return
    }
    editor.value.session.setMode(mode)
  }

  /**
   * 设置编辑器主题
   */
  function setTheme (theme: string): void {
    if (!editor.value) {
      console.warn('[useAceEditor] Cannot setTheme: editor not initialized')
      return
    }
    editor.value.setTheme(theme)
  }

  /**
   * 设置编辑器选项
   */
  function setOption<K extends keyof Ace.EditorOptions> (
    key: K,
    value: Ace.EditorOptions[K],
  ): void {
    editor.value?.setOption(key, value)
  }

  /**
   * 监听编辑器内容变化
   */
  function onChange (callback: (e: Ace.Delta) => void): void {
    editor.value?.on('change', callback as any)
  }

  /**
   * 销毁编辑器，清理资源
   */
  function dispose (): void {
    if (editor.value) {
      // 清除内容
      editor.value.session.setValue('')
      editor.value = undefined
      ready.value = false
      console.log('[useAceEditor] Editor disposed')
    }
  }

  return {
    // Refs
    aceRef,
    editor,
    ready: isReady,
    // Methods
    getEditor,
    setValue,
    getValue,
    getCursorPosition,
    moveCursorToPosition,
    scrollToLine,
    getSelectedText,
    setMode,
    setTheme,
    initEditor,
    setOption,
    onChange,
    dispose,
  }
}

export default useAceEditor
