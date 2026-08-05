<template>
  <main class="environment-page">
    <header class="environment-header">
      <div>
        <div class="text-overline text-medium-emphasis">
          {{ $t('environmentPage.eyebrow') }}
        </div>
        <h1>{{ $t('environmentPage.title') }}</h1>
        <p v-if="!scanning" class="environment-summary text-medium-emphasis">
          {{ $t('environmentPage.summary', { ready: readyCount, total: tools.length }) }}
        </p>
        <p v-else class="environment-summary text-medium-emphasis">
          {{ $t('environmentPage.scanning') }}
        </p>
        <p class="environment-guidance text-caption text-medium-emphasis">
          {{ $t('environmentPage.guidance') }}
        </p>
      </div>
      <div class="environment-actions">
        <v-btn
          :disabled="scanning"
          icon="mdi-refresh"
          :loading="scanning"
          variant="text"
          @click="scan"
        >
          <v-icon>mdi-refresh</v-icon>
          <v-tooltip activator="parent" location="bottom">
            {{ $t('environmentPage.rescan') }}
          </v-tooltip>
        </v-btn>
        <v-btn
          append-icon="mdi-arrow-right"
          color="primary"
          data-test="continue"
          :disabled="scanning"
          variant="flat"
          @click="continueToEditor"
        >
          {{ $t(fromSettings ? 'environmentPage.backToSettings' : 'environmentPage.continue') }}
        </v-btn>
      </div>
    </header>

    <v-progress-linear v-if="scanning" color="primary" indeterminate />
    <v-alert
      v-if="scanError || selectionError"
      class="mt-4"
      density="compact"
      type="error"
      variant="tonal"
    >
      {{ $t(selectionError ? 'environmentPage.selectionFailed' : 'environmentPage.scanFailed') }}
    </v-alert>

    <div :aria-busy="scanning" class="toolchain-grid">
      <section
        v-for="group in toolchains"
        :key="group.id"
        class="toolchain-section"
      >
        <div class="toolchain-title">
          <v-icon :icon="group.icon" size="20" />
          <h2>{{ group.title }}</h2>
          <span class="text-caption text-medium-emphasis">
            {{ readyIn(group.id) }}/{{ toolsIn(group.id).length }}
          </span>
        </div>

        <div v-if="scanning && tools.length === 0" class="tool-skeletons">
          <v-skeleton-loader v-for="index in 3" :key="index" type="list-item-two-line" />
        </div>
        <div v-else class="tool-list">
          <div
            v-for="tool in toolsIn(group.id)"
            :key="tool.id"
            class="tool-row"
          >
            <v-icon
              class="tool-status"
              :color="statusColor(tool.status)"
              :icon="statusIcon(tool.status)"
              size="18"
            />
            <div class="tool-identity">
              <div class="tool-name-line">
                <strong>{{ tool.name }}</strong>
                <span class="text-caption text-medium-emphasis">
                  {{ $t(`environmentPage.role.${tool.role}`) }}
                </span>
                <span v-if="tool.required" class="required-label text-caption">
                  {{ $t('environmentPage.required') }}
                </span>
              </div>
              <div class="tool-version text-body-2">
                {{ tool.version || $t(`environmentPage.status.${tool.status}`) }}
              </div>
              <v-select
                v-if="tool.candidates.length > 1"
                class="tool-select"
                data-test="environment-select"
                density="compact"
                hide-details
                :items="candidateItems(tool)"
                :loading="selectingTool === tool.id"
                :model-value="tool.path"
                variant="outlined"
                @update:model-value="value => selectTool(tool.id, value)"
              />
              <div
                v-else-if="tool.path"
                class="tool-path text-caption text-medium-emphasis"
                :title="tool.path"
              >
                {{ tool.path }}
              </div>
              <div
                v-else-if="tool.message"
                class="tool-path text-caption text-error"
              >
                {{ tool.message }}
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </main>
</template>

