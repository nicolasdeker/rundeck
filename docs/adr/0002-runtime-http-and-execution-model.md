# ADR-0002 — Runtime, HTTP stack and execution model

- Status: Accepted
- Date: 2026-11-07
- Phase: 0
- Deciders: owner via MISSION.md, autopilot

## Context

Legacy runs on embedded Jetty behind Spring Boot/Grails, listening on `server.port: 4440`
(`legacy/rundeckapp/grails-app/conf/application.yml:395`), with `grails.serverURL` as the canonical base URL and
`server.useForwardHeaders` (`RUNDECK_SERVER_FORWARDED`, `legacy/docker/official/README.md:125`) for reverse
proxies; the context path comes from `RUNDECK_SERVER_CONTEXTPATH` (`README.md:120`) and upload limits from
`RUNDECK_GRAILS_UPLOAD_MAXSIZE` (`README.md:130`). TLS is configured through a JKS keystore
(`legacy/packaging/lib/common/etc/rundeck/ssl/ssl.properties:1-2`: `keystore=/etc/rundeck/ssl/keystore`,
`keystore.password=adminadmin`). Executions run on Quartz worker threads and Java thread pools; log output is
written through the `.rdlog` format
(`legacy/core/src/main/java/com/dtolabs/rundeck/core/logging/internal/RundeckLogFormat.java`). MISSION §3.2 and
§3.4 fix the target: `tokio` + `axum`/`tower` + `hyper` 1.x, `rustls` only, structured concurrency, argv-only
child processes.

## Decision

### Runtime
1. `tokio` multi-thread runtime, worker threads = available cores (`rdx.runtime.workers` overrides). Blocking work
   runs on `spawn_blocking` or on dedicated threads fed by **bounded** queues; a full queue applies backpressure,
   never unbounded growth. A test asserts that no `tokio::spawn` exists outside the supervisors of `rdx-exec`,
   `rdx-workflow`, `rdx-sched`, `rdx-logging` (MISSION §8: every spawn has a cancellation path).
2. No `unsafe`, no `unwrap`/`expect` outside tests (workspace lints, ADR-0001).

### HTTP
3. `axum` on `hyper` 1.x with `tower` layers; **`rustls` only** — `cargo deny` bans `openssl-sys` and `native-tls`.
   HTTP/1.1 and HTTP/2 (h2 negotiated by ALPN over TLS; cleartext h2c off).
4. Listener and base URL keep the legacy keys: `server.port` (default 4440), `server.address`,
   `server.servlet.context-path`, `grails.serverURL`, `server.useForwardHeaders` (trusted-proxy handling of
   `X-Forwarded-For/Proto/Host`; forwarded headers are ignored unless this is on). The `RUNDECK_*` environment
   variables of the official image map to the same keys (ADR-0009).
5. TLS from PEM (`rdx.tls.cert`, `rdx.tls.key`) or PKCS#12 (`rdx.tls.pkcs12`, `rdx.tls.password`). JKS keystores are
   JVM-bound and not read; `rdx doctor` detects `ssl.properties` and prints the `keytool -importkeystore
   -deststoretype PKCS12` conversion. **C-018** (reason c).
6. Fixed middleware order for every route: request id (`X-Request-Id` echoed or generated) → tracing span
   (ADR-0008) → security headers (ADR-0007) → body limit → timeout → concurrency limit → compression → authentication
   → typed authorization (ADR-0007) → handler. Defaults: 30 s timeout on non-streaming routes, none on
   `execution/{id}/output` and SSE; body limit 10 MiB except multipart uploads, which use the legacy
   `grails.controllers.upload.maxFileSize`/`RUNDECK_GRAILS_UPLOAD_MAXSIZE` value when set; gzip/br compression
   except on `text/event-stream`; `rdx.http.max_in_flight` concurrency cap (default 1024) returning `503` with the
   legacy error envelope when exceeded.
7. Streaming never buffers a whole log: `execution output` reads `.rdlog` by offset and streams chunks; SSE
   (`/ui-api/v1/executions/{id}/events`) fans out from a bounded broadcast channel (default capacity 1024 events per
   subscriber); a subscriber that stalls for `rdx.stream.stall_timeout` (default 30 s) is disconnected and may
   resume with `Last-Event-ID`. Gate: 100 MB log, 10 followers, no memory growth beyond buffers (MISSION §4).
8. Graceful shutdown on `SIGTERM`/`SIGINT`: stop accepting; in-flight requests finish within
   `rdx.shutdown.request_grace` (30 s); running executions keep running up to `rdx.shutdown.execution_drain`
   (default 60 s), then are aborted and given the final state legacy gives an execution interrupted by a server
   stop (pinned by `specs/executions.md` against the oracle); log writers flush and close; scheduler leases are
   released (ADR-0006); exit code 0.

