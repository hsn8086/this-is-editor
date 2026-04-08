/**
 * 任务服务 - 处理测试任务相关的 API 调用
 */
import type { TaskResult, TestCase } from '@/pywebview-defines'
import { apiClient, type ApiClient } from '../base/api-client'

export class TaskService {
  constructor (private client: ApiClient = apiClient) {}

  /**
   * 编译代码
   * @returns "success" 或错误信息
   */
  async compile (): Promise<'success' | string> {
    return this.client.call<'success' | string>('compile')
  }

  /**
   * 运行单个测试任务
   * @param taskId 任务 ID
   * @param memoryLimit 内存限制（MB）
   * @param timeout 超时时间（秒）
   */
  async runTask (
    taskId: number,
    memoryLimit?: number,
    timeout?: number,
  ): Promise<TaskResult> {
    return this.client.call<TaskResult>(
      'run_task',
      taskId,
      memoryLimit,
      timeout,
    )
  }

  /**
   * 获取测试用例
   */
  async getTestcase (): Promise<TestCase> {
    return this.client.call<TestCase>('get_testcase')
  }

  /**
   * 保存测试用例
   * @param testcase 测试用例数据
   */
  async saveTestcase (testcase: TestCase): Promise<void> {
    await this.client.call<void>('save_testcase', testcase)
  }

  /**
   * 获取 CPU 核心数
   * @returns [物理核心数, 逻辑核心数]
   */
  async getCpuCount (): Promise<[number, number]> {
    return this.client.call<[number, number]>('get_cpu_count')
  }

  /**
   * 计算推荐的判题线程数
   * @returns 推荐的线程数
   */
  async getRecommendedJudgeThread (): Promise<number> {
    const [cpuCount, cpuCountLogical] = await this.getCpuCount()
    if (cpuCount === cpuCountLogical) {
      return Math.max(Math.floor((cpuCount * 3) / 2), 1)
    }
    return cpuCount
  }

  /**
   * 聚焦窗口
   */
  async focus (): Promise<void> {
    await this.client.call<void>('focus')
  }
}

// 默认服务实例
export const taskService = new TaskService()
