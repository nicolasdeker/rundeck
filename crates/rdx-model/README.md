# `rdx-model`

domain types (Job, Workflow, Option, Execution, Node, Project, Token, User, Webhook...), serde codecs

The domain types shared by every other crate, with `serde` codecs that reproduce the legacy JSON field names
and shapes. No I/O, no persistence, no HTTP.

## Legacy references (ported in later phases)

- `legacy/rundeckapp/grails-app/domain/rundeck/*.groovy` (22 GORM domain classes)
- `legacy/grails-webhooks/grails-app/domain/webhooks/Webhook.groovy`
- `legacy/core/src/main/java/com/dtolabs/rundeck/core/jobs/`
- `legacy/core/src/main/java/com/dtolabs/rundeck/core/common/` (`INodeEntry`, `IRundeckProject`, ...)
- `legacy/rundeckapp/src/main/groovy/com/dtolabs/rundeck/app/support/` (query/command objects)

## Parity specs this crate targets

- `specs/model.md`
- upstream `api/job/JobSpec`, `api/job/JobsSpec`, `api/execution/ExecutionSpec`

## Status

Phase 0: scaffold, no code. Dependencies arrive with the Phase 1 ADRs; the intended dependency direction is in [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md).
