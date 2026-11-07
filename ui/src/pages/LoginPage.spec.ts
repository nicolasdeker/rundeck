import { mount, type VueWrapper } from '@vue/test-utils'
import PrimeVue from 'primevue/config'
import { describe, expect, it } from 'vitest'
import { nextTick } from 'vue'

import { createAppI18n, type Locale } from '@/i18n'

import LoginPage from './LoginPage.vue'

function mountPage(locale: Locale = 'en'): VueWrapper {
  return mount(LoginPage, {
    global: { plugins: [createAppI18n(locale), [PrimeVue, { unstyled: true }]] },
  })
}

/** Dispatches a cancelable submit event and reports whether the page let it through. */
async function submit(wrapper: VueWrapper): Promise<boolean> {
  const event = new Event('submit', { cancelable: true })
  wrapper.get('form').element.dispatchEvent(event)
  await nextTick()
  return !event.defaultPrevented
}

describe('LoginPage', () => {
  it('posts the legacy form to /j_security_check', () => {
    const form = mountPage().get('form')
    expect(form.attributes('action')).toBe('/j_security_check')
    expect(form.attributes('method')).toBe('post')
  })

  it('renders j_username and j_password with their legacy labels (en)', () => {
    const page = mountPage()
    const username = page.get('input[name="j_username"]')
    const password = page.get('input[name="j_password"]')

    expect(username.attributes('type')).toBe('text')
    expect(password.attributes('type')).toBe('password')
    expect(page.get(`label[for="${username.attributes('id')}"]`).text()).toBe('Username')
    expect(page.get(`label[for="${password.attributes('id')}"]`).text()).toBe('Password')
    expect(page.get('button[type="submit"]').text()).toBe('Log In')
    expect(page.findAll('input')).toHaveLength(2)
  })

  it('translates the labels (fr)', () => {
    const page = mountPage('fr')
    expect(page.get('label[for="login"]').text()).toBe('Identifiant')
    expect(page.get('label[for="password"]').text()).toBe('Mot de passe')
    expect(page.get('button[type="submit"]').text()).toBe('Connexion')
  })

  it('refuses an empty username client-side and shows the legacy message', async () => {
    const page = mountPage()
    expect(await submit(page)).toBe(false)

    const alert = page.get('[role="alert"]')
    expect(alert.text()).toBe('Username cannot be empty')
    expect(page.get('input[name="j_username"]').attributes('aria-describedby')).toBe(
      alert.attributes('id'),
    )
  })

  it('lets the browser post once a username is given', async () => {
    const page = mountPage()
    expect(await submit(page)).toBe(false)

    await page.get('input[name="j_username"]').setValue('admin')
    expect(await submit(page)).toBe(true)
    expect(page.find('[role="alert"]').exists()).toBe(false)
  })
})
