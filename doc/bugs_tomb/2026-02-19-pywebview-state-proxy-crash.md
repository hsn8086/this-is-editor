# 2026-02-19 pywebview state Proxy crash

## 现象

- 启动 `uv run main.py --debug` 后，pywebview 注入脚本报错。
- 典型报错：`TypeError: (function () { ... return new Proxy(...) })() is not a function`。
- 随后出现一串 `Error while processing cwd._hash: 'PosixPath' object has no attribute '_hash'`。

## 环境

- Linux (GTK WebKit)
- pywebview 6.0

## 可能原因

- state.js 在 WebKit2 中被拼接为两段紧邻的 IIFE，导致 `IIFE() (IIFE())` 被解析为“把 IIFE 返回值当函数调用”。
- JS API 的对象反射遍历到 `Path` 之类不可序列化对象，触发 `pywebview.util.get_functions` 的错误日志。

## 处理

- 在后端 `window.state` 中注入 `_hash` 字段，并在 API 响应中返回 `_hash`，避免前端读取缺失字段。
- 保留日志用于后续定位 pywebview 注入链路。

## 复现步骤

1. `yarn dev`
2. 观察控制台日志与 `this_is_editor.log`
