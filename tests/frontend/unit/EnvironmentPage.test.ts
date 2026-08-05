import type { EnvironmentTool } from '@/pywebview-defines'
import { flushPromises, shallowMount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import EnvironmentPage from '@/components/EnvironmentPage.vue'

const mocks = vi.hoisted(() => ({
  scan: vi.fn(),
  completeSetup: vi.fn(),
  selectTool: vi.fn(),
  replace: vi.fn(),
  route: { query: {} as Record<string, string> },
}))

vi.mock('@/services', () => ({
  environmentService: {
    scan: mocks.scan,
    completeSetup: mocks.completeSetup,
    selectTool: mocks.selectTool,
  },
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ replace: mocks.replace }),
  useRoute: () => mocks.route,
}))

const tools: EnvironmentTool[] = [
  {
    id: 'python',
    name: 'Python',
    toolchain: 'python',
    role: 'runtime',
    required: true,
    status: 'ready',
    path: '/usr/bin/python3',
    version: 'Python 3.12',
    source: 'path',
    message: null,
    candidates: [
      {
        path: '/usr/bin/python3',
        version: 'Python 3.12',
        source: 'path',
        status: 'ready',
        message: null,
      },
      {
        path: '/opt/python3',
        version: 'Python 3.13',
        source: 'path',
        status: 'ready',
        message: null,
      },
    ],
  },
  {
    id: 'clangd',
    name: 'clangd',
    toolchain: 'cpp',
    role: 'analysis',
    required: false,
    status: 'missing',
    path: null,
    version: null,
    source: null,
    message: null,
    candidates: [],
  },
]

describe('EnvironmentPage', () => {
  const mountOptions = {
    global: {
      mocks: { $t: (key: string) => key },
      stubs: {
        VAlert: true,
        VBtn: {
          emits: ['click'],
          inheritAttrs: false,
          template: '<button v-bind="$attrs" @click="$emit(\'click\')"><slot /></button>',
        },
        VIcon: true,
        VProgressLinear: true,
        VSelect: {
          inheritAttrs: false,
          emits: ['update:modelValue'],
          template: '<button data-test="environment-select" @click="$emit(\'update:modelValue\', \'/opt/python3\')" />',
        },
        VSkeletonLoader: true,
        VTooltip: true,
      },
    },
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mocks.scan.mockResolvedValue(tools)
    mocks.completeSetup.mockResolvedValue(undefined)
    mocks.selectTool.mockResolvedValue(tools)
    mocks.replace.mockResolvedValue(undefined)
    mocks.route.query = {}
  })

  it('scans tools when mounted and renders both toolchains', async () => {
    const wrapper = shallowMount(EnvironmentPage, mountOptions)
    await flushPromises()

    expect(mocks.scan).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('Python')
    expect(wrapper.text()).toContain('clangd')
  })

  it('marks setup complete before opening the editor', async () => {
    const wrapper = shallowMount(EnvironmentPage, mountOptions)
    await flushPromises()

    await wrapper.find('[data-test="continue"]').trigger('click')
    await flushPromises()

    expect(mocks.completeSetup).toHaveBeenCalledOnce()
    expect(mocks.replace).toHaveBeenCalledWith('/editor')
  })

  it('allows continuing when a required environment is missing', async () => {
    mocks.scan.mockResolvedValue(tools.map(tool => tool.id === 'python'
      ? { ...tool, status: 'missing', path: null, version: null, candidates: [] }
      : tool))
    const wrapper = shallowMount(EnvironmentPage, mountOptions)
    await flushPromises()

    expect(wrapper.find('[data-test="continue"]').attributes('disabled')).toBeUndefined()
    await wrapper.find('[data-test="continue"]').trigger('click')
    await flushPromises()

    expect(mocks.replace).toHaveBeenCalledWith('/editor')
  })

  it('selects one of multiple detected environments', async () => {
    const wrapper = shallowMount(EnvironmentPage, mountOptions)
    await flushPromises()

    await wrapper.find('[data-test="environment-select"]').trigger('click')
    await flushPromises()

    expect(mocks.selectTool).toHaveBeenCalledWith('python', '/opt/python3')
  })

  it('returns to settings without changing first-run completion', async () => {
    mocks.route.query = { source: 'settings' }
    const wrapper = shallowMount(EnvironmentPage, mountOptions)
    await flushPromises()

    await wrapper.find('[data-test="continue"]').trigger('click')
    await flushPromises()

    expect(mocks.completeSetup).not.toHaveBeenCalled()
    expect(mocks.replace).toHaveBeenCalledWith('/setting')
  })
})
