# ADR-0004 — Frontend rebuilt: Vue 3 stack, salvage policy, UI-only API, review channel

- Status: Accepted
- Date: 2026-11-07
- Phase: 0
- Deciders: owner via MISSION.md, autopilot

## Context

The legacy UI is 260 GSP pages across the Grails modules (233 under `legacy/rundeckapp/grails-app/views/`) plus
the `ui-trellis` Vue SPA (`legacy/rundeckapp/grails-spa/packages/ui-trellis/`, Options API, Bootstrap, Knockout
remnants). It is server-rendered, desktop-first, and it is where `UI` plugins inject JavaScript (ADR-0003). The
login contract is Spring Security's form login: `POST /j_security_check` with `j_username`/`j_password`
(`legacy/rundeckapp/grails-app/conf/application.groovy:175-177`), login page `/user/login` (`:178`), logout
`/user/logout` → `/user/loggedout` (`:179-180`), failure `/user/error` (`:181`), default landing `/menu/home` (`:183`).
Deep links that users bookmark and that notifications carry are route patterns such as
`/project/$project/job/show/$id` (`legacy/rundeckapp/grails-app/controllers/rundeckapp/UrlMappings.groovy:301-302`)
and `/project/$project/execution/show/$id` (`:329`). Guided tours have an API (`/tour/listAll`, `/tour/list/$loaderName`,
`/tour/get/$loaderName/$tour`, `UrlMappings.groovy:359-361`, `TourController.groovy`). MISSION §1.6 and §3.8 fix
the stack and the product requirements; the owner reviews from a 375 px-wide phone.

## Decision

1. **Stack** (MISSION §3.8): Vue 3.5 with `<script setup lang="ts">` and the Composition API, TypeScript `strict`
   (no `any`), Vite, Pinia, vue-router, TanStack Query (Vue), PrimeVue 4 + Tailwind 4 for layout and tokens,
   CodeMirror 6 (scripts, YAML/JSON), vue-flow (workflow graph), date-fns + `@internationalized/date`, vue-i18n with
   the converted legacy bundles, `openapi-typescript` + `openapi-fetch` generated from `rdx`'s OpenAPI document,
   Vitest for unit tests, Playwright for e2e, Storybook for the component library, `pnpm`, ESLint flat config +
   Prettier. Exact versions are pinned (no `^`/`~`), `pnpm audit` clean or waived.
2. **Theme preset.** The stock PrimeVue Aura preset fails WCAG 2.2 AA contrast in light mode; the project preset
   `ui/src/styles/preset.ts` darkens the primary and error ramps and is the only preset used. A Vitest test computes
   the contrast ratio of every semantic token pair in both themes and fails below 4.5:1 for text and 3:1 for UI
   components.
3. **Component tests.** `@vue/test-utils` is the mounting harness (already scaffolded; needed for PrimeVue teleports
   and stubs). `@testing-library/vue` is added in Phase 1 with the first journey components so that tests query by
   role and label (the same discipline the §4 accessibility gate enforces); both are used together, test-utils for
   mechanics, Testing Library queries for assertions. This settles MISSION §3.8's "Vitest + Testing Library".
4. **Salvage policy.** Nothing from `legacy/rundeckapp/grails-spa` is copied as-is. Domain TypeScript types
   (e.g. `JobDefinition.ts`), i18n bundles and pure utility functions may be ported after review and strict typing;
   every component is rewritten; no GSP; the only server-rendered HTML is the SPA shell served by `rdx-web`.
   `v-html` only through DOMPurify; i18n keys only, no hardcoded strings; components ≤ 300 lines.
5. **Login journey keeps the legacy contract**: the login page posts `application/x-www-form-urlencoded`
   `j_username`/`j_password` to `/j_security_check`, follows the redirect semantics (`/menu/home` or the saved
   target, `/user/error` on failure), and uses `/user/logout`. The SPA then obtains its CSRF token from
   `/ui-api/v1/session` (ADR-0007).
6. **Deep links keep resolving**: `/project/$p/job/show/$id`, `/project/$p/execution/show/$id`, `/project/$p/jobs`,
   `/project/$p/nodes`, `/project/$p/activity`, `/project/$p/home`, `/menu/*`, `/user/login`, `/resources/*`. Legacy
   paths are served by the SPA router directly or redirected (302) to the new route by `rdx-web`; a Playwright test
   covers every entry of the deep-link table in `specs/ui-journeys.md`.
