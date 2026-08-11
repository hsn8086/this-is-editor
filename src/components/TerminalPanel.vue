<template>
  <!--
    location="bottom" 的 v-navigation-drawer 是 Vuetify layout 系统原生支持的，
    底色/边框直接来自主题 token，因此亮暗切换无需任何额外处理。
  -->
  <v-navigation-drawer
    v-model="visible"
    class="terminal-panel"
    location="bottom"
    permanent
    touchless
    :width="height"
  >
    <!-- 拖拽把手：改变面板高度 -->
    <div
      class="terminal-resizer"
      :title="$t('terminalPanel.resize')"
      @pointerdown="startResize"
    />

    <v-list class="terminal-toolbar py-0" density="compact" nav>
      <v-list-item class="my-1">
        <template #prepend>
          <v-icon :color="statusColor" size="small">mdi-console</v-icon>
        </template>
        <v-list-item-title class="text-caption">
          {{ $t('terminalPanel.title') }}
          <v-chip
            v-if="exitCode !== null"
            class="ml-1"
            :color="exitCode === 0 ? 'success' : 'error'"
            label
            size="x-small"
          >
            {{ $t('terminalPanel.exited', { code: exitCode }) }}
          </v-chip>
        </v-list-item-title>
        <template #append>
          <v-btn
            density="compact"
            icon="mdi-close-octagon-outline"
            size="small"
            :title="$t('terminalPanel.interrupt')"
            variant="text"
            @click="interrupt()"
          />
          <v-btn
            class="ml-1"
            density="compact"
            icon="mdi-broom"
            size="small"
            :title="$t('terminalPanel.clear')"
            variant="text"
            @click="clear()"
          />
          <v-btn
            class="ml-1"
            density="compact"
            icon="mdi-chevron-down"
            size="small"
            :title="$t('terminalPanel.hide')"
            variant="text"
            @click="hide()"
          />
        </template>
      </v-list-item>
    </v-list>
    <v-divider />

    <div ref="host" class="terminal-host" />
  </v-navigation-drawer>
</template>

<script lang="ts" setup>
  import { storeToRefs } from 'pinia'
  import { computed, nextTick, onUnmounted, ref, watch } from 'vue'
  import { useTerminal } from '@/composables/terminal/useTerminal'
  import { useTerminalStore } from '@/stores/terminal'

  const terminalStore = useTerminalStore()
  const { visible, height, exitCode, status } = storeToRefs(terminalStore)

  const host = ref<HTMLElement | undefined>()

  /** 状态到主题语义色的映射，避免用固定 Material 色导致亮暗下对比度不一致 */
  const statusColor = computed(() => {
    const map: Record<string, string> = {
      idle: 'medium-emphasis',
      connecting: 'primary',
      connected: 'success',
      exited: 'medium-emphasis',
      error: 'error',
    }
    return map[status.value] ?? 'medium-emphasis'
  })

  const { mount, dispose, fit, clear, interrupt } = useTerminal({
    container: host,
    resolvePort: async () => {
      const py = window.pywebview.api
      return py.get_port()
    },
    onConnected: () => terminalStore.setStatus('connected'),
    onExit: code => terminalStore.setExitCode(code),
    onError: () => terminalStore.setStatus('error'),
  })

  function hide (): void {
    terminalStore.setVisible(false)
  }

  // 面板首次展开时才创建 xterm 实例：没人用终端就不该有 shell 进程在跑
  watch(
    visible,
    async isVisible => {
      if (!isVisible) {
        return
      }
      terminalStore.setStatus('connecting')
      await nextTick()
      await mount()
      fit()
    },
    { immediate: true },
  )

  let resizeHandle: HTMLElement | undefined
  let resizePointerId: number | undefined
  let resizeStartY = 0
  let resizeStartHeight = 0

  function onResizeMove (event: PointerEvent): void {
    if (event.pointerId !== resizePointerId) {
      return
    }
    event.preventDefault()
    // 面板贴在底部，向上拖动即增高，故取反；至少给编辑器留 120px。
    const maxHeight = Math.max(120, window.innerHeight - 120)
    terminalStore.setHeight(
      Math.min(
        resizeStartHeight + (resizeStartY - event.clientY),
        maxHeight,
      ),
    )
  }

  function stopResize (event?: PointerEvent): void {
    if (event && event.pointerId !== resizePointerId) {
      return
    }
    if (
      resizeHandle
      && resizePointerId !== undefined
      && resizeHandle.hasPointerCapture(resizePointerId)
    ) {
      resizeHandle.releasePointerCapture(resizePointerId)
    }
    resizeHandle = undefined
    resizePointerId = undefined
    document.documentElement.classList.remove('terminal-is-resizing')
    window.removeEventListener('pointermove', onResizeMove)
    window.removeEventListener('pointerup', stopResize)
    window.removeEventListener('pointercancel', stopResize)
  }

  function startResize (event: PointerEvent): void {
    event.preventDefault()
    stopResize()
    resizeHandle = event.currentTarget as HTMLElement
    resizePointerId = event.pointerId
    resizeStartY = event.clientY
    resizeStartHeight = height.value

    // WKWebView 中指针离开 6px 把手后，只有 pointer capture 能保证继续收到事件。
    resizeHandle.setPointerCapture(resizePointerId)
    document.documentElement.classList.add('terminal-is-resizing')
    window.addEventListener('pointermove', onResizeMove, { passive: false })
    window.addEventListener('pointerup', stopResize)
    window.addEventListener('pointercancel', stopResize)
  }

  onUnmounted(() => {
    stopResize()
    dispose()
  })

  defineExpose({ clear, interrupt, fit })
</script>

<style scoped>
.terminal-panel :deep(.v-navigation-drawer__content) {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.terminal-resizer {
  flex: 0 0 6px;
  height: 6px;
  cursor: ns-resize;
  touch-action: none;
  user-select: none;
  /* 用 border token 而非写死颜色，亮暗两套主题都能拿到正确对比度 */
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.terminal-resizer:hover {
  background-color: rgba(var(--v-theme-primary), 0.24);
}

.terminal-toolbar {
  flex: 0 0 auto;
}

.terminal-host {
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
  padding: 4px 8px;
  /* xterm 自身会用 useTerminal 注入的 theme.background 填充，
     这里同样取 surface，避免尺寸未铺满时露出不同底色 */
  background-color: rgb(var(--v-theme-surface));
}

.terminal-host :deep(.xterm) {
  height: 100%;
}

.terminal-host :deep(.xterm-viewport) {
  overscroll-behavior: contain;
}

:global(html.terminal-is-resizing),
:global(html.terminal-is-resizing *) {
  cursor: ns-resize !important;
  user-select: none !important;
}

/* Vuetify 默认给 drawer 和 v-main 都加 0.2s 尺寸过渡。自定义拖拽期间必须
   逐帧跟手，否则 panel、主区域和 xterm canvas 三者各慢一拍并露出底色黑条。 */
:global(html.terminal-is-resizing .terminal-panel),
:global(html.terminal-is-resizing .v-main) {
  transition: none !important;
}
</style>
