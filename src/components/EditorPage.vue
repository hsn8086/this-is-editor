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
import type { SessionLspConfig } from "ace-linters/build/ace-language-client";
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
import { useTheme } from "vuetify";
import { getLanguageProvider } from "@/lsp";
import { debounce } from "lodash";
import CheckerPanel from "./CheckerPanel.vue";
import { useHotkey } from "vuetify";
import { useI18n } from "vue-i18n";
import html2canvas from "html2canvas";
import hljs from "highlight.js";
import hljs_github_dark from "highlight.js/styles/github-dark.css?url";
import hljs_github_light from "highlight.js/styles/github.css?url";
import { codeService, configService, fileService } from "@/services";
// Phase 2A/B: 引入新的 composables
import { useAceEditor, useEditorTheme, useEditorClipboard, useEditorContextMenu, useEditorKeyboard, useEditorFormat } from "@/composables/editor";
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

const theme = useTheme(); // useTheme must be called in setup

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

  const languageProvider = await getLanguageProvider();
  const keyboardCFG = config.keyboardShortcuts;
  runJudgeKey.value = keyboardCFG.runJudge.value as string;
  // Phase 2.1: 更新键盘快捷键配置并绑定
  keyboardShortcuts.value = keyboardCFG as {
    formatCode: { value: string };
    runJudge: { value: string };
  };
  bindKeyboard();

  const sessionConfig: SessionLspConfig = {
    filePath: (await fileService.getOpenedFile())!,
    joinWorkspaceURI: true,
  };
  languageProvider.registerEditor(ed, sessionConfig);
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
  if (editor.value === undefined) return;
  const languageProvider = await getLanguageProvider();
  languageProvider.closeDocument(editor.value.getSession());
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

async function takeCodeScreenshot() {
  if (!editor.value) return;
  try {
    const text = editor.value.getSelectedText() || editor.value.getValue();
    const lines = text.split("\n");

    const cs = getComputedStyle(editor.value.container);
    const fontSize = cs.fontSize || "13px";
    const fontFamily = cs.fontFamily || "monospace";
    const background = cs.backgroundColor || "#fff";
    const color = cs.color || "#000";
    const lineHeight =
      cs.lineHeight && cs.lineHeight !== "normal" ? cs.lineHeight : "1.4";

    const wrapper = document.createElement("div");
    wrapper.style.position = "absolute";
    wrapper.style.left = "-9999px";
    wrapper.style.top = "0px";
    wrapper.style.background = background;
    wrapper.style.color = color;
    wrapper.style.display = "flex";
    wrapper.style.padding = "12px";
    wrapper.style.boxSizing = "border-box";
    wrapper.style.borderRadius = "4px";
    wrapper.style.fontSize = fontSize;
    wrapper.style.fontFamily = fontFamily;
    wrapper.style.lineHeight = lineHeight;

    const gutter = document.createElement("div");
    gutter.style.userSelect = "none";
    gutter.style.textAlign = "right";
    gutter.style.paddingRight = "12px";
    gutter.style.marginRight = "12px";
    gutter.style.opacity = "0.6";
    gutter.style.fontSize = fontSize;
    gutter.style.fontFamily = fontFamily;
    gutter.style.lineHeight = lineHeight;
    gutter.style.whiteSpace = "pre";
    gutter.textContent = lines.map((_, i) => (i + 1).toString()).join("\n");

    const code = document.createElement("pre");
    code.style.margin = "0";
    code.style.whiteSpace = "pre";
    code.style.fontFamily = fontFamily;
    code.style.fontSize = fontSize;
    code.style.lineHeight = lineHeight;
    code.style.background = "transparent";
    code.style.color = color;
    code.style.overflow = "visible";
    code.innerHTML = hljs.highlightAuto(text).value;

    const style = document.createElement("link");
    style.rel = "stylesheet";
    style.href = theme.global.current.value.dark
      ? hljs_github_dark
      : hljs_github_light;
    document.head.appendChild(style);
    wrapper.appendChild(gutter);
    wrapper.appendChild(code);
    document.body.appendChild(wrapper);

    const canvas = await html2canvas(wrapper, {
      backgroundColor: null,
      scale: 2,
    });

    document.body.removeChild(wrapper);
    document.head.removeChild(style);

    if (navigator.clipboard && (navigator.clipboard as any).write) {
      const blob: Blob | null = await new Promise((res) =>
        canvas.toBlob((b) => res(b), "image/png")
      );
      if (blob) {
        await (navigator.clipboard as any).write([
          new (window as any).ClipboardItem({ "image/png": blob }),
        ]);
        return;
      }
    }

    const url = canvas.toDataURL("image/png");
    const a = document.createElement("a");
    a.href = url;
    a.download = "code-screenshot.png";
    document.body.appendChild(a);
    a.click();
    a.remove();
  } catch (err) {
    console.error("Failed to take screenshot:", err);
  }
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
