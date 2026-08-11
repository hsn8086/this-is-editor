import type { ITheme } from '@xterm/xterm'
import type { Ref } from 'vue'
import { FitAddon } from '@xterm/addon-fit'
import { Terminal } from '@xterm/xterm'
import { ref, watch } from 'vue'
import { useTheme } from 'vuetify'
import '@xterm/xterm/css/xterm.css'

/**
 * ANSI 16 色板。
 *
 * 刻意取自编辑器现有的两套 Ace 主题（暗色 src/styles/ace-theme-gruvbox.css、
 * 亮色 src/styles/ace-theme-github.css），这样终端里的着色输出与旁边代码
 * 高亮属于同一色系，而不是另起一套。
 *
 * 背景/前景/光标不写死在这里，改为在 buildTheme() 里从 Vuetify 主题 token
 * 取值，从而与面板本身的 surface 底色严格一致，并自动跟随亮暗切换。
 */
const ANSI_DARK = {
  black: '#3b3735',
  red: '#d75f5f',
  green: '#9ece6a',
  yellow: '#b8bb26',
  blue: '#7aa2f7',
  magenta: '#bb9af7',
  cyan: '#2ac3ed',
  white: '#c0caf5',
  brightBlack: '#7c6f64',
  brightRed: '#d75f5f',
  brightGreen: '#b8bb26',
  brightYellow: '#d3869b',
  brightBlue: '#83a598',
  brightMagenta: '#d3869b',
  brightCyan: '#8ec07c',
  brightWhite: '#ffffff',
} as const

const ANSI_LIGHT = {
  black: '#24292e',
  red: '#D73A49',
  green: '#22863A',
  yellow: '#E36209',
  blue: '#005CC5',
  magenta: '#6F42C1',
  cyan: '#032F62',
  white: '#6A737D',
  brightBlack: '#444d56',
  brightRed: '#B31D28',
  brightGreen: '#22863A',
  brightYellow: '#E36209',
  brightBlue: '#044289',
  brightMagenta: '#6F42C1',
  brightCyan: '#005CC5',
  brightWhite: '#24292E',
} as const

/** 与 src/styles/ace-theme.css 保持一致的等宽字体栈 */
const FONT_FAMILY
  = '"maple mono", ui-monospace, "SFMono-Regular", Menlo, Monaco, monospace'

export interface UseTerminalOptions {
  /** 终端挂载的容器元素 Ref */
  container: Ref<HTMLElement | undefined>
  /** 解析后端 WebSocket 端口，注入以便测试 */
  resolvePort: () => Promise<number>
  /** 是否自动跟随 Vuetify 亮暗切换，默认 true */
  autoWatch?: boolean
  /** 终端字号 */
  fontSize?: number
  /** 连接建立时回调 */
  onConnected?: () => void
  /** shell 退出时回调，参数为退出码 */
  onExit?: (code: number | null) => void
  /** 出错时回调 */
  onError?: (message: string) => void
}

export interface UseTerminalReturn {
  /** 终端是否已挂载并连上后端 */
  isReady: Ref<boolean>
  /** 当前是否暗色 */
  isDark: Ref<boolean>
  /** 创建 xterm 实例并连接后端 */
  mount: () => Promise<void>
  /** 断开连接并销毁实例 */
  dispose: () => void
  /** 重新适配容器尺寸并把新的行列数同步给后端 */
  fit: () => void
  /** 清屏 */
  clear: () => void
  /** 向 shell 发送中断信号（Ctrl-C） */
  interrupt: () => void
  /** 依据当前 Vuetify 主题重建配色并应用 */
  syncTheme: () => void
}

/**
 * 终端控制台：管理 xterm 实例、与后端 /terminal 的 WebSocket 双向流，
 * 以及配色与 Vuetify 亮暗主题的同步。
 *
 * 负责：
 * - 创建/销毁 xterm 实例与 FitAddon
 * - 建立 WebSocket，转发按键到 shell、把 shell 输出写回终端
 * - 监听 Vuetify 主题变化并实时换肤
 * - 容器尺寸变化时重新 fit 并把 cols/rows 通知后端
 *
 * 依赖：调用方需保证 container 在 mount() 时已渲染。
 *
 * 注意：必须在 setup 同步上下文中调用（内部使用 useTheme()）。
 * 生命周期为手动模式，调用方需在 onUnmounted 中调用 dispose()。
 */
