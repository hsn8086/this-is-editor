import { beforeAll, vi } from 'vitest'

// Mock localStorage for Pinia
const localStorageMock = {
  getItem: vi.fn().mockReturnValue(null),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  key: vi.fn().mockReturnValue(null),
  length: 0,
}
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
})

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn().mockReturnValue(null),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  key: vi.fn().mockReturnValue(null),
  length: 0,
}
Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
  writable: true,
})

// Mock Ace editor
vi.mock('ace-builds', () => ({
  Ace: {
    Edit: vi.fn().mockImplementation(() => ({
      setTheme: vi.fn(),
      setOption: vi.fn(),
      getValue: vi.fn().mockReturnValue(''),
      setValue: vi.fn(),
      getCursorPosition: vi.fn().mockReturnValue({ row: 0, column: 0 }),
      moveCursorToPosition: vi.fn(),
      scrollToLine: vi.fn(),
      session: {
        setMode: vi.fn(),
        setValue: vi.fn(),
        getLine: vi.fn().mockReturnValue(''),
        remove: vi.fn(),
        removeFullLines: vi.fn(),
        getSelectionRange: vi.fn(),
      },
      container: {
        style: {},
      },
      renderer: {
        updateFontSize: vi.fn(),
      },
      on: vi.fn(),
      setKeyboardHandler: vi.fn(),
      getSelectedText: vi.fn().mockReturnValue(''),
    })),
  },
}))

// Mock ace-linters
vi.mock('ace-linters/build/ace-language-client', () => ({
  AceLanguageClient: {
    for: vi.fn().mockImplementation((_serverDataList: any[], _options: any[]) => ({
      registerEditor: vi.fn(),
      closeDocument: vi.fn(),
      format: vi.fn(),
    })),
  },
}))

// Mock vue3-ace-editor
vi.mock('vue3-ace-editor', () => ({
  VAceEditor: {
    name: 'VAceEditor',
  },
}))

// Mock pywebview
beforeAll(() => {
  // Mock pywebview API
  const mockApi = {
    get_pinned_files: vi.fn().mockResolvedValue([]),
    add_pinned_file: vi.fn().mockResolvedValue(undefined),
    remove_pinned_file: vi.fn().mockResolvedValue(undefined),
    get_disks: vi.fn().mockResolvedValue([]),
    format_code: vi.fn().mockResolvedValue(''),
    focus: vi.fn().mockResolvedValue(undefined),
    save_scoll: vi.fn().mockResolvedValue(undefined),
    get_scoll: vi.fn().mockResolvedValue(0),
    get_cpu_count: vi.fn().mockResolvedValue([4, 8]),
    compile: vi.fn().mockResolvedValue('success'),
    cleanup_compiled_artifact: vi.fn().mockResolvedValue(undefined),
    run_task: vi.fn().mockResolvedValue({
      result: 'Accepted',
      stderr: '',
      status: 'success',
      time: 100,
      memory: 1024,
    }),
    get_testcase: vi.fn().mockResolvedValue({
      name: 'default',
      tests: [{ id: 1, input: '1\n', answer: '1\n' }],
      memoryLimit: 256,
      timeLimit: 1000,
    }),
    save_testcase: vi.fn().mockResolvedValue(undefined),
    set_config: vi.fn().mockResolvedValue(undefined),
    get_config: vi.fn().mockResolvedValue({
      editor: {
        aceMain: {},
        tie: {},
      },
      programmingLanguages: {},
      keyboardShortcuts: {},
    }),
    get_config_path: vi.fn().mockResolvedValue('/mock/config/path'),
    get_langs: vi.fn().mockResolvedValue([]),
    get_port: vi.fn().mockReturnValue(8000),
    get_code: vi.fn().mockResolvedValue({
      code: '',
      type: 'plaintext',
      alias: [],
    }),
    save_code: vi.fn().mockResolvedValue(undefined),
    set_cwd: vi.fn().mockResolvedValue(undefined),
    set_opened_file: vi.fn().mockResolvedValue(undefined),
    get_opened_file: vi.fn().mockResolvedValue(null),
    get_cwd: vi.fn().mockResolvedValue('/mock/cwd'),
    path_to_uri: vi.fn().mockResolvedValue('file:///mock/path'),
    path_ls: vi.fn().mockResolvedValue({
      now_path: '/mock',
      files: [],
    }),
    path_join: vi.fn().mockResolvedValue('/mock/path'),
    path_parent: vi.fn().mockResolvedValue('/mock'),
    path_get_info: vi.fn().mockResolvedValue({
      name: 'mock',
      stem: 'mock',
      path: '/mock',
      is_dir: false,
      is_file: true,
      is_symlink: false,
      size: 0,
      last_modified: '2024-01-01T00:00:00',
      type: 'file',
    }),
    path_get_text: vi.fn().mockResolvedValue(''),
    path_save_text: vi.fn().mockResolvedValue(undefined),
    path_mkdir: vi.fn().mockResolvedValue({ status: 'success', message: '' }),
    path_touch: vi.fn().mockResolvedValue({ status: 'success', message: '' }),
    path_rename: vi.fn().mockResolvedValue({ status: 'success', message: '' }),
    path_delete: vi.fn().mockResolvedValue({ status: 'success', message: '' }),
  }

  // Mock pywebview state
  const mockState = {
    addEventListener: vi.fn(),
    prob: null,
  }

  // Assign to window
  Object.defineProperty(window, 'pywebview', {
    value: {
      api: mockApi,
      state: mockState,
    },
    writable: true,
  })
})

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSING = 2
  static CLOSED = 3

  readyState = MockWebSocket.CONNECTING
  onopen: ((event: any) => void) | null = null
  onclose: ((event: any) => void) | null = null
  onmessage: ((event: any) => void) | null = null
  onerror: ((event: any) => void) | null = null

  constructor (public url: string) {
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN
      if (this.onopen) {
        this.onopen({})
      }
    }, 0)
  }

  send = vi.fn()
  close = vi.fn()
}

