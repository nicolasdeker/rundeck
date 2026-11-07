#!/usr/bin/env python3
"""Extract every URL mapping of legacy Rundeck 6.3.0 (Grails `UrlMappings.groovy`) as TSV.

Usage:  python3 -I scripts/inventory/routes.py [--root <repo>] [file ...] > routes.tsv

Stdlib only. Comments (`//`, `/* */`) are stripped outside string literals before parsing, so the
commented-out mappings of the legacy file are not counted. Columns:

    file  line  kind  pattern  methods  controller  action  extras  condition

* `kind`: `api` (pattern starts with `/api/$api_version`), `web` (any other concrete path), `generic`
  (`/$controller/$action?/$id?` convention mapping), `redirect`, `view`, `status` (404/405/500 handlers).
* `methods`: HTTP verbs from an `action = [GET: ..., POST: ...]` map or a `post "/..."` verb prefix;
  `*` when the mapping accepts any method (the controller decides, e.g. through `allowedMethods`).
* `extras`: fixed parameters set by the mapping (`status=true`, `async=false`, `filename=readme.md`, ...).
* `condition`: feature flag guarding the mapping (`rundeck.feature.webhooks.enabled`, ...), else `-`.

`${project}` is normalised to `$project`. The trailing `# ...` lines are the reproducible counts.
"""
from __future__ import annotations

import os
import re
import sys

FILES = [
    "legacy/rundeckapp/grails-app/controllers/rundeckapp/UrlMappings.groovy",
    "legacy/grails-webhooks/grails-app/controllers/webhooks/UrlMappings.groovy",
    "legacy/grails-metricsweb/grails-app/controllers/metricsweb/UrlMappings.groovy",
    "legacy/grails-repository/grails-app/controllers/repository/UrlMappings.groovy",
    "legacy/grails-rundeck-data-shared/grails-app/controllers/grails/rundeck/data/shared/UrlMappings.groovy",
    "legacy/grails-execution-mode-timer/grails-app/controllers/com/rundeck/plugin/UrlMappings.groovy",
    "legacy/grails-job-kill-handler/grails-app/controllers/com/rundeck/plugins/killhandler/UrlMappings.groovy",
    "legacy/grails-persistlocale/grails-app/controllers/grails/persistlocale/UrlMappings.groovy",
    "legacy/grails-securityheaders/grails-app/controllers/grails/securityheaders/UrlMappings.groovy",
]

VERBS = ("get", "post", "put", "delete", "patch", "head", "options")
METHOD_ORDER = {"GET": 0, "POST": 1, "PUT": 2, "DELETE": 3, "PATCH": 4, "HEAD": 5, "OPTIONS": 6}


def strip_comments(src: str) -> str:
    """Blank out comments outside string literals, preserving newlines (line numbers stay valid)."""
    out: list[str] = []
    i, n = 0, len(src)
    quote: str | None = None
    while i < n:
        c = src[i]
        if quote:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(src[i + 1])
                i += 2
                continue
            if c == quote:
                quote = None
            i += 1
            continue
        if c in ("'", '"'):
            quote = c
            out.append(c)
            i += 1
            continue
        if src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append("".join("\n" if ch == "\n" else " " for ch in src[i:j]))
            i = j
            continue
        out.append(c)
        i += 1
    return "".join(out)


