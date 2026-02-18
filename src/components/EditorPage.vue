<template>
  <CheckerPanel ref="checkPanel" v-if="enableCheckerPanel" />
  <v-menu
    :style="{ left: menuX + 'px', top: menuY + 'px' }"
    v-model="showMenu"
    absolute
    offset-y
  >
    <template #activator="{ props }">
      <v-ace-editor
        ref="aceRef"
        v-model:value="content"
        theme="github"
        style="height: 100%"
        :readonly="false"
        :options="editorOptions"
        :lang="lang"
        @contextmenu.prevent="onContextMenu"
      />
    </template>
    <v-list nav density="compact">
      <div v-for="(group, gIndex) in menuList" :key="gIndex">
        <v-divider v-if="gIndex > 0" class="my-1" />
        <v-list-item
          v-for="(item, index) in group"
          :key="index"
          dense
          @click="
            () => {
              item.action();
              showMenu = false;
            }
          "
        >
          <v-list-item-title>{{
            t("editorPage.menu." + item.title)
          }}</v-list-item-title>
        </v-list-item>
      </div>
    </v-list>
  </v-menu>
</template>

<script lang="ts" setup>
import type { SyntaxMode } from "ace-code/src/ext/static_highlight";
import { ref, onMounted, onUnmounted } from "vue";
import { storeToRefs } from "pinia";
import { useEditorStore } from "@/stores/editor";
import { VAceEditor } from "vue3-ace-editor";
import { Mode as python } from "ace-code/src/mode/python";
import { Mode as cpp } from "ace-code/src/mode/c_cpp";
import { Mode as json } from "ace-code/src/mode/json";
import "ace-builds/src-noconflict/mode-python";
import "ace-builds/src-noconflict/mode-c_cpp";
import { Ace } from "ace-builds";
import "ace-builds/src-noconflict/ext-language_tools";
import "@/ace-theme-tie"; // 自定义主题
import "@/ace-theme-tie-light";
import "ace-builds/src-noconflict/theme-github"; // 亮色主题基础
// Phase 2.2: 使用 LSP composable
import { useEditorLsp } from "@/composables/editor";
import { debounce } from "lodash";
import CheckerPanel from "./CheckerPanel.vue";
import { useHotkey } from "vuetify";
import { useI18n } from "vue-i18n";
import { codeService, configService, fileService } from "@/services";
// Phase 2A/B/2.3: 引入新的 composables
import { useAceEditor, useEditorTheme, useEditorClipboard, useEditorContextMenu, useEditorKeyboard, useEditorFormat, useEditorScreenshot } from "@/composables/editor";
const { t } = useI18n();

// Editor store
const editorStore = useEditorStore();
const { lang, content, enableCheckerPanel } = storeToRefs(editorStore);

const checkPanel: Ref<InstanceType<typeof CheckerPanel> | null> = ref(null);

const runJudgeKey = ref<string | undefined>();

useHotkey(runJudgeKey, async () => {
  checkPanel.value?.runAll();
});

const modeMP: Map<string, new () => SyntaxMode> = new Map([
  ["python", python],
  ["cpp", cpp],
  ["json", json],
]);

let editorOptions: Partial<Ace.EditorOptions> & { [key: string]: any };

// Phase 2A: 使用 composables 管理编辑器实例和主题
const { aceRef, editor, ready: editorReady, initEditor: initAceEditor, setValue, getValue, dispose: disposeEditor } = useAceEditor();
const { isDark, currentTheme, syncTheme } = useEditorTheme({ editor, autoWatch: true });
// Phase 2B: 使用 composables 管理剪贴板、右键菜单、键盘快捷键和格式化
const { cut, copy, copyAll, paste } = useEditorClipboard({ editor });
const { menuX, menuY, showMenu, onContextMenu, closeMenu } = useEditorContextMenu({ editor });
// Phase 2.1: 键盘快捷键和格式化
const keyboardShortcuts = ref({
  formatCode: { value: 'Ctrl-Shift-F' },
  runJudge: { value: 'F5' },
});
const { bindKeyboard, unbindKeyboard } = useEditorKeyboard({
  editor,
  keyboardShortcuts,
  onFormat: () => format((code) => resetCode(code)),
  onRunJudge: () => checkPanel.value?.runAll(),
  onCut: cut,
  onCopy: copy,
});
const { format } = useEditorFormat();
// Phase 2.3: 截图功能
const { takeScreenshot: takeCodeScreenshot, isCapturing: isScreenshotCapturing } = useEditorScreenshot({ editor, useVuetifyTheme: true });

