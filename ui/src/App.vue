<script setup lang="ts">
import { watchEffect } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'

import AppShell from '@/components/AppShell.vue'

const { t, locale } = useI18n()
const route = useRoute()

watchEffect(() => {
  document.documentElement.lang = locale.value
  const titleKey = route.meta.titleKey
  document.title =
    titleKey === undefined
      ? t('rdx.app.name')
      : t('rdx.page.title', { page: t(titleKey), app: t('rdx.app.name') })
})
</script>

<template>
  <AppShell>
    <RouterView />
  </AppShell>
</template>
