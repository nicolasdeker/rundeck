# `rdx-logging`

execution log pipeline: streaming writers/readers, rdlog, log file storage plugins, state tracking

The execution log pipeline: streaming log writers and readers with bounded buffers, the `rdlog` file format
(shared codec in `rdx-formats`), log file storage plugins (upload/retrieve/partial), and the execution state
tracking that feeds the SSE fan-out.

## Legacy references (ported in later phases)

- `legacy/core/src/main/java/com/dtolabs/rundeck/core/logging/`
- `legacy/core/src/main/java/com/dtolabs/rundeck/core/logging/internal/RundeckLogFormat.java`
- `legacy/rundeckapp/grails-app/services/rundeck/services/logging/`
- `legacy/rundeckapp/grails-app/services/rundeck/services/LogFileStorageService.groovy`
- `legacy/rundeckapp/grails-app/services/rundeck/services/execution/logstorage/`
- `legacy/rundeckapp/grails-app/domain/rundeck/LogFileStorageRequest.groovy`

## Parity specs this crate targets

- `specs/logging.md`, `specs/formats-rdlog.md`
- upstream `api/execution/ExecutionOutputSpec`, `api/execution/AbortSpec`; `selenium/jobs/LogFilterSpec` informs the journey

## Status

Phase 0: scaffold, no code. Dependencies arrive with the Phase 1 ADRs; the intended dependency direction is in [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md).
