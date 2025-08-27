<template>
  <v-navigation-drawer :rail="rail" permanent @click="changRail(!rail)">
    <v-list density="compact" nav @click.stop="">
      <v-list-item @click.stop="changRail(!rail)">
        <template v-slot:append>
          <v-icon> mdi-chevron-left </v-icon>
        </template>
      </v-list-item>

      <v-divider />
      <v-list-item
        @click.stop="runAll()"
        :title="runStatus"
        link
        class="mt-1"
        :disabled="runAllBtnDisabled"
      >
        <template v-slot:prepend>
          <v-icon> {{ runAllBtnIcon }} </v-icon>
        </template>
      </v-list-item>

      <v-divider />
      <!-- 这里创建新任务的时候可能还要作一下平滑过渡 -->
      <v-slide-y-transition class="py-0" tag="v-list" group>
        <div v-for="item in tasks" :key="item.id">
          <v-menu>
            <template v-slot:activator="{ props }">
              <v-list-item
                @click.left.stop="changeExpend(item, !item.expend)"
                @click.right.prevent.stop="props.onClick"
                link
              >
                <template v-slot:prepend>
                  <v-avatar :color="colors[item.status]"></v-avatar>
                </template>
                <v-list-item-title
                  >#{{ item.id }}
                  <v-chip
                    v-if="item.time !== undefined"
                    :color="colors[item.status]"
                    size="x-small"
                    class="ml-1"
                    label
                    dense
                  >
                    {{ (item.time * 1000).toFixed(0) }} ms /
                    {{
                      item.memory! > 1
                        ? item.memory!.toFixed(0) + " MB"
                        : (item.memory! * 1000).toFixed(0) + " KB"
                    }}
                  </v-chip></v-list-item-title
                >
              </v-list-item>
            </template>
            <v-list>
              <v-list-item @click="deleteTask(item.id)" link>
                <template v-slot:prepend>
                  <v-icon color="red"> mdi-delete </v-icon>
                </template>
                <v-list-item-title>Delete Task</v-list-item-title>
              </v-list-item>
              <v-list-item @click="clearAllTasks()" link>
                <!-- clean all -->
                <template v-slot:prepend>
                  <v-icon color="blue"> mdi-broom </v-icon>
                </template>
                <v-list-item-title>Clear All Tasks</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
          <v-expand-transition>
            <div v-show="item.expend">
              <v-divider />

              <v-textarea
                dense
                variant="solo-filled"
                label="Input"
                rows="1"
                class="mt-2 mb-0"
                max-rows="5"
                v-model="item.input"
                :disabled="item.disabledInput"
                auto-grow
                @update:focused="saveTasks()"
              />
              <v-textarea
                dense
                variant="solo-filled"
                label="Answer"
                class="mt-0 mb-0"
                rows="1"
                max-raws="5"
                v-model="item.answer"
                :disabled="item.disabledAnswer"
                auto-grow
                @update:focused="saveTasks()"
              />

              <v-textarea
                dense
                variant="solo-filled"
                class="mt-0 mb-0"
                label="Output"
                disabled
                rows="1"
                max-rows="5"
                auto-grow
                v-model="item.output"
              />
            </div>
          </v-expand-transition>
        </div>
      </v-slide-y-transition>
      <v-list-item @click="createTask()" link class="mt-1">
        <template v-slot:prepend>
          <v-icon> mdi-plus </v-icon>
        </template>
        <v-list-item-title>Add Task</v-list-item-title>
      </v-list-item>
    </v-list>
    <template v-slot:append>
      <v-list>
        <v-tooltip
          location="top"
          v-model="copyAllInfoDisplay"
          :open-on-hover="false"
          :open-on-focus="false"
        >
          <template v-slot:activator="{ props: activatorProps }">
            <v-list-item @click.stop="CopyAll()" link v-bind="activatorProps">
              <!-- Copy all -->
              <template v-slot:prepend>
                <v-icon> mdi-clipboard-multiple</v-icon>
              </template>
              <v-list-item-title>Copy All</v-list-item-title>
            </v-list-item>
          </template>
          <span>Copied to clipboard!</span>
        </v-tooltip>
        <v-tooltip
          location="top"
          :open-on-hover="false"
          :open-on-focus="false"
          v-model="pasteErrorDisplay"
        >
          <template v-slot:activator="{ props: activatorProps }">
            <v-list-item
              @click.stop="PasteFromClipboard()"
              link
              v-bind="activatorProps"
            >
              <!-- Paste from clipboard  -->
              <template v-slot:prepend>
                <v-icon> mdi-clipboard-arrow-down </v-icon>
              </template>
              <v-list-item-title>Paste from Clipboard</v-list-item-title>
            </v-list-item>
          </template>
          <v-alert
            type="error"
            text="Failed to paste tasks! Please ensure the clipboard contains valid task data."
            class="ma-0 pa-0"
            variant="text"
          ></v-alert>
        </v-tooltip>
      </v-list>
    </template>
  </v-navigation-drawer>
