import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'
import { useTerminalStore } from '@/stores/terminal'

describe('terminal store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('starts hidden and idle', () => {
    const store = useTerminalStore()

    expect(store.visible).toBe(false)
    expect(store.status).toBe('idle')
    expect(store.exitCode).toBeNull()
    expect(store.isConnected).toBe(false)
  })

  it('toggles visibility', () => {
    const store = useTerminalStore()

    store.toggleVisible()
    expect(store.visible).toBe(true)

    store.toggleVisible()
    expect(store.visible).toBe(false)
  })

  it('reports connection state through getters', () => {
    const store = useTerminalStore()

    store.setStatus('connecting')
    expect(store.isBusy).toBe(true)
    expect(store.isConnected).toBe(false)

    store.setStatus('connected')
    expect(store.isBusy).toBe(false)
    expect(store.isConnected).toBe(true)
  })

  it('records the exit code and marks the session exited', () => {
    const store = useTerminalStore()
    store.setStatus('connected')

    store.setExitCode(130)

    expect(store.status).toBe('exited')
    expect(store.exitCode).toBe(130)
  })

  it('clears a stale exit code when reconnecting', () => {
    const store = useTerminalStore()
    store.setExitCode(1)

    store.setStatus('connecting')

    expect(store.exitCode).toBeNull()
  })

  it('clamps the height so dragging cannot break the layout', () => {
    const store = useTerminalStore()

    store.setHeight(20)
    expect(store.height).toBe(120)

    store.setHeight(5000)
    expect(store.height).toBe(800)

    store.setHeight(320)
    expect(store.height).toBe(320)
  })

  it('resets every field', () => {
    const store = useTerminalStore()
    store.setVisible(true)
    store.setExitCode(2)
    store.setHeight(500)

    store.resetTerminalState()

    expect(store.visible).toBe(false)
    expect(store.status).toBe('idle')
    expect(store.exitCode).toBeNull()
    expect(store.height).toBe(260)
  })
})
