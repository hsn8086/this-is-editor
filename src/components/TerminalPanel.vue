<template>
  <!--
    location="bottom" 的 v-navigation-drawer 是 Vuetify layout 系统原生支持的，
    底色/边框直接来自主题 token，因此亮暗切换无需任何额外处理。
  -->
  <v-navigation-drawer
    v-model="visible"
    :height="height"
    location="bottom"
    permanent
    :width="undefined"
  >
    <!-- 拖拽把手：改变面板高度 -->
    <div
      class="terminal-resizer"
      :title="$t('terminalPanel.resize')"
      @pointerdown="startResize"
    />

    <v-list class="py-0" density="compact" nav>
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

  watch(height, async () => {
    await nextTick()
    fit()
  })

  function startResize (event: PointerEvent): void {
    event.preventDefault()
    const startY = event.clientY
    const startHeight = height.value

    function onMove (moveEvent: PointerEvent): void {
      // 面板贴在底部，向上拖动即增高，故取反
      terminalStore.setHeight(startHeight + (startY - moveEvent.clientY))
    }

    function onUp (): void {
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerup', onUp)
    }

    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerup', onUp)
  }

  onUnmounted(() => dispose())

  defineExpose({ clear, interrupt, fit })
</script>

<style scoped>
.terminal-resizer {
  height: 6px;
  cursor: ns-resize;
  /* 用 border token 而非写死颜色，亮暗两套主题都能拿到正确对比度 */
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.terminal-resizer:hover {
  background-color: rgba(var(--v-theme-primary), 0.24);
}

.terminal-host {
  /* 40px 标题行 + 1px 分隔线 + 6px 拖拽条 */
  height: calc(100% - 47px);
  padding: 4px 8px;
  /* xterm 自身会用 useTerminal 注入的 theme.background 填充，
     这里同样取 surface，避免尺寸未铺满时露出不同底色 */
  background-color: rgb(var(--v-theme-surface));
}
</style>
