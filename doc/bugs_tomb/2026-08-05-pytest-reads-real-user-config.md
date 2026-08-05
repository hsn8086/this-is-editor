# 2026-08-05 pytest 读取开发者真实用户配置

## 现象

- 本机执行 `uv run pytest tests/backend` 时 `test_snippet_autocompletion_is_enabled_by_default` 失败。
- 报错：`AssertionError: assert False is True`，`ace_main.get("enableSnippets")` 得到 `False`。
- 同一份代码在 CI（全新容器）上通过，只有本机复现，属于"本地红、线上绿"。

## 环境

- macOS，用户配置位于 `~/Library/Application Support/this_is_editor/config.json`
- 该文件是启用 snippet 功能之前生成的旧配置，`enableSnippets` 仍为 `false`

## 根本原因

- `pysrc/user_data.py` 在导入时就解析平台目录，`pysrc/config.py:77-80` 紧接着执行
  `config = merge(cfg, json.loads(config_p.read_text()))`。
- `merge()` 是**原地修改**，直接把磁盘上的用户配置合并进 `config_meta.config` 这个模块级字典。
- 测试用例导入 `from pysrc.config_meta import config as default_config` 拿到的正是被污染的同一个对象，
  于是"默认配置"实际上等于"开发者本机配置"。
- 副作用不止读取：测试还会在开发者真实目录里创建 `config.json`。

## 处理

- 在根 `conftest.py` **模块级**（早于任何 `pysrc` 导入）设置 `TIE_DEV_USER_DATA_DIR` 指向临时目录，
  并用 `atexit` 清理。`pysrc.runtime` 已支持该环境变量作为隔离入口。
- 已显式设置该变量时不覆盖，保留开发者手动指定目录的能力。

## 复现步骤

1. 让 `~/Library/Application Support/this_is_editor/config.json` 中 `editor.aceMain.enableSnippets` 为 `false`
2. `uv run pytest tests/backend`
3. 修复前失败，修复后 169 项全部通过，且真实配置文件不再被读写

## 教训

- 导入期副作用 + 原地修改共享字典，会让测试结果依赖开发机状态。
- 测试套件必须与用户目录隔离；隔离动作要发生在被测模块导入之前，autouse fixture 太晚。
