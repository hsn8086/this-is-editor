/// <reference types="vitest" />

import type { API, TestCase } from '@/pywebview-defines'

declare global {
  interface Window {
    pywebview: {
      api: API
      state: {
        addEventListener: (name: string, func: (arg: unknown) => void) => void
        prob: TestCase | null
      }
    }
  }
}

export {}
