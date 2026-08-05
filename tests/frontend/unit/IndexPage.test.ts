import { flushPromises, shallowMount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import IndexPage from '@/pages/index.vue'

const mocks = vi.hoisted(() => ({
  isSetupComplete: vi.fn(),
  replace: vi.fn(),
}))

vi.mock('@/services', () => ({
  environmentService: {
    isSetupComplete: mocks.isSetupComplete,
  },
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ replace: mocks.replace }),
}))

vi.mock('@/components/EnvironmentPage.vue', () => ({
  default: {
    name: 'EnvironmentPage',
    template: '<div data-test="environment-page" />',
  },
}))

describe('IndexPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.replace.mockResolvedValue(undefined)
  })

  it('shows environment setup on first run', async () => {
    mocks.isSetupComplete.mockResolvedValue(false)

    const wrapper = shallowMount(IndexPage, {
      global: { stubs: { VProgressCircular: true } },
    })
    await flushPromises()

    expect(wrapper.findComponent({ name: 'EnvironmentPage' }).exists()).toBe(true)
    expect(mocks.replace).not.toHaveBeenCalled()
  })

  it('opens the editor after setup has been completed', async () => {
    mocks.isSetupComplete.mockResolvedValue(true)

    shallowMount(IndexPage, {
      global: { stubs: { VProgressCircular: true } },
    })
    await flushPromises()

    expect(mocks.replace).toHaveBeenCalledWith('/editor')
  })
})
