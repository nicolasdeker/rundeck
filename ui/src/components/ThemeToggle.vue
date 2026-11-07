<script setup lang="ts">
import Button from 'primevue/button'
import { useI18n } from 'vue-i18n'

import { useThemeStore } from '@/stores/theme'

const { t } = useI18n()
const theme = useThemeStore()
</script>

<template>
  <Button
    type="button"
    severity="secondary"
    text
    rounded
    :icon="theme.isDark ? 'pi pi-sun' : 'pi pi-moon'"
    :aria-label="theme.isDark ? t('rdx.theme.switchToLight') : t('rdx.theme.switchToDark')"
    :aria-pressed="theme.isDark"
    data-testid="theme-toggle"
    @click="theme.toggle()"
  />
</template>
