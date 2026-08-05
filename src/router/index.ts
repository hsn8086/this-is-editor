/**
 * router/index.ts
 *
 * Automatic routes for `./src/pages/*.vue`
 */
/* eslint-disable import/no-duplicates -- auto-router exposes routes through separate virtual modules */

import { setupLayouts } from 'virtual:generated-layouts'
// Composables
import { createRouter, createWebHistory } from 'vue-router/auto'
import { routes } from 'vue-router/auto-routes'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: setupLayouts(routes),
})

function getLocalStorage (): Storage | undefined {
  try {
    return window.localStorage
  } catch {
    return undefined
  }
}

// Workaround for https://github.com/vitejs/vite/issues/11804
router.onError((err, to) => {
  if (err?.message?.includes?.('Failed to fetch dynamically imported module')) {
    const storage = getLocalStorage()
    if (storage?.getItem('vuetify:dynamic-reload')) {
      console.error('Dynamic import error, reloading page did not fix it', err)
    } else {
      console.log('Reloading page to fix dynamic import error')
      storage?.setItem('vuetify:dynamic-reload', 'true')
      location.assign(to.fullPath)
    }
  } else {
    console.error(err)
  }
})

router.isReady().then(() => {
  getLocalStorage()?.removeItem('vuetify:dynamic-reload')
})

export default router
