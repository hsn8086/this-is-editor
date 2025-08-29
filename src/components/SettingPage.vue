<template>
  <v-card :title="$t('settingPage.title')">
    <template v-slot:title>
      <div class="d-flex justify-space-between align-center">
        <span>{{ $t("settingPage.title") }}</span>
        <v-text-field
          v-model="search"
          prepend-inner-icon="mdi-magnify"
          class="ma-2"
          dense
          density="compact"
          hide-details
          variant="solo-filled"
          style="max-width: 300px"
          :placeholder="$t('settingPage.search')"
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
              :items="item.enum"
              @update:model-value="changeConfig(item.id, item.value)"
              :label="$t('settingPage.' + item.i18n)"
              class="flex-grow-1 ma-2"
              max-width="300"
            />
            <v-text-field
              v-else-if="typeof item.value === 'string'"
              v-model="item.value"
              @update:focused="changeConfig(item.id, item.value)"
              :label="$t('settingPage.' + item.i18n)"
              class="flex-grow-1 ma-2"
              max-width="300"
            />
            <v-text-field
              v-else-if="typeof item.value === 'number'"
              v-model.number="item.value"
              @update:focused="changeConfig(item.id, item.value)"
              :label="$t('settingPage.' + item.i18n)"
              type="number"
              class="flex-grow-1 ma-2"
              max-width="300"
            />
            <v-switch
              v-else-if="typeof item.value === 'boolean'"
              v-model="item.value"
              @change="changeConfig(item.id, item.value)"
              class="ma-2"
              variant="tonal"
            />

            <v-combobox
              v-else-if="
                typeof item.value === 'object' && Array.isArray(item.value)
              "
              v-model="item.value"
              :label="$t('settingPage.' + item.i18n)"
              @update:model-value="changeConfig(item.id, item.value)"
              chips
              clearable
              closable-chips
              hide-selected
              multiple
              max-width="300"
              class="flex-grow-1 ma-2"
            >
              <template v-slot:chip="{ props, item }">
                <v-chip v-bind="props" label size="x-small">
                  {{ item.raw }}
                </v-chip>
              </template>
            </v-combobox>
            <v-btn
              v-else
              prepend-icon="mdi-file-edit-outline"
              @click="openConfigFile()"
              class="ma-2"
              variant="tonal"
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
import { type API } from "@/pywebview-defines";
import { ref } from "vue";
import { type Config } from "@/pywebview-defines";
import { useTheme } from "vuetify";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import type { I18nType } from "@/plugins/i18n";

const { locale, t } = useI18n();
const theme = useTheme();

const config = ref<[string, ConfigItem[]][]>([]);
const search = ref("");
const py: API = window.pywebview.api;
onMounted(() => {
  init();
});
type ConfigItem = {
  id: string;
  display: string;
  value: any;
  group: string;
  i18n: string;
  enum?: readonly any[];
};
function sortConfig(config: ConfigItem[]): [string, ConfigItem[]][] {
  const groupMap: Record<string, ConfigItem[]> = {};
  for (const item of config) {
    if (!groupMap[item.group]) {
      groupMap[item.group] = [];
    }
    groupMap[item.group].push(item);
  }
  for (const group in groupMap) {
    groupMap[group].sort((a, b) => a.display.localeCompare(b.display));
  }
  let sortedConfig: [string, ConfigItem[]][] = Object.keys(groupMap)
    .sort()
    .map((group): [string, ConfigItem[]] => [group, groupMap[group]]);
  return sortedConfig;
}
function* parseConfig(
  cfg: Config,
  shuffix: string[] = []
): Generator<ConfigItem> {
  for (const [key, value] of Object.entries(cfg)) {
    const id = [...shuffix, key];
    if ("value" in value) {
      yield {
        ...value,
        id: id.join("."),
        group: id[0],
      };
    } else {
      yield* parseConfig(value, id);
    }
  }
}
async function changeConfig(id: string, value: any): Promise<void> {
  await py.set_config(id, value);
  switch (id) {
    case "editor.tie.theme": {
      const cfg = await py.get_config();
      if (cfg.editor.tie.theme.value === "dark")
        theme.global.name.value = "dark";
      else if (cfg.editor.tie.theme.value === "light")
        theme.global.name.value = "light";
      else theme.global.name.value = "system";
      break;
    }
    case "editor.tie.language": {
      const cfg = await py.get_config();
      locale.value = cfg.editor.tie.language.value as I18nType;
      break;
    }
  }
}
async function init() {
  const cfg = await py.get_config();
  config.value = sortConfig(Array.from(parseConfig(cfg)));
  console.log("config", config.value);
}

const router = useRouter();
async function openConfigFile() {
  const path = await py.get_config_path();
  await py.set_opened_file(path);
  await router.push("/editor");
}
</script>