// Phase 2.2: LSP 集成
const filePath = ref<string | undefined>(undefined);
const { isReady: lspReady, register: registerLsp, unregister: unregisterLsp } = useEditorLsp({
  editor,
  filePath,
  joinWorkspaceURI: true,
});

async function initEditor() {
  // Phase 2A: 首先使用 composable 初始化基础编辑器实例
  await initAceEditor();
  
  if (!editor.value) {
    console.warn("[EditorPage] Editor initialization failed");
    return;
  }

  const ed = editor.value;

  // Phase 2A: 使用 composable 同步主题
  syncTheme();

  const initialCode = await codeService.getCode();
  const langType = initialCode.type as import("@/stores/editor").EditorLang;
  editorStore.setLanguage(langType);
  editorStore.setContent(initialCode.code || ""); // Set initial code from backend

  // config
  const config = await configService.getConfig();
  console.log("Editor config:", config);
  for (const key in config.editor.aceMain)
    ed.setOption(
      key as keyof Ace.EditorOptions,
      config.editor.aceMain[key].value
    );
  if (config.programmingLanguages[initialCode.type])
    editorStore.setEnableCheckerPanel(
      config.programmingLanguages[initialCode.type].enableCheckerPanel ||
      false
    );
  // set line height
  ed.container.style.lineHeight = "2"; // todo: make configurable
  ed.renderer.updateFontSize();

  // editor.setKeyboardHandler("ace/keyboard/vscode");
  ed.on("change", (e) => {
    onCodeChange(ed.getValue());
  });

  const ModeConstructor = modeMP.get(initialCode.type);

  if (ModeConstructor) {
    ed.session.setMode(new ModeConstructor());
  } else {
    console.warn(
      `No mode found for type: ${initialCode.type}, using default mode.`
    );
    ed.session.setMode("ace/mode/text");
  }

  const keyboardCFG = config.keyboardShortcuts;
  runJudgeKey.value = keyboardCFG.runJudge.value as string;
  // Phase 2.1: 更新键盘快捷键配置并绑定
  keyboardShortcuts.value = keyboardCFG as {
    formatCode: { value: string };
    runJudge: { value: string };
  };
  bindKeyboard();

  // Phase 2.2: 设置文件路径并注册 LSP
  filePath.value = await fileService.getOpenedFile() || undefined;
  await registerLsp();
}

let lastModified = 0;
function onCodeChange(newCode: string) {
  debounce(codeService.saveCode, 500)(newCode);
  lastModified = performance.now();
}
onMounted(() => {
  initEditor();
});
onUnmounted(async () => {
  // Phase 2.2: 注销 LSP
  await unregisterLsp();
  // Phase 2.1: 解绑键盘快捷键
  unbindKeyboard();
  // Phase 2A: 使用 composable 的 dispose 方法
  disposeEditor();
  console.log("Editor unmounted and content cleared.");
});
window.addEventListener("file-changed", async (event) => {
  const text = (event as CustomEvent).detail;

  if (
    editor.value &&
    editor.value.getValue() &&
    text !== editor.value.getValue() &&
    performance.now() - lastModified > 1000
  ) {
    console.log("File changed externally, updating editor content.");

    resetCode(text);
  }
});
function resetCode(text: string) {
  if (!editor.value) return;
  // Phase 2A: 使用 composable 的 setValue（它会在内部保持光标位置）
  setValue(text, -1);
}

const menuList = [
  [
    {
      title: "runTest",
      action: () => {
        checkPanel.value?.runAll();
      },
    },
  ],
  [
    {
      title: "cut",
      action: cut,
    },
    {
      title: "copy",
      action: copy,
    },
    {
      title: "copyAll",
      action: copyAll,
    },
    {
      title: "paste",
      action: paste,
    },
  ],
  [
    { title: "formatCode", action: () => format((code) => resetCode(code)) },
    {
      title: "screenshot",
      action: takeCodeScreenshot,
    },
  ],
];
</script>
