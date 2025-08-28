# TIE
TIE来自"This Is Editor"的缩写，是一个基于Python和Vue.js的跨平台竞赛代码编辑器，旨在为程序设计竞赛提供一个高效、易用的代码编辑环境。
## 主要特性
- **跨平台支持**：兼容Windows和Linux操作系统。
- **多语言支持**：支持Python、C++等多种编程语言。
- **现代化界面**：采用Vue.js构建，提供直观的用户界面。
- **评测系统集成**：内置评测系统，方便进行代码测试和评测。
- **快速载入测试数据**：支持从`Competitive Companion`插件直接载入测试数据，兼容`CPH`数据格式。

## 下载与使用
- 请在[此处](https://github.com/hsn8086/this-is-editor/releases/latest)下载最新版本的TIE。
- 安装`python`与`cpp`环境。
- 可选安装`python-lsp-server`以获得更好的Python代码补全和错误提示。
- 可选安装`clangd`以获得更好的C++代码补全和错误提示。
- 可选安装`Competitive Companion`浏览器插件以便快速载入测试数据。

## 编译
- 克隆本仓库：`git clone https://github.com/hsn8086/this-is-editor.git`
- 进入项目目录：`cd this-is-editor`
- 安装依赖：`uv sync && yarn install`
- 编译：`yarn build-only && yarn build`

## License
- 本项目采用MIT许可证，详见[LICENSE](./LICENSE)文件。