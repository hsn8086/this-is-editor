import type { ApiClient } from '@/services/base/api-client'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { EnvironmentService } from '@/services/modules/environment-service'

vi.mock('@/services/base/api-client', () => ({
  apiClient: { call: vi.fn() },
}))

describe('EnvironmentService', () => {
  const call = vi.fn()
  const service = new EnvironmentService({ call } as unknown as ApiClient)

  beforeEach(() => {
    call.mockReset()
  })

  it('scans the environment without caching arguments', async () => {
    call.mockResolvedValue([])

    await expect(service.scan()).resolves.toEqual([])

    expect(call).toHaveBeenCalledWith('scan_environment')
  })

  it('reads and completes first-run setup', async () => {
    call.mockResolvedValueOnce(false).mockResolvedValueOnce(undefined)

    await expect(service.isSetupComplete()).resolves.toBe(false)
    await service.completeSetup()

    expect(call).toHaveBeenNthCalledWith(1, 'is_environment_setup_complete')
    expect(call).toHaveBeenNthCalledWith(2, 'complete_environment_setup')
  })

  it('selects an environment executable', async () => {
    call.mockResolvedValue([])

    await expect(service.selectTool('python', '/opt/python')).resolves.toEqual([])

    expect(call).toHaveBeenCalledWith('select_environment_tool', 'python', '/opt/python')
  })
})
