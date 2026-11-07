/**
 * English messages (default locale).
 *
 * Legacy keys are carried over verbatim (MISSION §1.6: every message key the new UI needs is
 * converted from `legacy/rundeckapp/grails-app/i18n/`):
 * - `user.login.username.label`, `user.login.password.label`, `user.login.login.button`,
 *   `user.login.empty.username`: legacy/rundeckapp/grails-app/i18n/messages.properties:1840-1843,
 *   rendered by legacy/rundeckapp/grails-app/views/user/login.gsp:175,180,184,196.
 * - `invalid.username.and.password`: messages.properties:1323, the `flash.loginErrorCode` set in
 *   legacy/rundeckapp/grails-app/controllers/rundeck/controllers/UserController.groovy:87 and
 *   rendered by login.gsp:192. Carried over now; Phase 1 wires the failed-login redirect to it.
 *
 * Keys prefixed `rdx.` are new to the rebuilt UI (the legacy page title `<app> - Login` had no key).
 * Message syntax is vue-i18n's: `{name}` interpolates, so `@` and `|` must not appear literally.
 */
export const en = {
  'user.login.username.label': 'Username',
  'user.login.password.label': 'Password',
  'user.login.login.button': 'Log In',
  'user.login.empty.username': 'Username cannot be empty',
  'invalid.username.and.password': 'Invalid username and password.',
  'rdx.app.name': 'rdx',
  'rdx.page.title': '{page} · {app}',
  'rdx.login.title': 'Sign in',
  'rdx.login.lead': 'Sign in to your rdx server.',
  'rdx.theme.switchToDark': 'Switch to dark theme',
  'rdx.theme.switchToLight': 'Switch to light theme',
  'rdx.a11y.skipToContent': 'Skip to main content',
} as const satisfies Record<string, string>

/** Every message key; the other locales must provide exactly this set (enforced by their type). */
export type MessageKey = keyof typeof en
