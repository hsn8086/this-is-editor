<template>
  <v-navigation-drawer permanent :rail="rail" @click="changRail(!rail)">
    <v-list density="compact" nav @click.stop="">
      <v-list-item @click.stop="changRail(!rail)">
        <template #append>
          <v-icon> mdi-chevron-left </v-icon>
        </template>
      </v-list-item>

      <v-divider />
      <v-list-item
        class="mt-1"
        :disabled="runAllBtnDisabled"
        link
        :title="$t('checkerPanel.runAllStatus', runStatus)"
        @click.stop="runAll()"
      >
        <template #prepend>
          <v-icon> {{ runAllBtnIcon }} </v-icon>
        </template>
      </v-list-item>
      <v-progress-linear
        v-if="runStatus === 2"
        v-model="progressOfTasks"
        height="1"
        stream
      />
      <v-divider v-else />

      <v-slide-y-transition class="py-0" group tag="v-list">
        <div v-for="item in tasks" :key="item.id">
          <v-menu>
            <template #activator="{ props }">
              <v-list-item
                link
                @click.left.stop="changeExpend(item, !item.expend)"
                @click.right.prevent.stop="props.onClick"
              >
                <template #prepend>
                  <v-avatar :color="colors[item.status]" />
                </template>
                <v-list-item-title>
                  #{{ item.id }}
                  <v-chip
                    v-if="item.time !== undefined"
                    class="ml-1"
                    :color="colors[item.status]"
                    dense
                    label
                    size="x-small"
                  >
                    {{ (item.time * 1000).toFixed(0) }} ms /
                    {{
                      item.memory! > 1
                        ? item.memory!.toFixed(0) + " MB"
                        : (item.memory! * 1000).toFixed(0) + " KB"
                    }}
                  </v-chip>
                </v-list-item-title>
              </v-list-item>
            </template>
            <v-list>
              <v-list-item link @click="deleteTask(item.id)">
                <template #prepend>
                  <v-icon color="red"> mdi-delete </v-icon>
                </template>
                <v-list-item-title>{{
                  $t("checkerPanel.deleteTask")
                }}</v-list-item-title>
              </v-list-item>
              <v-list-item link @click="clearAllTasks()">
                <template #prepend>
                  <v-icon color="blue"> mdi-broom </v-icon>
                </template>
                <v-list-item-title>{{
                  $t("checkerPanel.clearAllTasks")
                }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
          <v-expand-transition>
            <div v-show="item.expend">
              <v-divider />
              <v-textarea
                v-model="item.input"
                auto-grow
                class="mt-2 mb-0"
                dense
                :disabled="item.disabledInput"
                :label="$t('checkerPanel.input')"
                max-rows="5"
                rows="1"
                variant="solo-filled"
                @update:focused="saveTasks()"
              />
              <v-textarea
                v-model="item.answer"
                auto-grow
                class="mt-0 mb-0"
                dense
                :disabled="item.disabledAnswer"
                :label="$t('checkerPanel.answer')"
                max-raws="5"
                rows="1"
                variant="solo-filled"
                @update:focused="saveTasks()"
              />

              <v-textarea
                v-model="item.output"
                auto-grow
                class="mt-0 mb-0"
                dense
                :label="$t('checkerPanel.output')"
                max-rows="5"
                readonly
                rows="1"
                variant="solo-filled"
              />
              <v-textarea
                v-if="item.stderr.length > 0"
                v-model="item.stderr"
                auto-grow
                class="mt-0 mb-0"
                dense
                label="stderr"
                max-rows="5"
                readonly
                rows="1"
                variant="solo-filled"
              />
            </div>
          </v-expand-transition>
        </div>
      </v-slide-y-transition>
      <v-list-item class="mt-1" link @click="createTask()">
        <template #prepend>
          <v-icon> mdi-plus </v-icon>
        </template>
        <v-list-item-title>{{ $t("checkerPanel.addTask") }}</v-list-item-title>
      </v-list-item>
    </v-list>
    <template #append>
      <v-list>
        <v-tooltip
          v-model="copyAllInfoDisplay"
          location="top"
          :open-on-focus="false"
          :open-on-hover="false"
        >
          <template #activator="{ props: activatorProps }">
            <v-list-item link v-bind="activatorProps" @click.stop="CopyAll()">
              <template #prepend>
                <v-icon> mdi-clipboard-multiple</v-icon>
              </template>
              <v-list-item-title>{{
                $t("checkerPanel.copyAll")
              }}</v-list-item-title>
            </v-list-item>
          </template>
          <span>{{ $t("checkerPanel.copied") }}</span>
        </v-tooltip>
        <v-tooltip
          v-model="pasteErrorDisplay"
          location="top"
          :open-on-focus="false"
          :open-on-hover="false"
        >
          <template #activator="{ props: activatorProps }">
            <v-list-item
              link
              v-bind="activatorProps"
              @click.stop="PasteFromClipboard()"
            >
              <template #prepend>
                <v-icon> mdi-clipboard-arrow-down </v-icon>
              </template>
              <v-list-item-title>{{
                $t("checkerPanel.pasteFromClipboard")
              }}</v-list-item-title>
            </v-list-item>
          </template>
          <v-alert
            class="ma-0 pa-0"
            :text="$t('checkerPanel.pasteError')"
            type="error"
            variant="text"
          />
        </v-tooltip>
      </v-list>
    </template>
  </v-navigation-drawer>
</template>
<script lang="ts" setup>
  import type { TaskResult, TestCase } from '@/pywebview-defines'
  import { ceil, round } from 'lodash'

  import { storeToRefs } from 'pinia'
  import { computed, ref } from 'vue'
  import { useI18n } from 'vue-i18n'
  import { fileService, taskService } from '@/services'
  import { useCheckerStore } from '@/stores/checker'
  const { t } = useI18n()

  // Checker store
  const checkerStore = useCheckerStore()
  const {
    tasks,
    testcaseName,
    runStatus,
    completedTasks: completedOfTasks,
    testcaseInfo,
  } = storeToRefs(checkerStore)
  const progressOfTasks = computed(() => checkerStore.progress)

  defineExpose({
    runAll,
  })

  // Define color mappings for task statuses
  const colors: Record<string, string> = {
    null: 'grey',
    pending: 'blue',
    completed: 'green',
    failed: 'red',
    running: 'orange',
  }

  // Initialize the component when mounted
  onMounted(() => {
    init()
  })

  // Initialize the component by loading test cases and setting up the judge thread
  async function init () {
    await loadTestcase()
    await initJudgeThread()
  }

  // Load test cases from the backend and initialize tasks
  async function loadTestcase () {
    const newTestcaseInfo = await taskService.getTestcase()
    checkerStore.setTestcaseInfo(newTestcaseInfo)
    checkerStore.setTestcaseName(newTestcaseInfo.name)
    const newTasks = newTestcaseInfo.tests.map(test => ({
      id: test.id,
      input: test.input.length <= 8192 ? test.input : '<Input too long>',
      answer: test.answer.length <= 8192 ? test.answer : '<Answer too long>',
      disabledAnswer: test.answer.length > 8192,
      disabledInput: test.input.length > 8192,
      status: 'null' as const,
      output: '',
      stderr: '',
      expend: false,
    }))
    checkerStore.setTasks(newTasks)
  }

  // Manage the state of the navigation drawer (collapsed/expanded)
  const rail = ref(true)
  function changRail (value: boolean) {
    console.log(tasks)
    rail.value = value
    if (value === true) {
      console.log('Collapsing all tasks')
      checkerStore.collapseAllTasks()
    }
  }

  // Toggle the expanded state of a specific task
  function changeExpend (item: (typeof tasks.value)[0], value: boolean) {
    checkerStore.updateTask(item.id, { expend: value })
    rail.value = !value && rail.value
  }

  // Initialize the number of judge threads based on CPU count
  let judgeThread = 1 // Default to 1 thread until initialized
  async function initJudgeThread () {
    judgeThread = await taskService.getRecommendedJudgeThread()
  }

  // Manage the state of the "Run All" button
  const runAllBtnDisabled = ref(false)
  const runAllBtnIcon = ref('mdi-play')
  // Execute all tasks sequentially or in parallel based on the thread limit
  async function runAll () {
    runAllBtnDisabled.value = true
    runAllBtnIcon.value = 'mdi-pause'
    const limit = judgeThread
    // Reset task statuses and outputs
    checkerStore.resetAllTasksStatus()

    // Compile the test cases before running
    checkerStore.setRunStatus(1) // Compiling...
    try {
      const rst = await taskService.compile()
      if (rst !== 'success') throw new Error(rst)
    } catch (error) {
      console.error('Compilation failed:', error)
      for (const task of tasks.value) {
        checkerStore.updateTask(task.id, {
          status: 'failed',
          output: 'empty',
          stderr: error instanceof Error ? error.message : String(error),
        })
        checkerStore.expandTask(task.id)
      }
      rail.value = false
      checkerStore.resetRunStatus()
      runAllBtnDisabled.value = false
      runAllBtnIcon.value = 'mdi-play'
      return
    }

    // Run tasks with a limit on concurrent executions
    checkerStore.setRunStatus(2) // Running...
    const executing = new Set<Promise<TaskResult>>()
    const currentTestcaseInfo = testcaseInfo.value
    if (!currentTestcaseInfo) return

    for (const task of tasks.value) {
      if (executing.size >= limit) await Promise.race(executing)
      checkerStore.updateTask(task.id, { status: 'running' })
      const promise = taskService.runTask(
        task.id,
        currentTestcaseInfo.memoryLimit,
        currentTestcaseInfo.timeLimit,
      )

      executing.add(promise)
      promise
        .then(result => {
          const updates: Partial<typeof task> = {
            output: result.result,
            stderr: result.stderr,
            time: result.time,
            memory: result.memory,
          }
          if (result.status !== 'success') {
            updates.status = 'failed'
            if (result.result.length === 0) updates.output = '<EMPTY>'
            console.error(
              `Task ${task.id} failed: ${result.status} - ${result.result || result.stderr}`,
            )
            checkerStore.updateTask(task.id, updates)
            checkerStore.expandTask(task.id)
            rail.value = false
            return
          }
          updates.status = 'completed'
          checkerStore.updateTask(task.id, updates)
          checkerStore.updateTask(task.id, { expend: false })
        })
        .catch(error => {
          checkerStore.updateTask(task.id, {
            status: 'failed',
            output: 'empty',
            stderr: `Error: ${error.message}`,
          })
          checkerStore.expandTask(task.id)
          rail.value = false
          console.error(`Task ${task.id} encountered an error: ${error.message}`)
        })
        .finally(() => {
          checkerStore.incrementCompleted()
          executing.delete(promise)
          console.log(
            `Task ${task.id} completed. ${completedOfTasks.value}/${
              tasks.value.length
            } ${(completedOfTasks.value / tasks.value.length) * 100}`,
          )
        })
    }
    await Promise.all(executing)

    // Update the "Run All" button state after execution
    checkerStore.resetRunStatus()
    runAllBtnDisabled.value = false
    runAllBtnIcon.value = 'mdi-play'
  }

  // Create a new task with default values
  async function createTask () {
    const newId = tasks.value.length > 0
      ? Math.max(...tasks.value.map(t => t.id)) + 1
      : 1
    checkerStore.addTask({
      id: newId,
      input: '',
      output: '',
      stderr: '',
      answer: '',
      disabledInput: false,
      disabledAnswer: false,
      status: 'null',
      expend: true,
    })
    changRail(false)
  }

  // Save the current state of tasks to the backend
  async function saveTasks () {
    const tests = tasks.value.map(task => ({
      id: task.id,
      input: task.input,
      answer: task.answer,
    }))
    const currentTestcaseInfo = testcaseInfo.value
    if (currentTestcaseInfo) {
      const updatedTestcaseInfo = { ...currentTestcaseInfo, tests }
      await taskService.saveTestcase(updatedTestcaseInfo)
    }
  }

  // Delete a specific task by its ID
  async function deleteTask (id: number) {
    checkerStore.deleteTask(id)
    await saveTasks()
    await loadTestcase()
  }

  // Clear all tasks and reset the state
  async function clearAllTasks () {
    checkerStore.clearTasks()
    await saveTasks()
    await loadTestcase()
  }

  // Copy all task information to the clipboard
  const copyAllInfoDisplay = ref(false)
  async function CopyAll () {
    const tests = tasks.value.map(task => ({
      id: task.id,
      input: task.input,
      answer: task.answer,
    }))
    const allText = JSON.stringify(tests, null, 2)
    await navigator.clipboard.writeText(allText)

    // Notify the user that the copy operation was successful
    copyAllInfoDisplay.value = true
    setTimeout(() => {
      copyAllInfoDisplay.value = false
    }, 1000)
  }

  // Paste tasks from the clipboard, handling both JSON and plain text formats
  const pasteErrorDisplay = ref(false)
  async function PasteFromClipboard () {
    console.log(navigator.clipboard)
    const items = await navigator.clipboard.read()
    if (items.length > 0 && items[0].types.includes('text/uri-list')) {
      const files = (await navigator.clipboard.readText())
        .split('\n')
        .filter(f => f.trim().length > 0)
      interface FileType {
        in: string
        out: string
      }
      const fileRec: Record<string, FileType> = {}
      for (const file of files) {
        console.log(`Opening file from clipboard: ${file}`)
        console.log(await fileService.getText(file))
        const info = await fileService.getInfo(file)
        if (fileRec[info.stem] === undefined)
          fileRec[info.stem] = { in: '', out: '' }

        if (info.name.endsWith('.in')) {
          fileRec[info.stem].in = await fileService.getText(file)
        } else if (info.name.endsWith('.out') || info.name.endsWith('.ans')) {
          fileRec[info.stem].out = await fileService.getText(file)
        }
      }
      for (const key in fileRec) {
        const firstEmptyTask = tasks.value.find(
          task => !task.input || !task.answer,
        )

        if (firstEmptyTask) {
          const updates: Partial<typeof firstEmptyTask> = {}
          if (!firstEmptyTask.input) {
            updates.input = fileRec[key].in
          }
          if (!firstEmptyTask.answer) {
            updates.answer = fileRec[key].out
          }
          checkerStore.updateTask(firstEmptyTask.id, updates)
        } else {
          const newId = tasks.value.length > 0
            ? Math.max(...tasks.value.map(t => t.id)) + 1
            : 1
          checkerStore.addTask({
            id: newId,
            input: fileRec[key].in,
            output: '',
            stderr: '',
            answer: fileRec[key].out,
            disabledInput: false,
            disabledAnswer: false,
            status: 'null',
            expend: true,
          })
        }
      }
      await saveTasks()
      // await loadTestcase();
      await changRail(false)

      return
    }
    const text = await navigator.clipboard.readText()
    try {
      const parsed = JSON.parse(text)

      // Validate the JSON format
      if (!Array.isArray(parsed)) throw new Error('Invalid format')
      for (const item of parsed) {
        if (
          typeof item.id !== 'number'
          || typeof item.input !== 'string'
          || typeof item.answer !== 'string'
        ) {
          throw new TypeError('Invalid format')
        }
      }

      // Replace all tasks with the parsed data
      const currentTestcaseInfo = testcaseInfo.value
      if (currentTestcaseInfo) {
        const updatedTestcaseInfo = { ...currentTestcaseInfo, tests: parsed }
        await taskService.saveTestcase(updatedTestcaseInfo)
      }
      await loadTestcase()
    } catch {
      console.warn('Invalid JSON format, attempting to paste as plain text.')

      // Handle plain text input by filling the first empty task or creating a new one
      const firstEmptyTask = tasks.value.find(
        task => !task.input || !task.answer,
      )

      if (firstEmptyTask) {
        const updates: Partial<typeof firstEmptyTask> = {}
        if (!firstEmptyTask.input) {
          updates.input = text
        } else if (!firstEmptyTask.answer) {
          updates.answer = text
        }
        checkerStore.updateTask(firstEmptyTask.id, updates)
      } else {
        const newId = tasks.value.length > 0
          ? Math.max(...tasks.value.map(t => t.id)) + 1
          : 1
        checkerStore.addTask({
          id: newId,
          input: text,
          output: '',
          stderr: '',
          answer: '',
          disabledInput: false,
          disabledAnswer: false,
          status: 'null',
          expend: true,
        })
      }

      await saveTasks()
    }
  }
</script>
