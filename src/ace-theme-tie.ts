import ace from 'ace-builds/src-noconflict/ace'
import gruvboxCss from '@/styles/ace-theme-gruvbox.css?raw'
import customCssText from '@/styles/ace-theme.css?raw'

const darkCssText = gruvboxCss + customCssText

ace.define('ace/theme/tie', ['require', 'exports', 'module', 'ace/lib/dom'], function (require: any, exports: any, module: any) {
  exports.isDark = true
  exports.cssClass = 'ace-tie'
  exports.cssText = darkCssText
  const dom = require('../lib/dom')
  dom.importCssString(exports.cssText, exports.cssClass)
})
