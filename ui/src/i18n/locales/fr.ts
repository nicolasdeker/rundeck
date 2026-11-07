import { type MessageKey } from './en'

/**
 * French messages.
 *
 * Legacy keys come from legacy/rundeckapp/grails-app/i18n/messages_fr_FR.properties:1804-1807
 * (`user.login.*`) and :1294 (`invalid.username.and.password`), same keys as en.ts; the `rdx.*`
 * keys are translated here. The type forces the key set to match en.ts exactly.
 */
export const fr: Record<MessageKey, string> = {
  'user.login.username.label': 'Identifiant',
  'user.login.password.label': 'Mot de passe',
  'user.login.login.button': 'Connexion',
  'user.login.empty.username': 'Le nom d’utilisateur ne peut pas être vide',
  'invalid.username.and.password': 'Nom d’utilisateur et mot de passe non valides.',
  'rdx.app.name': 'rdx',
  'rdx.page.title': '{page} · {app}',
  'rdx.login.title': 'Se connecter',
  'rdx.login.lead': 'Connectez-vous à votre serveur rdx.',
  'rdx.theme.switchToDark': 'Passer au thème sombre',
  'rdx.theme.switchToLight': 'Passer au thème clair',
  'rdx.a11y.skipToContent': 'Aller au contenu principal',
}
