export interface Code {
    code: string;
    type: string;
    alias: string[];
}

export interface Lang {
    id: string;
    display: string;
    lsp: string[];
    suffix: string[];
    alias: string[];
}
export interface FileInfo {
    name: string;
    stem: string;
    path: string;
    is_dir: boolean;
    is_file: boolean;
    is_symlink: boolean;
    size: number;
    last_modified: string;
    type: string;
}
export interface FuncResponse_ls_dir {
    now_path: string;
    files: FileInfo[];
}
export interface Response {
    status: 'success' | 'error' | 'warning';
    message: string;
    data?: any;
}

export interface ConfigItem {
    display: string;
    value: string | boolean | number;
    i18n: string;
    enum?: string[]; // for select options
}

export interface Config {
    editor: {
        aceMain: {
            fontSize: ConfigItem;
            fontFamily: ConfigItem;
            enableBasicAutocompletion: ConfigItem;
            enableSnippets: ConfigItem;
            enableLiveAutocompletion: ConfigItem;
            animatedScroll: ConfigItem;
            scrollPastEnd: ConfigItem;
            showPrintMargin: ConfigItem;
            fixedWidthGutter: ConfigItem;
            fadeFoldWidgets: ConfigItem;
            displayIndentGuides: ConfigItem;
            highlightIndentGuides: ConfigItem;
            highlightGutterLine: ConfigItem;
            highlightActiveLine: ConfigItem;
            highlightSelectedWord: ConfigItem;
            cursorStyle: ConfigItem;
            tabSize: ConfigItem;
            tooltipFollowsMouse: ConfigItem;
            foldStyle: ConfigItem;
        } & { [key: string]: any },
        tie: {
            theme: ConfigItem;
            language: ConfigItem;
        } & { [key: string]: any },

    };
    programmingLanguages: {
        [key: string]: {
            executable?: ConfigItem;
            compileCommand?: ConfigItem;
            runCommand?: ConfigItem;
            fileExtensions: ConfigItem;
            alias: ConfigItem;
            display: string;
            enableCheckerPanel?: boolean;
            lsp?: {
                command: ConfigItem;
            } & { [key: string]: any };
            formatter?: {
                active: ConfigItem;
                command: ConfigItem;
                action: ConfigItem;
            } & { [key: string]: any };
        } & { [key: string]: any };
    };
    keyboardShortcuts: {
        runJudge: ConfigItem;
        formatCode: ConfigItem;
    } & { [key: string]: any };
}

export interface TestCase {
    name: string;
    tests: { id: number; input: string; answer: string }[];
    memoryLimit: number;
    timeLimit: number;
}
export interface TaskResult {
    result: string;
    status: string;
    time: number;
    memory: number;
}

export interface API {
    [x: string]: any;
    get_pinned_files: () => Promise<FileInfo[]>;
    add_pinned_file: (path: string) => Promise<void>;
    remove_pinned_file: (path: string) => Promise<void>;
    get_disks: () => Promise<FileInfo[]>;
    format_code: () => Promise<string>;
    focus: () => Promise<void>;
    save_scoll: (scroll: number) => Promise<void>;
    get_scoll: () => Promise<number>;
    get_cpu_count: () => Promise<[number, number]>;
    compile: () => Promise<"success" | string>;
    run_task: (task_id: number, memory_limit?: number, timeout?: number) => Promise<TaskResult>;
    get_testcase: () => Promise<TestCase>;
    save_testcase: (testcase: TestCase) => Promise<void>;
    set_config: (id_str: string, value: string | boolean | number) => Promise<void>;
    get_config: () => Promise<Config>;
    get_config_path: () => Promise<string>;
    get_langs: () => Promise<Lang[]>;
    get_port: () => number;
    get_code: () => Promise<Code>;
    save_code: (code: string) => Promise<void>;
    set_cwd: (path: string) => Promise<void>;
    set_opened_file: (path: string) => Promise<void>;
    get_opened_file: () => Promise<string | null>;
    get_cwd: () => Promise<string>;
    path_to_uri: (path: string) => Promise<string>;
    path_ls: (path: string | null) => Promise<FuncResponse_ls_dir>;
    path_join: (path1: string, path2: string) => Promise<string>;
    path_parent: (path: string) => Promise<string>;
    path_get_info: (path: string) => Promise<FileInfo>;
    path_get_text: (path: string) => Promise<string>;
    path_save_text: (path: string, text: string) => Promise<void>;
    path_mkdir: (path: string) => Promise<Response>;
    path_touch: (path: string) => Promise<Response>;
};
//window.state.probQueue
declare global {
    interface Window {
        pywebview: {
            api: API
            state: {
                addEventListener: (name: string, func: (arg: any) => void) => void;
                prob: TestCase | null;
            }
        };
    }
}