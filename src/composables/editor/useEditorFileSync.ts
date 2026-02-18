import { debounce, type DebouncedFunc } from "lodash";
import { ref, onMounted, onUnmounted, type Ref } from "vue";

/**
 * useEditorFileSync 选项
 */
export interface UseEditorFileSyncOptions {
  /** 保存代码的函数 */
  saveCode: (code: string) => Promise<void> | void;
  /** 设置编辑器内容的函数（用于 resetCode，保持光标位置） */
  setValue: (value: string, cursorPos?: number) => void;
  /** 获取编辑器内容的函数 */
  getValue: () => string;
  /** 自动保存 debounce 时间（默认 500ms） */
  debounceMs?: number;
  /** 外部变更冷却时间（默认 1000ms） */
  cooldownMs?: number;
  /** 编辑器就绪状态 */
  editorReady?: Ref<boolean>;
}

/**
 * useEditorFileSync 返回值
 */
export interface UseEditorFileSyncReturn {
  /** 最后修改时间戳 */
  lastModified: Ref<number>;
  /** 代码变更处理函数 */
  onCodeChange: DebouncedFunc<(newCode: string) => void>;
  /** 外部文件变更处理函数 */
  handleExternalChange: (text: string) => boolean;
  /** 重置代码到编辑器（保持光标位置） */
  resetCode: (text: string) => void;
  /** 是否正在冷却中（距离上次修改 < cooldownMs） */
  isInCooldown: () => boolean;
  /** 内容是否相同 */
  isContentEqual: (text: string) => boolean;
}

/**
 * 编辑器文件同步与自动保存
 *
 * 功能：
 * 1. 自动保存：代码变更后 debounce 保存（默认 500ms）
 * 2. 外部变更监听：监听 file-changed 事件，在冷却期外且内容不同时更新编辑器
 * 3. 冷却机制：距离上次修改超过 cooldownMs 才响应外部变更（避免冲突）
 * 4. 光标保持：resetCode 使用 setValue(text, -1) 保持光标位置
 *
 * @example
 * ```ts
 * const { onCodeChange, handleExternalChange, resetCode } = useEditorFileSync({
 *   saveCode: codeService.saveCode,
 *   setValue: (value, cursorPos) => editor.setValue(value, cursorPos),
 *   getValue: () => editor.getValue(),
 *   debounceMs: 500,
 *   cooldownMs: 1000,
 * });
 *
 * // 绑定到编辑器 change 事件
 * editor.on('change', () => onCodeChange(editor.getValue()));
 *
 * // 监听外部文件变更
 * window.addEventListener('file-changed', (e) => {
 *   handleExternalChange((e as CustomEvent).detail);
 * });
 * ```
 */
export function useEditorFileSync(
  options: UseEditorFileSyncOptions
): UseEditorFileSyncReturn {
  const {
    saveCode,
    setValue,
    getValue,
    debounceMs = 500,
    cooldownMs = 1000,
    editorReady = ref(true),
  } = options;

  // 最后修改时间戳（在输入变更时立即更新）
  const lastModified = ref(0);

  /**
   * 内部防抖保存函数（只负责保存，不更新 lastModified）
   */
  const debouncedSave = debounce(async (newCode: string) => {
    await saveCode(newCode);
  }, debounceMs);

  /**
   * 代码变更处理函数
   * 立即更新 lastModified，防抖只用于保存操作
   */
  const onCodeChange = Object.assign(
    (newCode: string): ReturnType<typeof debouncedSave> => {
      lastModified.value = performance.now();
      return debouncedSave(newCode);
    },
    {
      cancel: debouncedSave.cancel,
      flush: debouncedSave.flush,
    }
  ) as DebouncedFunc<(newCode: string) => void>;

  /**
   * 检查是否处于冷却期
   */
  const isInCooldown = (): boolean => {
    return performance.now() - lastModified.value < cooldownMs;
  };

  /**
   * 检查内容与当前编辑器内容是否相同
   */
  const isContentEqual = (text: string): boolean => {
    return text === getValue();
  };

  /**
   * 处理外部文件变更
   * @returns 是否实际更新了编辑器内容
   */
  const handleExternalChange = (text: string): boolean => {
    // 检查编辑器就绪
    if (!editorReady.value) {
      return false;
    }

    // 检查内容是否相同
    if (isContentEqual(text)) {
      return false;
    }

    // 检查是否处于冷却期
    if (isInCooldown()) {
      return false;
    }

    // 更新编辑器内容
    resetCode(text);
    return true;
  };

  /**
   * 重置编辑器代码（保持光标位置）
   * 通过 setValue 调用，确保光标一致性
   */
  const resetCode = (text: string): void => {
    // 使用 -1 作为 cursorPos 参数保持光标位置
    setValue(text, -1);
  };

  return {
    lastModified,
    onCodeChange,
    handleExternalChange,
    resetCode,
    isInCooldown,
    isContentEqual,
  };
}

/**
 * useEditorFileSyncWithListener - 包含事件监听的高级版本
 *
 * 自动管理 file-changed 事件监听器的注册和清理
 */
export interface UseEditorFileSyncWithListenerOptions
  extends UseEditorFileSyncOptions {
  /** 事件目标（默认 window） */
  eventTarget?: EventTarget;
  /** 外部变更事件名称（默认 'file-changed'） */
  eventName?: string;
  /** 变更处理回调 */
  onExternalChange?: (text: string, applied: boolean) => void;
}

export interface UseEditorFileSyncWithListenerReturn
  extends UseEditorFileSyncReturn {
  /** 手动注册监听器 */
  registerListener: () => void;
  /** 手动注销监听器 */
  unregisterListener: () => void;
}

/**
 * 带自动事件监听的文件同步 composable
 *
 * 自动处理 onMounted/onUnmounted 注册和清理事件监听器
 */
export function useEditorFileSyncWithListener(
  options: UseEditorFileSyncWithListenerOptions
): UseEditorFileSyncWithListenerReturn {
  const {
    onExternalChange,
    eventTarget = window,
    eventName = "file-changed",
    ...baseOptions
  } = options;

  const base = useEditorFileSync(baseOptions);
  let listener: ((event: Event) => void) | null = null;

  const createListener = (): ((event: Event) => void) => {
    return (event: Event) => {
      const text = (event as CustomEvent).detail;
      const applied = base.handleExternalChange(text);
      onExternalChange?.(text, applied);
    };
  };

  const registerListener = (): void => {
    if (listener) return; // 已注册
    listener = createListener();
    eventTarget.addEventListener(eventName, listener);
  };

  const unregisterListener = (): void => {
    if (listener) {
      eventTarget.removeEventListener(eventName, listener);
      listener = null;
    }
  };

  // 自动生命周期管理
  onMounted(() => {
    registerListener();
  });

  onUnmounted(() => {
    unregisterListener();
  });

  return {
    ...base,
    registerListener,
    unregisterListener,
  };
}

export default useEditorFileSync;
