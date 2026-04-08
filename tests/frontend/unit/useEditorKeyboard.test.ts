import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import { useEditorKeyboard } from '@/composables/editor/useEditorKeyboard'

// Track HashHandler instances and their commands
let lastHashHandlerInstance: { commands: any[] } | null = null

// Mock ace-code HashHandler
vi.mock('ace-code/src/keyboard/hash_handler', () => ({
  HashHandler: vi.fn().mockImplementation(function (this: any, commands: any[]) {
    this.commands = commands || []
    lastHashHandlerInstance = this
  }),
}))

// Mock ace-builds
vi.mock('ace-builds', () => ({
  Ace: {},
}))

describe('useEditorKeyboard Composable', () => {
  let mockEditor: any
  let mockCallbacks: {
    onFormat: ReturnType<typeof vi.fn>
    onRunJudge: ReturnType<typeof vi.fn>
    onCut: ReturnType<typeof vi.fn>
    onCopy: ReturnType<typeof vi.fn>
  }

  beforeEach(() => {
    lastHashHandlerInstance = null

    // 创建模拟的 Ace Editor 实例
    mockEditor = {
      setKeyboardHandler: vi.fn(),
    }

    // 创建模拟的回调函数
    mockCallbacks = {
      onFormat: vi.fn(),
      onRunJudge: vi.fn(),
      onCut: vi.fn(),
      onCopy: vi.fn(),
    }
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Initialization', () => {
    it('should initialize with default state', () => {
      const keyboardShortcuts = ref({
        formatCode: { value: 'Ctrl-Shift-F' },
        runJudge: { value: 'F5' },
      })
      const editorRef = ref(mockEditor)

      const { isBound, handler, bindKeyboard, unbindKeyboard } = useEditorKeyboard({
        editor: editorRef,
        keyboardShortcuts,
        ...mockCallbacks,
      })

      expect(isBound.value).toBe(false)
      expect(handler.value).toBeUndefined()
      expect(typeof bindKeyboard).toBe('function')
      expect(typeof unbindKeyboard).toBe('function')
    })

    it('should handle uninitialized editor', () => {
      const keyboardShortcuts = ref({
        formatCode: { value: 'Ctrl-Shift-F' },
        runJudge: { value: 'F5' },
      })
      const editorRef = ref(undefined)

      const { isBound, bindKeyboard } = useEditorKeyboard({
        editor: editorRef,
        keyboardShortcuts,
        ...mockCallbacks,
      })

      // 尝试绑定应该静默失败
      bindKeyboard()
      expect(isBound.value).toBe(false)
    })
  })

  describe('Keyboard Binding', () => {
    it('should bind keyboard shortcuts', () => {
      const keyboardShortcuts = ref({
        formatCode: { value: 'Ctrl-Shift-F' },
        runJudge: { value: 'F5' },
      })
      const editorRef = ref(mockEditor)

      const { isBound, bindKeyboard } = useEditorKeyboard({
        editor: editorRef,
        keyboardShortcuts,
        ...mockCallbacks,
      })

      bindKeyboard()

      expect(mockEditor.setKeyboardHandler).toHaveBeenCalled()
      expect(isBound.value).toBe(true)
    })

    it('should not bind twice', () => {
      const keyboardShortcuts = ref({
        formatCode: { value: 'Ctrl-Shift-F' },
        runJudge: { value: 'F5' },
      })
      const editorRef = ref(mockEditor)

      const { bindKeyboard } = useEditorKeyboard({
        editor: editorRef,
        keyboardShortcuts,
        ...mockCallbacks,
      })

      bindKeyboard()
      bindKeyboard() // 第二次调用

      expect(mockEditor.setKeyboardHandler).toHaveBeenCalledTimes(1)
    })

    it('should unbind keyboard shortcuts', () => {
      const keyboardShortcuts = ref({
        formatCode: { value: 'Ctrl-Shift-F' },
        runJudge: { value: 'F5' },
      })
      const editorRef = ref(mockEditor)

      const { isBound, bindKeyboard, unbindKeyboard } = useEditorKeyboard({
        editor: editorRef,
        keyboardShortcuts,
        ...mockCallbacks,
      })

      bindKeyboard()
      expect(isBound.value).toBe(true)

      unbindKeyboard()
      expect(mockEditor.setKeyboardHandler).toHaveBeenLastCalledWith(null)
      expect(isBound.value).toBe(false)
    })

    it('should handle unbind when not bound', () => {
      const keyboardShortcuts = ref({
        formatCode: { value: 'Ctrl-Shift-F' },
        runJudge: { value: 'F5' },
      })
      const editorRef = ref(mockEditor)

      const { unbindKeyboard } = useEditorKeyboard({
        editor: editorRef,
        keyboardShortcuts,
        ...mockCallbacks,
      })

      // 不应该抛出错误
      expect(() => unbindKeyboard()).not.toThrow()
    })
  })

  describe('Keyboard Shortcuts Configuration', () => {
    it('should use custom keyboard shortcuts', () => {
      const keyboardShortcuts = ref({
        formatCode: { value: 'Ctrl-Alt-F' },
        runJudge: { value: 'Ctrl-Enter' },
      })
      const editorRef = ref(mockEditor)

      const { bindKeyboard } = useEditorKeyboard({
        editor: editorRef,
        keyboardShortcuts,
        ...mockCallbacks,
      })

      bindKeyboard()

      // 验证 HashHandler 被调用并保存了实例
      expect(lastHashHandlerInstance).not.toBeNull()
      const commands = lastHashHandlerInstance!.commands

      // 验证命令配置
      expect(commands).toHaveLength(4)
      expect(commands[0].bindKey).toBe('Ctrl-Alt-F')
      expect(commands[0].name).toBe('format')
      expect(commands[3].bindKey).toBe('Ctrl-Enter')
      expect(commands[3].name).toBe('runJudge')
    })

    it('should include default cut and copy shortcuts', () => {
      const keyboardShortcuts = ref({
        formatCode: { value: 'Ctrl-Shift-F' },
        runJudge: { value: 'F5' },
      })
      const editorRef = ref(mockEditor)

      const { bindKeyboard } = useEditorKeyboard({
        editor: editorRef,
        keyboardShortcuts,
        ...mockCallbacks,
      })

      bindKeyboard()

      const commands = lastHashHandlerInstance!.commands

      // 验证默认快捷键
      const cutCommand = commands.find((c: any) => c.name === 'cut')
      const copyCommand = commands.find((c: any) => c.name === 'copy')

      expect(cutCommand).toBeDefined()
      expect(cutCommand.bindKey).toBe('Ctrl-X')
      expect(copyCommand).toBeDefined()
      expect(copyCommand.bindKey).toBe('Ctrl-C')
    })
  })

  describe('Command Execution', () => {
    it('should execute format callback', () => {
      const keyboardShortcuts = ref({
        formatCode: { value: 'Ctrl-Shift-F' },
        runJudge: { value: 'F5' },
      })
      const editorRef = ref(mockEditor)

      const { bindKeyboard } = useEditorKeyboard({
        editor: editorRef,
        keyboardShortcuts,
        ...mockCallbacks,
      })

      bindKeyboard()

      const commands = lastHashHandlerInstance!.commands
      const formatCommand = commands.find((c: any) => c.name === 'format')

      // 执行 format 命令
      formatCommand.exec()
      expect(mockCallbacks.onFormat).toHaveBeenCalled()
    })

    it('should execute runJudge callback', () => {
      const keyboardShortcuts = ref({
        formatCode: { value: 'Ctrl-Shift-F' },
        runJudge: { value: 'F5' },
      })
      const editorRef = ref(mockEditor)

      const { bindKeyboard } = useEditorKeyboard({
        editor: editorRef,
        keyboardShortcuts,
        ...mockCallbacks,
      })

      bindKeyboard()

      const commands = lastHashHandlerInstance!.commands
      const runJudgeCommand = commands.find((c: any) => c.name === 'runJudge')

      // 执行 runJudge 命令
      runJudgeCommand.exec()
      expect(mockCallbacks.onRunJudge).toHaveBeenCalled()
    })

    it('should execute cut callback', () => {
      const keyboardShortcuts = ref({
        formatCode: { value: 'Ctrl-Shift-F' },
        runJudge: { value: 'F5' },
      })
      const editorRef = ref(mockEditor)

      const { bindKeyboard } = useEditorKeyboard({
        editor: editorRef,
        keyboardShortcuts,
        ...mockCallbacks,
      })

      bindKeyboard()

      const commands = lastHashHandlerInstance!.commands
      const cutCommand = commands.find((c: any) => c.name === 'cut')

      // 执行 cut 命令
      cutCommand.exec()
      expect(mockCallbacks.onCut).toHaveBeenCalled()
    })

    it('should execute copy callback', () => {
      const keyboardShortcuts = ref({
        formatCode: { value: 'Ctrl-Shift-F' },
        runJudge: { value: 'F5' },
      })
      const editorRef = ref(mockEditor)

      const { bindKeyboard } = useEditorKeyboard({
        editor: editorRef,
        keyboardShortcuts,
        ...mockCallbacks,
      })

      bindKeyboard()

      const commands = lastHashHandlerInstance!.commands
      const copyCommand = commands.find((c: any) => c.name === 'copy')

      // 执行 copy 命令
      copyCommand.exec()
      expect(mockCallbacks.onCopy).toHaveBeenCalled()
    })
  })

  describe('Error Handling', () => {
    it('should handle setKeyboardHandler error', () => {
      mockEditor.setKeyboardHandler.mockImplementation(() => {
        throw new Error('Keyboard handler error')
      })

      const keyboardShortcuts = ref({
        formatCode: { value: 'Ctrl-Shift-F' },
        runJudge: { value: 'F5' },
      })
      const editorRef = ref(mockEditor)

      const { isBound, bindKeyboard } = useEditorKeyboard({
        editor: editorRef,
        keyboardShortcuts,
        ...mockCallbacks,
      })

      // 不应该抛出错误
      expect(() => bindKeyboard()).not.toThrow()
      expect(isBound.value).toBe(false)
    })

    it('should handle unbind when editor not initialized', () => {
      const keyboardShortcuts = ref({
        formatCode: { value: 'Ctrl-Shift-F' },
        runJudge: { value: 'F5' },
      })
      const editorRef = ref(undefined)

      const { unbindKeyboard } = useEditorKeyboard({
        editor: editorRef,
        keyboardShortcuts,
        ...mockCallbacks,
      })

      // 不应该抛出错误
      expect(() => unbindKeyboard()).not.toThrow()
    })
  })
})
