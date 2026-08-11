import { shallowMount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import DefaultLayout from '@/layouts/default.vue'

vi.mock('vue-router', () => ({
  useRoute: () => ({ path: '/setting' }),
  useRouter: () => ({ push: vi.fn() }),
}))

const VMainStub = {
  name: 'VMainStub',
  props: { scrollable: Boolean },
  template: '<main><slot /></main>',
}

describe('default layout', () => {
  it('keeps environment diagnostics out of the primary navigation', () => {
    const wrapper = shallowMount(DefaultLayout, {
      global: {
        stubs: {
          RouterView: true,
          VMain: VMainStub,
          VNavigationDrawer: { template: '<nav><slot /></nav>' },
          VList: { template: '<div><slot /></div>' },
          VListItem: {
            inheritAttrs: false,
            props: ['value'],
            template: '<button :data-value="value" />',
          },
        },
      },
    })

    const entries = wrapper.findAll('[data-value]').map(item => item.attributes('data-value'))
    expect(entries).toEqual(['editor', 'setting', 'file-sel'])
    expect(wrapper.findComponent(VMainStub).props('scrollable')).toBe(true)
  })
})
