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

const app = createApp(App)
registerPlugins(app)
if (window.pywebview && window.pywebview.api) {
    app.mount('#app')
} else {
    window.addEventListener('pywebviewready', () => {
        app.mount('#app')
    })
}
