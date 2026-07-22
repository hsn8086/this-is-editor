import type { AceLanguageClient, LanguageClientConfig, ProviderOptions } from 'ace-linters/build/ace-language-client'
export type LanguageProvider = ReturnType<typeof AceLanguageClient.for>

let languageProvider: LanguageProvider | undefined
let initializationPromise: Promise<LanguageProvider> | undefined
let activeWorkspacePath: string | undefined

async function getWorkspacePath (): Promise<string> {
  const py = window.pywebview.api
  const openedFile = await py.get_opened_file()
  return openedFile ? await py.path_parent(openedFile) : await py.get_cwd()
}

async function initLSP (workspacePath: string): Promise<LanguageProvider> {
  const py = window.pywebview.api
  const langs = await py.get_langs()
  const options: ProviderOptions = {
    workspacePath,
    functionality: {
      hover: true,
      completion: {
        overwriteCompleters: false,
        lspCompleterOptions: { triggerCharacters: { add: ['.'] } },
      },
      documentHighlights: true,
    },
  }
  const serverDataList: LanguageClientConfig[] = []
  const port = await py.get_port()
  for (const lang of langs) {
    const command = lang.lsp?.command
    if (!command || (Array.isArray(command) ? command.length === 0 : command.trim() === '')) {
      continue
    }
    const modes = [lang.id, ...lang.alias]
    const socketUrl = new URL(`ws://127.0.0.1:${port}/lsp/${lang.id}`)
    socketUrl.searchParams.set('workspace', workspacePath)

    serverDataList.push({
      module: () => import('ace-linters/build/language-client'),
      modes: modes.join('|'),
      serviceName: lang.id,
      type: 'socket' as const,
      socket: new WebSocket(socketUrl),
    })
  }

  const { AceLanguageClient } = await import('ace-linters/build/ace-language-client')
  const provider = AceLanguageClient.for(serverDataList, options)
  // ace-linters does not propagate ProviderOptions.workspacePath to its
  // internal service manager until this method is called.
  provider.changeWorkspaceFolder(workspacePath)
  return provider
}

export async function getLanguageProvider (): Promise<LanguageProvider> {
  const workspacePath = await getWorkspacePath()

  if (languageProvider) {
    if (workspacePath !== activeWorkspacePath) {
      languageProvider.changeWorkspaceFolder(workspacePath)
      activeWorkspacePath = workspacePath
    }
    return languageProvider
  }

  if (!initializationPromise) {
    activeWorkspacePath = workspacePath
    initializationPromise = initLSP(workspacePath)
  }
  try {
    languageProvider = await initializationPromise
    if (workspacePath !== activeWorkspacePath) {
      languageProvider.changeWorkspaceFolder(workspacePath)
      activeWorkspacePath = workspacePath
    }
    return languageProvider
  } catch (error) {
    initializationPromise = undefined
    activeWorkspacePath = undefined
    throw error
  }
}
