# `rdx-webhooks`

webhook endpoints + event plugins

Inbound webhooks: the `/api/*/webhook/*` endpoints, webhook authentication, the webhook event plugin service
(run-job and log-events providers) and the project export/import of webhook definitions.

## Legacy references (ported in later phases)

- `legacy/grails-webhooks/` (`Webhook.groovy` domain, `WebhookController.groovy`, `WebhookService.groovy`, `authenticator/`, `exporter/`, `importer/`)
- `legacy/core/src/main/java/com/dtolabs/rundeck/plugins/webhook/`

## Parity specs this crate targets

- `specs/webhooks.md`
- upstream `selenium/webhook/WebhooksSpec` informs the journey; no upstream API spec exists, so the oracle run is a captured legacy session

## Status

Phase 0: scaffold, no code. Dependencies arrive with the Phase 1 ADRs; the intended dependency direction is in [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md).
