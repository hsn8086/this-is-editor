import type { EnvironmentTool } from '@/pywebview-defines'
import { apiClient, type ApiClient } from '../base/api-client'

export class EnvironmentService {
  constructor (private client: ApiClient = apiClient) {}

  async scan (): Promise<EnvironmentTool[]> {
    return this.client.call<EnvironmentTool[]>('scan_environment')
  }

  async selectTool (toolId: string, executablePath: string): Promise<EnvironmentTool[]> {
    return this.client.call<EnvironmentTool[]>('select_environment_tool', toolId, executablePath)
  }

  async isSetupComplete (): Promise<boolean> {
    return this.client.call<boolean>('is_environment_setup_complete')
  }

  async completeSetup (): Promise<void> {
    await this.client.call<void>('complete_environment_setup')
  }
}

export const environmentService = new EnvironmentService()