</template>
<script lang="ts" setup>
import type { API, TaskResult, TestCase } from "@/pywebview-defines";

import { ref } from "vue";

defineExpose({
  runAll,
});

const colors: Record<string, string> = {
  null: "grey",
  pending: "blue",
  completed: "green",
  failed: "red",
  running: "orange",
};

const py: API = window.pywebview.api;
onMounted(() => {
  init();
});

async function init() {
  await loadTestcase();
  await initJudgeThread();
}

let testcaseInfo: TestCase;
const testcaseName = ref("");
const tasks = ref<TaskItem[]>([]);
type Status = "null" | "pending" | "completed" | "failed" | "running";
type TaskItem = {
  id: number;
  input: string;
  output: string;
  answer: string;
  status: Status;
  expend: boolean;
  disabledInput: boolean;
  disabledAnswer: boolean;
  time?: number;
  memory?: number;
};
async function loadTestcase() {
  testcaseInfo = await py.get_testcase();
  testcaseName.value = testcaseInfo.name;
  tasks.value = testcaseInfo.tests.map((test, index) => ({
    id: test.id,
    input: test.input.length <= 8192 ? test.input : "<Input too long>",
    answer: test.answer.length <= 8192 ? test.answer : "<Answer too long>",
    disabledAnswer: test.answer.length > 8192,
    disabledInput: test.input.length > 8192,
    status: "null" as Status,
    output: "",
    expend: false,
  }));
}

const rail = ref(false);
function changRail(value: boolean) {
  console.log(tasks);
  rail.value = value;
  if (value === true) {
    console.log("Collapsing all tasks");
    tasks.value.forEach((task) => {
      task.expend = false;
    });
  }
}

function changeExpend(item: TaskItem, value: boolean) {
  item.expend = value;
  rail.value = !value && rail.value;
}

