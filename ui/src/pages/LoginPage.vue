<script setup lang="ts">
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

/**
 * Legacy form-login contract (MISSION §1.1): a plain HTML POST to `/j_security_check` carrying
 * `j_username` and `j_password`. The browser submits the form itself; there is no XHR.
 */
const LOGIN_ACTION = '/j_security_check'

const { t } = useI18n()
const username = ref('')
const password = ref('')
const emptyUsername = ref(false)

/** Mirrors legacy login.gsp `onLoginClicked()`: an empty username never leaves the browser. */
function onSubmit(event: Event): void {
  if (username.value.trim() === '') {
    event.preventDefault()
    emptyUsername.value = true
    return
  }
  emptyUsername.value = false
}
</script>

<template>
  <div class="flex flex-1 items-start justify-center px-4 py-8 sm:items-center sm:py-16">
    <section class="w-full max-w-sm" aria-labelledby="login-title">
      <form
        :action="LOGIN_ACTION"
        method="post"
        class="flex flex-col gap-5 rounded-2xl border border-content-border bg-content p-6 shadow-sm sm:p-8"
        @submit="onSubmit"
      >
        <div class="flex flex-col gap-1">
          <h1 id="login-title" class="text-2xl font-semibold text-fg">
            {{ t('rdx.login.title') }}
          </h1>
          <p class="text-sm text-fg-muted">{{ t('rdx.login.lead') }}</p>
        </div>

        <div class="flex flex-col gap-2">
          <label for="login" class="text-sm font-medium text-fg">
            {{ t('user.login.username.label') }}
          </label>
          <InputText
            id="login"
            v-model="username"
            name="j_username"
            type="text"
            autocomplete="username"
            autocapitalize="none"
            spellcheck="false"
            autofocus
            fluid
            :invalid="emptyUsername"
            :aria-invalid="emptyUsername || undefined"
            :aria-describedby="emptyUsername ? 'empty-username-msg' : undefined"
          />
        </div>

        <div class="flex flex-col gap-2">
          <label for="password" class="text-sm font-medium text-fg">
            {{ t('user.login.password.label') }}
          </label>
          <InputText
            id="password"
            v-model="password"
            name="j_password"
            type="password"
            autocomplete="current-password"
            fluid
          />
        </div>

        <Message v-if="emptyUsername" id="empty-username-msg" severity="error" role="alert">
          {{ t('user.login.empty.username') }}
        </Message>

        <Button id="btn-login" type="submit" :label="t('user.login.login.button')" fluid />
      </form>
    </section>
  </div>
</template>
