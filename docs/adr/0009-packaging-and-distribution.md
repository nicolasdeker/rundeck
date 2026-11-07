# ADR-0009 — Packaging and distribution

- Status: Accepted
- Date: 2026-11-07
- Phase: 0
- Deciders: owner via MISSION.md, autopilot

## Context

Legacy ships a launcher jar/war, deb and rpm packages (`legacy/packaging/lib/{common,deb,...}`) and the official
container (`legacy/docker/official`). The packages install under `/etc/rundeck` (`RDECK_CONFIG`) and
`/var/lib/rundeck` (`RDECK_BASE`) (`legacy/packaging/lib/common/etc/rundeck/profile:35-36`), log to
`/var/log/rundeck`, run as the `rundeck` user created by the package (`legacy/packaging/lib/deb/scripts/postinst:47`
`adduser`), and start through `init.d`/upstart (`legacy/packaging/lib/deb/etc/init.d/rundeckd`,
`legacy/packaging/lib/deb/etc/init/rundeckd.conf`; no systemd unit found under `legacy/packaging`). The container
is configured by `RUNDECK_*` environment variables rendered by remco templates (`legacy/docker/official/README.md:110-218`:
`RUNDECK_SERVER_UUID`, `RUNDECK_GRAILS_URL`, `RUNDECK_SERVER_CONTEXTPATH`, `RUNDECK_SERVER_FORWARDED`,
`RUNDECK_GRAILS_UPLOAD_MAXSIZE`, `RUNDECK_SERVER_ADDRESS`, `RUNDECK_DATABASE_{URL,DRIVER,USERNAME,PASSWORD,MIGRATE_ONSTART}`,
`RUNDECK_LOGGING_{STRATEGY,AUDIT_ENABLED,LEVEL_*}`, `RUNDECK_STORAGE_{PROVIDER,CONVERTER}_#_*`,
`RUNDECK_PREAUTH_*`, `RUNDECK_TOKENS_FILE`). MISSION §3.10 fixes the target: static-ish Linux binaries, distroless
non-root container, deb/rpm mirroring legacy paths, Helm chart, SBOM, signed releases, reproducible builds.

## Decision

1. **Targets**: Linux `x86_64` and `aarch64`. Two flavors per architecture: `rdx` (glibc, dynamically links
   `libpam` — PAM needs `dlopen` of system modules) and `rdx-static` (musl, fully static, built without the `pam`
   feature; `check-config` rejects a `JettyPamLoginModule` entry with a message naming the glibc flavor). Both embed
   the UI (ADR-0004). Binary ≤ 60 MB including the UI; cold start to first request < 1 s (MISSION §4).
2. **Container**: distroless base, runs as UID/GID `1000` user `rundeck` (same name as legacy's user), read-only root
   filesystem, writable volumes only at `/home/rundeck/server/config`, `/home/rundeck/server/data`,
   `/home/rundeck/server/logs`, `/home/rundeck/projects` — the legacy image's paths (`README.md:65` and the remco
   templates) — so existing bind mounts work. Every `RUNDECK_*` variable listed in the Context keeps its name and
   meaning and is rendered into the same `rundeck-config.properties`/`framework.properties` keys the remco templates
   produce (no remco; `rdx` reads the variables directly). Unknown `RUNDECK_*` variables produce one warning each.
   Health/readiness probes use `/monitoring/health` and `/monitoring/health/readiness` (ADR-0008).
3. **deb/rpm** install `rdx` to `/usr/bin/rdx`, keep `/etc/rundeck` (config, `realm.properties`, `ssl/`,
   `log4j2.properties` accepted — ADR-0008), `/var/lib/rundeck` (`RDECK_BASE`: `data/`, `projects/`, `libext/`,
   `var/`), `/var/log/rundeck`, user and group `rundeck`, and ship a systemd unit `rdx.service` with
   `Alias=rundeckd.service` so `systemctl restart rundeckd` keeps working. `/etc/rundeck/profile` is read for
   `RDECK_BASE`, `RDECK_CONFIG` and the `-D` properties (ADR-0002 statement 12); JVM options are ignored with a warning.
   Packages never write `realm.properties` with credentials (ADR-0007, C-007).
4. **Helm chart** (`charts/rdx`): StatefulSet or Deployment, the `RUNDECK_*` variables as values, Postgres/MySQL
   connection via secret, PVCs for the four writable paths, probes as above, `rundeck.server.uuid` per replica for
   cluster mode (ADR-0006), `securityContext` non-root/read-only/no-capabilities by default.
