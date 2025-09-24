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
import type { API } from "@/pywebview-defines";
import type { SyntaxMode } from "ace-code/src/ext/static_highlight";
import type { SessionLspConfig } from "ace-linters/build/ace-language-client";
import type { VAceEditorInstance } from "vue3-ace-editor/types";
import { ref, onMounted, onUnmounted, nextTick } from "vue";
import { VAceEditor } from "vue3-ace-editor";
import { Mode as python } from "ace-code/src/mode/python";
import { Mode as cpp } from "ace-code/src/mode/c_cpp";
import { Mode as json } from "ace-code/src/mode/json";
import "ace-builds/src-noconflict/mode-python";
import "ace-builds/src-noconflict/mode-c_cpp";
import event from "ace-code/src/lib/event";
import keyUtil from "ace-code/src/lib/keys";
import { Ace } from "ace-builds";
import "ace-builds/src-noconflict/ext-language_tools";
import { HashHandler } from "ace-code/src/keyboard/hash_handler";
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
const { t } = useI18n();

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

const py: API = window.pywebview.api;

const content = ref();
const lang = ref("text");
const enableCheckerPanel = ref(false);
let editorOptions: Partial<Ace.EditorOptions> & { [key: string]: any };

const theme = useTheme(); // useTheme must be called in setup
let editor: Ace.Editor | undefined;
const aceRef = ref<VAceEditorInstance>();
async function initEditor() {
  if (aceRef.value) {
    editor = aceRef.value.getAceInstance();
    if (theme.global.current.value.dark) editor.setTheme("ace/theme/tie");
    else editor.setTheme("ace/theme/tie-light");
    const initialCode = await py.get_code();
    lang.value = initialCode.type;
    content.value = initialCode.code || ""; // Set initial code from backend

    // config
    const config = await py.get_config();
    console.log("Editor config:", config);
    for (const key in config.editor.aceMain)
      editor.setOption(
        key as keyof Ace.EditorOptions,
        config.editor.aceMain[key].value
      );
    if (config.programmingLanguages[initialCode.type])
      enableCheckerPanel.value =
        config.programmingLanguages[initialCode.type].enableCheckerPanel ||
        false;
    // set line height
    editor.container.style.lineHeight = "2"; // todo: make configurable
    editor.renderer.updateFontSize();

    // editor.setKeyboardHandler("ace/keyboard/vscode");
    editor.on("change", (e) => {
      onCodeChange(editor!.getValue());
    });

    const ModeConstructor = modeMP.get(initialCode.type);

    if (ModeConstructor) {
      editor.session.setMode(new ModeConstructor());
    } else {
      console.warn(
        `No mode found for type: ${initialCode.type}, using default mode.`
      );
      editor.session.setMode("ace/mode/text");
    }

    const languageProvider = await getLanguageProvider();
    const keyboardCFG = config.keyboardShortcuts;
    runJudgeKey.value = keyboardCFG.runJudge.value as string;
    let menuKb = new HashHandler([
      {
        bindKey: keyboardCFG.formatCode.value as string,
        name: "format", //todo: fix it
        exec: function () {
          console.log("Format command triggered");
          // languageProvider.format();
          format();
        },
      },
      {
        bindKey: "Ctrl-X",
        name: "cut",
        exec: cut,
      },
      {
        bindKey: "Ctrl-C",
        name: "copy",
        exec: copy,
      },
      {
        bindKey: keyboardCFG.runJudge.value as string,
        name: "runJudge",
        exec: function () {
          checkPanel.value?.runAll();
        },
      }, // todo
    ]);
    editor.setKeyboardHandler(menuKb);
    // event.addCommandKeyListener(window, function (e, hashId, keyCode) {
    //   console.log("Key pressed:", hashId, keyCode);
    //   let keyString = keyUtil.keyCodeToString(keyCode);
    //   let command = menuKb.findKeyCommand(hashId, keyString);
    //   if (command) {
    //     command.exec!();
    //     e.preventDefault();
    //   }
    // });

    const sessionConfig: SessionLspConfig = {
      filePath: (await py.get_opened_file())!,
      joinWorkspaceURI: true,
    };
    languageProvider.registerEditor(editor, sessionConfig);
  }
}

