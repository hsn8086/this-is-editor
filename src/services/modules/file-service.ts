/**
 * 文件服务 - 处理所有文件相关的 API 调用
 */
import type {
  FileInfo,
  FuncResponse_ls_dir,
  Response,
} from '@/pywebview-defines'
import { apiClient, type ApiClient } from '../base/api-client'

export class FileService {
  constructor (private client: ApiClient = apiClient) {}

  /**
   * 列出目录内容
   * @param path 目录路径（null 表示当前工作目录）
   */
  async lsDir (path: string | null): Promise<FuncResponse_ls_dir> {
    return this.client.call<FuncResponse_ls_dir>('path_ls', path)
  }

  /**
   * 获取文件信息
   * @param path 文件路径
   */
  async getInfo (path: string): Promise<FileInfo> {
    return this.client.call<FileInfo>('path_get_info', path)
  }

  /**
   * 读取文件文本内容
   * @param path 文件路径
   */
  async getText (path: string): Promise<string> {
    return this.client.call<string>('path_get_text', path)
  }

  /**
   * 保存文件文本内容
   * @param path 文件路径
   * @param text 文本内容
   */
  async saveText (path: string, text: string): Promise<void> {
    await this.client.call<void>('path_save_text', path, text)
  }

  /**
   * 创建目录
   * @param path 目录路径
   */
  async mkdir (path: string): Promise<Response> {
    return this.client.call<Response>('path_mkdir', path)
  }

  /**
   * 创建空文件
   * @param path 文件路径
   */
  async touch (path: string): Promise<Response> {
    return this.client.call<Response>('path_touch', path)
  }

  /**
   * 重命名文件或目录
   * @param source 原路径
   * @param target 新路径
   */
  async rename (source: string, target: string): Promise<Response> {
    return this.client.call<Response>('path_rename', source, target)
  }

  /**
   * 删除文件或目录
   * @param path 路径
   */
  async delete (path: string): Promise<Response> {
    return this.client.call<Response>('path_delete', path)
  }

  /**
   * 获取父目录
   * @param path 当前路径
   */
  async getParent (path: string): Promise<string> {
    return this.client.call<string>('path_parent', path)
  }

  /**
   * 连接路径
   * @param path1 路径 1
   * @param path2 路径 2
   */
  async join (path1: string, path2: string): Promise<string> {
    return this.client.call<string>('path_join', path1, path2)
  }

  /**
   * 获取磁盘列表
   */
  async getDisks (): Promise<FileInfo[]> {
    return this.client.call<FileInfo[]>('get_disks')
  }

  /**
   * 获取当前工作目录
   */
  async getCwd (): Promise<string> {
    return this.client.call<string>('get_cwd')
  }

  /**
   * 设置当前工作目录
   * @param path 目录路径
   */
  async setCwd (path: string): Promise<void> {
    await this.client.call<void>('set_cwd', path)
  }

  /**
   * 获取固定文件列表
   */
  async getPinnedFiles (): Promise<FileInfo[]> {
    return this.client.call<FileInfo[]>('get_pinned_files')
  }

  /**
   * 添加固定文件
   * @param path 文件路径
   */
  async addPinnedFile (path: string): Promise<void> {
    await this.client.call<void>('add_pinned_file', path)
    // 使缓存失效
    this.client.invalidateCache('get_pinned_files')
  }

  /**
   * 移除固定文件
   * @param path 文件路径
   */
  async removePinnedFile (path: string): Promise<void> {
    await this.client.call<void>('remove_pinned_file', path)
    // 使缓存失效
    this.client.invalidateCache('get_pinned_files')
  }

  /**
   * 设置当前打开的文件
   * @param path 文件路径
   */
  async setOpenedFile (path: string): Promise<void> {
    await this.client.call<void>('set_opened_file', path)
    // 清理与文件相关的缓存
    this.client.invalidateCache('path_get_info')
    this.client.invalidateCache('get_code')
    this.client.invalidateCache('get_testcase')
  }

  /**
   * 获取当前打开的文件路径
   */
  async getOpenedFile (): Promise<string | null> {
    return this.client.call<string | null>('get_opened_file')
  }

  /**
   * 保存滚动位置
   * @param scroll 滚动位置
   */
  async saveScroll (scroll: number): Promise<void> {
    await this.client.call<void>('save_scoll', scroll)
  }

  /**
   * 获取滚动位置
   */
  async getScroll (): Promise<number> {
    return this.client.call<number>('get_scoll')
  }
}

// 默认服务实例
export const fileService = new FileService()