5. **Supply chain**: SBOM per artifact (CycloneDX via `cargo-cyclonedx`, plus the `pnpm` SBOM for the UI), release
   artifacts signed with `cosign` (keyless, GitHub OIDC), SLSA-style provenance attestations, pinned lockfiles
   (`Cargo.lock`, `pnpm-lock.yaml`), `cargo deny`/`cargo audit`/`pnpm audit` clean or waived with expiry.
   `RDX_REPRODUCIBLE=1` sets `SOURCE_DATE_EPOCH`, `--remap-path-prefix` and deterministic UI builds; a CI job builds
   twice and diffs the binaries.
6. **Versioning**: `rdx --version` prints `rdx <semver> (compat rundeck 6.3.0, api 14-60)`. What `/api/*/system/info`
   reports in its version fields is a parity question decided in `specs/system.md` against the oracle (see
   `DECISIONS-PENDING.md`); the default is the legacy field set with `rdx`'s own version string only where no upstream
   test asserts the value.
7. **Release workflow** (`.github/workflows/release.yml`, Phase 6): builds all flavors, images (multi-arch manifest),
   deb/rpm, chart, SBOMs, signatures; smoke test boots each artifact against a legacy-initialized Postgres and runs
   a filtered parity run (MISSION §9).
8. **Defaults differ from legacy only where ADR-0007 says so**: no default admin, `0600` files, SQLite data file
   at `${RDECK_BASE}/data/rdx.sqlite` when no `dataSource.url` is configured (ADR-0005).

## Consequences

Positive: drop-in on existing hosts and existing bind mounts; one small artifact per platform; verifiable supply
chain; non-root, read-only containers by default.

Negative: two binary flavors to build and test; no Windows or macOS server builds (legacy packaging did not ship
them either); JVM tuning knobs in operator scripts become no-ops.

Risks: PAM linking on glibc distributions with different `libpam` sonames — mitigated by building against the
oldest supported glibc and testing on Debian/Ubuntu/RHEL images in the release smoke test; container path
assumptions in third-party compose files — mitigated by keeping the legacy image paths.

## Compatibility impact

Untouched: filesystem paths, `rundeck` user, `RUNDECK_*` variables, `/etc/rundeck/profile` variables, container
volume paths, `rundeckd` service name (alias). Deviations: none specific to packaging beyond those owned by
ADR-0007 (**C-006**, **C-007**) and ADR-0002 (**C-018** JKS). Additive: `rdx.service`, Helm chart, SBOM/signatures,
`rdx-static` flavor.

## Alternatives considered

- glibc-only builds — rejected: a static binary is the simplest artifact for most deployments; PAM is the only
  reason to keep a glibc flavor.
- Alpine/Debian-based container — rejected: distroless removes the shell and package manager attack surface; node
  steps run on nodes, not in the server image (the `localexec` provider runs the binary's own argv, no shell needed).
- Renaming paths to `/etc/rdx` — rejected: breaks drop-in installs and runbooks; the trademark note concerns the
  product name, not compatibility paths (ADR-0001).
- Shipping remco in the image — rejected: `rdx` reads `RUNDECK_*` directly; one fewer moving part.

## Migration / rollout

Packages: install the deb/rpm over the existing `/etc/rundeck` and `/var/lib/rundeck`; stop `rundeckd` (Java), start
`rdx` (`systemctl start rundeckd` still works through the alias). Container: swap the image, keep volumes and
environment variables. Kubernetes: adopt the Helm chart with the same variables.

## References

- MISSION.md §3.10, §4 (security, supply chain), §6 (Phase 6), §9.
- `legacy/packaging/lib/common/etc/rundeck/profile:35-36,98`; `legacy/packaging/lib/deb/scripts/postinst:47`
- `legacy/packaging/lib/deb/etc/init.d/rundeckd`; `legacy/packaging/lib/deb/etc/init/rundeckd.conf`
- `legacy/packaging/lib/common/etc/rundeck/ssl/ssl.properties:1-2`
- `legacy/docker/official/README.md:65,110-218`; `legacy/docker/official/remco/templates/*`
- Related: ADR-0002 (`-D` properties, TLS), ADR-0005 (SQLite path), ADR-0007 (C-006, C-007), ADR-0008 (probes).
