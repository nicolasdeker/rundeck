# rdx UI

The rebuilt frontend of `rdx` (MISSION §3.8, ADR-0004): Vue 3.5 + TypeScript strict, Vite, Pinia,
vue-router, vue-i18n, PrimeVue 4 (Aura preset) + Tailwind 4. Built with `pnpm`, embedded into the
`rdx` binary with `rust-embed` and served with hashed immutable caching.

Phase 0 scope: the app shell (top bar, theme toggle), the legacy deep link `/user/login` rendering
the form-login contract (`POST /j_security_check`, fields `j_username` / `j_password`), `en` and
`fr` locales, dark/light theme, and the lint / unit / e2e wiring. No API call is made yet.

## Dev loop

```sh
pnpm install --frozen-lockfile   # once (Node >= 22, pnpm 10.28.0 via `packageManager`)
pnpm dev                         # http://localhost:5173, proxies /api, /ui-api and /j_security_check
                                 # to `rdx serve` on http://localhost:4440 (override: RDX_BACKEND_URL)
```

| Script         | What it runs                                             |
| -------------- | -------------------------------------------------------- |
| `pnpm dev`     | Vite dev server with the backend proxy above             |
| `pnpm build`   | `vue-tsc --noEmit && vite build` → `dist/`               |
| `pnpm preview` | Serves `dist/` on the fixed port 4173 (used by the e2e)  |
| `pnpm lint`    | `eslint . && prettier --check . && vue-tsc --noEmit`     |
| `pnpm test`    | `vitest run` (jsdom; `src/**/*.spec.ts`)                 |
| `pnpm e2e`     | `playwright test` (chromium; builds and previews itself) |
| `pnpm format`  | `prettier --write .`                                     |

The root `Makefile` wraps these as `make ui-install`, `ui-lint`, `ui-test`, `ui-build`, `e2e`;
`make check` runs `ui-lint` and `ui-test`.

## Layout

```
src/main.ts            app bootstrap: Pinia, i18n, router, PrimeVue (Aura, darkModeSelector `.dark`)
src/App.vue            document title / lang, renders AppShell + RouterView
src/components/        AppShell.vue (top bar, skip link, main slot), ThemeToggle.vue
src/pages/             one component per route (LoginPage.vue), lazy-loaded by the router
src/router/            routes; legacy deep links stay canonical (`/user/login`), `/` redirects
src/stores/            Pinia stores (theme.ts: OS default, localStorage persistence, `<html>` class)
src/i18n/              vue-i18n setup; locales/en.ts, fr.ts with flat legacy keys (see comments)
src/styles/main.css    Tailwind 4 + PrimeVue token aliases + cascade-layer order
e2e/                   Playwright journeys, `j-NNN-<name>.spec.ts`
```

## Rules (from `CLAUDE.md` Conventions; the linter enforces what it can)

- `<script setup lang="ts">` only, TypeScript `strict` with `noUncheckedIndexedAccess`, no `any`.
- Components ≤ 300 lines; one page component per route; route-level code splitting.
- i18n keys only: no user-visible string in a template or script (`vue/no-bare-strings-in-template`).
  Legacy message keys are carried over verbatim; new keys are prefixed `rdx.`.
- `v-html` nowhere (`vue/no-v-html`); Phase 1 adds a DOMPurify directive for the few places that need it.
- Cyclomatic complexity ≤ 25 (ESLint `complexity`, as upstream).
- Dependencies are exact-pinned (`.npmrc`: `save-exact=true`, `save-prefix=""`), `pnpm-lock.yaml`
  is committed, and CI installs with `--frozen-lockfile`. Every new dependency needs a one-line
  justification in the commit and a clean `pnpm audit`.
- Mobile-first: every journey works at 375×812 and 1280×800, light and dark, with zero axe
  serious/critical violations (MISSION §4).
- `pnpm audit` must be clean (MISSION §4, §8). Transitive advisories are fixed with a scoped,
  exact `pnpm.overrides` pin in `package.json` (currently `js-beautify>glob` for GHSA-3g3m-2fjr-6pw4 and
  `minimatch@>=7.0.0 <11.0.1` for GHSA-g3hv-75wg-m249; both reach only dev tooling: ESLint,
  typescript-eslint and the `@vue/test-utils` pretty-printer); a waiver is only
  acceptable with a written reason and an expiry.
- Nothing is copied from `legacy/rundeckapp/grails-spa`; domain types and i18n bundles may be
  ported after review and typing.

## Theme

`src/stores/theme.ts` defaults to `prefers-color-scheme`, follows OS changes until the user picks a
theme, persists the pick under `localStorage["rdx.theme"]`, and toggles the `dark` class on `<html>`.
That one class is PrimeVue's `darkModeSelector` and the selector of Tailwind's `dark:` variant
(`@custom-variant dark` in `main.css`), so both systems switch together. Tailwind color utilities
(`bg-surface-*`, `text-fg`, `bg-content`, …) alias PrimeVue's design tokens.

## Legacy contract notes

- `LoginPage.vue` posts a plain HTML form to `/j_security_check` with `j_username` / `j_password`
  (MISSION §1.1); no XHR. It keeps the legacy element ids (`login`, `password`, `btn-login`,
  `empty-username-msg`) and the client-side empty-username check of `login.gsp`.
- Deliberate markup differences (behavior, not markup, is the contract — MISSION §1.6): the
  password field uses `autocomplete="current-password"` instead of the legacy `off`, so password
  managers work on phones; the failed-login message (`invalid.username.and.password`) is carried
  over as a key and wired when the backend login redirect exists (Phase 1).

## Planned for Phase 1 (not added yet, on purpose)

TanStack Query (Vue), CodeMirror 6, vue-flow, `openapi-typescript` + `openapi-fetch` (client
generated from the `rdx` OpenAPI document), Storybook, DOMPurify, date-fns +
`@internationalized/date`, `@intlify/unplugin-vue-i18n` (precompiled messages, drops the runtime
compiler from the bundle), PrimeVue `locale` translations for component aria strings, an accessible
show/hide password toggle, the remaining legacy languages (de, es_419, ja, nl, pt_BR, zh_cn).

## Screenshots for the owner

`pnpm e2e` runs the production build in `vite preview` and, for every journey, saves full-page
screenshots at 375 px and 1280 px in light and dark (device scale factor 2) into
`../docs/ui-review/<phase>/` — currently `docs/ui-review/phase-0/login-{375,1280}-{light,dark}.png`.
The owner reviews them from the GitHub app; `JOURNAL.md` links them at each gate. The same run
asserts the axe gate, so a screenshot only exists for a page that passed it.
