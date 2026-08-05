import { flushPromises, shallowMount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import SettingPage from '@/components/SettingPage.vue'

const mocks = vi.hoisted(() => ({
  push: vi.fn(),
  getConfig: vi.fn(),
  parseConfig: vi.fn(),
  sortConfig: vi.fn(),
}))

vi.mock('@/services', () => ({
  configService: {
    getConfig: mocks.getConfig,
    parseConfig: mocks.parseConfig,
    sortConfig: mocks.sortConfig,
    setConfig: vi.fn(),
    getConfigPath: vi.fn(),
  },
  fileService: { setOpenedFile: vi.fn() },
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mocks.push }),
}))

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ locale: { value: 'en-US' } }),
}))

vi.mock('vuetify', () => ({
  useTheme: () => ({ global: { name: { value: 'light' } } }),
}))

describe('SettingPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.getConfig.mockResolvedValue({})
    mocks.parseConfig.mockReturnValue([])
    mocks.sortConfig.mockReturnValue([])
    mocks.push.mockResolvedValue(undefined)
  })

  it('opens environment diagnostics from advanced settings', async () => {
    const wrapper = shallowMount(SettingPage, {
      global: {
        mocks: { $t: (key: string) => key },
        stubs: {
          VBtn: true,
          VCard: { template: '<div><slot name="title" /><slot /></div>' },
          VChip: true,
          VCombobox: true,
          VIcon: true,
          VList: { template: '<div><slot /></div>' },
          VListItem: {
            inheritAttrs: false,
            props: ['title'],
            emits: ['click'],
            template: '<button v-bind="$attrs" @click="$emit(\'click\')">{{ title }}</button>',
          },
          VListItemTitle: true,
          VListSubheader: true,
          VSelect: true,
          VSwitch: true,
          VTextField: true,
          VTooltip: true,
        },
      },
    })
    await flushPromises()

    await wrapper.find('[data-test="environment-diagnostics"]').trigger('click')
    await flushPromises()

    expect(mocks.push).toHaveBeenCalledWith({
      path: '/environment',
      query: { source: 'settings' },
    })
  })
})