export function useTerminal (options: UseTerminalOptions): UseTerminalReturn {
  const {
    container,
    resolvePort,
    autoWatch = true,
    fontSize = 13,
    onConnected,
    onExit,
    onError,
  } = options

  const vuetifyTheme = useTheme()
  const isReady = ref(false)
  const isDark = ref(vuetifyTheme.global.current.value.dark)

  let term: Terminal | undefined
  let fitAddon: FitAddon | undefined
  let socket: WebSocket | undefined
  let resizeObserver: ResizeObserver | undefined
  let fitFrame: number | undefined
  let disposed = false

  /** 从 Vuetify 当前主题 token 构建 xterm 配色 */
  function buildTheme (): ITheme {
    const current = vuetifyTheme.global.current.value
    const colors = current.colors
    const ansi = current.dark ? ANSI_DARK : ANSI_LIGHT
    return {
      // 与承载面板同一个 surface，终端不会显得像贴上去的另一块
      background: colors.surface,
      foreground: colors['on-surface'],
      cursor: colors.primary,
      cursorAccent: colors.surface,
      selectionBackground: current.dark
        ? 'rgba(255, 255, 255, 0.25)'
        : 'rgba(0, 0, 0, 0.18)',
      ...ansi,
    }
  }

  function syncTheme (): void {
    isDark.value = vuetifyTheme.global.current.value.dark
    if (!term) {
      return
    }
    term.options.theme = buildTheme()
  }

  function send (payload: Record<string, unknown>): void {
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(payload))
    }
  }

  function fit (): void {
    if (!term || !fitAddon) {
      return
    }
    try {
      fitAddon.fit()
      send({ type: 'resize', cols: term.cols, rows: term.rows })
    } catch (error) {
      console.warn('[useTerminal] Failed to fit terminal:', error)
    }
  }

  /** 合并同一帧内 ResizeObserver 的多次通知，避免拖拽时重复 layout。 */
  function scheduleFit (): void {
    if (fitFrame !== undefined) {
      return
    }
    fitFrame = window.requestAnimationFrame(() => {
      fitFrame = undefined
      fit()
    })
  }

  function clear (): void {
    term?.clear()
  }

  function interrupt (): void {
    send({ type: 'interrupt' })
  }

  async function mount (): Promise<void> {
    const element = container.value
    if (!element) {
      console.warn('[useTerminal] Cannot mount: container is not ready')
      return
    }
    if (term) {
      return
    }

    term = new Terminal({
      fontFamily: FONT_FAMILY,
      fontSize,
      theme: buildTheme(),
      cursorBlink: true,
      convertEol: false,
      scrollback: 5000,
      allowProposedApi: true,
    })
    fitAddon = new FitAddon()
    term.loadAddon(fitAddon)
    term.open(element)
    fitAddon.fit()

    try {
      const port = await resolvePort()
      if (disposed) {
        return
      }
      socket = new WebSocket(`ws://127.0.0.1:${port}/terminal`)
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error)
      console.error('[useTerminal] Failed to resolve backend port:', error)
      onError?.(message)
      return
    }

    socket.addEventListener('open', () => {
      isReady.value = true
      console.log('[useTerminal] Terminal socket connected')
      onConnected?.()
      fit()
    })

    socket.addEventListener('message', event => {
      let message: { type?: string, data?: string, code?: number | null }
      try {
        message = JSON.parse(event.data as string)
      } catch {
        console.warn('[useTerminal] Discarding malformed frame')
        return
      }
      if (message.type === 'output' && typeof message.data === 'string') {
        term?.write(message.data)
      } else if (message.type === 'exit') {
        isReady.value = false
        onExit?.(message.code ?? null)
      }
    })

    socket.addEventListener('error', () => {
      isReady.value = false
      console.error('[useTerminal] Terminal socket error')
      onError?.('socket error')
    })

    socket.addEventListener('close', () => {
      isReady.value = false
    })

    term.onData(data => send({ type: 'stdin', data }))

    // 面板可拖拽改变高度，尺寸一变就要重新计算行列并通知 shell
    if (typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(() => scheduleFit())
      resizeObserver.observe(element)
    }
  }

  function dispose (): void {
    disposed = true
    isReady.value = false
    resizeObserver?.disconnect()
    resizeObserver = undefined
    if (fitFrame !== undefined) {
      window.cancelAnimationFrame(fitFrame)
      fitFrame = undefined
    }
    if (socket) {
      socket.close()
      socket = undefined
    }
    term?.dispose()
    term = undefined
    fitAddon = undefined
    console.log('[useTerminal] Terminal disposed')
  }

  if (autoWatch) {
    watch(
      () => vuetifyTheme.global.current.value.dark,
      () => syncTheme(),
      { immediate: false },
    )
  }

  return {
    isReady,
    isDark,
    mount,
    dispose,
    fit,
    clear,
    interrupt,
    syncTheme,
  }
}

export default useTerminal
