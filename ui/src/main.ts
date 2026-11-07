import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import { createApp } from 'vue'

import App from '@/App.vue'
import { createAppI18n } from '@/i18n'
import { createAppRouter } from '@/router'
import { DARK_CLASS, useThemeStore } from '@/stores/theme'
import { rdxPreset } from '@/styles/preset'

import 'primeicons/primeicons.css'
import '@/styles/main.css'

const pinia = createPinia()
const app = createApp(App)

app.use(pinia)
app.use(createAppI18n())
app.use(createAppRouter())
app.use(PrimeVue, {
  ripple: false,
  theme: {
    preset: rdxPreset,
    options: {
      darkModeSelector: `.${DARK_CLASS}`,
      cssLayer: { name: 'primevue', order: 'theme, base, primevue' },
    },
  },
})

// Instantiating the store applies the persisted or system theme class before the first paint.
useThemeStore(pinia)

app.mount('#app')
