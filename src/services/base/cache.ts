/**
 * 简单的内存缓存实现
 */
export interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

export class Cache {
  private store = new Map<string, CacheEntry<unknown>>();

  /**
   * 获取缓存数据
   * @param key 缓存键
   * @returns 缓存数据或 undefined
   */
  get<T>(key: string): T | undefined {
    const entry = this.store.get(key);
    if (!entry) return undefined;

    const now = Date.now();
    if (now - entry.timestamp > entry.ttl) {
      this.store.delete(key);
      return undefined;
    }

    return entry.data as T;
  }

  /**
   * 设置缓存数据
   * @param key 缓存键
   * @param data 缓存数据
   * @param ttl 缓存时间（毫秒），默认 5 分钟
   */
  set<T>(key: string, data: T, ttl = 5 * 60 * 1000): void {
    this.store.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
    });
  }

  /**
   * 删除缓存
   * @param key 缓存键
   */
  delete(key: string): void {
    this.store.delete(key);
  }

  /**
   * 清空所有缓存
   */
  clear(): void {
    this.store.clear();
  }

  /**
   * 检查缓存是否存在且有效
   * @param key 缓存键
   */
  has(key: string): boolean {
    const entry = this.store.get(key);
    if (!entry) return false;

    const now = Date.now();
    if (now - entry.timestamp > entry.ttl) {
      this.store.delete(key);
      return false;
    }

    return true;
  }

  /**
   * 获取所有缓存键（仅返回未过期的）
   * @returns 缓存键数组
   */
  keys(): string[] {
    const validKeys: string[] = [];
    const now = Date.now();

    for (const [key, entry] of this.store.entries()) {
      if (now - entry.timestamp <= entry.ttl) {
        validKeys.push(key);
      } else {
        this.store.delete(key);
      }
    }

    return validKeys;
  }

  /**
   * 按前缀删除缓存
   * @param prefix 前缀字符串
   */
  deleteByPrefix(prefix: string): void {
    const now = Date.now();

    for (const [key, entry] of this.store.entries()) {
      // 先清理过期缓存
      if (now - entry.timestamp > entry.ttl) {
        this.store.delete(key);
        continue;
      }

      // 匹配前缀则删除
      if (key.startsWith(prefix)) {
        this.store.delete(key);
      }
    }
  }
}

// 全局缓存实例
export const globalCache = new Cache();
