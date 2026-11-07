import { defineConfig, mergeConfig } from 'vitest/config'

import viteConfig from './vite.config.ts'

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: 'jsdom',
      include: ['src/**/*.spec.ts'],
      exclude: ['e2e/**', 'node_modules/**', 'dist/**'],
      restoreMocks: true,
      unstubGlobals: true,
      unstubEnvs: true,
    },
  }),
)
