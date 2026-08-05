import type { Ace } from 'ace-builds'
import { ref, type Ref } from 'vue'

export interface UseEditorContextMenuOptions {
  /** Ace Editor 实例 Ref（用于 guard） */
  editor: Ref<Ace.Editor | undefined>
}

export interface UseEditorContextMenuReturn {
  /** 菜单 X 坐标 */
  menuX: Ref<number>
  /** 菜单 Y 坐标 */
  menuY: Ref<number>
  /** 是否显示菜单 */
  showMenu: Ref<boolean>
  /** 右键菜单事件处理器 */
  onContextMenu: (e: MouseEvent) => void
  /** 关闭菜单 */
  closeMenu: () => void
}

/**
 * 编辑器右键菜单控制 Composable
 *
 * 负责：
 * - 管理菜单位置（menuX, menuY）
 * - 管理菜单显示状态（showMenu）
 * - 处理右键点击事件
 *
 * 注意：editor 未初始化时不触发菜单
 */
export function useEditorContextMenu (options: UseEditorContextMenuOptions): UseEditorContextMenuReturn {
  const { editor } = options

  // 菜单位置和状态
  const menuX = ref(0)
  const menuY = ref(0)
  const showMenu = ref(false)

  /**
   * 右键菜单事件处理器
   * 设置菜单位置并显示菜单
   */
  function onContextMenu (e: MouseEvent): void {
    // Guard: editor 未初始化时不触发
    if (!editor.value) {
      console.warn('[useEditorContextMenu] Cannot show menu: editor not initialized')
      return
    }

    e.preventDefault()
    menuX.value = e.clientX
    menuY.value = e.clientY
    showMenu.value = true
  }

  /**
   * 关闭菜单
   */
  function closeMenu (): void {
    showMenu.value = false
  }

  return {
    menuX,
    menuY,
    showMenu,
    onContextMenu,
    closeMenu,
  }
}

export default useEditorContextMenu
