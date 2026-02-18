# AGENT.md - AI 代理开发指南

> 本文档为 AI 代理提供项目开发规范。**必须写测试、遵循 Conventional Commits、完成后提交代码**。

---

## 项目概览

TIE 是跨平台竞赛代码编辑器，前端 Vue 3，后端 Python (FastAPI/pywebview)。

**请先阅读：**[docs/PROJECT_STRUCTURE.md](./docs/PROJECT_STRUCTURE.md)

---

## 开发流程（必须遵循）

1. **理解需求**
   - 需求模糊必须澄清
2. **实现代码**
   - 保持类型注解与四格缩进（Python）
3. **编写测试**
   - 新功能 / 修复必须有测试（可 mock）
4. **运行检查**
   - Python：`uvx ruff format`、`uvx ruff check`、`uvx ty check`、`uv run pytest`
   - 前端：`yarn type-check`、`yarn lint`
5. **更新文档**
   - 结构变化须同步更新 `docs/PROJECT_STRUCTURE.md`
6. **提交代码**
   - 必须执行 git commit（Conventional Commits）

---

## 测试强制要求

- **每个修复或新增功能必须有测试**
- 允许 mock 外部依赖
- 若无法测试需说明原因并记录在提交信息中

---

## Git 提交规范

必须遵循 **Conventional Commits**：

```
<type>(<scope>): <description>
```

常用 type：

- `feat` 新功能
- `fix` 修复
- `docs` 文档
- `test` 测试
- `refactor` 重构
- `chore` 构建/工具

**示例：**

```
feat(editor): 添加自动补全
fix(runner): 修复超时检测
docs: 更新项目结构文档
```

---

## 完成后必须提交

所有代码变更完成后 **必须执行 git commit**。

---

## Bug 墓地规则（必须遵循）

- 位置：`doc/bugs_tomb/`
- **一事件一文件**
- 文件名：`YYYY-MM-DD-简短描述.md`

### 模板

```markdown
# [问题标题]

**日期**: YYYY-MM-DD
**发现者**:
**解决者**:
**状态**: 已解决 / 待解决 / 无法复现

---

## 问题描述

## 复现步骤

## 预期行为

## 实际行为

## 根本原因

## 解决方案

## 相关文件

## 教训总结

## 相关链接
```

**AGENT 必须在修改代码时关注 Bug 墓地的更新。**

---

最后更新：2026-02-18
