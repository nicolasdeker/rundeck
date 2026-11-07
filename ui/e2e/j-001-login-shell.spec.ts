import { fileURLToPath } from 'node:url'

import AxeBuilder from '@axe-core/playwright'
import { expect, test, type Page } from '@playwright/test'

/**
 * J-001 — Login shell (Phase 0).
 *
 * The legacy deep link `/user/login` renders the form-login contract (MISSION §1.1: POST
 * `/j_security_check` with `j_username` / `j_password`) inside the new app shell. Each viewport
 * and theme of the §4 Frontend gate is checked for visibility and axe serious/critical violations,
 * and photographed for the owner into docs/ui-review/phase-0/ (MISSION §3.8 review channel).
 */

const screenshotDir = fileURLToPath(new URL('../../docs/ui-review/phase-0/', import.meta.url))

const viewports = [
  { width: 375, height: 812 },
  { width: 1280, height: 800 },
] as const

const themes = ['light', 'dark'] as const

const loginForm = (page: Page) => page.locator('form[action="/j_security_check"][method="post"]')

async function expectNoSeriousAxeViolations(page: Page): Promise<void> {
  const results = await new AxeBuilder({ page }).analyze()
  const severe = results.violations.filter(
    (violation) => violation.impact === 'serious' || violation.impact === 'critical',
  )
  expect(severe, JSON.stringify(severe, null, 2)).toEqual([])
}

for (const viewport of viewports) {
  for (const theme of themes) {
    test.describe(`login shell ${viewport.width}x${viewport.height} ${theme}`, () => {
      test.use({ viewport, colorScheme: theme, deviceScaleFactor: 2 })

      test('renders the legacy login form, passes axe, screenshot', async ({ page }) => {
        await page.goto('/user/login')
        await expect(page).toHaveURL(/\/user\/login$/)

        const form = loginForm(page)
        await expect(form).toBeVisible()
        await expect(form.locator('input[name="j_username"]')).toBeVisible()
        await expect(form.locator('input[name="j_password"]')).toBeVisible()
        await expect(form.locator('input[name="j_password"]')).toHaveAttribute('type', 'password')
        await expect(form.locator('button[type="submit"]')).toBeVisible()

        // The theme store follows the emulated OS preference and reflects it on <html>.
        await expect(page.locator('html')).toHaveClass(
          theme === 'dark' ? /\bdark\b/ : /^(?!.*\bdark\b)/,
        )
        await expect(page.getByTestId('theme-toggle')).toBeVisible()

        await expectNoSeriousAxeViolations(page)

        await page.screenshot({
          path: `${screenshotDir}login-${viewport.width}-${theme}.png`,
          fullPage: true,
        })
      })
    })
  }
}

test.describe('login shell navigation', () => {
  test('/ redirects to the legacy login deep link', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveURL(/\/user\/login$/)
    await expect(loginForm(page)).toBeVisible()
  })

  test('the theme toggle switches and persists the theme', async ({ page }) => {
    await page.goto('/user/login')
    const html = page.locator('html')
    await expect(html).not.toHaveClass(/\bdark\b/)

    await page.getByTestId('theme-toggle').click()
    await expect(html).toHaveClass(/\bdark\b/)
    await expect(page.getByTestId('theme-toggle')).toHaveAttribute('aria-pressed', 'true')

    await page.reload()
    await expect(html).toHaveClass(/\bdark\b/)
  })

  test('an empty username is refused client-side with the legacy message', async ({ page }) => {
    await page.goto('/user/login')
    await page.locator('button[type="submit"]').click()
    await expect(page).toHaveURL(/\/user\/login$/)
    const alert = page.getByRole('alert')
    await expect(alert).toBeVisible()
    // PrimeVue animates the message in; axe must measure the final colors, not a frame of the
    // enter transition (CI run 42397663318 measured 4.34:1 mid-transition on a slower runner).
    await expect(alert).not.toHaveClass(/p-message-enter/)
    await expectNoSeriousAxeViolations(page)
  })
})