let judgeThread = 1; // waiting for init
async function initJudgeThread() {
  const [cpu_count, cpu_count_logical] = await py.get_cpu_count();
  if (cpu_count == cpu_count_logical)
    judgeThread = Math.max(Math.floor((cpu_count * 3) / 2), 1);
  else judgeThread = cpu_count;
}
const runAllBtnDisabled = ref(false);
const runAllBtnIcon = ref("mdi-play");
const runStatus = ref<string>("Run All");
async function runAll() {
  runAllBtnDisabled.value = true;
  runAllBtnIcon.value = "mdi-pause";
  const limit = judgeThread;
  for (const task of tasks.value) {
    task.status = "pending";
    task.output = "";
    task.time = undefined;
    task.memory = undefined;
  }

  runStatus.value = "Compiling...";
  await py.compile();

  runStatus.value = "Running...";
  const executing = new Set<Promise<TaskResult>>();
  for (const task of tasks.value) {
    if (executing.size >= limit) await Promise.race(executing);
    task.status = "running";
    const promise = py.run_task(
      task.id,
      testcaseInfo.memoryLimit,
      testcaseInfo.timeLimit
    );

    executing.add(promise);
    promise
      .then((result) => {
        task.output = result.result;
        task.time = result.time;
        task.memory = result.memory;
        if (result.status !== "success") {
          task.status = "failed";
          changeExpend(task, true); // 展开当前任务
          if (result.result.length === 0)
            task.output = `<${result.status.toUpperCase().replace(/_/g, " ")}>`;
          console.error(
            `Task ${task.id} failed: ${result.status} - ${result.result}`
          );
          return;
        } else changeExpend(task, false); // 关闭当前任务
        task.status = "completed";
      })
      .catch((error) => {
        task.status = "failed";
        task.output = `Error: ${error.message}`;
        changeExpend(task, true); // 展开当前任务
        console.error(`Task ${task.id} encountered an error: ${error.message}`);
      })
      .finally(() => {
        executing.delete(promise);
      });
  }
  await Promise.all(executing);
  runStatus.value = "All Done";
  runAllBtnDisabled.value = false;
  runAllBtnIcon.value = "mdi-play";
  setTimeout(() => {
    runStatus.value = "Run All";
  }, 2000);
}
async function createTask() {
  const newId = tasks.value.length
    ? Math.max(...tasks.value.map((t) => t.id)) + 1
    : 1;
  tasks.value.push({
    id: newId,
    input: "",
    output: "",
    answer: "",
    disabledInput: false,
    disabledAnswer: false,
    status: "null",
    expend: true,
  });
}
async function saveTasks() {
  const tests = tasks.value.map((task) => ({
    id: task.id,
    input: task.input,
    answer: task.answer,
  }));
  testcaseInfo.tests = tests;
  await py.save_testcase(testcaseInfo);
}
async function deleteTask(id: number) {
  tasks.value = tasks.value.filter((task) => task.id !== id);
  await saveTasks();
  await loadTestcase();
}
async function clearAllTasks() {
  tasks.value = [];
  await saveTasks();
  await loadTestcase();
}
const copyAllInfoDisplay = ref(false);
async function CopyAll() {
  const tests = tasks.value.map((task) => ({
    id: task.id,
    input: task.input,
    answer: task.answer,
  }));
  let allText = JSON.stringify(tests, null, 2);
  await navigator.clipboard.writeText(allText);
  // notify
  copyAllInfoDisplay.value = true;
  setTimeout(() => {
    copyAllInfoDisplay.value = false;
  }, 1000);
}
const pasteErrorDisplay = ref(false);
async function PasteFromClipboard() {
  const text = await navigator.clipboard.readText();
  try {
    const parsed = JSON.parse(text);

    // 检查是否是有效的 JSON 格式
    if (!Array.isArray(parsed)) throw new Error("Invalid format");
    for (const item of parsed) {
      if (
        typeof item.id !== "number" ||
        typeof item.input !== "string" ||
        typeof item.answer !== "string"
      ) {
        throw new Error("Invalid format");
      }
    }

    // 如果是有效的 JSON，保存到测试用例中
    testcaseInfo.tests = parsed;
    await py.save_testcase(testcaseInfo);
    await loadTestcase();
  } catch (error) {
    console.warn("Invalid JSON format, attempting to paste as plain text.");

    // 如果不是 JSON 格式，尝试将文本添加到第一个空的输入/输出中
    const firstEmptyTask = tasks.value.find(
      (task) => !task.input || !task.answer
    );

    if (firstEmptyTask) {
      // 如果存在空的输入/输出字段，添加文本到输入/输出字段
      if (!firstEmptyTask.input) {
        firstEmptyTask.input = text;
      } else if (!firstEmptyTask.answer) {
        firstEmptyTask.answer = text;
      }
    } else {
      // 如果没有空的输入/输出字段，新建一个任务并添加文本
      const newId = tasks.value.length
        ? Math.max(...tasks.value.map((t) => t.id)) + 1
        : 1;
      tasks.value.push({
        id: newId,
        input: text,
        output: "",
        answer: "",
        disabledInput: false,
        disabledAnswer: false,
        status: "null",
        expend: true,
      });
    }

    // 保存任务
    await saveTasks();
  }
}
</script>
