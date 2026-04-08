import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useCheckerStore, type TaskItem, type TaskStatus, type RunStatus } from '@/stores/checker'
import type { TestCase } from '@/pywebview-defines'

describe('checker Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  describe('State', () => {
    it('should have correct initial state', () => {
      const store = useCheckerStore()

      expect(store.tasks).toEqual([])
      expect(store.testcaseName).toBe('')
      expect(store.runStatus).toBe(0)
      expect(store.completedTasks).toBe(0)
      expect(store.testcaseInfo).toBeNull()
    })
  })

  describe('Getters', () => {
    describe('progress', () => {
      it('should return 0 when no tasks', () => {
        const store = useCheckerStore()
        expect(store.progress).toBe(0)
      })

      it('should calculate progress correctly', () => {
        const store = useCheckerStore()
        store.tasks = [
          createTask(1, 'completed'),
          createTask(2, 'completed'),
          createTask(3, 'pending'),
          createTask(4, 'pending'),
        ]
        store.completedTasks = 2
        expect(store.progress).toBe(50)
      })

      it('should round up progress', () => {
        const store = useCheckerStore()
        store.tasks = [
          createTask(1, 'completed'),
          createTask(2, 'completed'),
          createTask(3, 'pending'),
        ]
        store.completedTasks = 1
        expect(store.progress).toBe(34)
      })
    })

    describe('status flags', () => {
      it('isReady should return true when runStatus is 0', () => {
        const store = useCheckerStore()
        store.runStatus = 0
        expect(store.isReady).toBe(true)
        expect(store.isCompiling).toBe(false)
        expect(store.isRunning).toBe(false)
        expect(store.isDone).toBe(false)
      })

      it('isCompiling should return true when runStatus is 1', () => {
        const store = useCheckerStore()
        store.runStatus = 1
        expect(store.isReady).toBe(false)
        expect(store.isCompiling).toBe(true)
        expect(store.isRunning).toBe(false)
        expect(store.isDone).toBe(false)
      })

      it('isRunning should return true when runStatus is 2', () => {
        const store = useCheckerStore()
        store.runStatus = 2
        expect(store.isReady).toBe(false)
        expect(store.isCompiling).toBe(false)
        expect(store.isRunning).toBe(true)
        expect(store.isDone).toBe(false)
      })

      it('isDone should return true when runStatus is 3', () => {
        const store = useCheckerStore()
        store.runStatus = 3
        expect(store.isReady).toBe(false)
        expect(store.isCompiling).toBe(false)
        expect(store.isRunning).toBe(false)
        expect(store.isDone).toBe(true)
      })
    })

    describe('task counts', () => {
      it('taskCount should return number of tasks', () => {
        const store = useCheckerStore()
        store.tasks = [createTask(1), createTask(2)]
        expect(store.taskCount).toBe(2)
      })

      it('hasTasks should return false when no tasks', () => {
        const store = useCheckerStore()
        expect(store.hasTasks).toBe(false)
      })

      it('hasTasks should return true when has tasks', () => {
        const store = useCheckerStore()
        store.tasks = [createTask(1)]
        expect(store.hasTasks).toBe(true)
      })

      it('pendingTasks should count pending tasks', () => {
        const store = useCheckerStore()
        store.tasks = [
          createTask(1, 'pending'),
          createTask(2, 'completed'),
          createTask(3, 'pending'),
        ]
        expect(store.pendingTasks).toBe(2)
      })

      it('completedCount should count completed tasks', () => {
        const store = useCheckerStore()
        store.tasks = [
          createTask(1, 'completed'),
          createTask(2, 'failed'),
          createTask(3, 'completed'),
        ]
        expect(store.completedCount).toBe(2)
      })

      it('failedCount should count failed tasks', () => {
        const store = useCheckerStore()
        store.tasks = [
          createTask(1, 'completed'),
          createTask(2, 'failed'),
          createTask(3, 'failed'),
        ]
        expect(store.failedCount).toBe(2)
      })
    })
  })

  describe('Actions', () => {
    it('setTasks should replace tasks and reset completed', () => {
      const store = useCheckerStore()
      store.completedTasks = 5
      const newTasks = [createTask(1), createTask(2)]

      store.setTasks(newTasks)

      expect(store.tasks).toEqual(newTasks)
      expect(store.completedTasks).toBe(0)
    })

    it('addTask should append task to list', () => {
      const store = useCheckerStore()
      store.tasks = [createTask(1)]
      const newTask = createTask(2)

      store.addTask(newTask)

      expect(store.tasks.length).toBe(2)
      expect(store.tasks[1]).toEqual(newTask)
    })

    it('updateTask should update task properties', () => {
      const store = useCheckerStore()
      store.tasks = [createTask(1, 'pending', 'old input')]

      store.updateTask(1, { status: 'completed', input: 'new input' })

      expect(store.tasks[0].status).toBe('completed')
      expect(store.tasks[0].input).toBe('new input')
    })

    it('updateTask should do nothing if task not found', () => {
      const store = useCheckerStore()
      store.tasks = [createTask(1)]

      store.updateTask(999, { status: 'completed' })

      expect(store.tasks[0].status).toBe('null')
    })

    it('deleteTask should remove task by id', () => {
      const store = useCheckerStore()
      store.tasks = [createTask(1), createTask(2), createTask(3)]

      store.deleteTask(2)

      expect(store.tasks.length).toBe(2)
      expect(store.tasks.find(t => t.id === 2)).toBeUndefined()
    })

    it('clearTasks should remove all tasks', () => {
      const store = useCheckerStore()
      store.tasks = [createTask(1), createTask(2)]
      store.completedTasks = 1

      store.clearTasks()

      expect(store.tasks).toEqual([])
      expect(store.completedTasks).toBe(0)
    })

    it('setTestcaseName should update name', () => {
      const store = useCheckerStore()
      store.setTestcaseName('New Test')
      expect(store.testcaseName).toBe('New Test')
    })

    it('setTestcaseInfo should update info', () => {
      const store = useCheckerStore()
      const info: TestCase = {
        name: 'test',
        tests: [],
        memoryLimit: 256,
        timeLimit: 1000,
      }
      store.setTestcaseInfo(info)
      expect(store.testcaseInfo).toEqual(info)
    })

    it('setRunStatus should update status', () => {
      const store = useCheckerStore()
      store.setRunStatus(2)
      expect(store.runStatus).toBe(2)
    })

    it('resetRunStatus should reset status and completed', () => {
      const store = useCheckerStore()
      store.runStatus = 2
      store.completedTasks = 5

      store.resetRunStatus()

      expect(store.runStatus).toBe(0)
      expect(store.completedTasks).toBe(0)
    })

    it('incrementCompleted should increase count', () => {
      const store = useCheckerStore()
      store.completedTasks = 3
      store.incrementCompleted()
      expect(store.completedTasks).toBe(4)
    })

    it('resetAllTasksStatus should reset all task statuses', () => {
      const store = useCheckerStore()
      store.tasks = [
        createTask(1, 'completed', 'input', 'output', 'answer', 100, 10),
        createTask(2, 'failed', 'input2', 'output2', 'answer2', 200, 20),
      ]

      store.resetAllTasksStatus()

      store.tasks.forEach(task => {
        expect(task.status).toBe('pending')
        expect(task.output).toBe('')
        expect(task.time).toBeUndefined()
        expect(task.memory).toBeUndefined()
      })
      expect(store.completedTasks).toBe(0)
    })

    it('collapseAllTasks should set expend to false', () => {
      const store = useCheckerStore()
      store.tasks = [
        createTask(1, 'null', 'input', '', '', undefined, undefined, true),
        createTask(2, 'null', 'input', '', '', undefined, undefined, true),
      ]

      store.collapseAllTasks()

      store.tasks.forEach(task => {
        expect(task.expend).toBe(false)
      })
    })

    it('expandTask should set expend to true for specific task', () => {
      const store = useCheckerStore()
      store.tasks = [
        createTask(1, 'null', 'input', '', '', undefined, undefined, false),
        createTask(2, 'null', 'input', '', '', undefined, undefined, false),
      ]

      store.expandTask(1)

      expect(store.tasks[0].expend).toBe(true)
      expect(store.tasks[1].expend).toBe(false)
    })

    it('resetCheckerState should reset all state', () => {
      const store = useCheckerStore()
      store.tasks = [createTask(1)]
      store.testcaseName = 'Test'
      store.runStatus = 2
      store.completedTasks = 5
      store.testcaseInfo = { name: 'test', tests: [], memoryLimit: 256, timeLimit: 1000 }

      store.resetCheckerState()

      expect(store.tasks).toEqual([])
      expect(store.testcaseName).toBe('')
      expect(store.runStatus).toBe(0)
      expect(store.completedTasks).toBe(0)
      expect(store.testcaseInfo).toBeNull()
    })
  })
})

// Helper function to create task items
function createTask(
  id: number,
  status: TaskStatus = 'null',
  input = '',
  output = '',
  answer = '',
  time?: number,
  memory?: number,
  expend = false,
): TaskItem {
  return {
    id,
    input,
    output,
    answer,
    status,
    expend,
    disabledInput: false,
    disabledAnswer: false,
    time,
    memory,
  }
}
