# rdx architecture — Phase 0

This is the Phase 0 version: the crate map and the intended dependency direction. The execution and request
diagrams required by MISSION §4 arrive with the Phase 1 ADRs (`docs/adr/`), once the first vertical slice exists.
Nothing below is wired yet: in Phase 0 every crate compiles empty and the dependency graph is intentionally
**empty**, so that each edge is added by an ADR with a justification (MISSION §7 "every new crate justified").

## Crate map (MISSION §3.1)

| Crate | Layer | Role |
|---|---|---|
| `rdx` | binary | CLI: `serve`, `migrate`, `check-config`, `export`, `import`, `keys`, `acl check`, `doctor`; embeds `ui/` |
| `rdx-api` | edge | compatibility REST API v14–60 (axum), error envelope, content negotiation, OpenAPI |
| `rdx-ui-api` | edge | UI-only API `/ui-api/v1`: SSE, aggregated views, session/CSRF (not a contract) |
| `rdx-web` | edge | embedded SPA, security headers, legacy deep-link redirects |
| `rdx-webhooks` | edge | inbound webhook endpoints + webhook event plugins |
| `rdx-telemetry` | cross-cutting | tracing, Prometheus registry projected to the legacy Dropwizard JSON, health |
| `rdx-sched` | service | Quartz-compatible scheduler, cluster ownership, takeover, execution mode |
| `rdx-workflow` | service | workflow engine: strategies, rules, contexts, data expansion, log filters, orchestrators |
| `rdx-exec` | service | node executors (local, ssh, script), file copiers, process supervision |
| `rdx-logging` | service | execution log pipeline, rdlog, log file storage plugins, state tracking |
| `rdx-notify` | service | email/webhook notifications, notification plugins |
| `rdx-scm` | service | git export/import, SCM API |
| `rdx-nodes` | service | node model, node filter language, resource model sources, enhancers |
| `rdx-storage` | service | key storage tree, filesystem + DB backends, converters, AES-GCM |
| `rdx-authn` | service | realm.properties, LDAP, PAM, preauth, sessions, tokens |
| `rdx-authz` | service | aclpolicy evaluation engine (port of rundeck-authz-core) |
| `rdx-plugin` | service | plugin registry, descriptors, script plugin host, WASM host, built-in providers |
| `rdx-db` | infrastructure | sqlx repositories, legacy-compatible schema, `rdx_migrations` |
| `rdx-formats` | foundation | job XML/YAML/JSON, resources, aclpolicy, rdlog, project archive codecs |
| `rdx-config` | foundation | properties/JAAS/project.properties parsing, env overrides, typed config |
| `rdx-model` | foundation | domain types + serde codecs; no I/O |
| `quartz-cron` | foundation (standalone, repo root) | Quartz cron parser/evaluator |
| `rdx-testkit` | test support | temp projects, in-memory DB, fake nodes, golden files, oracle client |

## Dependency direction (intended; each edge lands with an ADR)

Dependencies point **downwards only**. A crate may depend on crates in the layers below it, never on a crate in
its own layer or above, with the two exceptions noted.

```
binary          rdx
                 │
edge            rdx-api   rdx-ui-api   rdx-web   rdx-webhooks
                 │
service         rdx-sched  rdx-workflow  rdx-exec  rdx-logging  rdx-notify  rdx-scm
                rdx-nodes  rdx-storage  rdx-authn  rdx-authz  rdx-plugin
                 │
infrastructure  rdx-db
                 │
foundation      rdx-formats   rdx-config   rdx-model   quartz-cron
                 │
std / external  tokio, axum, sqlx, serde, ...
```

Rules:

1. **Foundation** crates depend only on external crates. `rdx-model` is the shared vocabulary; `rdx-formats` and
   `rdx-config` depend on `rdx-model` (codecs produce domain types), never the reverse. `quartz-cron` depends on
   nothing in the workspace (it is publishable on its own).
2. **Infrastructure** (`rdx-db`) depends on `rdx-model` and `rdx-config`. It exposes repository traits; services
   consume traits, not `sqlx` types.
3. **Service** crates depend on foundation + infrastructure. Within the layer the only allowed edges are the
   ones the engine needs and an ADR records: `rdx-workflow → rdx-exec, rdx-nodes, rdx-logging, rdx-plugin`,
   `rdx-sched → quartz-cron`, `rdx-exec → rdx-storage` (keys for ssh), `rdx-authn → rdx-authz` (roles → policies
   evaluation never the other way), `* → rdx-plugin` (every pluggable service type resolves providers through
   the registry). No cycles; `cargo deny`'s graph and a `cargo tree` check in CI keep it that way.
4. **Edge** crates depend on services and are the only crates that know about HTTP. `rdx-api` is the parity
   contract; `rdx-ui-api` and `rdx-web` are new surfaces and may change freely. `rdx-webhooks` sits at the edge
   because it owns HTTP endpoints, and reaches the job-run service through `rdx-workflow`/`rdx-sched` interfaces.
5. **Cross-cutting**: `rdx-telemetry` is depended on by edge and service crates for `tracing` spans and metrics;
   it depends on nothing in the workspace.
6. **Binary**: `rdx` is the composition root. It is the only crate that depends on `anyhow` and the only one that
   knows every other crate. It never contains domain logic.
7. **Test support**: `rdx-testkit` is a `dev-dependency` only, allowed from any crate; it may depend on foundation
   and infrastructure crates and is never a dependency of `rdx`.

## Conventions enforced by the workspace

- Rust 2024, toolchain pinned in `rust-toolchain.toml`; `#![forbid(unsafe_code)]` and `missing_docs = deny`
  workspace-wide; clippy `pedantic` with the allow-list documented in `Cargo.toml`; `unwrap_used`/`expect_used`
  denied outside tests; `too_many_lines` denied above 80 lines (`clippy.toml`).
- `thiserror` in libraries, `anyhow` only in the binary (CLAUDE.md).
- Dependencies: exact need, one-line justification in the crate's `Cargo.toml`, `cargo deny` + `cargo audit`
  clean (`deny.toml`: Apache-2.0/MIT/BSD/ISC/Zlib/Unicode-3.0, MPL-2.0 case by case, crates.io only, no duplicate
  majors).
- `make check` = `fmt-check clippy test deny audit ui-lint ui-test` is the gate before every commit.
