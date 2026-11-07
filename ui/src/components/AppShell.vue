<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import ThemeToggle from '@/components/ThemeToggle.vue'

const { t } = useI18n()
</script>

<template>
  <div class="flex min-h-dvh flex-col">
    <a
      href="#main"
      class="sr-only focus:not-sr-only focus:absolute focus:top-3 focus:left-3 focus:z-50 focus:rounded-md focus:bg-primary focus:px-3 focus:py-2 focus:text-primary-contrast"
    >
      {{ t('rdx.a11y.skipToContent') }}
    </a>
    <header
      class="sticky top-0 z-10 flex h-14 items-center justify-between border-b border-content-border bg-surface-0/90 px-4 backdrop-blur dark:bg-surface-900/90"
    >
      <RouterLink :to="{ name: 'login' }" class="text-lg font-semibold tracking-tight text-fg">
        {{ t('rdx.app.name') }}
      </RouterLink>
      <ThemeToggle />
    </header>
    <main id="main" tabindex="-1" class="flex flex-1 flex-col outline-none">
      <slot />
    </main>
  </div>
</template>
