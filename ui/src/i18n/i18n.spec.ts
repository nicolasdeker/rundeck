import { describe, expect, it } from 'vitest'

import { SUPPORTED_LOCALES, createAppI18n, detectLocale, messages } from './index'
import { en } from './locales/en'

describe('locales', () => {
  it.each(SUPPORTED_LOCALES)('%s defines every key of en, non-empty, no extras', (locale) => {
    const bundle: Record<string, string> = messages[locale]
    expect(Object.keys(bundle).sort()).toEqual(Object.keys(en).sort())
    for (const [key, value] of Object.entries(bundle)) {
      expect(value.trim(), `${locale}: ${key}`).not.toBe('')
    }
  })

  it('resolves flat dotted legacy keys and interpolates', () => {
    const i18n = createAppI18n('fr')
    expect(i18n.global.t('user.login.username.label')).toBe('Identifiant')
    expect(i18n.global.t('rdx.page.title', { page: 'Connexion', app: 'rdx' })).toBe(
      'Connexion · rdx',
    )
  })
})

describe('detectLocale', () => {
  it('matches on the primary language subtag', () => {
    expect(detectLocale(['fr-CH', 'en-US'])).toBe('fr')
    expect(detectLocale(['EN-gb'])).toBe('en')
  })

  it('falls back to English for unsupported or empty lists', () => {
    expect(detectLocale(['de-DE', 'ja'])).toBe('en')
    expect(detectLocale([])).toBe('en')
  })
})
