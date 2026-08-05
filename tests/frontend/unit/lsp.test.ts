import { beforeEach, describe, expect, it, vi } from 'vitest'

const lspMocks = vi.hoisted(() => {
  const provider = {
    registerEditor: vi.fn(),
    closeDocument: vi.fn(),
    format: vi.fn(),
    changeWorkspaceFolder: vi.fn(),
  }
  return {
    provider,
    createProvider: vi.fn(() => provider),
  }
})

vi.mock('ace-linters/build/ace-language-client', () => ({
  AceLanguageClient: {
    for: lspMocks.createProvider,
  },
}))

describe('lsp.ts', () => {
  let mockApi: {
    get_langs: ReturnType<typeof vi.fn>
    get_port: ReturnType<typeof vi.fn>
    get_opened_file: ReturnType<typeof vi.fn>
    get_cwd: ReturnType<typeof vi.fn>
    path_parent: ReturnType<typeof vi.fn>
  }
  let mockWebSocket: ReturnType<typeof vi.fn>

  beforeEach(() => {
    vi.resetModules()
    lspMocks.createProvider.mockClear()
    lspMocks.provider.changeWorkspaceFolder.mockClear()

    mockApi = {
      get_langs: vi.fn().mockResolvedValue([
        {
          id: 'python',
          display: 'Python',
          lsp: { command: 'ty server' },
          suffix: ['.py'],
          alias: ['python3'],
        },
      ]),
      get_port: vi.fn().mockResolvedValue(8000),
      get_opened_file: vi.fn().mockResolvedValue('/work dir/main.py'),
      get_cwd: vi.fn().mockResolvedValue('/fallback'),
      path_parent: vi.fn().mockResolvedValue('/work dir'),
    }
    window.pywebview = {
      api: mockApi as any,
      state: {
        addEventListener: vi.fn(),
        prob: null,
      },
    }

    mockWebSocket = vi.fn().mockImplementation((url: URL) => ({
      url,
      send: vi.fn(),
      close: vi.fn(),
      readyState: 1,
    }))
    vi.stubGlobal('WebSocket', mockWebSocket)
  })

  it('initializes lazily with the opened file workspace', async () => {
    const { getLanguageProvider } = await import('@/lsp')

    expect(mockApi.get_langs).not.toHaveBeenCalled()

    await getLanguageProvider()
    const [serverDataList, options] = lspMocks.createProvider.mock.calls[0]

    expect(mockApi.path_parent).toHaveBeenCalledWith('/work dir/main.py')
    expect(options.workspacePath).toBe('/work dir')
    expect(options.functionality.completion.overwriteCompleters).toBe(false)
    expect(serverDataList).toEqual([
      expect.objectContaining({
        modes: 'python|python3',
        serviceName: 'python',
        type: 'socket',
      }),
    ])
    expect(String(mockWebSocket.mock.calls[0][0])).toBe(
      'ws://127.0.0.1:8000/lsp/python?workspace=%2Fwork+dir',
    )
    expect(lspMocks.provider.changeWorkspaceFolder).toHaveBeenCalledWith('/work dir')
  })

  it('falls back to the application cwd when no file is opened', async () => {
    mockApi.get_opened_file.mockResolvedValue(null)
    const { getLanguageProvider } = await import('@/lsp')

    await getLanguageProvider()

    expect(mockApi.get_cwd).toHaveBeenCalled()
    expect(lspMocks.provider.changeWorkspaceFolder).toHaveBeenCalledWith('/fallback')
  })

  it('reuses the provider and updates its workspace', async () => {
    const { getLanguageProvider } = await import('@/lsp')
    const provider = await getLanguageProvider()
    mockApi.get_opened_file.mockResolvedValue('/other/main.py')
    mockApi.path_parent.mockResolvedValue('/other')

    const reusedProvider = await getLanguageProvider()

    expect(reusedProvider).toBe(provider)
    expect(lspMocks.createProvider).toHaveBeenCalledTimes(1)
    expect(lspMocks.provider.changeWorkspaceFolder).toHaveBeenLastCalledWith('/other')
  })

  it('applies the latest workspace during concurrent initialization', async () => {
    let finishLanguageLoad: (languages: unknown[]) => void = () => {}
    mockApi.get_langs.mockReturnValue(new Promise(resolve => {
      finishLanguageLoad = resolve
    }))
    mockApi.get_opened_file
      .mockResolvedValueOnce('/first/main.py')
      .mockResolvedValueOnce('/second/main.py')
    mockApi.path_parent
      .mockResolvedValueOnce('/first')
      .mockResolvedValueOnce('/second')
    const { getLanguageProvider } = await import('@/lsp')

    const firstProvider = getLanguageProvider()
    await vi.waitFor(() => expect(mockApi.get_langs).toHaveBeenCalled())
    const secondProvider = getLanguageProvider()
    await vi.waitFor(() => expect(mockApi.path_parent).toHaveBeenCalledTimes(2))
    finishLanguageLoad([])

    await Promise.all([firstProvider, secondProvider])

    expect(lspMocks.provider.changeWorkspaceFolder).toHaveBeenNthCalledWith(1, '/first')
    expect(lspMocks.provider.changeWorkspaceFolder).toHaveBeenLastCalledWith('/second')
  })

  it('skips languages without an LSP command', async () => {
    mockApi.get_langs.mockResolvedValue([
      { id: 'plaintext', display: 'Plain Text', suffix: ['.txt'], alias: [] },
    ])
    const { getLanguageProvider } = await import('@/lsp')

    await getLanguageProvider()

    expect(mockWebSocket).not.toHaveBeenCalled()
    expect(lspMocks.createProvider).toHaveBeenCalledWith(
      [],
      expect.objectContaining({ workspacePath: '/work dir' }),
    )
  })
})
