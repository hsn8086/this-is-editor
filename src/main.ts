/**
 * main.ts
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

// Plugins

import { registerPlugins } from '@/plugins'

// Components
import App from './App.vue'

// Composables
import { createApp } from 'vue'

// Styles
import 'unfonts.css'

function init() {
    const app = createApp(App)
    registerPlugins(app)
    app.mount('#app')
}

if (window.pywebview && window.pywebview.api) {
    init()
} else {
    window.addEventListener('pywebviewready', () => {
        init()
    })
}
