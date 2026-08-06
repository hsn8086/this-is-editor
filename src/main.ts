/**
 * main.ts
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

// Plugins

// Composables
import { createApp } from 'vue'

import { registerPlugins } from '@/plugins'

// Components
import App from './App.vue'

// Styles
import 'unfonts.css'

function disableSpellcheck (): void {
  document.body.setAttribute('spellcheck', 'false')
  for (const element of document
    .querySelectorAll<HTMLInputElement | HTMLTextAreaElement>('input, textarea')) {
    element.spellcheck = false
  }
}

function init () {
  const app = createApp(App)
  registerPlugins(app)
  app.mount('#app')
  disableSpellcheck()
}

if (window.pywebview && window.pywebview.api) {
  init()
} else {
  window.addEventListener('pywebviewready', () => {
    init()
  })
}
