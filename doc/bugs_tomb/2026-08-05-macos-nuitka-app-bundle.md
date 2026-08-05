# 2026-08-05 macOS 上 Nuitka 打包失败

## 现象

- 本机执行 `uv run tools/builder.py --mode dir` 失败。
- 报错：`FATAL: options-nanny: Error, package 'Foundation' requires '--mode=app' to be used or else it cannot work.`
- 约 2 分钟后在依赖扫描阶段中止，不产出任何二进制。

## 环境

- macOS 26.4.1 (arm64)，clang 21.0.0
- Nuitka 2.7.12，Python 3.12.13
- pywebview 6.2.1

## 根本原因

- macOS 上 pywebview 通过 PyObjC 绑定 `Foundation` / `AppKit` / `WebKit` 等系统框架。
- Nuitka 的 options-nanny 规定这些 PyObjC 包只能打进 **app bundle**，
  普通 `--standalone` / `--onefile` 布局无法工作。
- `tools/builder.py` 只区分 Windows 与其它平台，没有 Darwin 分支，因此本机永远构建不出产物。
- CI 只跑 ubuntu-latest 与 windows-latest，问题被长期掩盖。

## 处理

- `tools/builder.py` 增加 Darwin 分支，追加 `--macos-create-app-bundle`。
- macOS 上 onefile 与 app bundle 互斥（`--mode=app` 文档："App is onefile except on macOS"），
  故 Darwin 分支改用 `elif`，跳过 `--onefile`。
- Windows / Linux 的参数组合保持不变，不影响现有发布产物。
- 新增 `test_build_command_creates_macos_app_bundle` 与 `test_build_command_omits_app_bundle_off_macos` 覆盖两条分支。

## 复现步骤

1. 在 macOS 上 `uv run tools/builder.py --mode dir`
2. 修复前在 options-nanny 阶段 FATAL
3. 修复后约 8 分钟产出 `.dist/main.app/Contents/MacOS/main`，
   且 `AppKit`/`Foundation`/`WebKit` 与 `web/` 静态资源均已打包

## 教训

- 构建脚本的平台分支要覆盖全部目标平台，否则"只在 CI 构建"会让本机开发链路悄悄失效。
- 打包器的平台专属约束（如 PyObjC 必须 app bundle）应在脚本里固化并加测试，而不是靠人记住。
