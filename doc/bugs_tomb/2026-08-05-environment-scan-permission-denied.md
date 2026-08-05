# 2026-08-05 环境扫描被 SIP 保护文件中断

## 现象

- 修好启动闪退后，app 能起来，但前端调用 `scan_environment` 报错：

```
File ".../pysrc/environment.py", line 196, in <genexpr>
File ".../pathlib.py", line 840, in stat
PermissionError: [Errno 13] Permission denied: '/usr/sbin/weakpass_edit'
```

- 后果：环境检测页拿不到任何工具，整次扫描直接中断。

## 环境

- macOS（SIP 开启），`/usr/sbin` 在 PATH 中
- `/usr/sbin/weakpass_edit` 等系统二进制对普通用户 `stat()` 返回 EACCES

## 根本原因

- `_path_executables()` 遍历 PATH 目录时，只给 `Path(directory).iterdir()` 套了 `try/except OSError`。
- 真正抛错的是生成器里的 `entry.is_file()`，不在保护范围内。
- 关键点：`Path.is_file()` **并非吞掉所有 OSError**。CPython 的 `_ignore_error()` 只忽略
  `ENOENT / ENOTDIR / EBADF / ELOOP`，`EACCES` 会照常抛出。
- 于是 PATH 里只要有一个不可 stat 的文件，整个 `scan_environment` 就崩了。

## 处理

- 新增 `_is_file()` helper，捕获 `OSError` 并返回 `False`。
- `_path_executables()` 的目录遍历与 `_find_executables()` 里对已配置绝对路径的判断都改用该 helper。
- 新增 `test_scan_survives_unreadable_path_entry`：mock `Path.is_file` 对特定文件抛 `PermissionError`，
  断言扫描仍能正常返回其它工具。已确认该测试在修复前会复现同样的报错。

## 复现步骤

1. macOS 上保证 PATH 含 `/usr/sbin`
2. 启动产物并触发环境扫描
3. 修复前 traceback 中断，修复后正常返回

## 教训

- `Path.is_file()` / `exists()` 只对"不存在"类错误安全，权限错误照抛；在遍历不可控目录时必须自己兜。
- `try/except` 要覆盖到真正求值的位置——生成器表达式是惰性的，异常在 `extend()` 消费时才抛，
  很容易漏出原本以为已保护的代码块。
