# 2026-08-05 打包产物启动即闪退：PEP 695 泛型

## 现象

- `.dist/main.app` 双击无反应 / 直接运行立刻退出，窗口一闪而过。
- 直接跑二进制才看到 traceback：

```
File ".../pysrc/runner.py", line 61, in <module pysrc.runner>
NameError: name 'T' is not defined
```

- `uv run main.py` 一切正常，**只有打包后才崩**。

## 环境

- Nuitka 2.7.12，Python 3.12.13，macOS arm64
- 与平台无关：属于 Nuitka 代码生成问题

## 根本原因

- `pysrc/runner.py` 使用了 PEP 695 泛型函数语法：

```python
def try_r[T](func: Callable[..., T], *args: object, default: T | None = None) -> T | None:
```

- 该语法要求解释器为类型参数建立独立的**注解作用域**。文件没有 `from __future__ import annotations`，
  因此 `T | None` 在 `def` 执行时就要求值，需要 `T` 在该作用域内可见。
- Nuitka 2.7.12 未实现这个作用域，编译后 `T` 无绑定，导入 `pysrc.runner` 即 `NameError`。
- 该模块在启动链路上：`main.py` → `pysrc.web` → `pysrc.js_api` → `pysrc.langs` → `pysrc.runner`，
  所以是启动即死。

## 引入路径（值得注意）

- 由 `f686da0 fix(python): resolve ruff lint issues`（2026-04-08）引入。
- ruff 的 `UP047`（non-pep695-generic-function）建议把经典 `TypeVar` 改写成 PEP 695 语法，
  改完源码和测试全绿，**没有任何检查会跑打包产物**，于是坏掉的构建一路发布出去。

## 处理

- `pysrc/runner.py` 改回经典 `T = TypeVar("T")`。
- `pyproject.toml` 全局 ignore `UP047`，并写明原因，避免以后又被"修"回去。
- 新增 `tests/backend/unit/test_nuitka_compat.py`：用 AST 扫描 `pysrc/`、`tools/` 下所有模块，
  发现 `FunctionDef/AsyncFunctionDef/ClassDef` 带 `type_params` 就失败。

## 复现步骤

1. `uv run tools/builder.py --mode dir`
2. `.dist/main.app/Contents/MacOS/main`
3. 修复前立即 `NameError` 退出；修复后正常启动并提供 Web 服务

## 教训

- **源码测试全绿 ≠ 产物可用。** 这个 bug 从 4 月潜伏到 8 月，就是因为 CI 只构建、从不启动产物。
- lint 工具的"现代化"建议会引入打包器不支持的语法；打包器支持度必须纳入考量。
- 建议后续在 CI 增加冒烟步骤：构建后真正启动产物，确认能起服务再发布。
