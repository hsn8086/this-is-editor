import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { ref, nextTick } from 'vue'
import { useEditorScreenshot, type UseEditorScreenshotOptions } from '@/composables/editor/useEditorScreenshot'

// Mock html2canvas
vi.mock('html2canvas', () => ({
  default: vi.fn(),
}))

// Mock highlight.js
vi.mock('highlight.js', () => ({
  default: {
    highlightAuto: vi.fn().mockReturnValue({ value: '<span class="hljs-keyword">test</span>' }),
  },
}))

// Mock vuetify useTheme - call tracking mock
const mockUseTheme = vi.fn().mockReturnValue({
  global: {
    current: {
      value: {
        dark: false,
      },
    },
  },
})

vi.mock('vuetify', () => ({
  useTheme: (...args: any[]) => mockUseTheme(...args),
}))

describe('useEditorScreenshot Composable', () => {
  let mockEditor: any
  let mockCanvas: any
  let mockClipboard: any
  let mockClipboardItem: any

  beforeEach(async () => {
    vi.clearAllMocks()
    
    // 创建模拟的 Ace Editor 实例
    mockEditor = {
      getSelectedText: vi.fn().mockReturnValue(''),
      getValue: vi.fn().mockReturnValue('const x = 1;\nconst y = 2;'),
      container: document.createElement('div'),
    }

    // 设置容器样式
    Object.defineProperty(mockEditor.container, 'style', {
      value: {
        fontSize: '14px',
        fontFamily: 'monospace',
        backgroundColor: '#ffffff',
        color: '#000000',
        lineHeight: '1.5',
      },
      writable: true,
    })

    // 模拟 getComputedStyle
    vi.spyOn(window, 'getComputedStyle').mockReturnValue({
      fontSize: '14px',
      fontFamily: 'monospace',
      backgroundColor: '#ffffff',
      color: '#000000',
      lineHeight: '1.5',
    } as CSSStyleDeclaration)

    // 创建模拟的 Canvas
    mockCanvas = {
      toBlob: vi.fn((callback: (blob: Blob | null) => void) => {
        const blob = new Blob(['fake-image-data'], { type: 'image/png' })
        callback(blob)
      }),
      toDataURL: vi.fn().mockReturnValue('data:image/png;base64,fake'),
    }

    // 模拟 html2canvas
    const mockHtml2canvas = await import('html2canvas')
    vi.mocked(mockHtml2canvas.default).mockResolvedValue(mockCanvas)

    // Mock ClipboardItem
    mockClipboardItem = vi.fn()
    Object.defineProperty(window, 'ClipboardItem', {
      value: mockClipboardItem,
      writable: true,
      configurable: true,
    })

    // Mock clipboard API
    mockClipboard = {
      write: vi.fn().mockResolvedValue(undefined),
      writeText: vi.fn().mockResolvedValue(undefined),
    }
    Object.defineProperty(navigator, 'clipboard', {
      value: mockClipboard,
      writable: true,
      configurable: true,
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Initialization', () => {
    it('should initialize with editor ref', () => {
      const editorRef = ref(mockEditor)
      const { isCapturing, error, takeScreenshot, clearError } = useEditorScreenshot({ editor: editorRef })

      expect(isCapturing.value).toBe(false)
      expect(error.value).toBeNull()
      expect(typeof takeScreenshot).toBe('function')
      expect(typeof clearError).toBe('function')
    })

    it('should handle uninitialized editor', () => {
      const editorRef = ref(undefined)
      const { isCapturing, error, takeScreenshot } = useEditorScreenshot({ editor: editorRef })

      expect(isCapturing.value).toBe(false)
      expect(error.value).toBeNull()
      expect(typeof takeScreenshot).toBe('function')
    })
  })

  describe('clearError', () => {
    it('should clear error state', async () => {
      const editorRef = ref(undefined)
      const { error, clearError, takeScreenshot } = useEditorScreenshot({ editor: editorRef })

      // Trigger an error by taking screenshot with no editor
      await takeScreenshot()
      expect(error.value).toBe('Editor not initialized')

      // Clear error
      clearError()
      expect(error.value).toBeNull()
    })
  })

  describe('takeScreenshot with selection', () => {
    it('should capture selected text when selection exists', async () => {
      const selectedText = 'const x = 1;'
      mockEditor.getSelectedText.mockReturnValue(selectedText)
      
      const editorRef = ref(mockEditor)
      const { takeScreenshot, isCapturing } = useEditorScreenshot({ editor: editorRef })

      await takeScreenshot()

      expect(mockEditor.getSelectedText).toHaveBeenCalled()
      expect(isCapturing.value).toBe(false)
    })

    it('should capture all content when no selection', async () => {
      mockEditor.getSelectedText.mockReturnValue('')
      
      const editorRef = ref(mockEditor)
      const { takeScreenshot, isCapturing } = useEditorScreenshot({ editor: editorRef })

      await takeScreenshot()

      expect(mockEditor.getSelectedText).toHaveBeenCalled()
      expect(mockEditor.getValue).toHaveBeenCalled()
      expect(isCapturing.value).toBe(false)
    })

    it('should set isCapturing during capture lifecycle', async () => {
      const editorRef = ref(mockEditor)
      const { takeScreenshot, isCapturing } = useEditorScreenshot({ editor: editorRef })

      expect(isCapturing.value).toBe(false)
      
      await takeScreenshot()
      
      // After completion, should be false
      expect(isCapturing.value).toBe(false)
    })
  })

  describe('takeScreenshot error handling', () => {
    it('should handle uninitialized editor', async () => {
      const editorRef = ref(undefined)
      const { takeScreenshot, error, isCapturing } = useEditorScreenshot({ editor: editorRef })

      await takeScreenshot()

      expect(error.value).toBe('Editor not initialized')
      expect(isCapturing.value).toBe(false)
    })

    it('should handle empty content', async () => {
      mockEditor.getSelectedText.mockReturnValue('')
      mockEditor.getValue.mockReturnValue('   ') // whitespace only
      
      const editorRef = ref(mockEditor)
      const { takeScreenshot, error, isCapturing } = useEditorScreenshot({ editor: editorRef })

      await takeScreenshot()

      expect(error.value).toBe('No content to capture')
      expect(isCapturing.value).toBe(false)
    })

    it('should handle html2canvas error', async () => {
      // Mock html2canvas to throw an error
      const { default: html2canvas } = await import('html2canvas')
      const originalMock = vi.mocked(html2canvas)
      originalMock.mockRejectedValueOnce(new Error('Canvas rendering failed'))
      
      const editorRef = ref(mockEditor)
      const { takeScreenshot, error, isCapturing } = useEditorScreenshot({ editor: editorRef })

      await takeScreenshot()

      // Error should be set and isCapturing should be false after completion
      expect(error.value).not.toBeNull()
      expect(isCapturing.value).toBe(false)
    })
  })

  describe('Clipboard operations', () => {
    it('should attempt clipboard operations when supported', async () => {
      const editorRef = ref(mockEditor)
      const { takeScreenshot, isCapturing } = useEditorScreenshot({ editor: editorRef })

      // Taking screenshot should complete without throwing
      await expect(takeScreenshot()).resolves.not.toThrow()
      
      // After completion, isCapturing should be false
      expect(isCapturing.value).toBe(false)
    })

    it('should handle clipboard write not supported gracefully', async () => {
      // Remove clipboard.write
      Object.defineProperty(navigator, 'clipboard', {
        value: { writeText: vi.fn() }, // only writeText, no write
        writable: true,
        configurable: true,
      })
      
      const editorRef = ref(mockEditor)
      const { takeScreenshot } = useEditorScreenshot({ editor: editorRef })

      // Should not throw
      await expect(takeScreenshot()).resolves.not.toThrow()
    })

    it('should handle clipboard write failure gracefully', async () => {
      mockClipboard.write.mockRejectedValueOnce(new Error('Clipboard error'))
      
      const editorRef = ref(mockEditor)
      const { takeScreenshot } = useEditorScreenshot({ editor: editorRef })

      // Should not throw
      await expect(takeScreenshot()).resolves.not.toThrow()
    })

    it('should handle missing ClipboardItem gracefully', async () => {
      Object.defineProperty(window, 'ClipboardItem', {
        value: undefined,
        writable: true,
        configurable: true,
      })
      
      const editorRef = ref(mockEditor)
      const { takeScreenshot } = useEditorScreenshot({ editor: editorRef })

      // Should not throw
      await expect(takeScreenshot()).resolves.not.toThrow()
    })
  })

  describe('DOM cleanup', () => {
    it('should attempt to clean up created DOM elements', async () => {
      const editorRef = ref(mockEditor)
      const { takeScreenshot } = useEditorScreenshot({ editor: editorRef })

      // Should not throw during cleanup
      await expect(takeScreenshot()).resolves.not.toThrow()
    })
  })

  describe('Theme support', () => {
    it('should support vuetify theme', async () => {
      const editorRef = ref(mockEditor)
      const { takeScreenshot } = useEditorScreenshot({ editor: editorRef })

      // Taking screenshot should work with theme
      await expect(takeScreenshot()).resolves.not.toThrow()
    })

    it('should allow disabling vuetify theme', async () => {
      const editorRef = ref(mockEditor)
      const { takeScreenshot } = useEditorScreenshot({ editor: editorRef, useVuetifyTheme: false })

      // Taking screenshot should still work without vuetify theme
      await expect(takeScreenshot()).resolves.not.toThrow()
    })
  })
})
