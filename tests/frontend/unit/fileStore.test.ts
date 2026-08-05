import type { FileInfo } from '@/pywebview-defines'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'
import { type FileItem, useFileStore } from '@/stores/file'

describe('file Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('State', () => {
    it('should have correct initial state', () => {
      const store = useFileStore()

      expect(store.folder).toBe('')
      expect(store.pinnedFiles).toEqual([])
      expect(store.ls).toEqual([])
      expect(store.disks).toEqual([])
    })
  })

  describe('Getters', () => {
    it('hasPinnedFiles should return false when empty', () => {
      const store = useFileStore()
      expect(store.hasPinnedFiles).toBe(false)
    })

    it('hasPinnedFiles should return true when has items', () => {
      const store = useFileStore()
      store.pinnedFiles = [{ name: 'test.py', path: '/test.py' } as FileInfo]
      expect(store.hasPinnedFiles).toBe(true)
    })

    it('currentFolderName should extract folder name from path', () => {
      const store = useFileStore()
      store.folder = '/home/user/projects'
      expect(store.currentFolderName).toBe('projects')
    })

    it('currentFolderName should handle Windows paths', () => {
      const store = useFileStore()
      store.folder = String.raw`C:\Users\test\docs`
      expect(store.currentFolderName).toBe('docs')
    })

    it('currentFolderName should return full path if no separator', () => {
      const store = useFileStore()
      store.folder = 'root'
      expect(store.currentFolderName).toBe('root')
    })

    it('currentFolderName should handle empty folder', () => {
      const store = useFileStore()
      store.folder = ''
      expect(store.currentFolderName).toBe('')
    })

    it('fileCount should count non-return files', () => {
      const store = useFileStore()
      store.ls = [
        { name: '...', isReturn: true } as FileItem,
        { name: 'file1.py', isReturn: false } as FileItem,
        { name: 'file2.py', isReturn: false } as FileItem,
      ]
      expect(store.fileCount).toBe(2)
    })

    it('fileCount should return 0 for empty ls', () => {
      const store = useFileStore()
      expect(store.fileCount).toBe(0)
    })
  })

  describe('Actions', () => {
    it('setFolder should update folder', () => {
      const store = useFileStore()
      store.setFolder('/new/path')
      expect(store.folder).toBe('/new/path')
    })

    it('setPinnedFiles should replace pinned files', () => {
      const store = useFileStore()
      const files: FileInfo[] = [
        { name: 'test.py', path: '/test.py' } as FileInfo,
      ]
      store.setPinnedFiles(files)
      expect(store.pinnedFiles).toEqual(files)
    })

    it('addPinnedFile should add new file', () => {
      const store = useFileStore()
      const file: FileInfo = { name: 'test.py', path: '/test.py' } as FileInfo
      store.addPinnedFile(file)
      expect(store.pinnedFiles).toContainEqual(file)
    })

    it('addPinnedFile should not add duplicate files', () => {
      const store = useFileStore()
      const file: FileInfo = { name: 'test.py', path: '/test.py' } as FileInfo
      store.addPinnedFile(file)
      store.addPinnedFile(file)
      expect(store.pinnedFiles.length).toBe(1)
    })

    it('removePinnedFile should remove file by path', () => {
      const store = useFileStore()
      store.pinnedFiles = [
        { name: 'file1.py', path: '/file1.py' } as FileInfo,
        { name: 'file2.py', path: '/file2.py' } as FileInfo,
      ]
      store.removePinnedFile('/file1.py')
      expect(store.pinnedFiles.length).toBe(1)
      expect(store.pinnedFiles[0].path).toBe('/file2.py')
    })

    it('setLs should update file list', () => {
      const store = useFileStore()
      const files: FileItem[] = [
        { name: 'file.py', isReturn: false } as FileItem,
      ]
      store.setLs(files)
      expect(store.ls).toEqual(files)
    })

    it('setDisks should update disks', () => {
      const store = useFileStore()
      const disks: FileInfo[] = [
        { name: 'C:', path: 'C:\\' } as FileInfo,
      ]
      store.setDisks(disks)
      expect(store.disks).toEqual(disks)
    })

    it('resetFileState should reset all state', () => {
      const store = useFileStore()
      store.setFolder('/test')
      store.setPinnedFiles([{ name: 'test.py', path: '/test.py' } as FileInfo])
      store.setLs([{ name: 'file.py', isReturn: false } as FileItem])

      store.resetFileState()

      expect(store.folder).toBe('')
      expect(store.pinnedFiles).toEqual([])
      expect(store.ls).toEqual([])
      expect(store.disks).toEqual([])
    })
  })
})