### Execution model
9. Each execution is a supervised task tree — workflow task → step tasks → node tasks — built with `JoinSet`s and a
   `CancellationToken` per level, so abort propagates downwards and completion upwards (structured concurrency).
   Per-execution limits: `threadcount` from the job (node dispatch parallelism), step/job `timeout`, optional
   `rdx.exec.max_log_bytes` (unlimited by default to preserve legacy behavior; a warning is logged when exceeded if set).
10. One **append-only event stream** per execution (log lines, step/node state transitions, progress) is the single
    source of truth; log writers (ADR-0008, `rdx-logging`), the execution state machine and the SSE fan-out are its
    consumers. Ordering seen by `output`/`state` endpoints is the stream order.
11. Child processes: `argv` arrays only (never a shell string; a lint test fails on `Command::new("sh")`/`"bash"` with
    `-c` outside the explicit shell-step provider that legacy also runs through a shell), environment allow-list
    (the legacy `RD_*` variables and the step's declared env — set pinned in `specs/execution.md`), working
    directory, optional PTY when the step requests it, stdin closed, own process group (`setsid`), abort = signal to
    the process group with a `SIGTERM` → grace → `SIGKILL` sequence, every child awaited (no zombies).
12. Legacy `-D` launcher properties are accepted by `rdx serve -D<key>=<value>` for the properties the official
    launcher scripts pass (`rundeck.jaaslogin`, `java.security.auth.login.config`, `loginmodule.name`,
    `loginmodule.conf.name`, `rdeck.config`, `rundeck.server.configDir`, `server.datastore.path`,
    `rundeck.server.serverDir`, `rdeck.projects`, `logging.config` — grep `-D[a-zA-Z.]*=` in
    `legacy/docker/official/lib/` and `legacy/packaging/lib/common/etc/rundeck/profile`); JVM-only flags (`-Xmx`,
    `-XX:*`) are ignored with one warning line.

## Consequences

Positive: bounded memory under load (§4 gates for 1,000 executions and 100 MB logs are reachable by construction);
abort is reliable (process groups, cancellation tokens); one TLS stack, no OpenSSL packaging issues; request
behavior is uniform because the middleware order is fixed.

Negative: PTY handling and process-group semantics are Unix-only (Windows is not a target, as for the legacy
packaging); operators with JKS keystores must convert once.

Risks: the final state of executions interrupted by shutdown must match legacy exactly (watched by the executions
spec); forwarded-header trust mistakes would break cookie `Secure` detection (ADR-0007) — covered by tests with and
without `server.useForwardHeaders`.

## Compatibility impact

Untouched: port, base URL, context path, forwarded-header semantics, every API route and response, `.rdlog`
format, `RD_*` environment contract, `X-Rundeck-API-Version` header. Deviations: **C-018** JKS keystores not read
(reason c). `X-Request-Id` and `Last-Event-ID` are additive. HTTP/2 is additive (clients negotiate).

## Alternatives considered

- `actix-web` — rejected: the `tower` middleware ecosystem and `axum` extractors fit the typed-authorization layer.
- OpenSSL/`native-tls` — rejected: static builds and reproducibility (ADR-0009), one audited TLS stack.
- One OS thread per execution — rejected: 1,000 concurrent executions must fit in ≤ 1/4 of legacy RSS.
- Buffering execution output in memory for simplicity — rejected by MISSION §3.2 and the §4 streaming gate.

## Migration / rollout

Nothing for HTTP, proxy and port settings. TLS: convert the JKS keystore to PKCS#12 or PEM once (printed by
`rdx doctor`). Launcher scripts that pass `-D` properties keep working through `rdx serve -D...`.

## References

- MISSION.md §3.2, §3.4, §4 (performance), §8.
- `legacy/rundeckapp/grails-app/conf/application.yml:395` (`server.port: 4440`)
- `legacy/docker/official/README.md:115,120,125,130` (`RUNDECK_GRAILS_URL`, `RUNDECK_SERVER_CONTEXTPATH`,
  `RUNDECK_SERVER_FORWARDED`, `RUNDECK_GRAILS_UPLOAD_MAXSIZE`)
- `legacy/packaging/lib/common/etc/rundeck/ssl/ssl.properties:1-2`
- `legacy/core/src/main/java/com/dtolabs/rundeck/core/logging/internal/RundeckLogFormat.java`
- Related: ADR-0007 (headers, cookies), ADR-0008 (tracing, logs), ADR-0009 (packaging, env names).
