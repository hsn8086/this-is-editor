import type { API } from '@/pywebview-defines'

/**
 * API 错误类，用于统一封装 API 调用错误
 */
export class ApiError extends Error {
  constructor (
    message: string,
    public readonly code = 'UNKNOWN_ERROR',
    public readonly originalError?: unknown,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

/**
 * 错误处理器
 */
export function handleApiError (error: unknown, context?: string): never {
  if (error instanceof ApiError) {
    throw error
  }

  const prefix = context ? `[${context}] ` : ''

  if (error instanceof Error) {
    throw new ApiError(
      `${prefix}${error.message}`,
      'API_ERROR',
      error,
    )
  }

  throw new ApiError(
    `${prefix}Unknown error occurred`,
    'UNKNOWN_ERROR',
    error,
  )
}

/**
 * 包装异步函数，统一处理错误
 */
export function withErrorHandling<T extends (...args: any[]) => Promise<any>> (
  fn: T,
  context?: string,
): (...args: Parameters<T>) => Promise<ReturnType<T>> {
  return async (...args: Parameters<T>): Promise<ReturnType<T>> => {
    try {
      return await fn(...args)
    } catch (error) {
      handleApiError(error, context)
    }
  }
}
