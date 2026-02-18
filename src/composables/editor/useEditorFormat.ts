import { ref, type Ref } from 'vue'
import type { Config } from '@/pywebview-defines'
import { configService, codeService, type ConfigService, type CodeService } from '@/services'

export type FormatAction = 'reload' | 'stdout' | 'skip'

export interface FormatterConfig {
  active: { value: boolean }
  command: { value: string }
  action: { value: FormatAction }
}

export interface UseEditorFormatOptions {
  /** 自定义配置服务（用于测试） */
  configService?: ConfigService
  /** 自定义代码服务（用于测试） */
  codeService?: CodeService
}

export interface UseEditorFormatReturn {
  /** 是否正在格式化 */
  isFormatting: Ref<boolean>
  /** 当前代码类型 */
  currentCodeType: Ref<string>
  /** 格式化配置 */
  formatterConfig: Ref<FormatterConfig | undefined>
  /** 加载格式化配置 */
  loadFormatterConfig: () => Promise<void>
  /** 格式化代码
   * @param resetCode 重置代码回调（用于 reload/stdout 操作）
   * @returns 是否成功执行格式化
   */
  format: (resetCode: (code: string) => void) => Promise<boolean>
}

/**
 * 编辑器代码格式化 Composable
 *
 * 负责：
 * - 读取配置获取 formatter 设置
 * - 根据 code type 获取对应的 formatter 配置
 * - 执行 format action（reload/stdout/skip）
 *
 * 依赖：configService、codeService
 *
 * 注意：formatter 未激活或不存在时会跳过
 */
export function useEditorFormat(options: UseEditorFormatOptions = {}): UseEditorFormatReturn {
  const cfgService = options.configService ?? configService
  const cdService = options.codeService ?? codeService

  const isFormatting = ref(false)
  const currentCodeType = ref('')
  const formatterConfig = ref<FormatterConfig | undefined>(undefined)

  /**
   * 加载格式化配置
   */
  async function loadFormatterConfig(): Promise<void> {
    try {
      const config = await cfgService.getConfig()
      const code = await cdService.getCode()

      currentCodeType.value = code.type

      if (!config.programmingLanguages[code.type]) {
        formatterConfig.value = undefined
        return
      }

      const formatter = config.programmingLanguages[code.type].formatter
      if (!formatter) {
        formatterConfig.value = undefined
        return
      }

      formatterConfig.value = formatter as FormatterConfig
    } catch (err) {
      console.error('[useEditorFormat] Failed to load formatter config:', err)
      formatterConfig.value = undefined
    }
  }

  /**
   * 格式化代码
   * @param resetCode 重置代码回调
   * @returns 是否成功执行格式化
   */
  async function format(resetCode: (code: string) => void): Promise<boolean> {
    // Guard: 未加载配置时先加载
    if (!formatterConfig.value) {
      await loadFormatterConfig()
    }

    // Guard: formatter 不存在或未激活
    if (!formatterConfig.value) {
      console.log('[useEditorFormat] No formatter config found, skipping')
      return false
    }

    if (!formatterConfig.value.active.value) {
      console.log('[useEditorFormat] Formatter is inactive, skipping')
      return false
    }

    isFormatting.value = true

    try {
      const action = formatterConfig.value.action.value
      console.log(`[useEditorFormat] Format action: ${action}`)

      switch (action) {
        case 'reload': {
          // 从磁盘重新加载文件
          const code = await cdService.getCode()
          resetCode(code.code)
          console.log('[useEditorFormat] Code reloaded from disk')
          return true
        }

        case 'stdout': {
          // 使用 formatter 的输出
          const formatted = await cdService.formatCode()
          resetCode(formatted)
          console.log('[useEditorFormat] Code formatted with stdout')
          return true
        }

        case 'skip':
        default: {
          // 跳过格式化
          console.log('[useEditorFormat] Format skipped')
          return false
        }
      }
    } catch (err) {
      console.error('[useEditorFormat] Format failed:', err)
      return false
    } finally {
      isFormatting.value = false
    }
  }

  return {
    isFormatting,
    currentCodeType,
    formatterConfig,
    loadFormatterConfig,
    format,
  }
}

export default useEditorFormat
