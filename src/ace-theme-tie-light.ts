import ace from 'ace-builds/src-noconflict/ace'
import githubCss from '@/styles/ace-theme-github.css?raw'

import customCssText from '@/styles/ace-theme.css?raw'

const lightCssText = githubCss.replace(/\.ace-github/g, '.ace-tie-light') + customCssText.replace(/\.ace-tie/g, '.ace-tie-light')
// console.log(lightCssText);
ace.define('ace/theme/tie-light', ['require', 'exports', 'module', 'ace/lib/dom'], function (require: any, exports: any, module: any) {
  exports.isDark = false
  exports.cssClass = 'ace-tie-light'
  exports.cssText = lightCssText
  const dom = require('../lib/dom')
  dom.importCssString(exports.cssText, exports.cssClass)
})
