import type { Cache } from './cache'
import type { API } from '@/pywebview-defines'
import { globalCache } from './cache'
import { ApiError, handleApiError } from './error-handler'

/**
 * API 客户端配置选项
 */
export interface ApiClientOptions {
  /** 是否启用缓存 */
  enableCache?: boolean
  /** 缓存实例（默认使用全局缓存） */
  cache?: Cache
  /** 默认缓存时间（毫秒） */
  defaultCacheTtl?: number
}

/**
 * 统一的 API 客户端
 * 封装 window.pywebview.api 调用，提供缓存和错误处理
 */
export class ApiClient {
  private api: API
  private cache: Cache
  private enableCache: boolean
  private defaultCacheTtl: number

  /**
   * 缓存策略配置：哪些方法应该被缓存
   */
  private static readonly CACHEABLE_METHODS = new Set([
    'get_config',
    'get_langs',
    'get_cpu_count',
    'get_pinned_files',
    'path_get_info',
  ])

  constructor (options: ApiClientOptions = {}) {
    this.api = window.pywebview.api
    this.cache = options.cache ?? globalCache
    this.enableCache = options.enableCache ?? true
    this.defaultCacheTtl = options.defaultCacheTtl ?? 5 * 60 * 1000
  }

  /**
   * 获取原始 API 对象（用于直接调用未封装的方法）
   */
  get rawApi (): API {
    return this.api
  }

  /**
   * 生成缓存键
   */
  private generateCacheKey (method: string, args: unknown[]): string | null {
    if (args.length === 0) {
      return method
    }
    try {
      return `${method}:${JSON.stringify(args)}`
    } catch {
      // JSON.stringify 失败（如循环引用），返回 null 表示跳过缓存
      return null
    }
  }

  /**
   * 检查方法是否应该被缓存
   */
  private shouldCache (method: string): boolean {
    return this.enableCache && ApiClient.CACHEABLE_METHODS.has(method)
  }

  /**
   * 调用 API 方法
   * @param method API 方法名
   * @param args 方法参数
   * @returns Promise 结果
   */
  async call<T>(method: keyof API, ...args: unknown[]): Promise<T> {
    const cacheKey = this.generateCacheKey(method as string, args)
    const canUseCache = cacheKey !== null && this.shouldCache(method as string)

    // 尝试从缓存获取
    if (canUseCache) {
      const cached = this.cache.get<T>(cacheKey)
      if (cached !== undefined) {
        return cached
      }
    }

    try {
      const fn = this.api[method]
      if (typeof fn !== 'function') {
        throw new ApiError(
          `API method "${String(method)}" does not exist`,
          'METHOD_NOT_FOUND',
        )
      }

      const result = await fn.apply(this.api, args)

      // 存入缓存
      if (canUseCache) {
        this.cache.set(cacheKey, result, this.defaultCacheTtl)
      }

      return result as T
    } catch (error) {
      handleApiError(error, `API.${String(method)}`)
    }
  }

  /**
   * 使指定方法的缓存失效
   * @param method API 方法名
   * @param args 方法参数（可选，不传则清除该方法所有缓存）
   */
  invalidateCache (method: string, args?: unknown[]): void {
    if (args) {
      const cacheKey = this.generateCacheKey(method, args)
      if (cacheKey !== null) {
        this.cache.delete(cacheKey)
      }
    } else {
      // 清除该方法的所有缓存（通过前缀匹配）
      // 匹配 "method:" 前缀或精确匹配 "method"
      this.cache.deleteByPrefix(`${method}:`)
      // 同时检查精确匹配（无参数的情况）
      this.cache.delete(method)
    }
  }

  /**
   * 清除所有缓存
   */
  clearCache (): void {
    this.cache.clear()
  }
}

// 默认客户端实例
export const apiClient = new ApiClient()

/**
 * 便捷函数：调用 API 方法
 */
export async function callApi<T> (
  method: keyof API,
  ...args: unknown[]
): Promise<T> {
  return apiClient.call<T>(method, ...args)
}
