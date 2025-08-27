<template>
  <v-app>
    <router-view />
    <!-- center -->
    <v-dialog v-model="probCreateDialog" width="auto" persistent>
      <!-- Sel prog lang -->

      <v-card max-width="600" min-width="400">
        <v-card-title class="headline">New Problem</v-card-title>
        <v-list density="compact" nav>
          <v-list-item
            v-for="lang in ['python', 'cpp']"
            :key="lang"
            @click="
              {
                probCreateDialog = false;
                createProblem(lang);
              }
            "
          >
            <v-list-item-title>{{ lang }}</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-card>
    </v-dialog>
  </v-app>
</template>
<style>
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(120, 120, 120, 0.6);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(100, 100, 100, 0.8);
}

body,
.scroll-container {
  scrollbar-gutter: stable;
  overflow: overlay;
}
</style>
<script lang="ts" setup>
import { useTheme } from "vuetify";
import type { TestCase } from "./pywebview-defines";
import router from "./router";
import { random } from "lodash";
const theme = useTheme();

const py = window.pywebview.api;
py.get_config().then((cfg) => {
  if (cfg.editor.tie.theme.value === "dark") theme.global.name.value = "dark";
  else if (cfg.editor.tie.theme.value === "light")
    theme.global.name.value = "light";
  else theme.global.name.value = "system";
});

let prob: TestCase;
const probCreateDialog = ref(false);
window.addEventListener("problem-received", (event) => {
  prob = (event as CustomEvent).detail;
  probCreateDialog.value = true;
  py.focus();
});
async function createProblem(lang: string) {
  console.log("create problem", prob, lang);
  const langMp: Record<string, string> = {
    python: "py",
    cpp: "cpp",
  };

  const workingDir = await py.get_cwd();
  const name = prob.name.replace(/\s+/g, "_") + "." + langMp[lang];
  const fp = await py.path_join(workingDir, name);
  await py.path_touch(fp);
  await py.set_opened_file(fp);
  await py.save_testcase(prob);
  await router.push("/");
  await router.push("/editor");
}
</script>
