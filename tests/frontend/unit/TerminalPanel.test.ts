import { shallowMount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, nextTick } from 'vue'
import TerminalPanel from '@/components/TerminalPanel.vue'
import { useTerminalStore } from '@/stores/terminal'

const terminalApi = {
  mount: vi.fn().mockResolvedValue(undefined),
  dispose: vi.fn(),
  fit: vi.fn(),
  clear: vi.fn(),
  interrupt: vi.fn(),
}

vi.mock('@/composables/terminal/useTerminal', () => ({
  useTerminal: vi.fn(() => terminalApi),
}))

const NavigationDrawerStub = defineComponent({
  inheritAttrs: false,
  props: {
    modelValue: Boolean,
    width: Number,
  },
  template: `
    <aside class="drawer-stub" :data-width="width">
      <div class="v-navigation-drawer__content"><slot /></div>
    </aside>
  `,
})

const initialInnerHeight = window.innerHeight

function mountPanel () {
  return shallowMount(TerminalPanel, {
    global: {
      mocks: {
        $t: (key: string) => key,
      },
      stubs: {
        VNavigationDrawer: NavigationDrawerStub,
        VList: { template: '<div><slot /></div>' },
        VListItem: { template: '<div><slot /><slot name="prepend" /><slot name="append" /></div>' },
        VListItemTitle: { template: '<div><slot /></div>' },
        VIcon: true,
        VChip: true,
        VBtn: true,
        VDivider: true,
      },
    },
  })
}

function pointerEvent (
  type: string,
  options: { clientY: number, pointerId: number },
): Event {
  const event = new Event(type, { bubbles: true, cancelable: true })
  Object.defineProperties(event, {
    clientY: { value: options.clientY },
    pointerId: { value: options.pointerId },
  })
  return event
}

describe('terminal panel', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    document.documentElement.classList.remove('terminal-is-resizing')
  })

  afterEach(() => {
    Object.defineProperty(window, 'innerHeight', {
      configurable: true,
      value: initialInnerHeight,
    })
  })

  it('passes its height through the drawer width prop', () => {
    const wrapper = mountPanel()

    // VNavigationDrawer always names its layout thickness `width`, including
    // for top/bottom drawers. Binding a non-existent height prop was the reason
    // the old resizer animated but never changed the panel.
    expect(wrapper.get('.drawer-stub').attributes('data-width')).toBe('260')
    wrapper.unmount()
  })

  it('resizes upward and cleans pointer state afterwards', async () => {
    const wrapper = mountPanel()
    const store = useTerminalStore()
    const handle = wrapper.get('.terminal-resizer').element as HTMLElement
    const captured = new Set<number>()
    handle.setPointerCapture = vi.fn(id => captured.add(id))
    handle.hasPointerCapture = vi.fn(id => captured.has(id))
    handle.releasePointerCapture = vi.fn(id => captured.delete(id))

    handle.dispatchEvent(pointerEvent('pointerdown', { clientY: 300, pointerId: 7 }))
    window.dispatchEvent(pointerEvent('pointermove', { clientY: 200, pointerId: 7 }))
    await nextTick()

    expect(store.height).toBe(360)
    expect(wrapper.get('.drawer-stub').attributes('data-width')).toBe('360')
    expect(document.documentElement.classList.contains('terminal-is-resizing')).toBe(true)

    window.dispatchEvent(pointerEvent('pointerup', { clientY: 200, pointerId: 7 }))
    expect(document.documentElement.classList.contains('terminal-is-resizing')).toBe(false)
    expect(handle.releasePointerCapture).toHaveBeenCalledWith(7)
    wrapper.unmount()
  })

  it('leaves editor space when dragged to the top of the viewport', async () => {
    const wrapper = mountPanel()
    const store = useTerminalStore()
    const handle = wrapper.get('.terminal-resizer').element as HTMLElement
    handle.setPointerCapture = vi.fn()
    handle.hasPointerCapture = vi.fn(() => false)

    Object.defineProperty(window, 'innerHeight', { configurable: true, value: 600 })
    handle.dispatchEvent(pointerEvent('pointerdown', { clientY: 300, pointerId: 8 }))
    window.dispatchEvent(pointerEvent('pointermove', { clientY: 0, pointerId: 8 }))
    await nextTick()

    expect(store.height).toBe(480)
    wrapper.unmount()
    expect(document.documentElement.classList.contains('terminal-is-resizing')).toBe(false)
    expect(terminalApi.dispose).toHaveBeenCalledOnce()
  })
})
