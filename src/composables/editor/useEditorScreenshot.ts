import type { Ace } from 'ace-builds'
import hljs from 'highlight.js'
import hljs_github_dark from 'highlight.js/styles/github-dark.css?url'
import hljs_github_light from 'highlight.js/styles/github.css?url'
import html2canvas from 'html2canvas'
import { ref, type Ref } from 'vue'
import { useTheme } from 'vuetify'

export interface UseEditorScreenshotOptions {
  /** Ace Editor 实例 Ref */
  editor: Ref<Ace.Editor | undefined>
  /**
   * 是否使用 Vuetify 主题（默认 true）
   * 设为 false 时可传入自定义主题配置
   */
  useVuetifyTheme?: boolean
}

export interface UseEditorScreenshotReturn {
  /** 是否正在截图 */
  isCapturing: Ref<boolean>
  /** 截图结果错误信息 */
  error: Ref<string | null>
  /**
   * 执行代码截图
   * 优先截取选区内容，否则截取全部内容
   * 优先写入剪贴板，不支持时自动下载
   */
  takeScreenshot: () => Promise<void>
  /**
   * 清除错误状态
   */
  clearError: () => void
}

/**
 * 编辑器截图 Composable
 *
 * 负责：
 * - 根据编辑器内容生成代码截图
 * - 使用 html2canvas 渲染 DOM 到 Canvas
 * - 使用 highlight.js 高亮代码
 * - 优先写入剪贴板（image/png），不支持时自动下载
 * - 自动适配当前 Vuetify 主题（暗色/亮色）
 *
 * 样式：
 * - 继承编辑器的字体、字号、行高
 * - 保留行号显示
 * - 支持代码高亮
 * - 2x 分辨率输出
 */
