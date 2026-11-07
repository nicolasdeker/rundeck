import { fileURLToPath, URL } from 'node:url'

import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

/**
 * Where `rdx serve` listens during development (Phase 1). The dev server proxies the backend
 * contracts there so the SPA never needs a second origin: the legacy REST API (`/api`), the
 * UI-only API (`/ui-api`, MISSION §3.8) and the legacy form login endpoint (`/j_security_check`).
 */
const backend = process.env['RDX_BACKEND_URL'] ?? 'http://localhost:4440'

const proxyTargets = ['/api', '/ui-api', '/j_security_check']

export default defineConfig({
  base: '/',
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    proxy: Object.fromEntries(
      proxyTargets.map((path) => [path, { target: backend, changeOrigin: false }]),
    ),
  },
  preview: {
    port: 4173,
    strictPort: true,
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: false,
    reportCompressedSize: true,
  },
})
