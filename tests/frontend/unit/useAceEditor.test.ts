import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { ref, nextTick } from 'vue'
import { useAceEditor, type UseAceEditorOptions } from '@/composables/editor/useAceEditor'

// Mock ace-builds
vi.mock('ace-builds', () => ({
  Ace: {},
}))

describe('useAceEditor Composable', () => {
  let mockEditor: any
  let mockAceInstance: any

  beforeEach(() => {
    // 创建模拟的 Ace Editor 实例
    mockEditor = {
      setValue: vi.fn(),
      getValue: vi.fn().mockReturnValue('test code'),
      getCursorPosition: vi.fn().mockReturnValue({ row: 10, column: 5 }),
      moveCursorToPosition: vi.fn(),
      scrollToLine: vi.fn(),
      getSelectedText: vi.fn().mockReturnValue('selected'),
      setTheme: vi.fn(),
      session: {
        setMode: vi.fn(),
        getLine: vi.fn().mockReturnValue('line content'),
        setValue: vi.fn(),
      },
      container: {
        style: {},
      },
      renderer: {
        updateFontSize: vi.fn(),
      },
      setOption: vi.fn(),
      on: vi.fn(),
      getSelectionRange: vi.fn(),
      removeFullLines: vi.fn(),
      moveCursorTo: vi.fn(),
      insert: vi.fn(),
    }

    mockAceInstance = {
      getAceInstance: vi.fn().mockReturnValue(mockEditor),
    }
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Initialization', () => {
    it('should initialize with default options', () => {
      const { aceRef, editor, ready } = useAceEditor()

      expect(aceRef.value).toBeUndefined()
      expect(editor.value).toBeUndefined()
      expect(ready.value).toBe(false)
    })

    it('should initialize with custom options', () => {
      const options: UseAceEditorOptions = {
        initialContent: 'initial code',
        editorOptions: { fontSize: 14 },
      }
      const { aceRef, editor, ready } = useAceEditor(options)

      expect(aceRef.value).toBeUndefined()
      expect(editor.value).toBeUndefined()
      expect(ready.value).toBe(false)
    })
  })

  describe('Editor Methods', () => {
    it('should provide getEditor method', () => {
      const { aceRef, editor, initEditor } = useAceEditor()
      aceRef.value = mockAceInstance as any

      expect(typeof initEditor).toBe('function')
      expect(editor.value).toBeUndefined()
    })

    it('should set and get value', async () => {
      const { aceRef, setValue, getValue, initEditor } = useAceEditor()
      aceRef.value = mockAceInstance as any

      await initEditor()

      setValue('new code')
      expect(mockEditor.setValue).toHaveBeenCalledWith('new code', -1)

      const value = getValue()
      expect(mockEditor.getValue).toHaveBeenCalled()
      expect(value).toBe('test code')
    })

    it('should get cursor position', async () => {
      const { aceRef, getCursorPosition, initEditor } = useAceEditor()
      aceRef.value = mockAceInstance as any

      await initEditor()

      const pos = getCursorPosition()
      expect(mockEditor.getCursorPosition).toHaveBeenCalled()
      expect(pos).toEqual({ row: 10, column: 5 })
    })

    it('should set theme', async () => {
      const { aceRef, setTheme, initEditor } = useAceEditor()
      aceRef.value = mockAceInstance as any

      await initEditor()

      setTheme('ace/theme/tie')
      expect(mockEditor.setTheme).toHaveBeenCalledWith('ace/theme/tie')
    })

    it('should set mode', async () => {
      const { aceRef, setMode, initEditor } = useAceEditor()
      aceRef.value = mockAceInstance as any

      await initEditor()

      setMode('ace/mode/python')
      expect(mockEditor.session.setMode).toHaveBeenCalledWith('ace/mode/python')
    })

    it('should handle change events', async () => {
      const { aceRef, onChange, initEditor } = useAceEditor()
      aceRef.value = mockAceInstance as any

      await initEditor()

      const callback = vi.fn()
      onChange(callback)
      expect(mockEditor.on).toHaveBeenCalledWith('change', expect.any(Function))
    })
  })

  describe('Edge Cases', () => {
    it('should handle setValue when editor not initialized', () => {
      const { setValue } = useAceEditor()
      
      // Should not throw
      expect(() => setValue('test')).not.toThrow()
    })

    it('should handle getValue when editor not initialized', () => {
      const { getValue } = useAceEditor()
      
      const value = getValue()
      expect(value).toBe('')
    })

    it('should handle setTheme when editor not initialized', () => {
      const { setTheme } = useAceEditor()
      
      // Should not throw
      expect(() => setTheme('ace/theme/tie')).not.toThrow()
    })

    it('should handle dispose', async () => {
      const { aceRef, initEditor, dispose, ready } = useAceEditor()
      aceRef.value = mockAceInstance as any

      await initEditor()
      expect(ready.value).toBe(true)

      dispose()
      expect(mockEditor.session.setValue).toHaveBeenCalledWith('')
    })

    it('should handle initEditor when aceRef is not ready', async () => {
      const { initEditor, ready } = useAceEditor()
      // aceRef is undefined

      const result = await initEditor()
      expect(result).toBeUndefined()
      expect(ready.value).toBe(false)
    })
  })

  describe('Cursor Position Preservation', () => {
    it('should preserve cursor position when setting value', async () => {
      const { aceRef, setValue, initEditor } = useAceEditor()
      aceRef.value = mockAceInstance as any

      await initEditor()

      mockEditor.getCursorPosition.mockReturnValue({ row: 5, column: 10 })
      mockEditor.session.getLine.mockReturnValue('line with content')

      setValue('new content', -1)

      expect(mockEditor.setValue).toHaveBeenCalledWith('new content', -1)
      // Should restore cursor position
      expect(mockEditor.moveCursorToPosition).toHaveBeenCalled()
    })
  })
})