export function useEditorScreenshot (options: UseEditorScreenshotOptions): UseEditorScreenshotReturn {
  const { editor, useVuetifyTheme = true } = options

  const isCapturing = ref(false)
  const error = ref<string | null>(null)

  // Vuetify 主题实例（延迟获取，仅在需要时使用）
  let vuetifyTheme: ReturnType<typeof useTheme> | null = null

  /**
   * 获取 Vuetify 主题实例（懒加载）
   */
  function getVuetifyTheme () {
    if (!vuetifyTheme && useVuetifyTheme) {
      vuetifyTheme = useTheme()
    }
    return vuetifyTheme
  }

  /**
   * 清除错误状态
   */
  function clearError (): void {
    error.value = null
  }

  /**
   * 获取当前是否为暗色主题
   */
  function isDarkTheme (): boolean {
    const theme = getVuetifyTheme()
    if (theme) {
      return theme.global.current.value.dark
    }
    return false
  }

  /**
   * 获取当前主题的 highlight.js 样式 URL
   */
  function getHighlightJsStyleUrl (): string {
    return isDarkTheme() ? hljs_github_dark : hljs_github_light
  }

  /**
   * 获取编辑器计算样式
   */
  function getEditorComputedStyle (): CSSStyleDeclaration | null {
    const ed = editor.value
    if (!ed) {
      return null
    }
    return getComputedStyle(ed.container)
  }

  /**
   * 创建截图 DOM 容器
   */
  function createScreenshotContainer (
    text: string,
    computedStyle: CSSStyleDeclaration,
  ): HTMLElement {
    const lines = text.split('\n')
    const fontSize = computedStyle.fontSize || '13px'
    const fontFamily = computedStyle.fontFamily || 'monospace'
    const background = computedStyle.backgroundColor || '#fff'
    const color = computedStyle.color || '#000'
    const lineHeight = computedStyle.lineHeight && computedStyle.lineHeight !== 'normal'
      ? computedStyle.lineHeight
      : '1.4'

    // 创建主容器
    const wrapper = document.createElement('div')
    wrapper.style.position = 'absolute'
    wrapper.style.left = '-9999px'
    wrapper.style.top = '0px'
    wrapper.style.background = background
    wrapper.style.color = color
    wrapper.style.display = 'flex'
    wrapper.style.padding = '12px'
    wrapper.style.boxSizing = 'border-box'
    wrapper.style.borderRadius = '4px'
    wrapper.style.fontSize = fontSize
    wrapper.style.fontFamily = fontFamily
    wrapper.style.lineHeight = lineHeight

    // 创建行号容器
    const gutter = document.createElement('div')
    gutter.style.userSelect = 'none'
    gutter.style.textAlign = 'right'
    gutter.style.paddingRight = '12px'
    gutter.style.marginRight = '12px'
    gutter.style.opacity = '0.6'
    gutter.style.fontSize = fontSize
    gutter.style.fontFamily = fontFamily
    gutter.style.lineHeight = lineHeight
    gutter.style.whiteSpace = 'pre'
    gutter.textContent = lines.map((_, i) => (i + 1).toString()).join('\n')

    // 创建代码容器
    const code = document.createElement('pre')
    code.style.margin = '0'
    code.style.whiteSpace = 'pre'
    code.style.fontFamily = fontFamily
    code.style.fontSize = fontSize
    code.style.lineHeight = lineHeight
    code.style.background = 'transparent'
    code.style.color = color
    code.style.overflow = 'visible'
    code.innerHTML = hljs.highlightAuto(text).value

    wrapper.append(gutter)
    wrapper.append(code)

    return wrapper
  }

  /**
   * 添加 highlight.js 样式到文档
   */
  function addHighlightJsStyle (): HTMLLinkElement {
    const style = document.createElement('link')
    style.rel = 'stylesheet'
    style.href = getHighlightJsStyleUrl()
    document.head.append(style)
    return style
  }

  /**
   * 将 canvas 内容写入剪贴板
   */
  async function writeToClipboard (canvas: HTMLCanvasElement): Promise<boolean> {
    if (!navigator.clipboard || !(navigator.clipboard as any).write) {
      return false
    }

    try {
      const blob: Blob | null = await new Promise(resolve =>
        canvas.toBlob(b => resolve(b), 'image/png'),
      )

      if (!blob) {
        console.warn('[useEditorScreenshot] Failed to create blob from canvas')
        return false
      }

      await (navigator.clipboard as any).write([
        new (window as any).ClipboardItem({ 'image/png': blob }),
      ])

      return true
    } catch (error_) {
      console.error('[useEditorScreenshot] Failed to write to clipboard:', error_)
      return false
    }
  }

  /**
   * 下载截图
   */
  function downloadScreenshot (canvas: HTMLCanvasElement, filename = 'code-screenshot.png'): void {
    const url = canvas.toDataURL('image/png')
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.append(a)
    a.click()
    a.remove()
  }

  /**
   * 清理 DOM 元素
   */
  function cleanup (wrapper: HTMLElement, style: HTMLLinkElement): void {
    try {
      if (wrapper.parentNode) {
        wrapper.remove()
      }
    } catch (error_) {
      console.warn('[useEditorScreenshot] Failed to remove wrapper:', error_)
    }

    try {
      if (style.parentNode) {
        style.remove()
      }
    } catch (error_) {
      console.warn('[useEditorScreenshot] Failed to remove style:', error_)
    }
  }

  /**
   * 执行代码截图
   *
   * 流程：
   * 1. 获取编辑器内容（优先选区）
   * 2. 获取编辑器样式
   * 3. 创建截图 DOM 并应用 highlight.js 高亮
   * 4. 使用 html2canvas 渲染为 Canvas
   * 5. 优先写入剪贴板，不支持时自动下载
   */
  async function takeScreenshot (): Promise<void> {
    const ed = editor.value
    if (!ed) {
      console.warn('[useEditorScreenshot] Cannot take screenshot: editor not initialized')
      error.value = 'Editor not initialized'
      return
    }

    isCapturing.value = true
    error.value = null

    let wrapper: HTMLElement | null = null
    let style: HTMLLinkElement | null = null

    try {
      // 获取内容：优先选区，否则全部
      const text = ed.getSelectedText() || ed.getValue()

      if (!text.trim()) {
        console.warn('[useEditorScreenshot] No content to capture')
        error.value = 'No content to capture'
        return
      }

      // 获取编辑器计算样式
      const computedStyle = getEditorComputedStyle()
      if (!computedStyle) {
        throw new Error('Failed to get editor computed style')
      }

      // 创建截图 DOM 容器
      wrapper = createScreenshotContainer(text, computedStyle)

      // 添加 highlight.js 样式
      style = addHighlightJsStyle()

      // 添加到 DOM 进行渲染
      document.body.append(wrapper)

      // 使用 html2canvas 生成截图
      const canvas = await html2canvas(wrapper, {
        backgroundColor: null,
        scale: 2,
      })

      // 尝试写入剪贴板，失败则下载
      const clipboardSuccess = await writeToClipboard(canvas)

      if (!clipboardSuccess) {
        downloadScreenshot(canvas)
      }

      console.log('[useEditorScreenshot] Screenshot captured successfully')
    } catch (error_) {
      const errorMessage = error_ instanceof Error ? error_.message : 'Unknown error'
      console.error('[useEditorScreenshot] Failed to take screenshot:', error_)
      error.value = errorMessage
    } finally {
      // 清理 DOM 元素
      if (wrapper && style) {
        cleanup(wrapper, style)
      }
      isCapturing.value = false
    }
  }

  return {
    isCapturing,
    error,
    takeScreenshot,
    clearError,
  }
}

export default useEditorScreenshot
