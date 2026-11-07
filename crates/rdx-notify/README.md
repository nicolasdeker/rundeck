# `rdx-notify`

email, webhook, notification plugins

Job notifications: the `onsuccess`/`onfailure`/`onstart`/`onavgduration`/`onretryablefailure` triggers, email
and webhook (HTTP) notifications with the legacy payloads and templates, and the notification plugin service.

## Legacy references (ported in later phases)

- `legacy/rundeckapp/grails-app/services/rundeck/services/NotificationService.groovy`
- `legacy/rundeckapp/grails-app/domain/rundeck/Notification.groovy`
- `legacy/core/src/main/java/com/dtolabs/rundeck/plugins/notification/`

## Parity specs this crate targets

- `specs/notifications.md`
- upstream `selenium/jobs/JobNotificationSpec` informs the journey; API coverage comes from the job import/export specs

## Status

Phase 0: scaffold, no code. Dependencies arrive with the Phase 1 ADRs; the intended dependency direction is in [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md).
