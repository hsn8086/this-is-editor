import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick, ref } from 'vue'
import { useEditorContextMenu, type UseEditorContextMenuOptions } from '@/composables/editor/useEditorContextMenu'

// Mock ace-builds
vi.mock('ace-builds', () => ({
  Ace: {},
}))

describe('useEditorContextMenu Composable', () => {
  let mockEditor: any

  beforeEach(() => {
    // 创建模拟的 Ace Editor 实例
    mockEditor = {
      getValue: vi.fn().mockReturnValue('test content'),
      getSelectedText: vi.fn().mockReturnValue(''),
    }
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Initialization', () => {
    it('should initialize with default values', () => {
      const editorRef = ref(mockEditor)
      const { menuX, menuY, showMenu, onContextMenu, closeMenu } = useEditorContextMenu({ editor: editorRef })

      expect(menuX.value).toBe(0)
      expect(menuY.value).toBe(0)
      expect(showMenu.value).toBe(false)
      expect(typeof onContextMenu).toBe('function')
      expect(typeof closeMenu).toBe('function')
    })

    it('should handle uninitialized editor', () => {
      const editorRef = ref(undefined)
      const { menuX, menuY, showMenu, onContextMenu, closeMenu } = useEditorContextMenu({ editor: editorRef })

      expect(menuX.value).toBe(0)
      expect(menuY.value).toBe(0)
      expect(showMenu.value).toBe(false)
      expect(typeof onContextMenu).toBe('function')
      expect(typeof closeMenu).toBe('function')
    })
  })

  describe('onContextMenu', () => {
    it('should update menu position and show menu when editor is initialized', () => {
      const editorRef = ref(mockEditor)
      const { menuX, menuY, showMenu, onContextMenu } = useEditorContextMenu({ editor: editorRef })

      const mockEvent = {
        clientX: 100,
        clientY: 200,
        preventDefault: vi.fn(),
      } as unknown as MouseEvent

      onContextMenu(mockEvent)

      expect(mockEvent.preventDefault).toHaveBeenCalled()
      expect(menuX.value).toBe(100)
      expect(menuY.value).toBe(200)
      expect(showMenu.value).toBe(true)
    })

    it('should not trigger when editor is not initialized', () => {
      const editorRef = ref(undefined)
      const { menuX, menuY, showMenu, onContextMenu } = useEditorContextMenu({ editor: editorRef })

      const mockEvent = {
        clientX: 100,
        clientY: 200,
        preventDefault: vi.fn(),
      } as unknown as MouseEvent

      onContextMenu(mockEvent)

      // Event should not be prevented and state should not change
      expect(mockEvent.preventDefault).not.toHaveBeenCalled()
      expect(menuX.value).toBe(0)
      expect(menuY.value).toBe(0)
      expect(showMenu.value).toBe(false)
    })

    it('should handle different mouse positions', () => {
      const editorRef = ref(mockEditor)
      const { menuX, menuY, showMenu, onContextMenu } = useEditorContextMenu({ editor: editorRef })

      // Test position 1
      let mockEvent = {
        clientX: 50,
        clientY: 75,
        preventDefault: vi.fn(),
      } as unknown as MouseEvent

      onContextMenu(mockEvent)

      expect(menuX.value).toBe(50)
      expect(menuY.value).toBe(75)
      expect(showMenu.value).toBe(true)

      // Test position 2
      mockEvent = {
        clientX: 300,
        clientY: 400,
        preventDefault: vi.fn(),
      } as unknown as MouseEvent

      onContextMenu(mockEvent)

      expect(menuX.value).toBe(300)
      expect(menuY.value).toBe(400)
      expect(showMenu.value).toBe(true)
    })

    it('should handle zero coordinates', () => {
      const editorRef = ref(mockEditor)
      const { menuX, menuY, showMenu, onContextMenu } = useEditorContextMenu({ editor: editorRef })

      const mockEvent = {
        clientX: 0,
        clientY: 0,
        preventDefault: vi.fn(),
      } as unknown as MouseEvent

      onContextMenu(mockEvent)

      expect(mockEvent.preventDefault).toHaveBeenCalled()
      expect(menuX.value).toBe(0)
      expect(menuY.value).toBe(0)
      expect(showMenu.value).toBe(true)
    })

    it('should handle negative coordinates (edge case)', () => {
      const editorRef = ref(mockEditor)
      const { menuX, menuY, showMenu, onContextMenu } = useEditorContextMenu({ editor: editorRef })

      const mockEvent = {
        clientX: -100,
        clientY: -200,
        preventDefault: vi.fn(),
      } as unknown as MouseEvent

      onContextMenu(mockEvent)

      expect(mockEvent.preventDefault).toHaveBeenCalled()
      expect(menuX.value).toBe(-100)
      expect(menuY.value).toBe(-200)
      expect(showMenu.value).toBe(true)
    })
  })

  describe('closeMenu', () => {
    it('should hide the menu', () => {
      const editorRef = ref(mockEditor)
      const { menuX, menuY, showMenu, onContextMenu, closeMenu } = useEditorContextMenu({ editor: editorRef })

      // First show the menu
      const mockEvent = {
        clientX: 100,
        clientY: 200,
        preventDefault: vi.fn(),
      } as unknown as MouseEvent

      onContextMenu(mockEvent)
      expect(showMenu.value).toBe(true)

      // Then close it
      closeMenu()
      expect(showMenu.value).toBe(false)
      // Position should remain unchanged
      expect(menuX.value).toBe(100)
      expect(menuY.value).toBe(200)
    })

    it('should work when menu is already hidden', () => {
      const editorRef = ref(mockEditor)
      const { showMenu, closeMenu } = useEditorContextMenu({ editor: editorRef })

      expect(showMenu.value).toBe(false)

      // Should not throw
      closeMenu()
      expect(showMenu.value).toBe(false)
    })
  })

  describe('Reactive Updates', () => {
    it('should maintain reactive state when editor changes', async () => {
      const editorRef = ref(mockEditor)
      const { menuX, menuY, showMenu, onContextMenu } = useEditorContextMenu({ editor: editorRef })

      const mockEvent = {
        clientX: 150,
        clientY: 250,
        preventDefault: vi.fn(),
      } as unknown as MouseEvent

      onContextMenu(mockEvent)

      expect(showMenu.value).toBe(true)

      // Simulate editor becoming undefined
      editorRef.value = undefined
      await nextTick()

      // State should remain as is
      expect(menuX.value).toBe(150)
      expect(menuY.value).toBe(250)
      expect(showMenu.value).toBe(true)

      // But new context menu events should not work
      const newMockEvent = {
        clientX: 300,
        clientY: 400,
        preventDefault: vi.fn(),
      } as unknown as MouseEvent

      onContextMenu(newMockEvent)

      // Event should not be prevented and state should not change
      expect(newMockEvent.preventDefault).not.toHaveBeenCalled()
      expect(menuX.value).toBe(150)
      expect(menuY.value).toBe(250)
    })
  })
})
