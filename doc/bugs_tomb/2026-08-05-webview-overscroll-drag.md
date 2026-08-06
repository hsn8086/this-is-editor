# 2026-08-05 不可滚动区域被拖动时整体轻微位移

**状态**: 已修复（等待报告者在真机确认视觉表现）

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

## 处理

- 在 `src/App.vue` 的全局样式里给 `html, body` 加 `overscroll-behavior: none`，
  在文档层关掉橡皮筋滚动。

**刻意只改文档层**：一开始顺手加了 `html, body, #app { height: 100%; overflow: hidden }`，
随后撤掉了——许可证页要渲染 400 多张卡片，设置页、环境页也都是长页面，
锁死 body 溢出很可能把它们的滚动搞坏。面板内部的 `.scroll-container` 同样不受影响。

## 验证程度（重要）

- 已确认规则进入构建产物：`web/assets/index-*.css` 中存在 `html,body{overscroll-behavior:none}`。
- **没有验证视觉症状是否真的消失**——拖拽回弹属于交互表现，无法用命令行断言。
- 因此根因一栏仍是推断。若真机上仍有位移，说明不是文档层的橡皮筋滚动，
  下一步应查窗口层：pywebview / WKWebView 的 `scrollView.bounces`。
- 也尚未确认 Linux (GTK WebKit) / Windows (EdgeChromium) 上是否存在同样现象；
  该属性在这两个内核上是安全的空操作或同义行为，不会引入回归。

## 复现步骤

1. 启动应用
2. 在没有滚动条、内容未溢出的区域按住并拖动
3. 观察界面整体是否轻微位移并回弹

## 备注

- 本条目仅为记录，尚未复现验证，也未尝试修复。
- 根因一栏是基于代码现状的推断，落实前需要先按"待验证"第 1 步确认。
