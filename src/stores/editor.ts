import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export type EditorLang = 'python' | 'cpp' | 'json' | 'text'

export const useEditorStore = defineStore('editor', () => {
  // State
  const lang = ref<EditorLang>('text')
  const content = ref<string>('')
  const enableCheckerPanel = ref<boolean>(false)

  // Getters
  const isCodeLanguage = computed(() => lang.value !== 'text')
  const canRunChecker = computed(() => enableCheckerPanel.value && isCodeLanguage.value)

  // Actions
  function setLanguage (newLang: EditorLang) {
    lang.value = newLang
  }

  function setContent (newContent: string) {
    content.value = newContent
  }

  function setEnableCheckerPanel (enabled: boolean) {
    enableCheckerPanel.value = enabled
  }

  function resetEditor () {
    lang.value = 'text'
    content.value = ''
    enableCheckerPanel.value = false
  }

  return {
    // State
    lang,
    content,
    enableCheckerPanel,
    // Getters
    isCodeLanguage,
    canRunChecker,
    // Actions
    setLanguage,
    setContent,
    setEnableCheckerPanel,
    resetEditor,
  }
})
