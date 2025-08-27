<template>
  <CheckerPanel ref="checkPanel" />
  <v-ace-editor
    ref="aceRef"
    v-model:value="content"
    theme="github"
    style="height: 100%"
    :readonly="false"
    :options="editorOptions"
    :lang="lang"
  />
</template>

<style scoped>
.evaluation-panel {
  /* padding: 0px; */
  height: 100vh; /* 确保面板高度与页面一致 */
  overflow-y: auto;
}
</style>

<script lang="ts" setup>
import type { API } from "@/pywebview-defines";
import type { SyntaxMode } from "ace-code/src/ext/static_highlight";
import type { SessionLspConfig } from "ace-linters/build/ace-language-client";
import type { VAceEditorInstance } from "vue3-ace-editor/types";
import { ref, onMounted, onUnmounted } from "vue";
import { VAceEditor } from "vue3-ace-editor";
import { Mode as python } from "ace-code/src/mode/python";
import { Mode as cpp } from "ace-code/src/mode/c_cpp";
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

const checkPanel: Ref<InstanceType<typeof CheckerPanel> | null> = ref(null);
useHotkey("f5", () => {
  checkPanel.value?.runAll();
});

const modeMP: Map<string, new () => SyntaxMode> = new Map([
  ["python", python],
  ["cpp", cpp],
]);

const py: API = window.pywebview.api;

const content = ref();
const lang = ref("text");

let editorOptions: Partial<Ace.EditorOptions> & { [key: string]: any }

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
    let menuKb = new HashHandler([
      {
        bindKey: "f10",
        name: "format", //todo: fix it
        exec: function () {
          console.log("Format command triggered");
          languageProvider.format();
        },
      },
      {
        bindKey: "f5",
        name: "runJudge",
        exec: function () {
          checkPanel.value?.runAll();
        },
      }, // todo
    ]);
    
    event.addCommandKeyListener(window, function (e, hashId, keyCode) {
      let keyString = keyUtil.keyCodeToString(keyCode);
      let command = menuKb.findKeyCommand(hashId, keyString);
      if (command) {
        command.exec!();
        e.preventDefault();
      }
    });

    const sessionConfig: SessionLspConfig = {
      filePath: (await py.get_opened_file())!,
      joinWorkspaceURI: true,
    };
    languageProvider.registerEditor(editor, sessionConfig);
  }
}

function onCodeChange(newCode: string) {
  debounce(py.save_code, 500)(newCode);
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
</script>
