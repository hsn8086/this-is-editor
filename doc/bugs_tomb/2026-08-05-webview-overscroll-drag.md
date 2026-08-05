# 2026-08-05 不可滚动区域被拖动时整体轻微位移

**状态**: 待解决

## 现象

- 在本机（macOS）运行时，对本不应该能拖动的界面区域按住拖拽，整个界面会跟着轻微位移。
- 松手后回弹归位，属于视觉抖动，不影响功能。
- 报告者判断"估计是浏览器特性"。

## 环境

- macOS，pywebview 6.2.1（WKWebView 内核）
- 尚未在 Linux (GTK WebKit) / Windows (EdgeChromium) 上确认是否复现

## 可能原因（**假设，未验证**）

- WKWebView 默认开启橡皮筋滚动（rubber-band / elastic overscroll）。
  即使内容没有溢出，在文档层拖拽仍会触发弹性位移，这是 macOS WebKit 的默认行为。
- 代码侧有两点与之吻合：
  - `src/App.vue:90-94` 给 `body` 设了 `overflow: overlay`，文档层保留了滚动上下文。
  - 全局没有任何 `overscroll-behavior` 声明；仓库里唯一一处
    (`src/styles/ace-theme.css:48` 的 `overscroll-behavior: contain`) 只作用于 Ace 编辑器内部元素，
    管不到 `html` / `body`。
- 因此文档级的弹性滚动没有被抑制。

## 待验证 / 可能的处理方向

1. 给 `html, body` 加 `overscroll-behavior: none`，确认位移是否消失。
   这是纯 CSS 改动，成本最低，应先试。
2. 若无效，可能是窗口层而非文档层的行为，需要看 pywebview / WKWebView 侧：
   例如 `window.gui` 的 bounce 设置，或 WKWebView 的 `scrollView.bounces`。
3. 确认三个平台的表现差异后再决定是全局改还是只在 macOS 生效。

## 复现步骤

1. 启动应用
2. 在没有滚动条、内容未溢出的区域按住并拖动
3. 观察界面整体是否轻微位移并回弹

## 备注

- 本条目仅为记录，尚未复现验证，也未尝试修复。
- 根因一栏是基于代码现状的推断，落实前需要先按"待验证"第 1 步确认。
