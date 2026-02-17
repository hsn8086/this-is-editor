import { beforeAll, vi } from 'vitest'

// Mock window.pywebview
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
    run_task: vi.fn().mockResolvedValue({
      result: 'Accepted',
      status: 'Done',
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
