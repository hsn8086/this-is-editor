# TIE 项目结构文档

> 目标：帮助贡献者快速定位模块与职责。修改或新增模块后，请同步更新本文件。

## 根目录概览

```
this-is-editor/
├── main.py                  # 应用入口：启动 FastAPI + pywebview 窗口
├── pyproject.toml           # Python 依赖/工具链配置（Ruff 等）
├── package.json             # 前端依赖与脚本
├── pytest.ini               # Pytest 配置
├── conftest.py              # Pytest 共享 fixtures
├── vitest.config.ts         # Vitest 配置
├── vitest.setup.ts          # Vitest 全局 setup
├── README.md                # 英文说明
├── docs/                    # 文档（含本文件）
├── doc/bugs_tomb/           # Bug 墓地（一个事件一个文件）
├── src/                     # 前端源码（Vue 3 + TS + Vuetify）
├── pysrc/                   # Python 后端源码
├── tools/                   # 构建脚本
├── tests/                   # 测试源码
│   ├── frontend/            # 前端测试
│   │   └── unit/            # 单元测试
│   └── backend/             # 后端测试
│       └── unit/            # 单元测试
├── public/                  # 静态资源（不经 Vite 处理）
├── web/                     # 前端构建产物（由 Vite 生成）
├── .opencode/               # AI 代理配置
├── .github/workflows/       # CI / Release
├── LICENSES/                # 第三方许可证清单（由 tools/gen_license.py 生成）
└── build/dist/main.*        # 构建中间产物与最终产物（由构建生成）
```

> 备注：`build/`、`dist/`、`.dist/`、`main.build/`、`main.dist/`、`main.onefile-build/`、`main.bin` 等为构建产物或中间文件，**不要手工编辑**。

---

## 前端：`src/`

技术栈：Vue 3 + TypeScript + Vuetify + Pinia + Vue Router + Ace Editor

| 路径 | 作用 |
| --- | --- |
| `src/main.ts` | 前端入口，初始化应用、插件、i18n | 
| `src/App.vue` | 根组件 | 
| `src/components/` | 主要功能组件：编辑器、评测、设置、许可证等 | 
| `src/pages/` | 路由页面（editor / setting / license 等） | 
| `src/router/` | 路由配置 | 
| `src/stores/` | Pinia 状态管理 | 
| `src/plugins/` | Vuetify / i18n 插件注册 | 
| `src/i18n/` | 国际化语言包 | 
| `src/styles/` | 全局样式与 Ace 主题样式 | 
| `src/services/` | 前端服务层：API 客户端与业务服务封装 | 
| `src/lsp.ts` | LSP 客户端集成 | 
| `src/pywebview-defines.ts` | 前端调用 pywebview API 的类型声明 | 
| `src/ace-theme-tie*.ts` | Ace 主题定制 | 

**服务层 `src/services/`**

前端 API 调用的封装层，统一管理 pywebview 交互：

| 路径 | 作用 |
| --- | --- |
| `base/api-client.ts` | 统一 API 客户端，封装 pywebview 调用，支持缓存 |
| `base/error-handler.ts` | API 错误类与统一错误处理 |
| `base/cache.ts` | 简单内存缓存实现 |
| `modules/config-service.ts` | 配置服务：获取/设置配置 |
| `modules/file-service.ts` | 文件服务：目录浏览、文件读写 |
| `modules/code-service.ts` | 代码服务：代码存取、格式化、语言列表 |
| `modules/task-service.ts` | 任务服务：编译、运行测试用例 |

**Composables `src/composables/`**

Vue 3 Composition API 的可复用逻辑封装（Phase 2A/B/2.1 新增）：

| 路径 | 作用 |
| --- | --- |
| `editor/useAceEditor.ts` | Ace Editor 实例管理：初始化、setValue/getValue、ready 状态 |
| `editor/useEditorTheme.ts` | 编辑器主题管理：监听 Vuetify 主题，同步 Ace 主题 |
| `editor/useEditorClipboard.ts` | 剪贴板操作：cut/copy/copyAll/paste |
| `editor/useEditorContextMenu.ts` | 右键菜单控制：菜单位置、显示状态 |
| `editor/useEditorKeyboard.ts` | 键盘快捷键管理：HashHandler 绑定/解绑（Phase 2.1） |
| `editor/useEditorFormat.ts` | 代码格式化：读取配置、执行 format action（Phase 2.1） |
| `editor/index.ts` | Composables 统一导出 |

**关键组件**

- `EditorPage.vue`：编辑器主界面（Ace + LSP）
- `CheckerPanel.vue`：评测/测试面板
- `FileSelPage.vue`：文件选择页
- `SettingPage.vue`：设置页
- `LicensesPage.vue`：许可证页

---

## 后端：`pysrc/`

技术栈：FastAPI + Uvicorn + pywebview + psutil

| 模块 | 作用 |
| --- | --- |
| `web.py` | FastAPI 服务：静态文件、LSP WebSocket 代理、问题接收（10043） | 
| `js_api.py` | pywebview JS API：文件/配置/测试用例/运行等 | 
| `runner.py` | 代码编译与运行、资源监控 | 
| `config.py` | 配置加载与合并 | 
| `config_meta.py` | 配置元数据 | 
| `langs.py` | 语言配置与命令映射 | 
| `judge.py` | 测试用例转换、输出校验 | 
| `models.py` | Pydantic 数据模型 | 
| `watch.py` | 文件变更监听 | 
| `user_data.py` | 用户数据目录管理 | 
| `utils.py` | 通用工具函数 | 

---

## 构建与工具：`tools/`

| 脚本 | 作用 |
| --- | --- |
| `builder.py` | Nuitka 构建脚本（onefile/dir、debug 组合） | 
| `gen_license.py` | 生成第三方许可证清单 | 

---

## 测试配置

| 文件 | 作用 |
| --- | --- |
| `pytest.ini` | Pytest 配置：测试路径、覆盖率、标记等 |
| `conftest.py` | Pytest 共享 fixtures |
| `vitest.config.ts` | Vitest 配置：测试环境、覆盖率等 |
| `vitest.setup.ts` | Vitest 全局 setup：mock window.pywebview、matchMedia、ResizeObserver |

### 测试目录结构

| 路径 | 作用 |
| --- | --- |
| `tests/frontend/unit/` | 前端单元测试（Vitest + Happy DOM） |
| `tests/backend/unit/` | 后端单元测试（Pytest） |

### 测试脚本

使用 `yarn` 或 `uv` 运行测试：

| 脚本 | 作用 |
| --- | --- |
| `yarn test` / `yarn test:run` | 运行前端测试 |
| `yarn test:coverage` | 运行前端测试并生成覆盖率报告 |
| `yarn test:ui` | 运行前端测试并打开 UI |
| `uv run pytest` | 运行后端测试 |
| `uv run pytest --cov` | 运行后端测试并生成覆盖率报告 |

---

## 其他重要目录

- `public/`：静态资源（如 favicon）
- `web/`：前端构建产物（Vite 输出）
- `docs/`：项目文档（README、结构文档等）
- `doc/bugs_tomb/`：Bug 墓地（一个事件一个文件）
- `.opencode/`：AI 代理配置
- `.github/workflows/`：CI / Release 配置

---

## 入口与关键配置

- `main.py`：应用启动入口（创建窗口、启动后端服务）
- `pyproject.toml`：Python 依赖、Ruff 规则、目标版本等
- `package.json`：前端依赖与脚本（`yarn dev/build` 等）

---

如新增模块或调整目录结构，请同步更新本文件，并在 AGENT.md 中注明。最后更新：2026-02-18。
