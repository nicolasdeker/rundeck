import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    /** i18n key of the page title; App.vue appends the product name. */
    titleKey?: string
  }
}

/**
 * Routes. Legacy deep links keep resolving (MISSION §1.6): `/user/login` is the legacy login
 * path and stays the canonical one; `/` lands there until a home exists (Phase 1).
 */
export const routes: RouteRecordRaw[] = [
  { path: '/', redirect: { name: 'login' } },
  {
    path: '/user/login',
    name: 'login',
    component: () => import('@/pages/LoginPage.vue'),
    meta: { titleKey: 'rdx.login.title' },
  },
]

/** Creates the application router (HTML5 history under Vite's `base`). */
export function createAppRouter() {
  return createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes,
  })
}
