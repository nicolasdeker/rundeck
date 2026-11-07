# `rdx-config`

properties/JAAS/project.properties parsing, env overrides, typed config, legacy key names

Parses `rundeck-config.properties`, `framework.properties`, `project.properties`, JAAS login configuration and
the `RUNDECK_*` environment overrides of the official container into a typed, validated configuration. Legacy
key names are kept verbatim (MISSION §1.2, CLAUDE.md Conventions).

## Legacy references (ported in later phases)

- `legacy/rundeckapp/grails-app/conf/application.groovy` (defaults)
- `legacy/rundeckapp/grails-app/services/rundeck/services/ConfigurationService.groovy`
- `legacy/rundeckapp/grails-app/services/rundeck/services/FrameworkService.groovy`
- `legacy/core/src/main/java/com/dtolabs/rundeck/core/common/Framework.java`
- `legacy/core/src/main/java/com/dtolabs/rundeck/core/utils/PropertyLookup.java`
- `legacy/docker/official/` (environment variable names, remco templates)
- `legacy/packaging/` (file locations)

## Parity specs this crate targets

- `specs/config.md`
- upstream `api/project/ConfigSpec`, `api/system/SysInformationSpec`

## Status

Phase 0: scaffold, no code. Dependencies arrive with the Phase 1 ADRs; the intended dependency direction is in [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md).
