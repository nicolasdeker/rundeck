import { definePreset } from '@primeuix/themes'
import Aura from '@primeuix/themes/aura'

/**
 * The rdx PrimeVue preset: Aura with its light-mode colors raised to WCAG 2.2 AA contrast
 * (MISSION §4: zero axe serious/critical violations on every journey).
 *
 * Measured by axe on the login page with stock Aura (e2e J-001): white button labels on
 * emerald-500 2.53:1 (hovered emerald-600 3.67:1), red-600 error text on red-50 4.33:1.
 * With this preset: white on emerald-700 5.5:1, red-700 on red-50 5.9:1. Dark mode (primary-400
 * under surface-900 text) already passed and is left as Aura defines it.
 */
export const rdxPreset = definePreset(Aura, {
  semantic: {
    colorScheme: {
      light: {
        primary: {
          color: '{primary.700}',
          contrastColor: '#ffffff',
          hoverColor: '{primary.800}',
          activeColor: '{primary.900}',
        },
        highlight: {
          background: '{primary.50}',
          focusBackground: '{primary.100}',
          color: '{primary.800}',
          focusColor: '{primary.900}',
        },
      },
    },
  },
  components: {
    message: {
      colorScheme: {
        light: {
          error: {
            color: '{red.700}',
          },
        },
      },
    },
  },
})
