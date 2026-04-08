<template>
  <v-navigation-drawer expand-on-hover permanent rail>
    <v-list nav>
      <v-list-item
        v-for="disk in disks"
        :key="disk.name"
        :prepend-icon="'mdi-harddisk'"
        :title="disk.name"
        @click="changeDirectory(disk.path)"
      />
      <v-divider v-if="pinnedFiles.length > 0" />
      <v-menu v-for="pinned in pinnedFiles" :key="pinned.name">
        <template #activator="{ props }">
          <v-list-item
            :key="pinned.name"
            density="compact"
            :prepend-icon="pinned.is_dir ? 'mdi-folder' : 'mdi-file'"
            :title="pinned.name"
            @click.left="fileClick(pinned)"
            @click.right.prevent.stop="props.onClick"
          />
        </template>
        <v-list>
          <v-list-item
            @click="
              async () => {
                await fileService.removePinnedFile(pinned.path);
                await fetchPinnedFiles();
              }
            "
          >
            <v-list-item-title>Unpin</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </v-list>
  </v-navigation-drawer>
  <div ref="scrollContainer" class="scroll-container" @scroll="onScroll">
    <div class="fab-fixed">
      <v-fab
        :absolute="true"
        aria-label="Create File or Folder"
        color="primary"
        icon
        location="bottom right"
        size="large"
      >
        <v-icon>{{ fabOpen ? "mdi-close" : "mdi-plus" }}</v-icon>
        <v-speed-dial
          v-model="fabOpen"
          activator="parent"
          location="left center"
          transition="scale-transition"
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
      <div v-if="scrollTop >= 100" class="fab-fixed-top">
        <v-btn
          aria-label="Scroll to Top"
          color="primary"
          icon
          size="large"
          @click="scrollToTop"
        >
          <v-icon>mdi-arrow-collapse-up</v-icon>
        </v-btn>
      </div>
    </v-fade-transition>
    <v-dialog v-model="dialog" max-width="500px">
      <v-card>
        <v-card-title class="headline">
          {{
            dialogType === "rename"
              ? "Rename"
              : dialogType === "file"
                ? "Create File"
                : "Create Folder"
          }}
        </v-card-title>
        <v-card-text>
          <v-text-field
            v-if="dialogType === 'file'"
            v-model="createName"
            label="File Name"
            :rules="[(value) => !!value || 'File name is required']"
            @keydown="onCreateInputKeydown"
          />
          <v-text-field
            v-else-if="dialogType === 'folder'"
            v-model="createName"
            label="Folder Name"
            :rules="[(value) => !!value || 'Folder name is required']"
            @keydown="onCreateInputKeydown"
          />
          <v-text-field
            v-else-if="dialogType === 'rename'"
            v-model="createName"
            label="New Name"
            :rules="[(value) => !!value || 'New name is required']"
            @keydown="onCreateInputKeydown"
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
        <v-menu v-for="file in ls">
          <template #activator="{ props }">
            <v-list-item
              :key="folder + '/' + file.name"
              :prepend-icon="file.is_dir ? 'mdi-folder' : 'mdi-file'"
              :title="file.name"
              :value="file.name"
              @click.left="fileClick(file)"
              @click.right.prevent.stop="props.onClick"
            >
              <div style="display: flex; gap: 4px">
                <v-chip label size="x-small">{{ file.type }}</v-chip>
                <v-chip label size="x-small">{{ file.last_modified }}</v-chip>
              </div>
            </v-list-item>
          </template>
          <v-list>
            <v-list-item
              @click="
                async () => {
                  await fileService.addPinnedFile(file.path);
                  await fetchPinnedFiles();
                }
              "
            >
              <v-list-item-title>Pin</v-list-item-title>
            </v-list-item>
            <v-list-item
              v-if="!(('isReturn' in file) && file.isReturn)"
              @click="openRenameDialog(file)"
            >
              <v-list-item-title>Rename</v-list-item-title>
            </v-list-item>
            <v-list-item
              v-if="!(('isReturn' in file) && file.isReturn)"
              @click="deleteItem(file)"
            >
              <v-list-item-title>Delete</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
        <!-- <v-virtual-scroll :items="ls">
          <template v-slot="{ item }">
            <v-menu>
              <template #activator="{ props }">
                <v-list-item
                  :key="folder + '/' + item.name"
                  @click.left="fileClick(item)"
                  @click.right.prevent.stop="props.onClick"
                  :prepend-icon="item.is_dir ? 'mdi-folder' : 'mdi-file'"
                  :title="item.name"
                  :value="item.name"
                >
                  <div style="display: flex; gap: 4px">
                    <v-chip label size="x-small">{{ item.type }}</v-chip>
                    <v-chip label size="x-small">{{
                      item.last_modified
                    }}</v-chip>
                  </div>
                </v-list-item>
              </template>
              <v-list>
                <v-list-item
                  @click="
                    async () => {
                      await py.add_pinned_file(item.path);
                      await fetchPinnedFiles();
                    }
                  "
                >
                  <v-list-item-title>Pin</v-list-item-title>
                </v-list-item>
              </v-list>
            </v-menu>
          </template>
        </v-virtual-scroll> -->
      </v-list>
    </v-card>
  </div>
