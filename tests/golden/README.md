# tests/golden — request/response pairs recorded from the legacy oracle

Golden files are the "oracle, not opinion" evidence of MISSION §5 step 3: a request sent to the **unchanged**
legacy Rundeck 6.3.0 fixture (`scripts/oracle.sh up`) and the exact answer it gave. Rust tests load them to assert
that `rdx` answers the same way (status, stable headers, body) before any upstream Spock spec is run.

## How a golden file is written

```
scripts/oracle.sh up                                   # legacy fixture, prints ORACLE_URL / ORACLE_TOKEN
scripts/oracle.sh capture system-info GET /api/60/system/info
scripts/oracle.sh capture project-create POST /api/60/projects body.json
```

`capture <name> <METHOD> <path> [json-body-file]` performs the request against the running oracle with
`X-Rundeck-Auth-Token: admintoken` (the static token of the fixture's `tokens.properties`) and
`Accept: application/json` (`ORACLE_ACCEPT` overrides it, e.g. `application/xml`; `ORACLE_CONTENT_TYPE` for the body),
then writes `tests/golden/<name>.json`. `<name>` may contain `/` to group files (`job/import-yaml`); the path is used
verbatim, so the API version is the caller's choice (`/api/60/...`, `/api/14/...` for older-version behaviour).

## File layout (`schema: 1`)

```json
{
  "schema": 1,
  "name": "system-info",
  "captured": { "at": "2026-11-07T12:00:00Z", "oracle_image": "rundeck/rundeck:6.3.0", "commit": "<git sha>", "tool": "scripts/oracle.sh capture" },
  "request":  { "method": "GET", "path": "/api/60/system/info", "headers": { "accept": "application/json" }, "body": null },
  "response": { "status": 200, "headers": { "content-type": "application/json;charset=UTF-8", "x-rundeck-api-version": "60" },
                "body_is_json": true, "body": { "system": { "...": "..." } } }
}
```

- `response.headers` are lower-cased and **normalized**: volatile headers are dropped (`date`, `set-cookie`,
  `expires`, `connection`, `keep-alive`, `transfer-encoding`, `content-length`, `etag`, `last-modified`,
  `x-request-id`, anything ending in `request-id`, `x-b3-*`, `traceparent`, `tracestate`). What is kept
  (`content-type`, `x-rundeck-api-version`, `x-rundeck-api-xml-response-wrapper`, `location`, `www-authenticate`, ...)
  is part of the contract.
- `response.body` is the parsed JSON when the body is JSON (`body_is_json: true`), otherwise the raw text (XML, plain
  text, HTML). Bodies are **not** normalized at capture time: values that legitimately vary between runs
  (timestamps, UUIDs, execution ids, hostnames, `serverUUID`) are handled by the Rust comparison helper, which
  takes an explicit allow-list of volatile JSON pointers per golden file. Keep that list in the test, next to the file
  it applies to, so a reviewer sees what is being ignored.
- Never edit a golden file by hand; re-capture it. A golden file must come from the oracle image named in
  `captured.oracle_image`; if the oracle moves to another tag, re-capture everything (`git log` keeps the history).

## Rules

- A golden file is evidence, not a stub: `rdx` must produce the same response, modulo the documented volatile fields
  and the deviations of `docs/COMPAT.md`. A test that needs to ignore more than that is a parity gap — record it in
  `PARITY.md`, do not loosen the comparison.
- Keep captures small and single-purpose (one endpoint, one case); name them `<area>/<case>.json` once an area has more
  than a handful.
- The oracle fixture state is not reset between captures: when a capture depends on data (a project, a job), create
  it in the same session and capture the whole sequence, or document the precondition in the test that uses the file.