7. **Product requirements**: mobile-first (every core journey works at 375×812), dark/light themes, keyboard
   navigation and WCAG 2.2 AA, route-level code splitting (initial JS ≤ 250 kB gzip, route chunks ≤ 150 kB gzip),
   optimistic updates, live execution view over SSE (`/ui-api/v1/executions/{id}/events`: log lines, step/node
   state, progress; 100k lines virtualized at 60 fps; reconnect with resume), job editor with workflow graph and
   YAML/JSON round-trip, node browser with the legacy filter language and autocomplete, activity timeline, key
   storage browser, ACL editor with live validation, project settings, plugin configuration forms generated from
   descriptors (ADR-0003), global search / command palette. Lighthouse mobile ≥ 90/95/95 and zero serious `axe`
   violations on every journey (MISSION §4).
8. **UI-only API** `/ui-api/v1` (`rdx-ui-api`): SSE streams, aggregated dashboard views, session/CSRF endpoints.
   Documented as **non-contract**, versioned in the path, every endpoint authorized through `rdx-authz` like the
   legacy API, never a second way to mutate domain state (mutations go through `/api/*`). **C-015** (additive).
9. **Guided tours**: the `/tour/*` API shapes and the `TourLoader` service type are kept; the tour presentation is
   redone in the new UI (Phase 5). **C-012**.
10. **Delivery**: `ui/` builds to static assets embedded with `rust-embed`; hashed file names served with
    `Cache-Control: public, max-age=31536000, immutable`, the shell with `no-store` (**C-021**); dev loop `pnpm dev`
    proxying to `rdx serve`.
11. **Review channel**: `pnpm e2e` writes screenshots at 375 px and 1280 px, light and dark, of every journey into
    `docs/ui-review/<phase>/`; the gate summary in `JOURNAL.md` links them so the owner can view them in the GitHub
    app.
12. The whole UI replacement is the pre-approved deviation **C-013**; the 57 upstream Selenium specs are not an
    oracle for it — the Playwright journeys in `ui/e2e/` are (MISSION §1.6).

*Alternative considered: React 19 + TanStack Router/Query + shadcn/ui. Rejected for v1 to keep the i18n bundles,
domain types and the upstream community's Vue direction salvageable. One-line change in ADR-0004 if the owner
reverses it.*

## Consequences

Positive: a UI that works on a phone and meets measurable accessibility and performance gates; one API contract for
humans and machines; a typed client generated from the server's own OpenAPI document, so UI/API drift fails CI.

Negative: no legacy markup is reused, so every journey is new work with a Playwright test; `UI` plugins are lost
until the Phase 5 extension API; two UI stacks exist in the repository during the mission (one read-only).

Risks: journey inventory gaps (mitigated by generating `specs/ui-journeys.md` from the Selenium specs, the GSP list
and the SPA routes); PrimeVue upgrades changing token names (pinned versions, contrast test).

## Compatibility impact

Untouched: the API the UI consumes, the login form contract, deep-link URLs (served or redirected), i18n message
keys and languages. Deviations/additions: **C-012** tours UI redone, **C-013** UI rebuilt, **C-015** `/ui-api/v1`
added, **C-021** asset caching. `UI` plugins: see ADR-0003 (C-010).

## Alternatives considered

- React 19 stack — see the italic line above (kept verbatim from MISSION §3.8).
- Keep `ui-trellis` and migrate it incrementally — rejected: Options API, Bootstrap 3 styling, GSP coupling, no
  mobile layout; the salvage policy keeps what is worth keeping (types, i18n, utilities).
- Server-side rendering (SSR) — rejected: no SEO need, one static bundle embeds cleanly in the binary.
- Stock Aura preset — rejected by measurement (light-mode contrast below AA).

## Migration / rollout

Nothing for users: bookmarks and notification links keep resolving; the login page keeps the same URL and form
contract. Operators who deployed `UI` plugins wait for the Phase 5 extension API.

## References

- MISSION.md §1.6, §3.8, §4 (frontend gates), §6 (Phase 1, 3, 5).
- `legacy/rundeckapp/grails-app/conf/application.groovy:175-183`
- `legacy/rundeckapp/grails-app/controllers/rundeckapp/UrlMappings.groovy:301-302,329,359-361`
- `legacy/rundeckapp/grails-app/controllers/rundeck/controllers/TourController.groovy`
- `legacy/rundeckapp/grails-spa/packages/ui-trellis/`, `legacy/rundeckapp/grails-app/views/**/*.gsp`, `legacy/rundeckapp/grails-app/i18n/`
- `ui/src/styles/preset.ts`; related: ADR-0003 (`UI` plugins), ADR-0007 (session/CSRF), `specs/ui-journeys.md`.
