import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useEditorStore, type EditorLang } from '@/stores/editor'

describe('editor Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('State', () => {
    it('should have correct initial state', () => {
      const store = useEditorStore()

      expect(store.lang).toBe('text')
      expect(store.content).toBe('')
      expect(store.enableCheckerPanel).toBe(false)
    })
  })

  describe('Getters', () => {
    it('isCodeLanguage should return false for text', () => {
      const store = useEditorStore()
      store.lang = 'text'
      expect(store.isCodeLanguage).toBe(false)
    })

    it('isCodeLanguage should return true for python', () => {
      const store = useEditorStore()
      store.lang = 'python'
      expect(store.isCodeLanguage).toBe(true)
    })

    it('isCodeLanguage should return true for cpp', () => {
      const store = useEditorStore()
      store.lang = 'cpp'
      expect(store.isCodeLanguage).toBe(true)
    })

    it('canRunChecker should return true when checker enabled and is code', () => {
      const store = useEditorStore()
      store.lang = 'python'
      store.enableCheckerPanel = true
      expect(store.canRunChecker).toBe(true)
    })

    it('canRunChecker should return false when checker disabled', () => {
      const store = useEditorStore()
      store.lang = 'python'
      store.enableCheckerPanel = false
      expect(store.canRunChecker).toBe(false)
    })

    it('canRunChecker should return false for text language', () => {
      const store = useEditorStore()
      store.lang = 'text'
      store.enableCheckerPanel = true
      expect(store.canRunChecker).toBe(false)
    })
  })

  describe('Actions', () => {
    it('setLanguage should update lang', () => {
      const store = useEditorStore()
      store.setLanguage('python')
      expect(store.lang).toBe('python')
    })

    it('setContent should update content', () => {
      const store = useEditorStore()
      const newContent = 'print("Hello")'
      store.setContent(newContent)
      expect(store.content).toBe(newContent)
    })

    it('setEnableCheckerPanel should update enableCheckerPanel', () => {
      const store = useEditorStore()
      store.setEnableCheckerPanel(true)
      expect(store.enableCheckerPanel).toBe(true)
    })

    it('resetEditor should reset all state to defaults', () => {
      const store = useEditorStore()
      store.setLanguage('cpp')
      store.setContent('int main() {}')
      store.setEnableCheckerPanel(true)

      store.resetEditor()

      expect(store.lang).toBe('text')
      expect(store.content).toBe('')
      expect(store.enableCheckerPanel).toBe(false)
    })
  })

  describe('Language Types', () => {
    it.each([
      ['python', true],
      ['cpp', true],
      ['json', true],
      ['text', false],
    ] as [EditorLang, boolean][])('lang %s should have isCodeLanguage = %s', (lang, expected) => {
      const store = useEditorStore()
      store.setLanguage(lang)
      expect(store.isCodeLanguage).toBe(expected)
    })
  })
})
