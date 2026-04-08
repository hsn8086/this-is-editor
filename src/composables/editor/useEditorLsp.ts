import { ref, type Ref, watch, unref } from 'vue'
import type { Ace } from 'ace-builds'
import type { SessionLspConfig } from 'ace-linters/build/ace-language-client'
import { getLanguageProvider, type LanguageProvider } from '@/lsp'

export interface UseEditorLspOptions {
  /** Ace Editor 实例 */
  editor: Ref<Ace.Editor | undefined>
  /** 文件路径（支持 Ref 或普通 string） */
  filePath: Ref<string | undefined> | string | undefined
  /** 是否加入 Workspace URI（默认 true） */
  joinWorkspaceURI?: boolean
}

export interface UseEditorLspReturn {
  /** LSP 是否已就绪 */
  isReady: Ref<boolean>
  /** 注册 LSP 到当前编辑器 */
  register: () => Promise<boolean>
  /** 注销 LSP（关闭 document） */
  unregister: () => Promise<void>
}

/**
 * 编辑器 LSP 集成 Composable
 *
 * 负责：
 * - 管理 LSP LanguageProvider 的获取与缓存
 * - 注册/注销编辑器到 LSP（registerEditor/closeDocument）
 * - 提供 isReady 状态
 * - 监听 filePath 变化自动重新注册
 *
 * 依赖：getLanguageProvider (from @/lsp)
 *
 * 注意：
 * - 需要在编辑器初始化完成后调用 register()
 * - 组件卸载时应调用 unregister() 清理资源
 * - filePath 为 undefined 时无法注册
 */
export function useEditorLsp(options: UseEditorLspOptions): UseEditorLspReturn {
  const { editor, filePath, joinWorkspaceURI = true } = options

  // State
  const isReady = ref(false)
  let languageProvider: LanguageProvider | undefined = undefined
  let isRegistered = false

  /**
   * 获取 LanguageProvider（带缓存）
   */
  async function getProvider(): Promise<LanguageProvider | undefined> {
    if (languageProvider) {
      return languageProvider
    }
    try {
      languageProvider = await getLanguageProvider()
      return languageProvider
    } catch (err) {
      console.error('[useEditorLsp] Failed to get language provider:', err)
      return undefined
    }
  }

  /**
   * 注册 LSP 到编辑器
   * @returns 是否成功注册
   */
  async function register(): Promise<boolean> {
    const ed = unref(editor)
    const fp = unref(filePath)

    if (!ed) {
      console.warn('[useEditorLsp] Cannot register: editor is not ready')
      return false
    }

    if (!fp) {
      console.warn('[useEditorLsp] Cannot register: filePath is not set')
      return false
    }

    // 如果已经注册过，先注销
    if (isRegistered) {
      await unregister()
    }

    const provider = await getProvider()
    if (!provider) {
      console.warn('[useEditorLsp] Cannot register: language provider not available')
      return false
    }

    const sessionConfig: SessionLspConfig = {
      filePath: fp,
      joinWorkspaceURI,
    }

    try {
      // 类型桥接: ace-linters 使用 ace-code 类型定义，但编辑器实例来自 ace-builds
      // 两者运行时兼容，仅 TS 类型定义冲突，通过 unknown 断言绕过
      provider.registerEditor(ed as unknown as import('ace-code/src/editor').Editor, sessionConfig)
      isRegistered = true
      isReady.value = true
      console.log('[useEditorLsp] LSP registered for file:', fp)
      return true
    } catch (err) {
      console.error('[useEditorLsp] Failed to register editor:', err)
      isReady.value = false
      return false
    }
  }

  /**
   * 注销 LSP（关闭 document）
   */
  async function unregister(): Promise<void> {
    const ed = unref(editor)

    if (!ed || !isRegistered) {
      isReady.value = false
      return
    }

    const provider = await getProvider()
    if (!provider) {
      isReady.value = false
      isRegistered = false
      return
    }

    try {
      // 类型桥接: ace-linters 使用 ace-code 的 EditSession 类型，但编辑器返回的是 ace-builds 类型
      // 两者运行时兼容，仅 TS 类型定义冲突，通过 unknown 断言绕过
      provider.closeDocument(ed.getSession() as unknown as import('ace-code/src/edit_session').EditSession)
      console.log('[useEditorLsp] LSP unregistered for editor')
    } catch (err) {
      console.error('[useEditorLsp] Failed to close document:', err)
    } finally {
      isRegistered = false
      isReady.value = false
    }
  }

  // 监听 filePath 变化，自动重新注册
  if (typeof filePath === 'object' && filePath !== null) {
    watch(
      filePath,
      async (newPath, oldPath) => {
        if (newPath !== oldPath && unref(editor)) {
          console.log('[useEditorLsp] filePath changed, re-registering LSP')
          await register()
        }
      },
      { immediate: false }
    )
  }

  return {
    isReady,
    register,
    unregister,
  }
}

export default useEditorLsp
