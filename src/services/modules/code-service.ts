/**
 * 代码服务 - 处理代码编辑相关的 API 调用
 */
import type { Code, Lang } from "@/pywebview-defines";
import { apiClient, type ApiClient } from "../base/api-client";

export class CodeService {
  constructor(private client: ApiClient = apiClient) {}

  /**
   * 获取当前代码和类型
   */
  async getCode(): Promise<Code> {
    return this.client.call<Code>("get_code");
  }

  /**
   * 保存代码
   * @param code 代码内容
   */
  async saveCode(code: string): Promise<void> {
    await this.client.call<void>("save_code", code);
  }

  /**
   * 格式化代码
   * @returns 格式化后的代码
   */
  async formatCode(): Promise<string> {
    return this.client.call<string>("format_code");
  }

  /**
   * 获取支持的编程语言列表
   */
  async getLangs(): Promise<Lang[]> {
    return this.client.call<Lang[]>("get_langs");
  }

  /**
   * 获取 LSP 服务端口
   */
  getPort(): number {
    return this.client.rawApi.get_port();
  }

  /**
   * 将路径转换为 URI
   * @param path 文件路径
   */
  async pathToUri(path: string): Promise<string> {
    return this.client.call<string>("path_to_uri", path);
  }
}

// 默认服务实例
export const codeService = new CodeService();
