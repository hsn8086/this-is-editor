import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick, ref } from 'vue'
import { useEditorLsp, type UseEditorLspOptions } from '@/composables/editor/useEditorLsp'

// Mock @/lsp module
const mockRegisterEditor = vi.fn()
const mockCloseDocument = vi.fn()
const mockGetLanguageProvider = vi.fn()

vi.mock('@/lsp', () => ({
  getLanguageProvider: () => mockGetLanguageProvider(),
}))

describe('useEditorLsp Composable', () => {
  let mockEditor: any
  let mockSession: any
  let mockLanguageProvider: any

  beforeEach(() => {
    // 重置 mock
    vi.clearAllMocks()
    mockRegisterEditor.mockReset()
    mockCloseDocument.mockReset()
    mockGetLanguageProvider.mockReset()

    // 创建 mock session
    mockSession = {
      getValue: vi.fn().mockReturnValue('test code'),
      setMode: vi.fn(),
    }

    // 创建 mock editor
    mockEditor = {
      getSession: vi.fn().mockReturnValue(mockSession),
      setValue: vi.fn(),
    }

    // 创建 mock language provider
    mockLanguageProvider = {
      registerEditor: mockRegisterEditor,
      closeDocument: mockCloseDocument,
    }

    // 默认 getLanguageProvider 返回 mock
    mockGetLanguageProvider.mockResolvedValue(mockLanguageProvider)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Initialization', () => {
    it('should initialize with default state', () => {
      const editor = ref(mockEditor)
      const filePath = ref('/test/file.py')

      const { isReady } = useEditorLsp({ editor, filePath })

      expect(isReady.value).toBe(false)
    })

    it('should accept string filePath', () => {
      const editor = ref(mockEditor)
      const filePath = '/test/file.py'

      const { isReady } = useEditorLsp({ editor, filePath })

      expect(isReady.value).toBe(false)
    })

    it('should handle undefined filePath', () => {
      const editor = ref(mockEditor)
      const filePath = ref<string | undefined>(undefined)

      const { isReady } = useEditorLsp({ editor, filePath })

      expect(isReady.value).toBe(false)
    })
  })

  describe('Register', () => {
    it('should register LSP when editor and filePath are ready', async () => {
      const editor = ref(mockEditor)
      const filePath = ref('/test/file.py')

      const { isReady, register } = useEditorLsp({ editor, filePath })

      const result = await register()

      expect(result).toBe(true)
      expect(isReady.value).toBe(true)
      expect(mockGetLanguageProvider).toHaveBeenCalled()
      expect(mockRegisterEditor).toHaveBeenCalledWith(
        mockEditor,
        expect.objectContaining({
          filePath: '/test/file.py',
          joinWorkspaceURI: true,
        }),
      )
    })

    it('should use custom joinWorkspaceURI', async () => {
      const editor = ref(mockEditor)
      const filePath = ref('/test/file.py')

      const { register } = useEditorLsp({ editor, filePath, joinWorkspaceURI: false })

      await register()

      expect(mockRegisterEditor).toHaveBeenCalledWith(
        mockEditor,
        expect.objectContaining({
          filePath: '/test/file.py',
          joinWorkspaceURI: false,
        }),
      )
    })

    it('should return false when editor is not ready', async () => {
      const editor = ref(undefined)
      const filePath = ref('/test/file.py')

      const { isReady, register } = useEditorLsp({ editor, filePath })

      const result = await register()

      expect(result).toBe(false)
      expect(isReady.value).toBe(false)
      expect(mockRegisterEditor).not.toHaveBeenCalled()
    })

    it('should return false when filePath is not set', async () => {
      const editor = ref(mockEditor)
      const filePath = ref<string | undefined>(undefined)

      const { isReady, register } = useEditorLsp({ editor, filePath })

      const result = await register()

      expect(result).toBe(false)
      expect(isReady.value).toBe(false)
      expect(mockRegisterEditor).not.toHaveBeenCalled()
    })

    it('should return false when language provider is not available', async () => {
      mockGetLanguageProvider.mockResolvedValue(undefined)

      const editor = ref(mockEditor)
      const filePath = ref('/test/file.py')

      const { isReady, register } = useEditorLsp({ editor, filePath })

      const result = await register()

      expect(result).toBe(false)
      expect(isReady.value).toBe(false)
    })

    it('should handle register error gracefully', async () => {
      mockRegisterEditor.mockImplementation(() => {
        throw new Error('Register failed')
      })

      const editor = ref(mockEditor)
      const filePath = ref('/test/file.py')

      const { isReady, register } = useEditorLsp({ editor, filePath })

      const result = await register()

      expect(result).toBe(false)
      expect(isReady.value).toBe(false)
    })

    it('should re-register when already registered', async () => {
      const editor = ref(mockEditor)
      const filePath = ref('/test/file.py')

      const { register } = useEditorLsp({ editor, filePath })

      await register()
      expect(mockRegisterEditor).toHaveBeenCalledTimes(1)

      await register()
      // 第二次注册会先注销再注册
      expect(mockCloseDocument).toHaveBeenCalledWith(mockSession)
      expect(mockRegisterEditor).toHaveBeenCalledTimes(2)
    })
  })

  describe('Unregister', () => {
    it('should unregister LSP successfully', async () => {
      const editor = ref(mockEditor)
      const filePath = ref('/test/file.py')

      const { isReady, register, unregister } = useEditorLsp({ editor, filePath })

      await register()
      expect(isReady.value).toBe(true)

      await unregister()

      expect(isReady.value).toBe(false)
      expect(mockCloseDocument).toHaveBeenCalledWith(mockSession)
    })

    it('should handle unregister when not registered', async () => {
      const editor = ref(mockEditor)
      const filePath = ref('/test/file.py')

      const { isReady, unregister } = useEditorLsp({ editor, filePath })

      // 直接注销（未注册状态）
      await unregister()

      expect(isReady.value).toBe(false)
      expect(mockCloseDocument).not.toHaveBeenCalled()
    })

    it('should handle unregister when editor is undefined', async () => {
      const editor = ref(mockEditor)
      const filePath = ref('/test/file.py')

      const { register, unregister } = useEditorLsp({ editor, filePath })

      await register()

      // 将 editor 设为 undefined
      editor.value = undefined

      await unregister()

      // 不会抛出错误
      expect(mockCloseDocument).not.toHaveBeenCalled()
    })

    it('should handle closeDocument error gracefully', async () => {
      mockCloseDocument.mockImplementation(() => {
        throw new Error('Close failed')
      })

      const editor = ref(mockEditor)
      const filePath = ref('/test/file.py')

      const { isReady, register, unregister } = useEditorLsp({ editor, filePath })

      await register()
      expect(isReady.value).toBe(true)

      // 应该不抛出错误
      await expect(unregister()).resolves.not.toThrow()

      expect(isReady.value).toBe(false)
    })
  })

  describe('FilePath Watch', () => {
    it('should auto re-register when filePath changes', async () => {
      const editor = ref(mockEditor)
      const filePath = ref('/test/file1.py')

      const { register } = useEditorLsp({ editor, filePath })

      await register()
      expect(mockRegisterEditor).toHaveBeenCalledTimes(1)

      // 改变 filePath
      filePath.value = '/test/file2.py'
      await nextTick()
      // 需要等待 watch 触发
      await new Promise(resolve => setTimeout(resolve, 0))

      expect(mockCloseDocument).toHaveBeenCalled()
      expect(mockRegisterEditor).toHaveBeenCalledTimes(2)
      expect(mockRegisterEditor).toHaveBeenLastCalledWith(
        mockEditor,
        expect.objectContaining({
          filePath: '/test/file2.py',
        }),
      )
    })

    it('should not re-register when editor is not ready', async () => {
      const editor = ref(undefined)
      const filePath = ref('/test/file1.py')

      useEditorLsp({ editor, filePath })

      // 改变 filePath（editor 未就绪）
      filePath.value = '/test/file2.py'
      await nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))

      expect(mockRegisterEditor).not.toHaveBeenCalled()
    })
  })

  describe('String filePath', () => {
    it('should work with string filePath', async () => {
      const editor = ref(mockEditor)
      const filePath = '/test/file.py'

      const { register } = useEditorLsp({ editor, filePath })

      const result = await register()

      expect(result).toBe(true)
      expect(mockRegisterEditor).toHaveBeenCalledWith(
        mockEditor,
        expect.objectContaining({
          filePath: '/test/file.py',
        }),
      )
    })
  })

  describe('Language Provider Caching', () => {
    it('should cache language provider after first call', async () => {
      const editor = ref(mockEditor)
      const filePath = ref('/test/file.py')

      const { register } = useEditorLsp({ editor, filePath })

      await register()
      await register()

      // getLanguageProvider 应该只被调用一次（因为有缓存）
      expect(mockGetLanguageProvider).toHaveBeenCalledTimes(1)
    })
  })
})