vi.stubGlobal('WebSocket', MockWebSocket)

// Mock html2canvas
vi.mock('html2canvas', () => ({
  default: vi.fn().mockImplementation(() =>
    Promise.resolve({
      toBlob: vi.fn(callback => callback(null)),
      toDataURL: vi.fn().mockReturnValue('data:image/png;base64,mock'),
    }),
  ),
}))

// Mock highlight.js
vi.mock('highlight.js', () => ({
  default: {
    highlightAuto: vi.fn().mockReturnValue({ value: '<code>test</code>' }),
  },
  highlightAuto: vi.fn().mockReturnValue({ value: '<code>test</code>' }),
}))

// Mock vue-i18n
vi.mock('vue-i18n', () => ({
  useI18n: vi.fn().mockReturnValue({
    t: vi.fn((key: string) => key),
    locale: { value: 'en-US' },
  }),
}))

// Mock Vue hooks - use importOriginal to get actual Vue exports
vi.mock('vue', async importOriginal => {
  const actual = await importOriginal() as any
  return {
    ...actual,
    // Use actual ref/computed for Pinia stores to work correctly
    onMounted: actual?.onMounted || vi.fn(),
    onUnmounted: actual?.onUnmounted || vi.fn(),
    nextTick: actual?.nextTick || vi.fn().mockResolvedValue(undefined),
    defineExpose: actual?.defineExpose || vi.fn(),
    watch: actual?.watch || vi.fn(),
    triggerRef: actual?.triggerRef || vi.fn(),
  }
})
vi.mock('vuetify', () => {
  const VComponent = {
    name: 'VComponent',
    props: {
      modelValue: Boolean,
    },
    emits: ['update:modelValue'],
  }
  return {
    useTheme: vi.fn().mockReturnValue({
      global: {
        current: {
          value: {
            dark: true,
          },
        },
      },
    }),
    useHotkey: vi.fn().mockReturnValue({
      use: vi.fn(),
    }),
    VApp: VComponent,
    VMain: VComponent,
    VNavigationDrawer: VComponent,
    VList: VComponent,
    VListItem: VComponent,
    VMenu: VComponent,
    VIcon: VComponent,
    VDivider: VComponent,
    VTextarea: VComponent,
    VChip: VComponent,
    VAvatar: VComponent,
    VProgressLinear: VComponent,
    VTooltip: VComponent,
    VAlert: VComponent,
  }
})

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock ResizeObserver
class MockResizeObserver {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}

Object.defineProperty(window, 'ResizeObserver', {
  writable: true,
  value: MockResizeObserver,
})

// Mock console.error to suppress errors in tests (optional)
const originalConsoleError = console.error
console.error = (...args: unknown[]) => {
  // Filter out known harmless errors in test environment
  const message = args[0]
  if (
    typeof message === 'string'
    && (message.includes('[Vue warn]')
      || message.includes('ResizeObserver')
      || message.includes('Hydration'))
  ) {
    return
  }
  originalConsoleError(...args)
}