async function format() {
  const config = await py.get_config();
  const codeType = (await py.get_code()).type;
  if (!config.programmingLanguages[codeType]) return;
  const formater_cfg = config.programmingLanguages[codeType].formatter;
  if (!formater_cfg) return;
  if (!formater_cfg.active.value) return;

  const formatted = await py.format_code();
  if (formater_cfg.action.value === "reload") {
    // reload the file from disk
    const text = (await py.get_code()).code;
    resetCode(text);
    return;
  } else if (formater_cfg.action.value === "stdout") resetCode(formatted);
}

let lastModified = 0;
function onCodeChange(newCode: string) {
  debounce(py.save_code, 500)(newCode);
  lastModified = performance.now();
}
onMounted(() => {
  initEditor();
});
onUnmounted(async () => {
  if (editor === undefined) return;
  const languageProvider = await getLanguageProvider();
  languageProvider.closeDocument(editor.getSession());
  editor.session.setValue(""); // Clear the editor content on unmount
  console.log("Editor unmounted and content cleared.");
});
window.addEventListener("file-changed", async (event) => {
  const text = (event as CustomEvent).detail;

  if (
    editor &&
    editor.getValue() &&
    text !== editor.getValue() &&
    performance.now() - lastModified > 1000
  ) {
    console.log("File changed externally, updating editor content.");

    resetCode(text);
  }
});
function resetCode(text: any) {
  if (!editor) return;
  const cursorPos = editor.getCursorPosition();
  editor.setValue(text, -1); // -1 to prevent moving cursor to start

  // ensure the column is within the line length
  const lineLen = editor.session.getLine(cursorPos.row)?.length ?? 0;
  const safeColumn = Math.min(cursorPos.column, lineLen);

  editor.moveCursorToPosition({ row: cursorPos.row, column: safeColumn });
  editor.scrollToLine(cursorPos.row, true, true, function () {});
}

function cut() {
  if (!editor) return;
  let content;
  if ((content = window.getSelection()?.toString())) {
    navigator.clipboard.writeText(content);
    editor.session.remove(editor.getSelectionRange());
  } else {
    const p = editor.getCursorPosition();
    if ((content = editor.session.getLine(p?.row || 0))) {
      navigator.clipboard.writeText(content.trim());
      editor.session.removeFullLines(p?.row || 0, p?.row || 0);
      editor.moveCursorTo(p?.row || 0, 0);
    }
  }
}
function copy() {
  if (!editor) return;
  let content;
  if ((content = window.getSelection()?.toString())) {
    navigator.clipboard.writeText(content);
  } else {
    const p = editor.getCursorPosition();
    if ((content = editor.session.getLine(p?.row || 0))) {
      navigator.clipboard.writeText(content.trim());
    }
  }
}

async function takeCodeScreenshot() {
  if (!editor) return;
  try {
    const text = editor.getSelectedText() || editor.getValue();
    const lines = text.split("\n");

    const cs = getComputedStyle(editor.container);
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
      title: "paste",
      action: async () => {
        editor?.insert(await navigator.clipboard.readText());
      },
    },
  ],
  [
    { title: "formatCode", action: format },
    {
      title: "screenshot",
      action: takeCodeScreenshot,
    },
  ],
];

const menuX = ref(0);
const menuY = ref(0);
const showMenu = ref(false);
function onContextMenu(e: MouseEvent) {
  if (!editor) return;

  e.preventDefault();
  menuX.value = e.clientX;
  menuY.value = e.clientY;
  showMenu.value = true;
}
</script>
