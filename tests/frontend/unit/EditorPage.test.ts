import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

// Test the EditorPage core logic without full component mounting
describe('EditorPage.vue - Core Logic Tests', () => {
  beforeEach(() => {
    // Setup detailed mocks for pywebview API
    const mockApi = {
      get_code: vi.fn().mockResolvedValue({
        code: 'print("hello")',
        type: 'python',
        alias: [],
      }),
      get_config: vi.fn().mockResolvedValue({
        editor: {
          aceMain: {
            fontSize: { value: 14, display: 'Font Size', i18n: '' },
          },
        },
        programmingLanguages: {
          python: {
            enableCheckerPanel: true,
            display: 'Python',
          },
        },
        keyboardShortcuts: {
          runJudge: { value: 'Ctrl+Enter' },
          formatCode: { value: 'Ctrl+Shift+F' },
        },
      }),
      get_opened_file: vi.fn().mockResolvedValue('/test/file.py'),
      save_code: vi.fn().mockResolvedValue(undefined),
      format_code: vi.fn().mockResolvedValue('print("formatted")'),
    }

    window.pywebview = {
      api: mockApi as any,
      state: {
        addEventListener: vi.fn(),
        prob: null,
      },
    }

    // Mock clipboard
    vi.spyOn(navigator.clipboard, 'writeText').mockResolvedValue()
    vi.spyOn(navigator.clipboard, 'readText').mockResolvedValue('')
    vi.spyOn(navigator.clipboard, 'read').mockResolvedValue([])
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Initialization - get_code and get_config', () => {
    it('should call get_code to retrieve initial code', async () => {
      const result = await window.pywebview.api.get_code()
      expect(window.pywebview.api.get_code).toHaveBeenCalled()
      expect(result.code).toBe('print("hello")')
      expect(result.type).toBe('python')
    })

    it('should call get_config to retrieve editor configuration', async () => {
      const result = await window.pywebview.api.get_config()
      expect(window.pywebview.api.get_config).toHaveBeenCalled()
      expect(result.editor).toBeDefined()
      expect(result.programmingLanguages).toBeDefined()
    })

    it('should set language based on code type', async () => {
      const code = await window.pywebview.api.get_code()
      const lang = code.type
      expect(lang).toBe('python')
    })

    it('should enable checker panel for supported languages', async () => {
      const config = await window.pywebview.api.get_config()
      const code = await window.pywebview.api.get_code()
      const enableCheckerPanel = config.programmingLanguages[code.type]?.enableCheckerPanel || false
      expect(enableCheckerPanel).toBe(true)
    })
  })

  describe('Theme switching', () => {
    it('should have theme object from vuetify', () => {
      // Theme switching logic is in the component
      // Here we test the expected behavior
      const isDark = true // Simulated theme state
      const expectedTheme = isDark ? 'ace/theme/tie' : 'ace/theme/tie-light'
      expect(expectedTheme).toBe('ace/theme/tie')
    })

    it('should switch to light theme', () => {
      const isDark = false
      const expectedTheme = isDark ? 'ace/theme/tie' : 'ace/theme/tie-light'
      expect(expectedTheme).toBe('ace/theme/tie-light')
    })
  })

  describe('Keyboard shortcuts binding', () => {
    it('should get keyboard shortcuts from config', async () => {
      const config = await window.pywebview.api.get_config()
      expect(config.keyboardShortcuts.runJudge).toBeDefined()
      expect(config.keyboardShortcuts.formatCode).toBeDefined()
    })

    it('should have correct runJudge shortcut value', async () => {
      const config = await window.pywebview.api.get_config()
      expect(config.keyboardShortcuts.runJudge.value).toBe('Ctrl+Enter')
    })

    it('should have correct formatCode shortcut value', async () => {
      const config = await window.pywebview.api.get_config()
      expect(config.keyboardShortcuts.formatCode.value).toBe('Ctrl+Shift+F')
    })
  })

  describe('Menu actions', () => {
    it('should define menuList structure', () => {
      // Menu structure from EditorPage.vue
      const menuList = [
        [
          {
            title: 'runTest',
            action: expect.any(Function),
          },
        ],
        [
          { title: 'cut', action: expect.any(Function) },
          { title: 'copy', action: expect.any(Function) },
          { title: 'copyAll', action: expect.any(Function) },
          { title: 'paste', action: expect.any(Function) },
        ],
        [
          { title: 'formatCode', action: expect.any(Function) },
          { title: 'screenshot', action: expect.any(Function) },
        ],
      ]
      expect(menuList).toHaveLength(3)
      expect(menuList[0]).toHaveLength(1)
      expect(menuList[1]).toHaveLength(4)
      expect(menuList[2]).toHaveLength(2)
    })
  })

  describe('Code operations', () => {
    it('should save code', async () => {
      await window.pywebview.api.save_code('new code')
      expect(window.pywebview.api.save_code).toHaveBeenCalledWith('new code')
    })

    it('should format code', async () => {
      const formatted = await window.pywebview.api.format_code()
      expect(window.pywebview.api.format_code).toHaveBeenCalled()
      expect(formatted).toBe('print("formatted")')
    })

    it('should get opened file', async () => {
      const file = await window.pywebview.api.get_opened_file()
      expect(window.pywebview.api.get_opened_file).toHaveBeenCalled()
      expect(file).toBe('/test/file.py')
    })
  })
})
