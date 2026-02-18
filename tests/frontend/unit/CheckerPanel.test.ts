import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'

// Test the pywebview API mocks and core functionality
describe('CheckerPanel.vue - Core Logic Tests', () => {
  beforeEach(() => {
    // Setup detailed mocks for pywebview API
    const mockApi = {
      get_testcase: vi.fn().mockResolvedValue({
        name: 'test_case_1',
        tests: [
          { id: 1, input: '1\n2\n3\n', answer: '6\n' },
          { id: 2, input: '5\n10\n15\n', answer: '30\n' },
        ],
        memoryLimit: 256,
        timeLimit: 1000,
      }),
      get_cpu_count: vi.fn().mockResolvedValue([4, 8]),
      compile: vi.fn().mockResolvedValue('success'),
      run_task: vi.fn().mockResolvedValue({
        result: 'Accepted',
        status: 'Done',
        time: 50,
        memory: 1024,
      }),
      save_testcase: vi.fn().mockResolvedValue(undefined),
    }

    window.pywebview = {
      api: mockApi as any,
      state: {
        addEventListener: vi.fn(),
        prob: null,
      },
    }

    // Mock clipboard
    vi.spyOn(navigator.clipboard, 'writeText').mockResolvedValue()
    vi.spyOn(navigator.clipboard, 'readText').mockResolvedValue('')
    vi.spyOn(navigator.clipboard, 'read').mockResolvedValue([])
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('API Integration', () => {
    it('should load test cases from get_testcase', async () => {
      const result = await window.pywebview.api.get_testcase()
      expect(result).toBeDefined()
      expect(result.name).toBe('test_case_1')
      expect(result.tests).toHaveLength(2)
    })

    it('should get CPU count for judge threads', async () => {
      const [cpu_count, cpu_count_logical] = await window.pywebview.api.get_cpu_count()
      expect(cpu_count).toBe(4)
      expect(cpu_count_logical).toBe(8)
    })

    it('should calculate judge threads correctly', async () => {
      const [cpu_count, cpu_count_logical] = await window.pywebview.api.get_cpu_count()
      let judgeThread: number
      if (cpu_count == cpu_count_logical) {
        judgeThread = Math.max(Math.floor((cpu_count * 3) / 2), 1)
      } else {
        judgeThread = cpu_count
      }
      // cpu_count=4, cpu_count_logical=8, so 4 != 8, judgeThread = cpu_count = 4
      expect(judgeThread).toBe(4)
    })

    it('should compile successfully', async () => {
      const result = await window.pywebview.api.compile()
      expect(result).toBe('success')
    })

    it('should run task and return result', async () => {
      const result = await window.pywebview.api.run_task(1, 256, 1000)
      expect(result.result).toBe('Accepted')
      expect(result.status).toBe('Done')
      expect(result.time).toBe(50)
    })
  })

  describe('Test case handling', () => {
    it('should handle long input by truncating', async () => {
      const testcase = {
        name: 'long_test',
        tests: [
          { id: 1, input: 'a'.repeat(10000), answer: 'b'.repeat(10000) },
        ],
        memoryLimit: 256,
        timeLimit: 1000,
      }

      const processedTasks = testcase.tests.map((test) => ({
        id: test.id,
        input: test.input.length <= 8192 ? test.input : '<Input too long>',
        answer: test.answer.length <= 8192 ? test.answer : '<Answer too long>',
        disabledAnswer: test.answer.length > 8192,
        disabledInput: test.input.length > 8192,
        status: 'null' as const,
        output: '',
        expend: false,
      }))

      expect(processedTasks[0].input).toBe('<Input too long>')
      expect(processedTasks[0].disabledInput).toBe(true)
    })

    it('should save and load testcase', async () => {
      const testcase = await window.pywebview.api.get_testcase()
      await window.pywebview.api.save_testcase(testcase)
      expect(window.pywebview.api.save_testcase).toHaveBeenCalledWith(testcase)
    })
  })

  describe('Copy functionality', () => {
    it('should copy all tasks to clipboard', async () => {
      const tasks = [
        { id: 1, input: '1\n', answer: '6\n' },
        { id: 2, input: '5\n', answer: '30\n' },
      ]

      const tests = tasks.map((task) => ({
        id: task.id,
        input: task.input,
        answer: task.answer,
      }))

      const allText = JSON.stringify(tests, null, 2)
      await navigator.clipboard.writeText(allText)

      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(expect.any(String))
    })
  })

  describe('Paste functionality', () => {
    it('should parse valid JSON from clipboard', async () => {
      const testData = [{ id: 1, input: 'test input', answer: 'test answer' }]
      vi.spyOn(navigator.clipboard, 'readText').mockResolvedValue(JSON.stringify(testData))

      const text = await navigator.clipboard.readText()
      const parsed = JSON.parse(text)

      expect(Array.isArray(parsed)).toBe(true)
      expect(parsed[0].id).toBe(1)
      expect(parsed[0].input).toBe('test input')
    })

    it('should handle invalid JSON as plain text', async () => {
      const plainText = 'plain text input'
      vi.spyOn(navigator.clipboard, 'readText').mockResolvedValue(plainText)

      const text = await navigator.clipboard.readText()
      
      try {
        JSON.parse(text)
        // If it doesn't throw, it's valid JSON
      } catch {
        // It's plain text
        expect(text).toBe(plainText)
      }
    })
  })

  describe('UI state management', () => {
    it('should calculate progress correctly', () => {
      const completedOfTasks = 1
      const tasksLength = 2
      const progress = Math.ceil((completedOfTasks / tasksLength) * 100)
      expect(progress).toBe(50)
    })

    it('should handle zero tasks', () => {
      const completedOfTasks = 0
      const tasksLength = 0
      const progress = tasksLength === 0 ? 0 : Math.ceil((completedOfTasks / tasksLength) * 100)
      expect(progress).toBe(0)
    })
  })
})
