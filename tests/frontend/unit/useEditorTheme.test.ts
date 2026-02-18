import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { ref, nextTick } from 'vue'
import { useEditorTheme, type AceTheme } from '@/composables/editor/useEditorTheme'

// Mock vuetify - 需要返回完整的 theme 对象结构
const createMockVuetifyTheme = (isDark: boolean) => ({
  global: {
    current: {
      value: {
        dark: isDark,
      },
    },
  },
})

let currentMockTheme = createMockVuetifyTheme(false)

vi.mock('vuetify', () => ({
  useTheme: vi.fn(() => currentMockTheme),
}))

describe('useEditorTheme Composable', () => {
  let mockEditor: any

  beforeEach(() => {
    mockEditor = {
      setTheme: vi.fn(),
    }
    // Reset to light theme by default
    currentMockTheme = createMockVuetifyTheme(false)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Initialization', () => {
    it('should initialize with light theme by default', () => {
      const editor = ref(mockEditor)
      const { isDark, currentTheme } = useEditorTheme({ editor, autoWatch: false })

      expect(isDark.value).toBe(false)
      expect(currentTheme.value).toBe('ace/theme/tie-light')
    })

    it('should initialize with dark theme when vuetify is dark', () => {
      currentMockTheme = createMockVuetifyTheme(true)
      const editor = ref(mockEditor)
      const { isDark, currentTheme } = useEditorTheme({ editor, autoWatch: false })

      expect(isDark.value).toBe(true)
      expect(currentTheme.value).toBe('ace/theme/tie')
    })
  })

  describe('Theme Synchronization', () => {
    it('should sync theme to editor', () => {
      const editor = ref(mockEditor)
      const { syncTheme } = useEditorTheme({ editor, autoWatch: false })

      syncTheme()

      expect(mockEditor.setTheme).toHaveBeenCalledWith('ace/theme/tie-light')
    })

    it('should sync dark theme correctly', () => {
      currentMockTheme = createMockVuetifyTheme(true)
      const editor = ref(mockEditor)
      const { syncTheme } = useEditorTheme({ editor, autoWatch: false })

      syncTheme()

      expect(mockEditor.setTheme).toHaveBeenCalledWith('ace/theme/tie')
    })

    it('should manually set ace theme', () => {
      const editor = ref(mockEditor)
      const { setAceTheme, currentTheme } = useEditorTheme({ editor, autoWatch: false })

      setAceTheme('ace/theme/tie')

      expect(mockEditor.setTheme).toHaveBeenCalledWith('ace/theme/tie')
      expect(currentTheme.value).toBe('ace/theme/tie')
    })
  })

  describe('Edge Cases', () => {
    it('should handle editor not initialized when setting theme', () => {
      const editor = ref(undefined)
      const { setAceTheme } = useEditorTheme({ editor, autoWatch: false })

      // Should not throw
      expect(() => setAceTheme('ace/theme/tie')).not.toThrow()
    })

    it('should handle editor not initialized when syncing theme', () => {
      const editor = ref(undefined)
      const { syncTheme } = useEditorTheme({ editor, autoWatch: false })

      // Should not throw
      expect(() => syncTheme()).not.toThrow()
    })

    it('should handle setTheme error gracefully', () => {
      mockEditor.setTheme.mockImplementation(() => {
        throw new Error('Theme error')
      })

      const editor = ref(mockEditor)
      const { setAceTheme } = useEditorTheme({ editor, autoWatch: false })

      // Should not throw
      expect(() => setAceTheme('ace/theme/tie')).not.toThrow()
    })
  })

  describe('Auto Watch', () => {
    it('should watch theme changes when autoWatch is true', () => {
      const editor = ref(mockEditor)
      const { stopWatch } = useEditorTheme({ editor, autoWatch: true })

      // Should return stopWatch function
      expect(typeof stopWatch).toBe('function')

      // Clean up
      stopWatch?.()
    })

    it('should not watch theme changes when autoWatch is false', () => {
      const editor = ref(mockEditor)
      const { stopWatch } = useEditorTheme({ editor, autoWatch: false })

      // stopWatch should be undefined when autoWatch is false
      expect(stopWatch).toBeUndefined()
    })
  })

  describe('Theme Values', () => {
    it('should have correct dark theme value', () => {
      const editor = ref(mockEditor)
      const { setAceTheme, currentTheme } = useEditorTheme({ editor, autoWatch: false })

      setAceTheme('ace/theme/tie')
      expect(currentTheme.value).toBe('ace/theme/tie')
    })

    it('should have correct light theme value', () => {
      const editor = ref(mockEditor)
      const { setAceTheme, currentTheme } = useEditorTheme({ editor, autoWatch: false })

      setAceTheme('ace/theme/tie-light')
      expect(currentTheme.value).toBe('ace/theme/tie-light')
    })
  })
})
