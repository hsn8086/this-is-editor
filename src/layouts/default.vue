<template>
  <v-navigation-drawer :rail="true" permanent>
    <v-list density="compact" nav>
      <v-list-item
        v-for="item in menu"
        :key="item.value"
        :value="item.value"
        :prepend-icon="item.icon"
        :title="item.title"
        @click="list_click(item.value)"
        :active="selected === item.value"
      />
    </v-list>
  </v-navigation-drawer>
  <v-main>
    <router-view />
  </v-main>
  <!-- <AppFooter /> -->
</template>

<!-- <style>
.ace_autocomplete {
  z-index: 10000;
  font-family: "maple mono", monospace !important;
  font-size: 14px !important;
  line-height: 1.8 !important;
  min-width: 400px !important;
  background-color: rgb(var(--v-theme-surface)) !important;
  color: rgb(var(--v-theme-on-surface)) !important;
  border: 0px !important; /* 去掉边框 */
  border-radius: 4px; /* 可选：圆角 */
}
.ace_doc-tooltip,
.ace_tooltip {
  z-index: 10000;
  font-family: "maple mono", monospace !important;
  font-size: 14px !important;
  line-height: 1.8 !important;
  min-width: 400px !important;
  background-color: rgb(var(--v-theme-surface)) !important;
  color: rgb(var(--v-theme-on-surface)) !important;
  border: 0px !important; /* 去掉边框 */
  border-radius: 4px; /* 可选：圆角 */
  padding: 8px; /* 可选：内边距 */
}
.ace_error {
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='-12 -14 48 48'><path fill='red' d='M13,13H11V7H13M13,17H11V15H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z'/></svg>") !important;
}
.language_highlight_error {
  border-bottom: 2px solid red !important;
}
.ace_warning {
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='-12 -14 48 48'><path fill='orange' d='M13,13H11V7H13M13,17H11V15H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z'/></svg>") !important;
}
/* #lightbulb {
  background: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' ><path fill='yellow' d='M12,6A6,6 0 0,1 18,12C18,14.22 16.79,16.16 15,17.2V19A1,1 0 0,1 14,20H10A1,1 0 0,1 9,19V17.2C7.21,16.16 6,14.22 6,12A6,6 0 0,1 12,6M14,21V22A1,1 0 0,1 13,23H11A1,1 0 0,1 10,22V21H14M20,11H23V13H20V11M1,11H4V13H1V11M13,1V4H11V1H13M4.92,3.5L7.05,5.64L5.63,7.05L3.5,4.93L4.92,3.5M16.95,5.63L19.07,3.5L20.5,4.93L18.37,7.05L16.95,5.63Z'/></svg>") !important;
} */
</style> -->

<script lang="ts" setup>
import { useRouter, useRoute } from "vue-router";

const router = useRouter();
const route = useRoute();


const selected = ref(route.path.replace("/", "") || "editor");

const menu = [
  { title: "Editor", icon: "mdi-code-braces", value: "editor" },
  { title: "Setting", icon: "mdi-cog", value: "setting" },
  { title: "File Selector", icon: "mdi-folder", value: "file-sel" },
];

watch(
  () => route.path,
  (newPath) => {
    selected.value = newPath.replace("/", "") || "editor";
  }
);

function list_click(value: string) {
  // 处理列表项点击事件
  console.log("List item clicked:", value);

  router.push(`/${value}`);
}

</script>
