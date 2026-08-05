import * as ace from 'ace-builds'
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest'

vi.unmock('ace-builds')

interface Completion {
  caption: string
  snippet?: string
}

const editors: ace.Ace.Editor[] = []

beforeAll(async () => {
  Object.assign(globalThis, { ace })
  await import('ace-builds/src-noconflict/ext-language_tools')
  await import('ace-builds/src-noconflict/mode-python')
  await import('ace-builds/src-noconflict/mode-c_cpp')
  await import('ace-builds/src-noconflict/snippets/python')
  await import('ace-builds/src-noconflict/snippets/c_cpp')
})

async function snippetCompletions (mode: string): Promise<Completion[]> {
  const container = document.createElement('div')
  document.body.append(container)
  const editor = ace.edit(container)
  editors.push(editor)
  editor.setOptions({
    enableBasicAutocompletion: true,
    enableLiveAutocompletion: true,
    enableSnippets: true,
  })
  editor.session.setMode(`ace/mode/${mode}`)

  const completer = editor.completers?.find(item => item.id === 'snippetCompleter')
  if (!completer) {
    throw new Error('Snippet completer was not registered')
  }

  return new Promise((resolve, reject) => {
    completer.getCompletions(
      editor,
      editor.session,
      { row: 0, column: 0 },
      '',
      (error, completions) => error ? reject(error) : resolve(completions as Completion[]),
    )
  })
}

afterEach(() => {
  for (const editor of editors.splice(0)) {
    const container = editor.container
    editor.destroy()
    container.remove()
  }
})

describe('snippet autocompletion', () => {
  it('offers expandable Python snippets', async () => {
    const completions = await snippetCompletions('python')

    expect(completions.some(item => item.caption === 'def' && item.snippet)).toBe(true)
  })

  it('offers expandable C++ snippets', async () => {
    const completions = await snippetCompletions('c_cpp')

    expect(completions.some(item => item.caption === 'vector' && item.snippet)).toBe(true)
  })
})
