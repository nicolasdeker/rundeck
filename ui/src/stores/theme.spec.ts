import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { DARK_CLASS, THEME_STORAGE_KEY, useThemeStore } from './theme'

type ChangeListener = (event: { matches: boolean }) => void

/** Stubs `matchMedia` with a fixed OS preference and returns a handle to simulate OS changes. */
function stubSystemPreference(prefersDark: boolean): { change: (prefersDark: boolean) => void } {
  const listeners: ChangeListener[] = []
  vi.stubGlobal(
    'matchMedia',
    vi.fn((query: string) => ({
      matches: prefersDark,
      media: query,
      addEventListener: (_type: string, listener: ChangeListener) => {
        listeners.push(listener)
      },
    })),
  )
  return {
    change(next: boolean) {
      for (const listener of listeners) {
        listener({ matches: next })
      }
    },
  }
}

function htmlIsDark(): boolean {
  return document.documentElement.classList.contains(DARK_CLASS)
}

beforeEach(() => {
  setActivePinia(createPinia())
  localStorage.clear()
  document.documentElement.classList.remove(DARK_CLASS)
})

describe('theme store', () => {
  it('defaults to dark when the OS prefers dark and nothing is stored', () => {
    stubSystemPreference(true)
    const store = useThemeStore()
    expect(store.theme).toBe('dark')
    expect(store.isDark).toBe(true)
    expect(store.followsSystem).toBe(true)
    expect(htmlIsDark()).toBe(true)
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBeNull()
  })

  it('defaults to light when the OS prefers light', () => {
    stubSystemPreference(false)
    const store = useThemeStore()
    expect(store.theme).toBe('light')
    expect(htmlIsDark()).toBe(false)
  })

  it('defaults to light when matchMedia is unavailable', () => {
    vi.stubGlobal('matchMedia', undefined)
    const store = useThemeStore()
    expect(store.theme).toBe('light')
  })

  it('prefers the stored choice over the OS preference', () => {
    localStorage.setItem(THEME_STORAGE_KEY, 'light')
    stubSystemPreference(true)
    const store = useThemeStore()
    expect(store.theme).toBe('light')
    expect(store.followsSystem).toBe(false)
    expect(htmlIsDark()).toBe(false)
  })

  it('ignores an invalid stored value', () => {
    localStorage.setItem(THEME_STORAGE_KEY, 'sepia')
    stubSystemPreference(true)
    const store = useThemeStore()
    expect(store.theme).toBe('dark')
    expect(store.followsSystem).toBe(true)
  })

  it('toggle flips the theme, the html class and persists the choice', () => {
    stubSystemPreference(false)
    const store = useThemeStore()

    store.toggle()
    expect(store.theme).toBe('dark')
    expect(htmlIsDark()).toBe(true)
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('dark')

    store.toggle()
    expect(store.theme).toBe('light')
    expect(htmlIsDark()).toBe(false)
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('light')
  })

  it('restores the persisted choice in a new store instance', () => {
    stubSystemPreference(false)
    useThemeStore().toggle()

    setActivePinia(createPinia())
    const fresh = useThemeStore()
    expect(fresh.theme).toBe('dark')
    expect(htmlIsDark()).toBe(true)
  })

  it('follows OS changes until the user picks a theme', () => {
    const os = stubSystemPreference(false)
    const store = useThemeStore()

    os.change(true)
    expect(store.theme).toBe('dark')
    expect(htmlIsDark()).toBe(true)

    store.set('light')
    os.change(true)
    expect(store.theme).toBe('light')
    expect(htmlIsDark()).toBe(false)
  })

  it('keeps working when localStorage throws', () => {
    stubSystemPreference(false)
    const denied = () => {
      throw new DOMException('denied', 'SecurityError')
    }
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(denied)
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(denied)

    const store = useThemeStore()
    expect(store.theme).toBe('light')
    store.toggle()
    expect(store.theme).toBe('dark')
    expect(htmlIsDark()).toBe(true)
  })
})
