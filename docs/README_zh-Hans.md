# 🌟 TIE - This Is Editor

TIE 是 "This Is Editor" 的缩写，是一个基于 **Python** 和 **Vue.js** 的跨平台竞赛代码编辑器，专为程序设计竞赛打造，提供高效、易用的代码编辑环境。

---

## ✨ 主要特性
- **🌍 跨平台支持**：兼容 **Windows** 和 **Linux** 操作系统。
- **🌐 多语言支持**：支持 **Python**、**C++** 等多种编程语言。
- **🖥️ 现代化界面**：采用 **Vue.js** 构建，提供直观、简洁的用户界面。
- **⚡ 评测系统集成**：内置评测系统，方便进行代码测试和评测，支持同时检测代码的 **时间** 和 **空间** 占用。
- **📂 快速载入测试数据**：通过集成 `Competitive Companion` 插件，支持直接导入测试数据，兼容 `CPH` 数据格式；同时支持从剪贴板导入测试数据，自动填充至第一个空位或拉取完整题面，提升操作效率。
- **🔍 代码补全与错误提示**：集成语言服务器协议（LSP），提供智能代码补全和实时错误提示。
- **🛠️ 高度可配置**：支持自定义编译和运行命令，满足不同竞赛需求。

---

## 🚧 未来计划
- SPJ 支持
- 更多语言支持
- 配置界面优化
- 格式化支持
- 快速创建文件
- 代码模板/代码片段
- 比赛模式
- 题面时空限制修改
- 代码生图
- 一键复制代码
- i18n
- gdb

___

## 📥 下载与使用
1. 请在 [此处](https://github.com/hsn8086/this-is-editor/releases/latest) 下载最新版本的 TIE。
2. 安装 **Python** 和 **C++** 环境。
3. 可选安装：
   - **`python-lsp-server`**：提升 Python 代码补全和错误提示体验。
   - **`clangd`**：提升 C++ 代码补全和错误提示体验。
   - **`Competitive Companion`** 浏览器插件：快速载入测试数据。

💡 **推荐字体**：为了获得更好的代码显示效果，建议使用 [Maple Mono](https://pangocdn.com/mononoki/) 字体。

---

## ⚙️ 编译
1. 克隆本仓库：
   ```bash
   git clone https://github.com/hsn8086/this-is-editor.git
   ```
2. 进入项目目录：
   ```bash
   cd this-is-editor
   ```
3. 安装依赖：
   ```bash
   uv sync && yarn install
   ```
4. 编译：
   ```bash
   yarn build
   ```

---

## 📜 License
本项目采用 **MIT 许可证**，详见 [LICENSE](./LICENSE) 文件。

---
🚀 **TIE**，让你的竞赛代码编辑体验更上一层楼！