# UI review — Phase 0 (login shell)

Screenshots produced by `pnpm e2e` (`ui/e2e/j-001-login-shell.spec.ts`) from the production
build served by `vite preview`, Chromium, device scale factor 2, full page. Each image was taken
only after the page passed the axe gate (zero serious/critical violations) at that viewport and theme.

| Journey | Route | Viewport | Theme | File |
| ------- | ----- | -------- | ----- | ---- |
| J-001 login shell | `/user/login` | 375×812 | light | [login-375-light.png](login-375-light.png) |
| J-001 login shell | `/user/login` | 375×812 | dark | [login-375-dark.png](login-375-dark.png) |
| J-001 login shell | `/user/login` | 1280×800 | light | [login-1280-light.png](login-1280-light.png) |
| J-001 login shell | `/user/login` | 1280×800 | dark | [login-1280-dark.png](login-1280-dark.png) |

What to look at: the top bar (product name, theme toggle), the login card with the two legacy
fields and the Log In button, readability of both themes, and that nothing overflows at 375 px.

Regenerate: `cd ui && pnpm e2e` (or `make e2e` from the root).
