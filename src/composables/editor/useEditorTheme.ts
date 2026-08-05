import type { Ace } from 'ace-builds'
import { ref, type Ref, watch } from 'vue'
import { useTheme } from 'vuetify'

export type AceTheme = 'ace/theme/tie' | 'ace/theme/tie-light'

export interface UseEditorThemeOptions {
  /** 编辑器实例 */
  editor: Ref<Ace.Editor | undefined>
  /** 是否自动监听主题变化 */
  autoWatch?: boolean
}

export interface UseEditorThemeReturn {
  /** 当前是否为暗色主题 */
  isDark: Ref<boolean>
  /** 当前 Ace 主题名称 */
  currentTheme: Ref<AceTheme>
  /** 手动设置 Ace 主题 */
  setAceTheme: (theme: AceTheme) => void
  /** 根据 Vuetify 主题同步 Ace 主题 */
  syncTheme: () => void
  /** 停止监听（当 autoWatch 为 true 时可用） */
  stopWatch?: () => void
}

/**
 * Ace Editor 主题管理 Composable
 *
 * 负责：
 * - 监听 Vuetify 主题状态
 * - 自动设置 Ace 主题（tie/tie-light）
 *
 * 主题映射：
 * - Vuetify 暗色主题 -> ace/theme/tie
 * - Vuetify 亮色主题 -> ace/theme/tie-light
 */
export function useEditorTheme (options: UseEditorThemeOptions): UseEditorThemeReturn {
  const { editor, autoWatch = true } = options

  // 获取 Vuetify 主题
  const vuetifyTheme = useTheme()

  // 响应式状态
  const isDark = ref(vuetifyTheme.global.current.value.dark)
  const currentTheme = ref<AceTheme>(
    isDark.value ? 'ace/theme/tie' : 'ace/theme/tie-light',
  )

  /**
   * 设置 Ace 编辑器主题
   * @param theme Ace 主题名称
   */
  function setAceTheme (theme: AceTheme): void {
    const ed = editor.value
    if (!ed) {
      console.warn('[useEditorTheme] Cannot set theme: editor not initialized')
      return
    }

    try {
      ed.setTheme(theme)
      currentTheme.value = theme
      console.log(`[useEditorTheme] Theme set to: ${theme}`)
    } catch (error) {
      console.error('[useEditorTheme] Failed to set theme:', error)
    }
  }

  /**
   * 根据 Vuetify 主题同步 Ace 主题
   */
  function syncTheme (): void {
    const dark = vuetifyTheme.global.current.value.dark
    isDark.value = dark

    const newTheme: AceTheme = dark ? 'ace/theme/tie' : 'ace/theme/tie-light'
    setAceTheme(newTheme)
  }

  // 监听 Vuetify 主题变化
  let stopWatchFn: (() => void) | undefined

  if (autoWatch) {
    stopWatchFn = watch(
      () => vuetifyTheme.global.current.value.dark,
      newDark => {
        console.log(`[useEditorTheme] Vuetify theme changed: dark=${newDark}`)
        syncTheme()
      },
      { immediate: false },
    )
  }

  return {
    isDark,
    currentTheme,
    setAceTheme,
    syncTheme,
    stopWatch: stopWatchFn,
  }
}

export default useEditorTheme
