#!/usr/bin/env python3
"""Summarise the upstream Selenium specs (class, annotations, page objects, feature methods) as TSV.

Usage:  python3 -I scripts/inventory/selenium_specs.py [--root <repo>] > selenium.tsv

Columns: file  class  annotations  pages  features_count  features (joined by ` | `).
Feature methods are the Spock `def "..."()` / `def '...'()` declarations; page objects are the
`org.rundeck.util.gui.pages.*` imports. Nothing is read beyond these regexes.
"""
from __future__ import annotations

import os
import re
import sys

SEL_DIR = "legacy/functional-test/src/test/groovy/org/rundeck/tests/functional/selenium"


def main(argv: list[str]) -> int:
    root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    if len(argv) > 2 and argv[1] == "--root":
        root = argv[2]
    files = []
    for dp, _, fns in os.walk(os.path.join(root, SEL_DIR)):
        files += [os.path.join(dp, f) for f in fns if f.endswith("Spec.groovy")]
    print("file\tclass\tannotations\tpages\tfeatures_count\tfeatures")
    total_features = 0
    for f in sorted(files):
        with open(f, encoding="utf-8", errors="replace") as fh:
            src = fh.read()
        cls = re.search(r"^class\s+(\w+)\s+extends\s+(\w+)", src, re.M)
        annotations = re.findall(r"^@(\w+)", src, re.M)
        pages = re.findall(r"^import org\.rundeck\.util\.gui\.pages\.([\w.]+)", src, re.M)
        features = re.findall(r"^\s+(?:def|void)\s+(?:\"([^\"]+)\"|'([^']+)')\s*\(", src, re.M)
        names = [a or b for a, b in features]
        total_features += len(names)
        print(
            "\t".join(
                [
                    os.path.relpath(f, root),
                    f"{cls.group(1)} extends {cls.group(2)}" if cls else "-",
                    ",".join(annotations) or "-",
                    ",".join(pages) or "-",
                    str(len(names)),
                    " | ".join(names),
                ]
            )
        )
    print(f"# selenium specs: {len(files)}; feature methods: {total_features}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
