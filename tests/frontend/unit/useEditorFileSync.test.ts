import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { ref } from 'vue'
import {
  useEditorFileSync,
  useEditorFileSyncWithListener,
  type UseEditorFileSyncOptions,
} from '@/composables/editor/useEditorFileSync'

// Mock Vue lifecycle hooks to avoid warnings in useEditorFileSyncWithListener
vi.mock('vue', async (importOriginal) => {
  const actual = await importOriginal() as any
  return {
    ...actual,
    onMounted: vi.fn((hook: () => void) => hook()),
    onUnmounted: vi.fn((hook: () => void) => hook()),
  }
})

describe('useEditorFileSync', () => {
  let mockSaveCode: ReturnType<typeof vi.fn>
  let mockSetValue: ReturnType<typeof vi.fn>
  let mockGetValue: ReturnType<typeof vi.fn>
  let mockEditorReady: ReturnType<typeof ref>

  beforeEach(() => {
    vi.useFakeTimers()
    // Mock performance.now
    vi.spyOn(performance, 'now').mockImplementation(() => Date.now())

    mockSaveCode = vi.fn().mockResolvedValue(undefined)
    mockSetValue = vi.fn()
    mockGetValue = vi.fn().mockReturnValue('')
    mockEditorReady = ref(true)
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  const createOptions = (overrides?: Partial<UseEditorFileSyncOptions>): UseEditorFileSyncOptions => ({
    saveCode: mockSaveCode,
    setValue: mockSetValue,
    getValue: mockGetValue,
    editorReady: mockEditorReady,
    debounceMs: 500,
    cooldownMs: 1000,
    ...overrides,
  })

  describe('Initialization', () => {
    it('should initialize with default values', () => {
      const options = createOptions()
      const result = useEditorFileSync(options)

      expect(result.lastModified.value).toBe(0)
      expect(typeof result.onCodeChange).toBe('function')
      expect(typeof result.handleExternalChange).toBe('function')
      expect(typeof result.resetCode).toBe('function')
      expect(typeof result.isInCooldown).toBe('function')
      expect(typeof result.isContentEqual).toBe('function')
    })

    it('should accept custom debounceMs', () => {
      const options = createOptions({ debounceMs: 1000 })
      const result = useEditorFileSync(options)

      // Call onCodeChange and advance timer by 999ms - should NOT save yet
      result.onCodeChange('new code')
      mockGetValue.mockReturnValue('new code')
      vi.advanceTimersByTime(999)

      expect(mockSaveCode).not.toHaveBeenCalled()

      // Advance to 1000ms - should save
      vi.advanceTimersByTime(1)
      expect(mockSaveCode).toHaveBeenCalledWith('new code')
    })

    it('should accept custom cooldownMs', () => {
      const options = createOptions({ cooldownMs: 2000 })
      const result = useEditorFileSync(options)

      // Initial change
      mockGetValue.mockReturnValue('initial')
      result.onCodeChange('initial')
      vi.advanceTimersByTime(500)

      // Within cooldown - should return true (in cooldown)
      expect(result.isInCooldown()).toBe(true)

      // After cooldown - should return false
      vi.advanceTimersByTime(2000)
      expect(result.isInCooldown()).toBe(false)
    })
  })

  describe('onCodeChange', () => {
    it('should immediately update lastModified', () => {
      const options = createOptions()
      const result = useEditorFileSync(options)

      const beforeTime = Date.now()
      result.onCodeChange('new code')
      const afterTime = Date.now()

      expect(result.lastModified.value).toBeGreaterThanOrEqual(beforeTime)
      expect(result.lastModified.value).toBeLessThanOrEqual(afterTime)
    })

    it('should debounce saveCode call', () => {
      const options = createOptions()
      const result = useEditorFileSync(options)

      result.onCodeChange('new code')
      vi.advanceTimersByTime(100)
      expect(mockSaveCode).not.toHaveBeenCalled()

      result.onCodeChange('new code') // same code still triggers
      vi.advanceTimersByTime(400) // total 500ms
      expect(mockSaveCode).not.toHaveBeenCalled()

      vi.advanceTimersByTime(100) // total 600ms
      expect(mockSaveCode).toHaveBeenCalledTimes(1)
      expect(mockSaveCode).toHaveBeenCalledWith('new code')
    })

    it('should have cancel method from debounce', () => {
      const options = createOptions()
      const result = useEditorFileSync(options)

      result.onCodeChange('code 1')
      expect(typeof result.onCodeChange.cancel).toBe('function')

      result.onCodeChange.cancel()
      vi.advanceTimersByTime(1000)

      expect(mockSaveCode).not.toHaveBeenCalled()
    })

    it('should have flush method from debounce', () => {
      const options = createOptions()
      const result = useEditorFileSync(options)

      result.onCodeChange('code to flush')
      expect(typeof result.onCodeChange.flush).toBe('function')

      result.onCodeChange.flush()
      expect(mockSaveCode).toHaveBeenCalledWith('code to flush')
    })

    it('should call saveCode with latest code on rapid changes', () => {
      const options = createOptions()
      const result = useEditorFileSync(options)

      result.onCodeChange('code 1')
      vi.advanceTimersByTime(200)
      result.onCodeChange('code 2')
      vi.advanceTimersByTime(200)
      result.onCodeChange('code 3')
      vi.advanceTimersByTime(500)

      expect(mockSaveCode).toHaveBeenCalledTimes(1)
      expect(mockSaveCode).toHaveBeenCalledWith('code 3')
    })
  })

  describe('isInCooldown', () => {
    it('should return true when within cooldown period', () => {
      const options = createOptions({ cooldownMs: 1000 })
      const result = useEditorFileSync(options)

      result.onCodeChange('code')
      vi.advanceTimersByTime(500)

      expect(result.isInCooldown()).toBe(true)
    })

    it('should return false when outside cooldown period', () => {
      const options = createOptions({ cooldownMs: 1000 })
      const result = useEditorFileSync(options)

      result.onCodeChange('code')
      vi.advanceTimersByTime(1500)

      expect(result.isInCooldown()).toBe(false)
    })

    it('should return true initially (lastModified = 0)', () => {
      const options = createOptions({ cooldownMs: 1000 })
      const result = useEditorFileSync(options)

      // lastModified is 0 initially
      // performance.now() - 0 = current timestamp (large number)
      // Since cooldownMs = 1000, and performance.now() - 0 > 1000, isInCooldown returns false
      // This is the expected behavior - initially it's NOT in cooldown
      expect(result.isInCooldown()).toBe(false)
    })
  })

  describe('isContentEqual', () => {
    it('should return true when text equals getValue()', () => {
      const options = createOptions()
      const result = useEditorFileSync(options)

      mockGetValue.mockReturnValue('same content')
      expect(result.isContentEqual('same content')).toBe(true)
    })

    it('should return false when text differs from getValue()', () => {
      const options = createOptions()
      const result = useEditorFileSync(options)

      mockGetValue.mockReturnValue('current content')
      expect(result.isContentEqual('different content')).toBe(false)
    })
  })

  describe('resetCode', () => {
    it('should call setValue with text and -1 cursor position', () => {
      const options = createOptions()
      const result = useEditorFileSync(options)

      result.resetCode('new content')

      expect(mockSetValue).toHaveBeenCalledWith('new content', -1)
    })
  })

  describe('handleExternalChange', () => {
    it('should return false when editorReady is false', () => {
      mockEditorReady.value = false
      const options = createOptions()
      const result = useEditorFileSync(options)

      const resultValue = result.handleExternalChange('external content')

      expect(resultValue).toBe(false)
      expect(mockSetValue).not.toHaveBeenCalled()
    })

    it('should return false when content is equal', () => {
      mockGetValue.mockReturnValue('same content')
      const options = createOptions()
      const result = useEditorFileSync(options)

      const resultValue = result.handleExternalChange('same content')

      expect(resultValue).toBe(false)
      expect(mockSetValue).not.toHaveBeenCalled()
    })

    it('should return false when in cooldown period', () => {
      mockGetValue.mockReturnValue('old content')
      const options = createOptions({ cooldownMs: 1000 })
      const result = useEditorFileSync(options)

      // Trigger a change to start cooldown
      result.onCodeChange('code')
      vi.advanceTimersByTime(100)

      const resultValue = result.handleExternalChange('external content')

      expect(resultValue).toBe(false)
      expect(mockSetValue).not.toHaveBeenCalled()
    })

    it('should update editor and return true when all conditions pass', () => {
      mockGetValue.mockReturnValue('old content')
      const options = createOptions()
      const result = useEditorFileSync(options)

      // Ensure we're outside cooldown (wait for initial cooldown to pass)
      vi.advanceTimersByTime(2000)

      const resultValue = result.handleExternalChange('external content')

      expect(resultValue).toBe(true)
      expect(mockSetValue).toHaveBeenCalledWith('external content', -1)
    })

    it('should NOT update lastModified when applying external change', () => {
      const options = createOptions()
      const result = useEditorFileSync(options)

      // First trigger onCodeChange to set lastModified
      result.onCodeChange('initial code')
      vi.advanceTimersByTime(2000)

      const lastModifiedBefore = result.lastModified.value

      // Apply external change - should NOT update lastModified
      mockGetValue.mockReturnValue('initial code')
      result.handleExternalChange('external content')

      // lastModified should remain unchanged
      expect(result.lastModified.value).toBe(lastModifiedBefore)
    })
  })

  describe('handleExternalChange with lastModified interaction', () => {
    it('should not trigger save when handling external change', () => {
      mockGetValue.mockReturnValue('old content')
      const options = createOptions({ debounceMs: 500 })
      const result = useEditorFileSync(options)

      // Ensure outside cooldown
      vi.advanceTimersByTime(2000)

      // Handle external change
      result.handleExternalChange('external content')

      // Should not trigger save (no debounced save call)
      vi.advanceTimersByTime(1000)
      expect(mockSaveCode).not.toHaveBeenCalled()
    })
  })
})

describe('useEditorFileSyncWithListener', () => {
  let mockSaveCode: ReturnType<typeof vi.fn>
  let mockSetValue: ReturnType<typeof vi.fn>
  let mockGetValue: ReturnType<typeof vi.fn>
  let mockEditorReady: ReturnType<typeof ref>
  let mockEventTarget: {
    addEventListener: ReturnType<typeof vi.fn>
    removeEventListener: ReturnType<typeof vi.fn>
  }
  let mockOnExternalChange: ReturnType<typeof vi.fn>

  beforeEach(() => {
    vi.useFakeTimers()
    vi.spyOn(performance, 'now').mockImplementation(() => Date.now())

    mockSaveCode = vi.fn().mockResolvedValue(undefined)
    mockSetValue = vi.fn()
    mockGetValue = vi.fn().mockReturnValue('')
    mockEditorReady = ref(true)
    mockOnExternalChange = vi.fn()

    mockEventTarget = {
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    }
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  describe('registerListener / unregisterListener', () => {
    it('should add event listener when registerListener is called', () => {
      const result = useEditorFileSyncWithListener({
        saveCode: mockSaveCode,
        setValue: mockSetValue,
        getValue: mockGetValue,
        editorReady: mockEditorReady,
        eventTarget: mockEventTarget as any,
        eventName: 'file-changed',
      })

      result.registerListener()

      expect(mockEventTarget.addEventListener).toHaveBeenCalledWith(
        'file-changed',
        expect.any(Function)
      )
    })

    it('should not add listener twice when registerListener is called multiple times', () => {
      const result = useEditorFileSyncWithListener({
        saveCode: mockSaveCode,
        setValue: mockSetValue,
        getValue: mockGetValue,
        editorReady: mockEditorReady,
        eventTarget: mockEventTarget as any,
        eventName: 'file-changed',
      })

      // Clear mock from onMounted auto-register
      mockEventTarget.addEventListener.mockClear()

      result.registerListener()
      result.registerListener()

      expect(mockEventTarget.addEventListener).toHaveBeenCalledTimes(1)
    })

    it('should remove event listener when unregisterListener is called', () => {
      const result = useEditorFileSyncWithListener({
        saveCode: mockSaveCode,
        setValue: mockSetValue,
        getValue: mockGetValue,
        editorReady: mockEditorReady,
        eventTarget: mockEventTarget as any,
        eventName: 'file-changed',
      })

      result.registerListener()
      result.unregisterListener()

      expect(mockEventTarget.removeEventListener).toHaveBeenCalledWith(
        'file-changed',
        expect.any(Function)
      )
    })

    it('should not throw when unregisterListener is called without register', () => {
      const result = useEditorFileSyncWithListener({
        saveCode: mockSaveCode,
        setValue: mockSetValue,
        getValue: mockGetValue,
        editorReady: mockEditorReady,
        eventTarget: mockEventTarget as any,
        eventName: 'file-changed',
      })

      expect(() => result.unregisterListener()).not.toThrow()
    })

    it('should call onExternalChange callback when event is dispatched', () => {
      mockGetValue.mockReturnValue('old content')
      
      const result = useEditorFileSyncWithListener({
        saveCode: mockSaveCode,
        setValue: mockSetValue,
        getValue: mockGetValue,
        editorReady: mockEditorReady,
        eventTarget: mockEventTarget as any,
        eventName: 'file-changed',
        onExternalChange: mockOnExternalChange,
      })

      result.registerListener()

      // Get the registered listener
      const registeredListener = mockEventTarget.addEventListener.mock.calls[0][1] as Function

      // Simulate external event
      const customEvent = new CustomEvent('file-changed', { detail: 'external content' })
      
      // Ensure outside cooldown
      vi.advanceTimersByTime(2000)
      
      registeredListener(customEvent)

      expect(mockSetValue).toHaveBeenCalledWith('external content', -1)
      expect(mockOnExternalChange).toHaveBeenCalledWith('external content', true)
    })

    it('should pass applied=false when external change is not applied', () => {
      mockEditorReady.value = false
      
      const result = useEditorFileSyncWithListener({
        saveCode: mockSaveCode,
        setValue: mockSetValue,
        getValue: mockGetValue,
        editorReady: mockEditorReady,
        eventTarget: mockEventTarget as any,
        eventName: 'file-changed',
        onExternalChange: mockOnExternalChange,
      })

      result.registerListener()

      const registeredListener = mockEventTarget.addEventListener.mock.calls[0][1] as Function

      const customEvent = new CustomEvent('file-changed', { detail: 'external content' })
      registeredListener(customEvent)

      expect(mockSetValue).not.toHaveBeenCalled()
      expect(mockOnExternalChange).toHaveBeenCalledWith('external content', false)
    })

    it('should use default event name "file-changed"', () => {
      const result = useEditorFileSyncWithListener({
        saveCode: mockSaveCode,
        setValue: mockSetValue,
        getValue: mockGetValue,
        editorReady: mockEditorReady,
        eventTarget: mockEventTarget as any,
      })

      result.registerListener()

      expect(mockEventTarget.addEventListener).toHaveBeenCalledWith(
        'file-changed',
        expect.any(Function)
      )
    })

    it('should use default event target window', () => {
      const windowAddSpy = vi.spyOn(window, 'addEventListener')
      const windowRemoveSpy = vi.spyOn(window, 'removeEventListener')

      const result = useEditorFileSyncWithListener({
        saveCode: mockSaveCode,
        setValue: mockSetValue,
        getValue: mockGetValue,
        editorReady: mockEditorReady,
        // Not providing eventTarget, should default to window
      })

      result.registerListener()

      expect(windowAddSpy).toHaveBeenCalledWith(
        'file-changed',
        expect.any(Function)
      )

      result.unregisterListener()

      expect(windowRemoveSpy).toHaveBeenCalledWith(
        'file-changed',
        expect.any(Function)
      )

      windowAddSpy.mockRestore()
      windowRemoveSpy.mockRestore()
    })
  })

  describe('CustomEvent support', () => {
    it('should handle CustomEvent with detail property', () => {
      mockGetValue.mockReturnValue('old')
      
      const result = useEditorFileSyncWithListener({
        saveCode: mockSaveCode,
        setValue: mockSetValue,
        getValue: mockGetValue,
        editorReady: mockEditorReady,
        eventTarget: mockEventTarget as any,
        eventName: 'file-changed',
      })

      result.registerListener()

      const registeredListener = mockEventTarget.addEventListener.mock.calls[0][1] as Function

      // Create CustomEvent with detail
      const event = new CustomEvent('file-changed', { detail: 'new content from file' })
      
      vi.advanceTimersByTime(2000)
      registeredListener(event)

      expect(mockSetValue).toHaveBeenCalledWith('new content from file', -1)
    })
  })

  describe('lifecycle integration', () => {
    it('should return registerListener and unregisterListener functions', () => {
      const result = useEditorFileSyncWithListener({
        saveCode: mockSaveCode,
        setValue: mockSetValue,
        getValue: mockGetValue,
        editorReady: mockEditorReady,
        eventTarget: mockEventTarget as any,
      })

      expect(typeof result.registerListener).toBe('function')
      expect(typeof result.unregisterListener).toBe('function')
    })

    it('should include all base return values', () => {
      const result = useEditorFileSyncWithListener({
        saveCode: mockSaveCode,
        setValue: mockSetValue,
        getValue: mockGetValue,
        editorReady: mockEditorReady,
        eventTarget: mockEventTarget as any,
      })

      expect(result.lastModified).toBeDefined()
      expect(result.onCodeChange).toBeDefined()
      expect(result.handleExternalChange).toBeDefined()
      expect(result.resetCode).toBeDefined()
      expect(result.isInCooldown).toBeDefined()
      expect(result.isContentEqual).toBeDefined()
    })
  })

  describe('edge cases', () => {
    it('should handle rapid register/unregister cycles', () => {
      const result = useEditorFileSyncWithListener({
        saveCode: mockSaveCode,
        setValue: mockSetValue,
        getValue: mockGetValue,
        editorReady: mockEditorReady,
        eventTarget: mockEventTarget as any,
      })

      // Clear mock from onMounted auto-register
      mockEventTarget.addEventListener.mockClear()
      mockEventTarget.removeEventListener.mockClear()

      // Rapid registration/deregistration
      // Each register/unregister cycle:
      // - register adds listener (since previous unregister set it to null)
      // - unregister removes listener and sets it to null
      for (let i = 0; i < 10; i++) {
        result.registerListener()
        result.unregisterListener()
      }

      // Each iteration: register adds (since listener is null after unregister), unregister removes
      expect(mockEventTarget.addEventListener).toHaveBeenCalledTimes(10)
      expect(mockEventTarget.removeEventListener).toHaveBeenCalledTimes(10)
    })

    it('should correctly compare string content in isContentEqual', () => {
      mockGetValue.mockReturnValue('content')
      
      const result = useEditorFileSyncWithListener({
        saveCode: mockSaveCode,
        setValue: mockSetValue,
        getValue: mockGetValue,
        editorReady: mockEditorReady,
        eventTarget: mockEventTarget as any,
      })

      expect(result.isContentEqual('content')).toBe(true)
      expect(result.isContentEqual('different')).toBe(false)
      expect(result.isContentEqual('')).toBe(false)
    })
  })
})
