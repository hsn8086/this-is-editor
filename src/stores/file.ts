import type { FileInfo } from '@/pywebview-defines'
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export interface FileItem extends FileInfo {
  isReturn?: boolean
}

export const useFileStore = defineStore('file', () => {
  // State
  const folder = ref<string>('')
  const pinnedFiles = ref<FileInfo[]>([])
  const ls = ref<FileItem[]>([])
  const disks = ref<FileInfo[]>([])

  // Getters
  const hasPinnedFiles = computed(() => pinnedFiles.value.length > 0)
  const currentFolderName = computed(() => {
    if (!folder.value) {
      return ''
    }
    const parts = folder.value.split(/[/\\]/)
    return parts[parts.length - 1] || folder.value
  })
  const fileCount = computed(() => ls.value.filter(f => !f.isReturn).length)

  // Actions
  function setFolder (newFolder: string) {
    folder.value = newFolder
  }

  function setPinnedFiles (files: FileInfo[]) {
    pinnedFiles.value = files
  }

  function addPinnedFile (file: FileInfo) {
    if (!pinnedFiles.value.some(f => f.path === file.path)) {
      pinnedFiles.value.push(file)
    }
  }

  function removePinnedFile (path: string) {
    pinnedFiles.value = pinnedFiles.value.filter(f => f.path !== path)
  }

  function setLs (files: FileItem[]) {
    ls.value = files
  }

  function setDisks (diskList: FileInfo[]) {
    disks.value = diskList
  }

  function resetFileState () {
    folder.value = ''
    pinnedFiles.value = []
    ls.value = []
    disks.value = []
  }

  return {
    // State
    folder,
    pinnedFiles,
    ls,
    disks,
    // Getters
    hasPinnedFiles,
    currentFolderName,
    fileCount,
    // Actions
    setFolder,
    setPinnedFiles,
    addPinnedFile,
    removePinnedFile,
    setLs,
    setDisks,
    resetFileState,
  }
})
