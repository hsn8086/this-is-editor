en-US | [zh-Hans](./docs/README_zh-Hans.md)
# TIE
TIE stands for "This Is Editor," a cross-platform competitive programming code editor based on Python and Vue.js. It aims to provide an efficient and user-friendly coding environment for programming contests.

## Key Features
- **Cross-Platform Support**: Compatible with Windows and Linux operating systems.
- **Multi-Language Support**: Supports multiple programming languages such as Python and C++.
- **Modern Interface**: Built with Vue.js, offering an intuitive user interface.
- **Integrated Judging System**: Comes with a built-in judging system for code testing and evaluation.
- **Quick Test Data Loading**: Supports direct loading of test data from the `Competitive Companion` plugin, compatible with the `CPH` data format.

## Download and Usage
- Download the latest version of TIE [here](https://github.com/hsn8086/this-is-editor/releases/latest).
- Install `python` and `cpp` environments.
- Optionally, install `python-lsp-server` for better Python code completion and error hints.
- Optionally, install `clangd` for better C++ code completion and error hints.
- Optionally, install the `Competitive Companion` browser plugin for quick test data loading.

## Build
- Clone this repository: `git clone https://github.com/hsn8086/this-is-editor.git`
- Navigate to the project directory: `cd this-is-editor`
- Install dependencies: `uv sync && yarn install`
- Build: `yarn build-only && yarn build`

## License
- This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.