import { beforeAll, describe, expect, it } from 'vitest'

describe('Smoke Tests', () => {
  describe('Environment Setup', () => {
    it('should have window.pywebview defined', () => {
      expect(window).toBeDefined()
      expect(window.pywebview).toBeDefined()
      expect(window.pywebview.api).toBeDefined()
      expect(window.pywebview.state).toBeDefined()
    })

    it('should have matchMedia available', () => {
      expect(window.matchMedia).toBeDefined()
      expect(typeof window.matchMedia).toBe('function')
    })

    it('should have ResizeObserver available', () => {
      expect(window.ResizeObserver).toBeDefined()
    })
  })

  describe('Pywebview API Mock', () => {
    it('should have get_pinned_files method', async () => {
      const result = await window.pywebview.api.get_pinned_files()
      expect(result).toEqual([])
    })

    it('should have get_config method', async () => {
      const config = await window.pywebview.api.get_config()
      expect(config).toBeDefined()
      expect(config.editor).toBeDefined()
    })

    it('should have get_langs method', async () => {
      const langs = await window.pywebview.api.get_langs()
      expect(Array.isArray(langs)).toBe(true)
    })

    it('should have get_port method', () => {
      const port = window.pywebview.api.get_port()
      expect(typeof port).toBe('number')
    })

    it('should have path_ls method', async () => {
      const result = await window.pywebview.api.path_ls('/mock')
      expect(result).toBeDefined()
      expect(result.now_path).toBe('/mock')
      expect(Array.isArray(result.files)).toBe(true)
    })
  })

  describe('Pywebview State Mock', () => {
    it('should have addEventListener method', () => {
      expect(typeof window.pywebview.state.addEventListener).toBe('function')
    })

    it('should have prob initially null', () => {
      expect(window.pywebview.state.prob).toBeNull()
    })
  })
})
