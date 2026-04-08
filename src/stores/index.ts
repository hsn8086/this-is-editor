// Utilities
import { createPinia } from 'pinia'

// Export stores
export { useEditorStore, type EditorLang } from './editor'
export { useFileStore, type FileItem } from './file'
export { useCheckerStore, type TaskItem, type TaskStatus, type RunStatus } from './checker'

export default createPinia()
