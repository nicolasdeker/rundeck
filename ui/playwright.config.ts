import { defineConfig, devices } from '@playwright/test'

/** Fixed port of `pnpm preview` (vite.config.ts `preview.port`, `--strictPort`). */
const previewPort = 4173
const baseURL = `http://localhost:${previewPort}`
const isCI = Boolean(process.env['CI'])

/**
 * Playwright e2e configuration (MISSION §3.8 review channel, §4 Frontend gates).
 *
 * - Chromium only, using the preinstalled browsers (`PLAYWRIGHT_BROWSERS_PATH`); never run
 *   `playwright install` here.
 * - No retries anywhere: a flaky journey is a bug, not something to hide (MISSION §8).
 * - Traces off by default; `pnpm e2e --trace on` when investigating.
 * - The web server is the production build served by `vite preview`, so screenshots and axe
 *   results reflect what the binary will embed.
 */
export default defineConfig({
  testDir: './e2e',
  outputDir: './test-results',
  fullyParallel: true,
  forbidOnly: isCI,
  retries: 0,
  workers: isCI ? 1 : undefined,
  reporter: isCI
    ? [['list'], ['html', { open: 'never', outputFolder: 'playwright-report' }]]
    : [['list']],
  use: {
    baseURL,
    trace: 'off',
    screenshot: 'off',
    video: 'off',
    locale: 'en-US',
    // Deterministic rendering for axe and screenshots: no CSS transitions/animations in flight.
    reducedMotion: 'reduce',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'pnpm build && pnpm preview',
    url: `${baseURL}/user/login`,
    reuseExistingServer: !isCI,
    timeout: 180_000,
    stdout: 'ignore',
    stderr: 'pipe',
  },
})
