import { createI18n } from 'vue-i18n'

import { en } from './locales/en'
import { fr } from './locales/fr'

/** Locales shipped with the UI; the legacy bundles' other languages are converted in Phase 1. */
export const SUPPORTED_LOCALES = ['en', 'fr'] as const

/** A supported locale code. */
export type Locale = (typeof SUPPORTED_LOCALES)[number]

/** Fallback locale, also the one the e2e screenshots are taken in. */
export const DEFAULT_LOCALE: Locale = 'en'

/** All message bundles, keyed by locale. Keys are flat, dotted legacy keys (`flatJson`). */
export const messages = { en, fr } satisfies Record<Locale, Record<string, string>>

/** Type guard for a supported locale code. */
export function isLocale(value: string): value is Locale {
  return (SUPPORTED_LOCALES as readonly string[]).includes(value)
}

function browserLanguages(): readonly string[] {
  return typeof navigator === 'undefined' ? [] : navigator.languages
}

/**
 * Picks the first supported language of the browser's preference list, matching on the primary
 * subtag (`fr-CH` → `fr`), and falls back to English.
 */
export function detectLocale(languages: readonly string[] = browserLanguages()): Locale {
  for (const tag of languages) {
    const primary = tag.toLowerCase().split('-')[0]
    if (primary !== undefined && isLocale(primary)) {
      return primary
    }
  }
  return DEFAULT_LOCALE
}

/** Creates the vue-i18n instance (Composition API mode, flat legacy keys). */
export function createAppI18n(locale: Locale = detectLocale()) {
  return createI18n({
    legacy: false,
    locale,
    fallbackLocale: DEFAULT_LOCALE,
    flatJson: true,
    messages,
    fallbackWarn: false,
  })
}
