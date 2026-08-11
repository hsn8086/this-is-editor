# 2026-08-11 编辑器菜单溢出、双层滚动与终端拖拽失效

**状态**: 已修复并用 Playwright 验证

## 现象

1. 在编辑器底部右键后，菜单向下超出窗口；只能拉页面最右侧滚动条，鼠标滚轮无法滚菜单。
2. 根滚动条旁出现一条黑色 gutter，即使页面没有实际溢出仍存在。
3. 呼出终端后，整个终端 drawer 可以滚动；xterm 自身又有一套滚动，形成双层滚动。
4. 终端分割线 hover 有颜色动画，拖动却完全不改变终端区域高度。

## 根本原因

### 右键菜单

- `EditorPage.vue` 把整块 Ace 放进 `VMenu` 的 activator slot，再传入 `absolute` 和手工 `left/top`。
- 当前 Vuetify 的 `VMenu` 在 `makeVMenuProps()` 中明确从 `VOverlay` props 里 **omit 了 `absolute`**，
  所以该参数不是有效定位 API。
- 菜单没有视口内最大高度，底部打开时会撑高 document；没有内部 overflow 时，滚轮自然无法滚菜单。

### 黑线

- 应用全局样式给 body 配了 `scrollbar-gutter: stable`。
- 更关键的是 Vuetify reset 固定写了 `html { overflow-y: scroll }`，无溢出时也永久保留根滚动条。
- Playwright 实测：viewport 800px 时 `documentElement.clientWidth` 只有 792px，右边永久少 8px。

### 终端双层滚动

- Vuetify 默认：`.v-navigation-drawer__content { overflow-y: auto }`。
- xterm 的 `.xterm-viewport` 本身也必须滚动，因此 drawer 和终端各有一层滚动。

### 拖拽无效

- `VNavigationDrawer` 只有 `width` prop，没有 `height` prop。
- 即使 `location="bottom"`，Vuetify 内部的 layout thickness 仍从 `props.width` 计算。
- 旧代码传 `:height="height"`；Vue 只把它当作无效 DOM attribute，Pinia 的值确实在变，
  但 Vuetify layout 尺寸从未改变，所以只看到把手动画。

## 处理

- 右键菜单改用 `target=[clientX, clientY]` + Vuetify connected location strategy，
  由框架在视口边缘翻转/位移；设 `max-height: calc(100dvh - 16px)`，滚动放到内部 `VList`。
- body 不再预留 stable gutter；覆盖 Vuetify 为 `html { overflow-y: auto }`，长页面仍按需滚动。
- 终端绑定 `:width="height"`，这是 Vuetify 对所有 drawer 方位统一使用的 layout size prop。
- drawer content 改为 flex column + `overflow:hidden`；只有 xterm viewport 保留滚动。
- 拖拽加入 pointer capture、pointercancel、多指针过滤、卸载清理，并至少给编辑器留 120px。

## 验证

Playwright，800x360：

- 底部 y=340 右键：菜单 `top=12, bottom=347`，未超出 360px 视口。
- 菜单 `clientHeight=335, scrollHeight=378`；滚轮后 `scrollTop 0 -> 43`，页面 `scrollY=0`。
- document `scrollHeight=clientHeight=360`，不会再被菜单撑高。
- 修复后 `documentElement.clientWidth=viewport width=800`，永久 8px gutter 消失。

Playwright，800x600：

- 终端 drawer content `overflow-y=hidden`，xterm viewport `overflow-y=scroll`。
- 分割线向上拖 100px：终端 `260 -> 360`，编辑器 `340 -> 240`。
- document `scrollHeight=clientHeight=600`，终端没有引入页面级滚动。

组件单测：`TerminalPanel.test.ts` 断言 top/bottom drawer 通过 `width` 接收 260px，
拖拽后实际 prop 更新为 360px，并覆盖 viewport 上限与指针状态清理。

## 教训

- 不能从视觉名词推断组件 prop：bottom drawer 的“高度”在 Vuetify API 里仍叫 `width`，
  应查组件实现或文档，而不是假设。
- 可滚动组件嵌套时必须明确唯一 scroll owner；xterm 已有 viewport，外层只能裁剪。
- overlay 应使用框架的 target/location strategy，不应把 viewport 坐标硬塞进普通 CSS 定位。
- 框架 reset 里的 `overflow-y: scroll` 会在桌面 WebView 中表现为永久 gutter，需要按应用语义覆盖。
