<template>
  <v-card title="Settings">
    <template v-slot:title>
      <div class="d-flex justify-space-between align-center">
        <span>Settings</span>
        <v-text-field
          v-model="search"
          prepend-inner-icon="mdi-magnify"
          class="ml-4"
          dense
          density="compact"
          hide-details
          variant="solo-filled"
          style="max-width: 300px"
        />
      </div>
    </template>

    <v-list dense>
      <template v-for="[group, cfg] in config">
        <v-list-subheader>{{ group }}</v-list-subheader>

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
              item.display
            }}</v-list-item-title>
            <v-select
              v-if="item.enum"
              v-model="item.value"
              :items="item.enum"
              @update:model-value="changeConfig(item.id, item.value)"
              :label="item.display"
              class="flex-grow-1"
              max-width="300"
            />
            <v-text-field
              v-else-if="typeof item.value === 'string'"
              v-model="item.value"
              @update:focused="changeConfig(item.id, item.value)"
              :label="item.display"
              class="flex-grow-1"
              max-width="300"
            />
            <v-text-field
              v-else-if="typeof item.value === 'number'"
              v-model.number="item.value"
              @update:focused="changeConfig(item.id, item.value)"
              :label="item.display"
              type="number"
              class="flex-grow-1"
              max-width="300"
            />
            <v-switch
              v-else
              v-model="item.value"
              @change="changeConfig(item.id, item.value)"
            />
          </div>
        </v-list-item>
      </template>
      <!-- About -->
      <v-list-subheader>About</v-list-subheader>
      <v-list-group value="Users">
        <template v-slot:activator="{ props }">
          <v-list-item
            v-bind="props"
            prepend-icon="mdi-information-outline"
            title="Licenses"
          />
        </template>

        <LicensesPage />
      </v-list-group>
    </v-list>
  </v-card>
</template>
<script lang="ts" setup>
import { type API } from "@/pywebview-defines";
import { ref, type Ref } from "vue";
import { type Config } from "@/pywebview-defines";
import { useTheme } from "vuetify";
import LicensePage from "./LicensesPage.vue";
import AboutPage from "./LicensesPage.vue";
import LicensesPage from "./LicensesPage.vue";
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
  enum?: readonly any[]; // Explicitly define 'enum' as an optional array
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
  if (id === "editor.tie.theme") {
    const cfg = await py.get_config();
    if (cfg.editor.tie.theme.value === "dark") theme.global.name.value = "dark";
    else if (cfg.editor.tie.theme.value === "light")
      theme.global.name.value = "light";
    else theme.global.name.value = "system";
  }
}
async function init() {
  const cfg = await py.get_config();
  config.value = sortConfig(Array.from(parseConfig(cfg)));
  console.log("config", config.value);
}
</script>
