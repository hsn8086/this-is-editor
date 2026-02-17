/// <reference types="vitest" />

import { resolve } from 'node:path'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['./vitest.setup.ts'],
    include: [
      'tests/frontend/unit/**/*.test.ts',
      'tests/frontend/unit/**/*.test.tsx',
      'tests/frontend/unit/**/*.test.vue',
    ],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: [
        'src/**/*.ts',
        'src/**/*.tsx',
        'src/**/*.vue',
      ],
      exclude: [
        'src/**/*.d.ts',
        'src/main.ts',
        'src/auto-imports.d.ts',
        'src/typed-router.d.ts',
        'src/components.d.ts',
      ],
    },
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
})
