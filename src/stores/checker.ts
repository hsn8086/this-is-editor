import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { TestCase } from '@/pywebview-defines'

export type TaskStatus = 'null' | 'pending' | 'completed' | 'failed' | 'running'

export interface TaskItem {
  id: number
  input: string
  output: string
  answer: string
  status: TaskStatus
  expend: boolean
  disabledInput: boolean
  disabledAnswer: boolean
  time?: number
  memory?: number
}

export type RunStatus = 0 | 1 | 2 | 3 // 0: Ready, 1: Compiling, 2: Running, 3: Done

export const useCheckerStore = defineStore('checker', () => {
  // State
  const tasks = ref<TaskItem[]>([])
  const testcaseName = ref<string>('')
  const runStatus = ref<RunStatus>(0)
  const completedTasks = ref<number>(0)
  const testcaseInfo = ref<TestCase | null>(null)

  // Getters
  const progress = computed(() => {
    if (tasks.value.length === 0) return 0
    return Math.ceil((completedTasks.value / tasks.value.length) * 100)
  })

  const isRunning = computed(() => runStatus.value === 2)
  const isCompiling = computed(() => runStatus.value === 1)
  const isReady = computed(() => runStatus.value === 0)
  const isDone = computed(() => runStatus.value === 3)

  const taskCount = computed(() => tasks.value.length)
  const hasTasks = computed(() => tasks.value.length > 0)

  const pendingTasks = computed(() =>
    tasks.value.filter(t => t.status === 'pending').length
  )

  const completedCount = computed(() =>
    tasks.value.filter(t => t.status === 'completed').length
  )

  const failedCount = computed(() =>
    tasks.value.filter(t => t.status === 'failed').length
  )

  // Actions
  function setTasks(newTasks: TaskItem[]) {
    tasks.value = newTasks
    completedTasks.value = 0
  }

  function addTask(task: TaskItem) {
    tasks.value.push(task)
  }

  function updateTask(id: number, updates: Partial<TaskItem>) {
    const task = tasks.value.find(t => t.id === id)
    if (task) {
      Object.assign(task, updates)
    }
  }

  function deleteTask(id: number) {
    tasks.value = tasks.value.filter(t => t.id !== id)
  }

  function clearTasks() {
    tasks.value = []
    completedTasks.value = 0
  }

  function setTestcaseName(name: string) {
    testcaseName.value = name
  }

  function setTestcaseInfo(info: TestCase) {
    testcaseInfo.value = info
  }

  function setRunStatus(status: RunStatus) {
    runStatus.value = status
  }

  function resetRunStatus() {
    runStatus.value = 0
    completedTasks.value = 0
  }

  function incrementCompleted() {
    completedTasks.value += 1
  }

  function resetAllTasksStatus() {
    tasks.value.forEach(task => {
      task.status = 'pending'
      task.output = ''
      task.time = undefined
      task.memory = undefined
    })
    completedTasks.value = 0
  }

  function collapseAllTasks() {
    tasks.value.forEach(task => {
      task.expend = false
    })
  }

  function expandTask(id: number) {
    const task = tasks.value.find(t => t.id === id)
    if (task) {
      task.expend = true
    }
  }

  function resetCheckerState() {
    tasks.value = []
    testcaseName.value = ''
    runStatus.value = 0
    completedTasks.value = 0
    testcaseInfo.value = null
  }

  return {
    // State
    tasks,
    testcaseName,
    runStatus,
    completedTasks,
    testcaseInfo,
    // Getters
    progress,
    isRunning,
    isCompiling,
    isReady,
    isDone,
    taskCount,
    hasTasks,
    pendingTasks,
    completedCount,
    failedCount,
    // Actions
    setTasks,
    addTask,
    updateTask,
    deleteTask,
    clearTasks,
    setTestcaseName,
    setTestcaseInfo,
    setRunStatus,
    resetRunStatus,
    incrementCompleted,
    resetAllTasksStatus,
    collapseAllTasks,
    expandTask,
    resetCheckerState,
  }
})
