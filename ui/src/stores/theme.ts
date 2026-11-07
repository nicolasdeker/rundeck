import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'

/** The two color themes of the UI (MISSION §3.8: dark/light themes). */
export type Theme = 'light' | 'dark'

/** `localStorage` key holding the user's explicit choice; absent while the OS preference is followed. */
export const THEME_STORAGE_KEY = 'rdx.theme'

/**
 * Class set on `<html>` for the dark theme. It is PrimeVue's `darkModeSelector` (main.ts) and the
 * selector of Tailwind's `dark:` variant (styles/main.css), so one class drives both systems.
 */
export const DARK_CLASS = 'dark'

const DARK_MEDIA_QUERY = '(prefers-color-scheme: dark)'

/** Type guard for values read back from storage. */
export function isTheme(value: unknown): value is Theme {
  return value === 'light' || value === 'dark'
}

function storage(): Storage | undefined {
  try {
    return globalThis.localStorage
  } catch {
    // Private mode or blocked site data: the choice then lives for this page only.
    return undefined
  }
}

/** The persisted choice, or `null` when absent, invalid or when storage is unavailable. */
export function readStoredTheme(): Theme | null {
  try {
    const raw = storage()?.getItem(THEME_STORAGE_KEY)
    return isTheme(raw) ? raw : null
  } catch {
    return null
  }
}

/** Persists an explicit choice; silently keeps going when storage is unavailable. */
export function writeStoredTheme(theme: Theme): void {
  try {
    storage()?.setItem(THEME_STORAGE_KEY, theme)
  } catch {
    // See storage(): nothing to do, the in-memory state is already applied.
  }
}

function darkMediaQuery(): MediaQueryList | undefined {
  return typeof globalThis.matchMedia === 'function'
    ? globalThis.matchMedia(DARK_MEDIA_QUERY)
    : undefined
}

/** The theme the operating system currently prefers (`light` when it cannot be queried). */
export function systemTheme(): Theme {
  return darkMediaQuery()?.matches ? 'dark' : 'light'
}

/** Reflects a theme on `<html>` so PrimeVue and Tailwind switch together. */
export function applyTheme(theme: Theme): void {
  globalThis.document?.documentElement.classList.toggle(DARK_CLASS, theme === 'dark')
}

/**
 * Theme store: defaults to the OS preference, follows OS changes until the user picks a theme,
 * persists that pick in `localStorage` and keeps the `<html>` class in sync.
 */
export const useThemeStore = defineStore('theme', () => {
  const stored = readStoredTheme()
  const theme = ref<Theme>(stored ?? systemTheme())
  const followsSystem = ref(stored === null)
  const isDark = computed(() => theme.value === 'dark')

  function set(next: Theme): void {
    theme.value = next
    followsSystem.value = false
    writeStoredTheme(next)
  }

  function toggle(): void {
    set(isDark.value ? 'light' : 'dark')
  }

  // Synchronous: the class must be on <html> as soon as the state changes (no flicker, no tick).
  watch(theme, applyTheme, { immediate: true, flush: 'sync' })

  const query = darkMediaQuery()
  if (query && typeof query.addEventListener === 'function') {
    query.addEventListener('change', (event: MediaQueryListEvent) => {
      if (followsSystem.value) {
        theme.value = event.matches ? 'dark' : 'light'
      }
    })
  }

  return { theme, isDark, followsSystem, set, toggle }
})
