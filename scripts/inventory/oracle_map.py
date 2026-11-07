#!/usr/bin/env python3
"""Map each legacy API route pattern to the upstream functional specs whose source contains its path.

Usage:  python3 -I scripts/inventory/routes.py > routes.tsv
        python3 -I scripts/inventory/oracle_map.py routes.tsv [--root <repo>] [--evidence] > oracle.tsv

Method (no guessing): the part of the pattern after `/api/$api_version` is turned into a regex where
`$var` matches one path segment (including Groovy `${expr}` interpolations), `$var**` matches the rest
of the path, optional segments are optional, and the match must start right after a quote or after
`/api/<anything>` and end at a quote, `?`, whitespace or end of line. Every `*.groovy` file under
`legacy/functional-test/src/test/groovy/org/rundeck/tests/functional/api/**` whose text matches is
listed as an oracle spec (class name); matches in the shared helpers under
`legacy/functional-test/src/test/groovy/org/rundeck/util/**` are listed separately as `helpers`
(coverage that reaches the route only through a utility class). Columns:

    pattern  methods  controller  action  specs  helpers

`specs` is `none` when no spec source mentions the path. `--evidence` prints `# file:line: text` lines
after each row so the mapping can be audited.
"""
from __future__ import annotations

import os
import re
import sys

SPEC_DIR = "legacy/functional-test/src/test/groovy/org/rundeck/tests/functional/api"
HELPER_DIR = "legacy/functional-test/src/test/groovy/org/rundeck/util"
SEG = r"[^/\"'\s?]+"
REST = r"[^\"'\s?]*"


CATCHALL = "/api/$api_version/$other/$extra**?"


def pattern_regex(pattern: str) -> re.Pattern[str] | None:
    """Regex for one route, or None for the catch-all (it would match every path)."""
    if pattern == CATCHALL:
        return None
    path = pattern[len("/api/$api_version") :]
    if path == "":
        # the bare API root: only an explicit `/api/<version>` followed by a delimiter counts
        return re.compile(r"/api/[^/\"'\s]+(?=[\"'?\s]|$)")
    out = []
    i = 0
    while i < len(path):
        m = re.match(r"\$(\w+)(\*\*)?(\?)?", path[i:])
        if m:
            star, opt = m.group(2), m.group(3)
            # drop the literal '/' already emitted when the segment is optional
            if opt and out and out[-1] == "/":
                out.pop()
                out.append("(?:/" + (REST if star else SEG) + ")?")
            else:
                out.append(REST if star else SEG)
            i += m.end()
            continue
        if path.startswith("(.$format)?", i):
            out.append(r"(?:\.[a-zA-Z]+)?")
            i += len("(.$format)?")
            continue
        out.append(re.escape(path[i]))
        i += 1
    body = "".join(out)
    return re.compile(r"(?:[\"']|/api/[^/\"'\s]+)" + body + r"(?=[\"'?\s]|$)")


def groovy_files(root: str, rel: str) -> list[str]:
    files = []
    for dp, _, fns in os.walk(os.path.join(root, rel)):
        for fn in fns:
            if fn.endswith(".groovy"):
                files.append(os.path.join(dp, fn))
    return sorted(files)


def main(argv: list[str]) -> int:
    root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    evidence = False
    args = argv[1:]
    if "--evidence" in args:
        evidence = True
        args.remove("--evidence")
    if "--root" in args:
        k = args.index("--root")
        root = args[k + 1]
        del args[k : k + 2]
    if not args:
        print(__doc__, file=sys.stderr)
        return 2
    with open(args[0], encoding="utf-8") as fh:
        header = fh.readline().rstrip("\n").split("\t")
        rows = [dict(zip(header, ln.rstrip("\n").split("\t"))) for ln in fh if ln.strip() and not ln.startswith("#")]
    sources = {}
    for group, rel in (("specs", SPEC_DIR), ("helpers", HELPER_DIR)):
        for f in groovy_files(root, rel):
            with open(f, encoding="utf-8", errors="replace") as fh:
                sources[f] = (group, fh.read().splitlines())
    print("pattern\tmethods\tcontroller\taction\tspecs\thelpers")
    stats = {"routes": 0, "with_spec": 0, "helpers_only": 0, "none": 0}
    for r in rows:
        if r["kind"] != "api":
            continue
        rx = pattern_regex(r["pattern"])
        hits: dict[str, list[tuple[str, int, str]]] = {"specs": [], "helpers": []}
        if rx is None:
            # catch-all for unknown paths: BadVersionSpec/UnauthorizedSpec hit it only indirectly, so it is
            # reported as not mapped rather than mapped to every spec that uses any API path
            print("\t".join([r["pattern"], r["methods"], r["controller"], r["action"], "none (catch-all; not path-mappable)", "-"]))
            stats["routes"] += 1
            stats["none"] += 1
            continue
        for f, (group, lines) in sources.items():
            for no, text in enumerate(lines, 1):
                if rx.search(text):
                    hits[group].append((f, no, text.strip()))
        specs = sorted({os.path.basename(f)[:-7] for f, _, _ in hits["specs"]})
        helpers = sorted({os.path.basename(f)[:-7] for f, _, _ in hits["helpers"]})
        stats["routes"] += 1
        if specs:
            stats["with_spec"] += 1
        elif helpers:
            stats["helpers_only"] += 1
        else:
            stats["none"] += 1
        print(
            "\t".join(
                [
                    r["pattern"],
                    r["methods"],
                    r["controller"],
                    r["action"],
                    ",".join(specs) or "none",
                    ",".join(helpers) or "-",
                ]
            )
        )
        if evidence:
            for group in ("specs", "helpers"):
                for f, no, text in hits[group]:
                    print(f"#   {os.path.relpath(f, root)}:{no}: {text[:140]}")
    print("# api routes: {routes}; with spec: {with_spec}; helpers only: {helpers_only}; none: {none}".format(**stats))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
