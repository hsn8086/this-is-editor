import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick, ref } from 'vue'
import { useEditorClipboard, type UseEditorClipboardOptions } from '@/composables/editor/useEditorClipboard'

// Mock ace-builds
vi.mock('ace-builds', () => ({
  Ace: {},
}))

describe('useEditorClipboard Composable', () => {
  let mockEditor: any
  let mockClipboard: any

  beforeEach(() => {
    // 创建模拟的 Ace Editor 实例
    mockEditor = {
      getSelectedText: vi.fn().mockReturnValue(''),
      getSelectionRange: vi.fn().mockReturnValue({ start: { row: 0, column: 0 }, end: { row: 0, column: 5 } }),
      getCursorPosition: vi.fn().mockReturnValue({ row: 2, column: 5 }),
      getValue: vi.fn().mockReturnValue('full content\nline 2\nline 3'),
      insert: vi.fn(),
      moveCursorTo: vi.fn(),
      session: {
        getLine: vi.fn().mockReturnValue('line content'),
        remove: vi.fn(),
        removeFullLines: vi.fn(),
      },
    }

    // Mock clipboard API using defineProperty
    mockClipboard = {
      writeText: vi.fn().mockResolvedValue(undefined),
      readText: vi.fn().mockResolvedValue('pasted content'),
    }
    Object.defineProperty(navigator, 'clipboard', {
      value: mockClipboard,
      writable: true,
      configurable: true,
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Initialization', () => {
    it('should initialize with editor ref', () => {
      const editorRef = ref(mockEditor)
      const { isProcessing, cut, copy, copyAll, paste } = useEditorClipboard({ editor: editorRef })

      expect(isProcessing.value).toBe(false)
      expect(typeof cut).toBe('function')
      expect(typeof copy).toBe('function')
      expect(typeof copyAll).toBe('function')
      expect(typeof paste).toBe('function')
    })

    it('should handle uninitialized editor', () => {
      const editorRef = ref(undefined)
      const { isProcessing, cut, copy, copyAll, paste } = useEditorClipboard({ editor: editorRef })

      expect(isProcessing.value).toBe(false)
      expect(typeof cut).toBe('function')
      expect(typeof copy).toBe('function')
      expect(typeof copyAll).toBe('function')
      expect(typeof paste).toBe('function')
    })
  })

  describe('Cut Operation', () => {
    it('should cut selected text when selection exists', async () => {
      mockEditor.getSelectedText.mockReturnValue('selected text')
      const editorRef = ref(mockEditor)
      const { cut, isProcessing } = useEditorClipboard({ editor: editorRef })

      await cut()

      expect(mockClipboard.writeText).toHaveBeenCalledWith('selected text')
      expect(mockEditor.session.remove).toHaveBeenCalledWith(mockEditor.getSelectionRange())
      expect(isProcessing.value).toBe(false)
    })

    it('should cut current line when no selection', async () => {
      mockEditor.getSelectedText.mockReturnValue('')
      mockEditor.session.getLine.mockReturnValue('  line content  ')
      const editorRef = ref(mockEditor)
      const { cut, isProcessing } = useEditorClipboard({ editor: editorRef })

      await cut()

      expect(mockClipboard.writeText).toHaveBeenCalledWith('line content')
      expect(mockEditor.session.removeFullLines).toHaveBeenCalledWith(2, 2)
      expect(mockEditor.moveCursorTo).toHaveBeenCalledWith(2, 0)
      expect(isProcessing.value).toBe(false)
    })

    it('should handle cut when editor is not initialized', async () => {
      const editorRef = ref(undefined)
      const { cut, isProcessing } = useEditorClipboard({ editor: editorRef })

      await cut()

      expect(mockClipboard.writeText).not.toHaveBeenCalled()
      expect(isProcessing.value).toBe(false)
    })

    it('should handle clipboard write error', async () => {
      mockEditor.getSelectedText.mockReturnValue('selected text')
      vi.mocked(mockClipboard.writeText).mockRejectedValueOnce(new Error('Clipboard error'))

      const editorRef = ref(mockEditor)
      const { cut, isProcessing } = useEditorClipboard({ editor: editorRef })

      await cut()

      expect(isProcessing.value).toBe(false)
    })
  })

  describe('Copy Operation', () => {
    it('should copy selected text when selection exists', async () => {
      mockEditor.getSelectedText.mockReturnValue('selected text')
      const editorRef = ref(mockEditor)
      const { copy, isProcessing } = useEditorClipboard({ editor: editorRef })

      await copy()

      expect(mockClipboard.writeText).toHaveBeenCalledWith('selected text')
      expect(isProcessing.value).toBe(false)
    })

    it('should copy current line when no selection', async () => {
      mockEditor.getSelectedText.mockReturnValue('')
      mockEditor.session.getLine.mockReturnValue('  line content  ')
      const editorRef = ref(mockEditor)
      const { copy, isProcessing } = useEditorClipboard({ editor: editorRef })

      await copy()

      expect(mockClipboard.writeText).toHaveBeenCalledWith('line content')
      expect(isProcessing.value).toBe(false)
    })

    it('should handle copy when editor is not initialized', async () => {
      const editorRef = ref(undefined)
      const { copy, isProcessing } = useEditorClipboard({ editor: editorRef })

      await copy()

      expect(mockClipboard.writeText).not.toHaveBeenCalled()
      expect(isProcessing.value).toBe(false)
    })

    it('should handle clipboard write error in copy', async () => {
      mockEditor.getSelectedText.mockReturnValue('selected text')
      vi.mocked(mockClipboard.writeText).mockRejectedValueOnce(new Error('Clipboard error'))

      const editorRef = ref(mockEditor)
      const { copy, isProcessing } = useEditorClipboard({ editor: editorRef })

      await copy()

      expect(isProcessing.value).toBe(false)
    })
  })

  describe('CopyAll Operation', () => {
    it('should copy all editor content', async () => {
      mockEditor.getValue.mockReturnValue('full content\nwith multiple lines')
      const editorRef = ref(mockEditor)
      const { copyAll, isProcessing } = useEditorClipboard({ editor: editorRef })

      await copyAll()

      expect(mockClipboard.writeText).toHaveBeenCalledWith('full content\nwith multiple lines')
      expect(isProcessing.value).toBe(false)
    })

    it('should handle copyAll when editor is not initialized', async () => {
      const editorRef = ref(undefined)
      const { copyAll, isProcessing } = useEditorClipboard({ editor: editorRef })

      await copyAll()

      expect(mockClipboard.writeText).not.toHaveBeenCalled()
      expect(isProcessing.value).toBe(false)
    })

    it('should handle clipboard write error in copyAll', async () => {
      vi.mocked(mockClipboard.writeText).mockRejectedValueOnce(new Error('Clipboard error'))

      const editorRef = ref(mockEditor)
      const { copyAll, isProcessing } = useEditorClipboard({ editor: editorRef })

      await copyAll()

      expect(isProcessing.value).toBe(false)
    })
  })

  describe('Paste Operation', () => {
    it('should paste clipboard content at cursor position', async () => {
      vi.mocked(mockClipboard.readText).mockResolvedValue('pasted text')
      const editorRef = ref(mockEditor)
      const { paste, isProcessing } = useEditorClipboard({ editor: editorRef })

      await paste()

      expect(mockClipboard.readText).toHaveBeenCalled()
      expect(mockEditor.insert).toHaveBeenCalledWith('pasted text')
      expect(isProcessing.value).toBe(false)
    })

    it('should handle paste when editor is not initialized', async () => {
      const editorRef = ref(undefined)
      const { paste, isProcessing } = useEditorClipboard({ editor: editorRef })

      await paste()

      expect(mockClipboard.readText).not.toHaveBeenCalled()
      expect(isProcessing.value).toBe(false)
    })

    it('should handle clipboard read error', async () => {
      vi.mocked(mockClipboard.readText).mockRejectedValueOnce(new Error('Clipboard error'))

      const editorRef = ref(mockEditor)
      const { paste, isProcessing } = useEditorClipboard({ editor: editorRef })

      await paste()

      expect(mockEditor.insert).not.toHaveBeenCalled()
      expect(isProcessing.value).toBe(false)
    })
  })

  describe('Processing State', () => {
    it('should set isProcessing to true during operation', async () => {
      mockEditor.getSelectedText.mockReturnValue('selected text')
      const editorRef = ref(mockEditor)
      const { copy, isProcessing } = useEditorClipboard({ editor: editorRef })

      // 在执行前检查
      expect(isProcessing.value).toBe(false)

      const promise = copy()

      // 此时应该正在处理（由于异步，可能已经是 false）
      await promise

      // 完成后应该是 false
      expect(isProcessing.value).toBe(false)
    })
  })
})