def balanced(src: str, start: int, open_ch: str, close_ch: str) -> int:
    """Return the index just after the bracket that closes the one at `start` (string-aware)."""
    depth = 0
    i, n = start, len(src)
    quote: str | None = None
    while i < n:
        c = src[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in ("'", '"'):
            quote = c
        elif c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError(f"unbalanced {open_ch} at {start}")


def split_top_level(s: str) -> list[str]:
    parts, depth, cur = [], 0, []
    quote: str | None = None
    for c in s:
        if quote:
            cur.append(c)
            if c == quote:
                quote = None
            continue
        if c in ("'", '"'):
            quote = c
        elif c in "[({":
            depth += 1
        elif c in "])}":
            depth -= 1
        elif c == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
            continue
        cur.append(c)
    if "".join(cur).strip():
        parts.append("".join(cur))
    return parts


def unquote(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
        return v[1:-1]
    return v


def parse_kv(body: str, sep_re: str) -> dict[str, str]:
    """Parse `key: value` (args) or `key = value` (block) pairs; nested `constraints {}` is dropped."""
    body = re.sub(r"constraints\s*\{[^{}]*\}", " ", body)
    result: dict[str, str] = {}
    pat = re.compile(r"(\w+)\s*" + sep_re + r"\s*(\[[^\]]*\]|'[^']*'|\"[^\"]*\"|[\w.]+)")
    for m in pat.finditer(body):
        result[m.group(1)] = m.group(2).strip()
    return result


def methods_of(action_val: str | None, verb: str | None) -> tuple[str, str]:
    """Return (methods, action) from an action value (string or `[GET:'x', ...]` map)."""
    if action_val is None:
        return ((verb.upper() if verb else "*"), "-")
    if action_val.startswith("["):
        pairs = split_top_level(action_val[1:-1])
        meths, acts = [], []
        for p in pairs:
            if ":" not in p:
                continue
            k, v = p.split(":", 1)
            meths.append(k.strip().upper())
            acts.append(f"{k.strip().upper()}={unquote(v)}")
        meths.sort(key=lambda m: METHOD_ORDER.get(m, 99))
        return (",".join(meths), ";".join(acts))
    return ((verb.upper() if verb else "*"), unquote(action_val))


def conditions(src: str) -> list[tuple[int, int, str]]:
    """Spans of `if (<cond>) { ... }` blocks with the feature flag they test."""
    spans = []
    for m in re.finditer(r"\bif\s*\(", src):
        close = balanced(src, m.end() - 1, "(", ")")
        cond = src[m.end() : close - 1]
        brace = src.find("{", close)
        if brace < 0:
            continue
        end = balanced(src, brace, "{", "}")
        flag = re.search(r"rundeck\.feature\.[a-zA-Z]+\.enabled", cond)
        spans.append((brace, end, flag.group(0) if flag else cond.strip()))
    return spans


STMT = re.compile(
    r"(?:\bname\s+(?P<name>\w+)\s*:\s*)?(?:\b(?P<verb>" + "|".join(VERBS) + r")\s+)?"
    r"\"(?P<pat>(?:/[^\"\n]*|\d{3}))\"\s*(?P<open>[({])"
)


def extract(path: str, root: str) -> list[dict[str, str]]:
    with open(os.path.join(root, path), encoding="utf-8") as fh:
        raw = fh.read()
    src = strip_comments(raw)
    spans = conditions(src)
    rows = []
    pos = 0
    while True:
        m = STMT.search(src, pos)
        if not m:
            break
        pattern = re.sub(r"\$\{(\w+)\}", r"$\1", m.group("pat"))
        line = src.count("\n", 0, m.start("pat")) + 1
        args: dict[str, str] = {}
        block: dict[str, str] = {}
        end = m.end()
        if m.group("open") == "(":
            close = balanced(src, m.end() - 1, "(", ")")
            args = parse_kv(src[m.end() : close - 1], ":")
            end = close
            nxt = re.match(r"\s*\{", src[end:])
            if nxt:
                bstart = end + nxt.end() - 1
                bend = balanced(src, bstart, "{", "}")
                block = parse_kv(src[bstart + 1 : bend - 1], "=")
                end = bend
        else:
            bend = balanced(src, m.end() - 1, "{", "}")
            block = parse_kv(src[m.end() : bend - 1], "=")
            end = bend
        pos = end
        merged = {**args, **block}
        controller = unquote(merged.get("controller", "-"))
        methods, action = methods_of(merged.get("action"), m.group("verb"))
        extras = ";".join(
            f"{k}={unquote(v)}"
            for k, v in merged.items()
            if k not in ("controller", "action", "redirect", "view", "constraints")
        )
        if "redirect" in merged:
            kind = "redirect"
            action = f"redirect={merged['redirect']}"
        elif "view" in merged:
            kind = "view"
            action = f"view={unquote(merged['view'])}"
        elif pattern.isdigit():
            kind = "status"
        elif pattern.startswith("/api/$api_version"):
            kind = "api"
        elif "$controller" in pattern:
            kind = "generic"
        else:
            kind = "web"
        cond = "-"
        for s, e, flag in spans:
            if s <= m.start() < e:
                cond = flag
        rows.append(
            {
                "file": path,
                "line": str(line),
                "kind": kind,
                "pattern": pattern,
                "methods": methods,
                "controller": controller,
                "action": action,
                "extras": extras or "-",
                "condition": cond,
            }
        )
    return rows


def main(argv: list[str]) -> int:
    root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    files = list(FILES)
    args = argv[1:]
    if args and args[0] == "--root":
        root = args[1]
        args = args[2:]
    if args:
        files = args
    cols = ["file", "line", "kind", "pattern", "methods", "controller", "action", "extras", "condition"]
    print("\t".join(cols))
    counts: dict[str, dict[str, int]] = {}
    total = 0
    for f in files:
        rows = extract(f, root)
        for r in rows:
            print("\t".join(r[c] for c in cols))
            counts.setdefault(f, {}).setdefault(r["kind"], 0)
            counts[f][r["kind"]] += 1
            total += 1
    api_total = 0
    for f, by_kind in counts.items():
        api_total += by_kind.get("api", 0)
        print(f"# {f}: " + ", ".join(f"{k}={v}" for k, v in sorted(by_kind.items())))
    print(f"# api patterns total: {api_total}")
    print(f"# mappings total: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
