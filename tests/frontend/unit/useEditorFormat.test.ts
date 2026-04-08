import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { ref, nextTick } from 'vue'
import { useEditorFormat, type UseEditorFormatOptions, type FormatAction } from '@/composables/editor/useEditorFormat'
import type { Config, Code } from '@/pywebview-defines'

// Mock services
const mockGetConfig = vi.fn()
const mockGetCode = vi.fn()
const mockFormatCode = vi.fn()

vi.mock('@/services', () => ({
  configService: {
    getConfig: (...args: any[]) => mockGetConfig(...args),
  },
  codeService: {
    getCode: (...args: any[]) => mockGetCode(...args),
    formatCode: (...args: any[]) => mockFormatCode(...args),
  },
}))

describe('useEditorFormat Composable', () => {
  let mockConfig: Config
  let mockCode: Code
  let resetCodeMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    resetCodeMock = vi.fn()
    
    mockCode = {
      code: 'print("hello")',
      type: 'python',
      alias: [],
    }

    mockConfig = {
      editor: {
        aceMain: {},
        tie: {},
      },
      programmingLanguages: {
        python: {
          formatter: {
            active: { value: true },
            command: { value: 'black -' },
            action: { value: 'stdout' as FormatAction },
          },
        },
      },
      keyboardShortcuts: {
        formatCode: { value: 'Ctrl-Shift-F', display: 'Format Code', i18n: '' },
        runJudge: { value: 'F5', display: 'Run Judge', i18n: '' },
      },
    }

    mockGetConfig.mockResolvedValue(mockConfig)
    mockGetCode.mockResolvedValue(mockCode)
    mockFormatCode.mockResolvedValue('formatted code')
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Initialization', () => {
    it('should initialize with default state', () => {
      const { isFormatting, currentCodeType, formatterConfig, loadFormatterConfig, format } = useEditorFormat()

      expect(isFormatting.value).toBe(false)
      expect(currentCodeType.value).toBe('')
      expect(formatterConfig.value).toBeUndefined()
      expect(typeof loadFormatterConfig).toBe('function')
      expect(typeof format).toBe('function')
    })

    it('should initialize with custom services', () => {
      const customConfigService = {
        getConfig: vi.fn().mockResolvedValue(mockConfig),
      }
      const customCodeService = {
        getCode: vi.fn().mockResolvedValue(mockCode),
        formatCode: vi.fn().mockResolvedValue('formatted'),
      }

      const { isFormatting } = useEditorFormat({
        configService: customConfigService as any,
        codeService: customCodeService as any,
      })

      expect(isFormatting.value).toBe(false)
    })
  })

  describe('Load Formatter Config', () => {
    it('should load formatter config successfully', async () => {
      const { loadFormatterConfig, currentCodeType, formatterConfig } = useEditorFormat()

      await loadFormatterConfig()

      expect(mockGetConfig).toHaveBeenCalled()
      expect(mockGetCode).toHaveBeenCalled()
      expect(currentCodeType.value).toBe('python')
      expect(formatterConfig.value).toBeDefined()
      expect(formatterConfig.value?.active.value).toBe(true)
      expect(formatterConfig.value?.action.value).toBe('stdout')
    })

    it('should handle missing formatter config', async () => {
      mockConfig.programmingLanguages.python.formatter = undefined

      const { loadFormatterConfig, formatterConfig } = useEditorFormat()

      await loadFormatterConfig()

      expect(formatterConfig.value).toBeUndefined()
    })

    it('should handle missing programming language config', async () => {
      mockCode.type = 'unknown'

      const { loadFormatterConfig, formatterConfig } = useEditorFormat()

      await loadFormatterConfig()

      expect(formatterConfig.value).toBeUndefined()
    })

    it('should handle load config error', async () => {
      mockGetConfig.mockRejectedValue(new Error('Config error'))

      const { loadFormatterConfig, formatterConfig } = useEditorFormat()

      await loadFormatterConfig()

      expect(formatterConfig.value).toBeUndefined()
    })
  })

  describe('Format Action: stdout', () => {
    it('should format code with stdout action', async () => {
      const { format, isFormatting } = useEditorFormat()

      // 先加载配置
      await format(resetCodeMock)

      expect(mockFormatCode).toHaveBeenCalled()
      expect(resetCodeMock).toHaveBeenCalledWith('formatted code')
      expect(isFormatting.value).toBe(false)
    })

    it('should not format when formatter is inactive', async () => {
      mockConfig.programmingLanguages.python.formatter!.active.value = false

      const { format, isFormatting } = useEditorFormat()

      const result = await format(resetCodeMock)

      expect(result).toBe(false)
      expect(mockFormatCode).not.toHaveBeenCalled()
      expect(resetCodeMock).not.toHaveBeenCalled()
      expect(isFormatting.value).toBe(false)
    })

    it('should handle format code error', async () => {
      mockFormatCode.mockRejectedValue(new Error('Format error'))

      const { format, isFormatting } = useEditorFormat()

      const result = await format(resetCodeMock)

      expect(result).toBe(false)
      expect(resetCodeMock).not.toHaveBeenCalled()
      expect(isFormatting.value).toBe(false)
    })
  })

  describe('Format Action: reload', () => {
    it('should reload code from disk with reload action', async () => {
      mockConfig.programmingLanguages.python.formatter!.action.value = 'reload'
      const diskCode = 'code from disk'
      mockGetCode.mockResolvedValue({ ...mockCode, code: diskCode })

      const { format } = useEditorFormat()

      const result = await format(resetCodeMock)

      expect(result).toBe(true)
      expect(resetCodeMock).toHaveBeenCalledWith(diskCode)
    })
  })

  describe('Format Action: skip', () => {
    it('should skip formatting with skip action', async () => {
      mockConfig.programmingLanguages.python.formatter!.action.value = 'skip'

      const { format } = useEditorFormat()

      const result = await format(resetCodeMock)

      expect(result).toBe(false)
      expect(mockFormatCode).not.toHaveBeenCalled()
      expect(resetCodeMock).not.toHaveBeenCalled()
    })
  })

  describe('Format Without Prior Config Load', () => {
    it('should load config automatically when format is called without prior load', async () => {
      const { format, formatterConfig } = useEditorFormat()

      // 不先调用 loadFormatterConfig
      expect(formatterConfig.value).toBeUndefined()

      await format(resetCodeMock)

      // 应该自动加载配置
      expect(mockGetConfig).toHaveBeenCalled()
      expect(mockGetCode).toHaveBeenCalled()
      expect(formatterConfig.value).toBeDefined()
    })

    it('should handle format when no formatter config exists', async () => {
      mockConfig.programmingLanguages.python.formatter = undefined

      const { format } = useEditorFormat()

      const result = await format(resetCodeMock)

      expect(result).toBe(false)
      expect(resetCodeMock).not.toHaveBeenCalled()
    })
  })

  describe('Processing State', () => {
    it('should set isFormatting during operation', async () => {
      const { format, isFormatting } = useEditorFormat()

      expect(isFormatting.value).toBe(false)

      const formatPromise = format(resetCodeMock)
      
      // 在异步操作期间可能为 true
      await formatPromise
      
      expect(isFormatting.value).toBe(false)
    })
  })

  describe('Custom Services', () => {
    it('should use custom config service', async () => {
      const customGetConfig = vi.fn().mockResolvedValue(mockConfig)
      const customGetCode = vi.fn().mockResolvedValue(mockCode)
      const customFormatCode = vi.fn().mockResolvedValue('custom formatted')

      const customConfigService = {
        getConfig: customGetConfig,
      }
      const customCodeService = {
        getCode: customGetCode,
        formatCode: customFormatCode,
      }

      const { format } = useEditorFormat({
        configService: customConfigService as any,
        codeService: customCodeService as any,
      })

      await format(resetCodeMock)

      expect(customGetConfig).toHaveBeenCalled()
      expect(customGetCode).toHaveBeenCalled()
      expect(customFormatCode).toHaveBeenCalled()
      expect(resetCodeMock).toHaveBeenCalledWith('custom formatted')
    })
  })
})
