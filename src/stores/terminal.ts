import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

/** 终端连接状态 */
export type TerminalStatus = 'idle' | 'connecting' | 'connected' | 'exited' | 'error'

export const useTerminalStore = defineStore('terminal', () => {
  // State
  const visible = ref<boolean>(false)
  const status = ref<TerminalStatus>('idle')
  const exitCode = ref<number | null>(null)
  /** 面板高度（px），由用户拖拽调整后持久保存在内存中 */
  const height = ref<number>(260)

  // Getters
  const isConnected = computed(() => status.value === 'connected')
  const isBusy = computed(() => status.value === 'connecting')

  // Actions
  function setVisible (value: boolean) {
    visible.value = value
  }

  function toggleVisible () {
    visible.value = !visible.value
  }

  function setStatus (value: TerminalStatus) {
    status.value = value
    if (value !== 'exited') {
      exitCode.value = null
    }
  }

  function setExitCode (code: number | null) {
    exitCode.value = code
    status.value = 'exited'
  }

  function setHeight (value: number) {
    // 夹在可用范围内，避免拖拽把面板拉到不可用的尺寸
    height.value = Math.min(Math.max(value, 120), 800)
  }

  function resetTerminalState () {
    visible.value = false
    status.value = 'idle'
    exitCode.value = null
    height.value = 260
  }

  return {
    // State
    visible,
    status,
    exitCode,
    height,
    // Getters
    isConnected,
    isBusy,
    // Actions
    setVisible,
    toggleVisible,
    setStatus,
    setExitCode,
    setHeight,
    resetTerminalState,
  }
})
