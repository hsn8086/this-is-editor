<template>
  <div class="scroll-container" @scroll="onScroll" ref="scrollContainer">
    <div class="fab-fixed">
      <v-fab
        location="bottom right"
        :absolute="true"
        color="primary"
        size="large"
        
        aria-label="Create File or Folder"
        icon
      >
        <v-icon>{{ fabOpen ? "mdi-close" : "mdi-plus" }}</v-icon>
        <v-speed-dial
          v-model="fabOpen"
          location="left center"
          transition="scale-transition"
          activator="parent"
        >
          <v-btn icon>
            <v-icon
              size="24"
              @click="
                dialogType = 'folder';
                dialog = true;
              "
            >
              mdi-folder-plus
            </v-icon>
          </v-btn>
          <v-btn icon>
            <v-icon
              size="24"
              @click="
                dialogType = 'file';
                dialog = true;
              "
            >
              mdi-file-plus
            </v-icon>
          </v-btn>
        </v-speed-dial>
      </v-fab>
    </div>
    <!-- 回顶部按钮 -->
    <v-fade-transition>
      <div class="fab-fixed-top" v-if="scrollTop >= 100">
        <v-btn
          icon
          color="primary"
          @click="scrollToTop"
          aria-label="Scroll to Top"
          size="large"
        >
          <v-icon>mdi-arrow-collapse-up</v-icon>
        </v-btn>
      </div>
    </v-fade-transition>
    <v-dialog v-model="dialog" max-width="500px">
      <v-card>
        <v-card-title class="headline">
          {{ dialogType === "file" ? "Create File" : "Create Folder" }}
        </v-card-title>
        <v-card-text>
          <v-text-field
            v-model="createName"
            v-if="dialogType === 'file'"
            label="File Name"
            :rules="[(value) => !!value || 'File name is required']"
          />
          <v-text-field
            v-model="createName"
            v-else-if="dialogType === 'folder'"
            label="Folder Name"
            :rules="[(value) => !!value || 'Folder name is required']"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="dialog = false">Cancel</v-btn>
          <v-btn color="primary" @click="createItem">Create</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <v-card class="base" density="compact" nav style="min-height: 100%">
      <v-list>
        <v-list-item
          v-for="file in ls"
          :key="folder + '/' + file.name"
          @click="file_click(file.name, file.isReturn)"
          :prepend-icon="file.is_dir ? 'mdi-folder' : 'mdi-file'"
          :title="file.name"
          :value="file.name"
        >
          <div style="display: flex; gap: 4px">
            <v-chip label size="x-small">{{ file.type }}</v-chip>
            <v-chip label size="x-small">{{ file.last_modified }}</v-chip>
          </div>
        </v-list-item>
      </v-list>
    </v-card>
  </div>
</template>
<style scoped>
fileSelector {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.fab-fixed {
  position: fixed;
  right: 32px;
  bottom: 32px;
  z-index: 100;
}
.scroll-container {
  height: 100vh;
  overflow-y: auto;
}
.fab-fixed-top {
  position: fixed;
  right: 32px;
  bottom: 96px;
  z-index: 100;
}
</style>

<script lang="ts" setup>
import type { FuncResponse_ls_dir, FileInfo, API } from "@/pywebview-defines";

import { ref } from "vue";
import { debounce } from "lodash";

import router from "@/router";

const fabOpen = ref(false);
const folderLoading = ref(false);

const py: API = window.pywebview.api;
onMounted(() => {
  init();
});

async function init() {
  await fetchFiles();
  await initScrool();
}

const folder = ref<string>();
const ls = ref<File[]>([]);

interface File extends FileInfo {
  isReturn: boolean;
}

async function changeDirectory(path: string) {
  await py.set_cwd(path);
  await fetchFiles(path);
}

async function fetchFiles(path: string | null = null) {
  const response: FuncResponse_ls_dir = await py.path_ls(path);
  ls.value = [
    {
      name: "...",
      type: "return to parent",
      last_modified: "",
      is_dir: true,
      is_file: false,
      is_symlink: false,
      size: 0,
      isReturn: true,
    },
  ];
  for (const file of response.files)
    ls.value.push({ ...file, isReturn: false });
  folder.value = response.now_path;
}

// file click
async function file_click(name: string, returnValue: boolean) {
  folderLoading.value = true;
  let path: string;
  if (returnValue) {
    // If it is return
    const parentPath = await py.path_parent(folder.value!);
    await changeDirectory(parentPath);
  } else if (
    (await py.path_get_info((path = await py.path_join(folder.value!, name))))
      .is_dir
  ) {
    // If open dir
    changeDirectory(path);
  } else {
    // If open file
    await py.set_opened_file(await py.path_join(folder.value!, name));
    router.push("/editor");
    await py.set_cwd(folder.value!);
  }
  folderLoading.value = false;
}

const dialog = ref(false);
const dialogType = ref<"file" | "folder">("file");
const createName = ref<string>("");
async function createItem() {
  const p = await py.path_join(folder.value!, createName.value);
  if (dialogType.value === "file") await py.path_touch(p);
  else if (dialogType.value === "folder") await py.path_mkdir(p);
  dialog.value = false; // Close dialog
  createName.value = ""; // Reset textfield
  fetchFiles(folder.value);
}

// scoll
const scrollTop = ref(0);
const scrollContainer: Ref<HTMLElement | null> = ref(null);
async function initScrool() {
  const savedScroll = await py.get_scoll();
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = savedScroll;
    scrollTop.value = savedScroll;
  }
}
const saveScrollDebounced = debounce(
  (scrollValue: number) => py.save_scoll(scrollValue),
  500
);

async function onScroll(event: Event) {
  const target = event.target as HTMLElement;
  scrollTop.value = target.scrollTop;
  saveScrollDebounced(scrollTop.value);
}
async function scrollToTop() {
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = 0;
    await py.save_scoll(0);
  }
}
</script>