<script lang="ts" setup>
  import type { EnvironmentCandidate, EnvironmentTool } from '@/pywebview-defines'
  import { computed, onMounted, ref } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import { environmentService } from '@/services'

  const tools = ref<EnvironmentTool[]>([])
  const scanning = ref(false)
  const scanError = ref(false)
  const selectionError = ref(false)
  const selectingTool = ref<string>()
  const router = useRouter()
  const route = useRoute()
  const fromSettings = computed(() => route.query.source === 'settings')

  const toolchains = computed(() => [
    { id: 'python' as const, title: 'Python', icon: 'mdi-language-python' },
    { id: 'cpp' as const, title: 'C++', icon: 'mdi-language-cpp' },
  ])
  const readyCount = computed(() => tools.value.filter(tool => tool.status === 'ready').length)

  function toolsIn (toolchain: EnvironmentTool['toolchain']): EnvironmentTool[] {
    return tools.value.filter(tool => tool.toolchain === toolchain)
  }

  function readyIn (toolchain: EnvironmentTool['toolchain']): number {
    return toolsIn(toolchain).filter(tool => tool.status === 'ready').length
  }

  function statusIcon (status: EnvironmentTool['status']): string {
    if (status === 'ready') return 'mdi-check-circle'
    if (status === 'error') return 'mdi-alert-circle'
    return 'mdi-minus-circle-outline'
  }

  function statusColor (status: EnvironmentTool['status']): string {
    if (status === 'ready') return 'success'
    if (status === 'error') return 'error'
    return 'medium-emphasis'
  }

  function candidateItems (tool: EnvironmentTool) {
    return tool.candidates.map((candidate: EnvironmentCandidate) => ({
      title: candidate.version
        ? `${candidate.version} - ${candidate.path}`
        : candidate.path,
      value: candidate.path,
      props: { disabled: candidate.status !== 'ready' },
    }))
  }

  async function scan (): Promise<void> {
    scanning.value = true
    scanError.value = false
    selectionError.value = false
    try {
      tools.value = await environmentService.scan()
    } catch (error) {
      scanError.value = true
      console.error('[EnvironmentPage] Scan failed:', error)
    } finally {
      scanning.value = false
    }
  }

  async function selectTool (toolId: string, executablePath: string | null): Promise<void> {
    if (!executablePath) return
    selectingTool.value = toolId
    selectionError.value = false
    try {
      tools.value = await environmentService.selectTool(toolId, executablePath)
    } catch (error) {
      selectionError.value = true
      console.error('[EnvironmentPage] Environment selection failed:', error)
    } finally {
      selectingTool.value = undefined
    }
  }

  async function continueToEditor (): Promise<void> {
    if (fromSettings.value) {
      await router.replace('/setting')
      return
    }
    await environmentService.completeSetup()
    await router.replace('/editor')
  }

  onMounted(scan)
</script>

<style scoped>
  .environment-page {
    width: min(100%, 1040px);
    min-height: 100%;
    margin: 0 auto;
    padding: 44px 48px 56px;
  }

  .environment-header {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 32px;
    padding-bottom: 24px;
  }

  .environment-header h1 {
    margin: 2px 0 0;
    font-size: 32px;
    font-weight: 600;
    line-height: 1.2;
    letter-spacing: 0;
  }

  .environment-summary {
    margin: 8px 0 0;
  }

  .environment-guidance {
    max-width: 620px;
    margin: 6px 0 0;
  }

  .environment-actions {
    display: flex;
    flex: 0 0 auto;
    align-items: center;
    gap: 8px;
  }

  .toolchain-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    margin-top: 32px;
    border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  }

  .toolchain-section {
    min-width: 0;
    padding: 28px 32px 0 0;
  }

  .toolchain-section + .toolchain-section {
    padding-right: 0;
    padding-left: 32px;
    border-left: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  }

  .toolchain-title {
    display: grid;
    grid-template-columns: 24px 1fr auto;
    align-items: center;
    gap: 8px;
    min-height: 32px;
    margin-bottom: 10px;
  }

  .toolchain-title h2 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    letter-spacing: 0;
  }

  .tool-list {
    border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  }

  .tool-row {
    display: grid;
    grid-template-columns: 20px minmax(0, 1fr);
    gap: 12px;
    min-height: 104px;
    padding: 18px 0;
    border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  }

  .tool-status {
    margin-top: 2px;
  }

  .tool-identity {
    min-width: 0;
  }

  .tool-name-line {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: 6px 10px;
  }

  .required-label {
    color: rgb(var(--v-theme-warning));
  }

  .tool-version {
    margin-top: 5px;
  }

  .tool-path {
    margin-top: 4px;
    overflow-wrap: anywhere;
  }

  .tool-select {
    margin-top: 10px;
  }

  @media (max-width: 760px) {
    .environment-page {
      padding: 28px 22px 40px;
    }

    .environment-header {
      align-items: flex-start;
      flex-direction: column;
      gap: 20px;
    }

    .environment-actions {
      width: 100%;
      justify-content: flex-end;
    }

    .toolchain-grid {
      grid-template-columns: minmax(0, 1fr);
    }

    .toolchain-section,
    .toolchain-section + .toolchain-section {
      padding: 24px 0 0;
      border-left: 0;
    }
  }
</style>
