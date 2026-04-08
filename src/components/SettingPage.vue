<template>
  <v-card :title="$t('settingPage.title')">
    <template #title>
      <div class="d-flex justify-space-between align-center">
        <span>{{ $t("settingPage.title") }}</span>
        <v-text-field
          v-model="search"
          class="ma-2"
          dense
          density="compact"
          hide-details
          :placeholder="$t('settingPage.search')"
          prepend-inner-icon="mdi-magnify"
          style="max-width: 300px"
          variant="solo-filled"
        />
      </div>
    </template>

    <v-list dense>
      <template v-for="[group, cfg] in config">
        <v-list-subheader>{{
          $t(`settingPage.group.${group}`)
        }}</v-list-subheader>

        <v-list-item
          v-for="item in cfg.filter(
            (i) =>
              i.display.toLowerCase().includes(search.toLowerCase()) ||
              i.id.toLowerCase().includes(search.toLowerCase())
          )"
          :key="item.id"
        >
          <div
            class="d-flex justify-space-between align-center"
            style="width: 100%"
          >
            <v-list-item-title class="text-left">{{
              $t("settingPage." + item.i18n)
            }}</v-list-item-title>
            <v-select
              v-if="item.enum"
              v-model="item.value"
              class="flex-grow-1 ma-2"
              :items="item.enum"
              :label="$t('settingPage.' + item.i18n)"
              max-width="300"
              @update:model-value="changeConfig(item.id, item.value)"
            />
            <v-text-field
              v-else-if="typeof item.value === 'string'"
              v-model="item.value"
              class="flex-grow-1 ma-2"
              :label="$t('settingPage.' + item.i18n)"
              max-width="300"
              @update:focused="changeConfig(item.id, item.value)"
            />
            <v-text-field
              v-else-if="typeof item.value === 'number'"
              v-model.number="item.value"
              class="flex-grow-1 ma-2"
              :label="$t('settingPage.' + item.i18n)"
              max-width="300"
              type="number"
              @update:focused="changeConfig(item.id, item.value)"
            />
            <v-switch
              v-else-if="typeof item.value === 'boolean'"
              v-model="item.value"
              class="ma-2"
              variant="tonal"
              @change="changeConfig(item.id, item.value)"
            />

            <v-combobox
              v-else-if="
                typeof item.value === 'object' && Array.isArray(item.value)
              "
              v-model="item.value"
              chips
              class="flex-grow-1 ma-2"
              clearable
              closable-chips
              hide-selected
              :label="$t('settingPage.' + item.i18n)"
              max-width="300"
              multiple
              @update:model-value="changeConfig(item.id, item.value)"
            >
              <template #chip="{ props, item }">
                <v-chip v-bind="props" label size="x-small">
                  {{ item.raw }}
                </v-chip>
              </template>
            </v-combobox>
            <v-btn
              v-else
              class="ma-2"
              prepend-icon="mdi-file-edit-outline"
              variant="tonal"
              @click="openConfigFile()"
            >
              {{ $t("settingPage.openConfigFile") }}
            </v-btn>
          </div>
        </v-list-item>
      </template>
      <v-list-subheader>{{ $t("settingPage.advance") }}</v-list-subheader>
      <v-list-item
        prepend-icon="mdi-file-edit-outline"
        :title="$t('settingPage.openConfigFile')"
        @click="openConfigFile()"
      />
      <!-- About -->
      <v-list-subheader>{{ $t("settingPage.about") }}</v-list-subheader>

      <v-list-item
        prepend-icon="mdi-information-outline"
        :title="$t('settingPage.licenses')"
        @click="$router.push('/license')"
      />
    </v-list>
  </v-card>
</template>
<script lang="ts" setup>
  import type { I18nType } from '@/plugins/i18n'
  import type { Config } from '@/pywebview-defines'
  import { ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { useRouter } from 'vue-router'
  import { useTheme } from 'vuetify'
  import { configService, fileService } from '@/services'

  const { locale, t } = useI18n()
  const theme = useTheme()

  const config = ref<[string, ConfigItem[]][]>([])
  const search = ref('')

  onMounted(() => {
    init()
  })
  type ConfigItem = {
    id: string
    display: string
    value: any
    group: string
    i18n: string
    enum?: readonly any[]
  }
  async function changeConfig (id: string, value: any): Promise<void> {
    await configService.setConfig(id, value)
    switch (id) {
      case 'editor.tie.theme': {
        const cfg = await configService.getConfig()
        if (cfg.editor.tie.theme.value === 'dark')
          theme.global.name.value = 'dark'
        else if (cfg.editor.tie.theme.value === 'light')
          theme.global.name.value = 'light'
        else theme.global.name.value = 'system'
        break
      }
      case 'editor.tie.language': {
        const cfg = await configService.getConfig()
        locale.value = cfg.editor.tie.language.value as I18nType
        break
      }
    }
  }
  async function init () {
    const cfg = await configService.getConfig()
    config.value = configService.sortConfig(
      Array.from(configService.parseConfig(cfg)),
    )
    console.log('config', config.value)
  }

  const router = useRouter()
  async function openConfigFile () {
    const path = await configService.getConfigPath()
    await fileService.setOpenedFile(path)
    await router.push('/editor')
  }
</script>