</template>
<script lang="ts" setup>
  import type { FileInfo, FuncResponse_ls_dir } from '@/pywebview-defines'
  import type { FileItem } from '@/stores/file'

  import { debounce } from 'lodash'
  import { storeToRefs } from 'pinia'
  import { ref } from 'vue'
  import {
    createAndOpenItem,
    deleteItemAndRefresh,
    handleCreateInputKeydown,
    renameAndOpenItem,
  } from '@/components/file-sel-create'
  import router from '@/router'
  import { fileService } from '@/services'

  import { useFileStore } from '@/stores/file'

  const fabOpen = ref(false)
  const folderLoading = ref(false)

  // File store
  const fileStore = useFileStore()
  const { folder, pinnedFiles, ls, disks } = storeToRefs(fileStore)

  onMounted(() => {
    init()
    fetchDisks()
  })

  async function init () {
    await fetchFiles()
    await initScrool()
    await fetchPinnedFiles()
  }

  async function fetchPinnedFiles () {
    fileStore.setPinnedFiles(await fileService.getPinnedFiles())
  }

  async function changeDirectory (path: string) {
    await fileService.setCwd(path)
    await fetchFiles(path)
  }

  async function fetchFiles (path: string | null = null) {
    const response: FuncResponse_ls_dir = await fileService.lsDir(path)
    const newLs = [
      {
        name: '...',
        stem: '...',
        path: '',
        type: 'return to parent',
        last_modified: '',
        is_dir: true,
        is_file: false,
        is_symlink: false,
        size: 0,
        isReturn: true,
      }, // todo: 会不会有更优雅的方式?
    ]
    for (const file of response.files)
      newLs.push({ ...file, isReturn: false })
    fileStore.setLs(newLs)
    fileStore.setFolder(response.now_path)
  }

  async function fetchDisks () {
    fileStore.setDisks(await fileService.getDisks())
  }

  // file click
  async function fileClick (file: FileItem | FileInfo) {
    folderLoading.value = true
    if ('isReturn' in file && file.isReturn) {
      // If it is return
      const parentPath = await fileService.getParent(folder.value!)
      await changeDirectory(parentPath)
    } else if (file.is_dir) {
      // If open dir
      changeDirectory(file.path)
    } else {
      // If open file
      await fileService.setOpenedFile(file.path)
      router.push('/editor')
      await fileService.setCwd(folder.value!)
    }
    folderLoading.value = false
  }

  const dialog = ref(false)
  const dialogType = ref<'file' | 'folder' | 'rename'>('file')
  const createName = ref<string>('')
  const targetItem = ref<FileItem | FileInfo | null>(null)

  async function onCreateInputKeydown (event: KeyboardEvent) {
    await handleCreateInputKeydown(event, createItem)
  }

  async function createItem () {
    if (dialogType.value === 'rename' && targetItem.value) {
      await renameAndOpenItem({
        path: targetItem.value.path,
        name: createName.value,
        join: fileService.join.bind(fileService),
        getParent: fileService.getParent.bind(fileService),
        rename: fileService.rename.bind(fileService),
        openFile: async (path: string) => {
          await fileService.setOpenedFile(path)
          await router.push('/editor')
          await fileService.setCwd(folder.value!)
        },
        openFolder: async (path: string) => {
          await changeDirectory(path)
        },
        reset: () => {
          dialog.value = false
          createName.value = ''
          targetItem.value = null
        },
        isDir: targetItem.value.is_dir,
      })
      return
    }

    const createDialogType = dialogType.value
    if (createDialogType === 'rename') return

    await createAndOpenItem({
      folder: folder.value!,
      createName: createName.value,
      dialogType: createDialogType,
      join: fileService.join.bind(fileService),
      touch: fileService.touch.bind(fileService),
      mkdir: fileService.mkdir.bind(fileService),
      openFile: async (path: string) => {
        await fileService.setOpenedFile(path)
        await router.push('/editor')
        await fileService.setCwd(folder.value!)
      },
      openFolder: async (path: string) => {
        await changeDirectory(path)
      },
      reset: () => {
        dialog.value = false
        createName.value = ''
        targetItem.value = null
      },
    })
  }

  function openRenameDialog (file: FileItem | FileInfo) {
    targetItem.value = file
    createName.value = file.name
    dialogType.value = 'rename'
    dialog.value = true
  }

  async function deleteItem (file: FileItem | FileInfo) {
    await deleteItemAndRefresh({
      path: file.path,
      currentFolder: folder.value!,
      deletePath: fileService.delete.bind(fileService),
      refreshFolder: async (path: string) => {
        await fetchFiles(path)
      },
    })
  }

  // scoll
  const scrollTop = ref(0)
  const scrollContainer: Ref<HTMLElement | null> = ref(null)
  async function initScrool () {
    const savedScroll = await fileService.getScroll()
    if (scrollContainer.value) {
      scrollContainer.value.scrollTop = savedScroll
      scrollTop.value = savedScroll
    }
  }
  const saveScrollDebounced = debounce(
    (scrollValue: number) => fileService.saveScroll(scrollValue),
    500,
  )

  async function onScroll (event: Event) {
    const target = event.target as HTMLElement
    scrollTop.value = target.scrollTop
    saveScrollDebounced(scrollTop.value)
  }
  async function scrollToTop () {
    if (scrollContainer.value) {
      scrollContainer.value.scrollTop = 0
      await fileService.saveScroll(0)
    }
  }
</script>

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
