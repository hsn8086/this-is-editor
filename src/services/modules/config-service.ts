/**
 * 配置服务 - 处理所有配置相关的 API 调用
 */
import type { Config, ConfigItem } from "@/pywebview-defines";
import { apiClient, type ApiClient } from "../base/api-client";

export class ConfigService {
  constructor(private client: ApiClient = apiClient) {}

  /**
   * 获取完整配置
   */
  async getConfig(): Promise<Config> {
    return this.client.call<Config>("get_config");
  }

  /**
   * 获取配置文件路径
   */
  async getConfigPath(): Promise<string> {
    return this.client.call<string>("get_config_path");
  }

  /**
   * 设置配置项
   * @param id 配置项 ID
   * @param value 配置值
   */
  async setConfig(
    id: string,
    value: string | boolean | number
  ): Promise<void> {
    await this.client.call<void>("set_config", id, value);
    // 清除配置相关的缓存
    this.client.invalidateCache("get_config");
  }

  /**
   * 解析配置为扁平结构
   * @param cfg 配置对象
   * @param suffix 后缀路径（用于递归）
   */
  *parseConfig(
    cfg: Config,
    suffix: string[] = []
  ): Generator<ConfigItem & { id: string; group: string }> {
    for (const [key, value] of Object.entries(cfg)) {
      const id = [...suffix, key];
      if (value && typeof value === "object" && "value" in value) {
        yield {
          ...value,
          id: id.join("."),
          group: id[0],
        } as ConfigItem & { id: string; group: string };
      } else if (value && typeof value === "object") {
        yield* this.parseConfig(value as Config, id);
      }
    }
  }

  /**
   * 排序配置（按分组）
   * @param config 配置项数组
   */
  sortConfig<T extends { group: string }>(config: T[]): [string, T[]][] {
    const groupMap: Record<string, T[]> = {};
    for (const item of config) {
      if (!groupMap[item.group]) {
        groupMap[item.group] = [];
      }
      groupMap[item.group].push(item);
    }
    for (const group in groupMap) {
      groupMap[group].sort((a, b) => {
        const aStr = ("display" in a ? (a as any).display : "");
        const bStr = ("display" in b ? (b as any).display : "");
        return aStr.localeCompare(bStr);
      });
    }
    return Object.keys(groupMap).map((group): [string, T[]] => [
      group,
      groupMap[group],
    ]);
  }
}

// 默认服务实例
export const configService = new ConfigService();
