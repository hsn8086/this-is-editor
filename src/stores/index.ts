// Utilities
import { createPinia } from 'pinia'

export { type RunStatus, type TaskItem, type TaskStatus, useCheckerStore } from './checker'
// Export stores
export { type EditorLang, useEditorStore } from './editor'
export { type FileItem, useFileStore } from './file'

export default createPinia()
