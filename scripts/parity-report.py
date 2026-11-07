#!/usr/bin/env python3
"""parity-report.py — turn the upstream functional suite's JUnit XML into the parity report (MISSION §5 step 5, §7).

Standard library only; run as ``python3 -I scripts/parity-report.py``. Called by scripts/parity.sh and by
.github/workflows/parity.yml (matrix legs write one report each, the ``report`` job merges them).

Modes
  build (default)  INPUTS are JUnit XML files (legacy/functional-test/build/test-results/<task>/TEST-*.xml, written by
                   Gradle's Test task). Requires --target, --image, --task.
  --merge          INPUTS are JSON reports produced by this script (CI matrix legs); their target/task must agree.
  --markdown       print a Markdown summary of the resulting report to stdout (GITHUB_STEP_SUMMARY, PARITY.md).
  --gate           exit 1 when the report has unexcused failures or ran zero tests (never fake green: an empty
                   result is an error, not a pass); exit 0 otherwise. Without --gate the exit code is 0 after writing.

Report schema (``schema: 1``)
  {schema, target, image, commit, task, filter, started, finished, run_url, gradle_exit,
   specs: [{class, tests, passed, failed, skipped, errors, duration_s, failures: [{test, message, kind}]}],
   totals: {specs, tests, passed, failed, errors, skipped, duration_s, unexcused_failures},
   known_skips_applied: [{spec, test, status, reason, ref, matched: [class#test, ...]}]}

Known skips (tests/parity-skips.toml) are applied only to the ``rdx`` target: a failure matching an entry is excused
(still counted in ``failed``/``errors``, but not in ``unexcused_failures``). On the ``legacy`` target a failure is a
baseline fact to record (MISSION §6 Phase 0), so nothing is excused there.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import fnmatch
import json
import os
import subprocess
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

SCHEMA = 1
MESSAGE_LIMIT = 500
VALID_STATUS = {"deviated", "blocked"}
SKIP_KEYS = {"spec", "test", "status", "reason", "ref"}


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def git_commit(root: Path) -> str:
    try:
        return subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=True, capture_output=True,
                              text=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def run_url() -> str | None:
    server, repo, run_id = (os.environ.get(k) for k in ("GITHUB_SERVER_URL", "GITHUB_REPOSITORY", "GITHUB_RUN_ID"))
    if server and repo and run_id:
        return f"{server}/{repo}/actions/runs/{run_id}"
    return None


# --- known skips -----------------------------------------------------------------------------------------------------
def load_skips(path: Path, root: Path) -> list[dict[str, Any]]:
    """Parse and validate tests/parity-skips.toml. Any schema error is fatal: a malformed skip file must never excuse."""
    with path.open("rb") as fh:
        data = tomllib.load(fh)
    if data.get("schema") != SCHEMA:
        raise SystemExit(f"{path}: expected schema = {SCHEMA}, got {data.get('schema')!r}")
    unknown_top = set(data) - {"schema", "skip"}
    if unknown_top:
        raise SystemExit(f"{path}: unknown top-level keys {sorted(unknown_top)}")
    skips = data.get("skip", [])
    if not isinstance(skips, list):
        raise SystemExit(f"{path}: [[skip]] must be an array of tables")
    for i, skip in enumerate(skips):
        keys = set(skip)
        if keys != SKIP_KEYS:
            raise SystemExit(f"{path}: skip #{i + 1} must have exactly the keys {sorted(SKIP_KEYS)}, got {sorted(keys)}")
        if skip["status"] not in VALID_STATUS:
            raise SystemExit(f"{path}: skip #{i + 1} status must be one of {sorted(VALID_STATUS)}")
        if not all(isinstance(skip[k], str) and skip[k].strip() for k in SKIP_KEYS):
            raise SystemExit(f"{path}: skip #{i + 1} has an empty value")
        ref = skip["ref"]
        if not (ref.startswith("docs/adr/") or ref.startswith("BLOCKED/")) or not ref.endswith(".md"):
            raise SystemExit(f"{path}: skip #{i + 1} ref must be docs/adr/<n>-*.md or BLOCKED/<id>.md, got {ref!r}")
        if not (root / ref).is_file():
            raise SystemExit(f"{path}: skip #{i + 1} ref {ref!r} does not exist (a skip needs its ADR or BLOCKED file)")
    return skips


def skip_matches(skip: dict[str, Any], class_name: str, test_name: str) -> bool:
    return fnmatch.fnmatchcase(class_name, skip["spec"]) and (skip["test"] == "*" or fnmatch.fnmatchcase(test_name, skip["test"]))


# --- JUnit XML ----------------------------------------------------------------------------------------------------
def _message(elem: ET.Element) -> str:
    msg = (elem.get("message") or "").strip()
    if not msg:
        msg = (elem.text or "").strip().splitlines()[0] if (elem.text or "").strip() else ""
    if not msg:
        msg = elem.get("type") or elem.tag
    return msg[:MESSAGE_LIMIT]


def parse_junit(paths: list[Path]) -> dict[str, dict[str, Any]]:
    """Aggregate <testcase> elements per class name (Gradle writes one TEST-<class>.xml per spec)."""
    specs: dict[str, dict[str, Any]] = {}
    for path in paths:
        try:
            tree = ET.parse(path)  # noqa: S314 — files are produced by Gradle on this runner, not untrusted input
        except ET.ParseError as exc:
            raise SystemExit(f"{path}: not valid JUnit XML ({exc})") from exc
        root = tree.getroot()
        suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
        for suite in suites:
            for case in suite.iter("testcase"):
                cls = case.get("classname") or suite.get("name") or path.stem
                spec = specs.setdefault(cls, {"class": cls, "tests": 0, "passed": 0, "failed": 0, "skipped": 0,
                                              "errors": 0, "duration_s": 0.0, "failures": []})
                spec["tests"] += 1
                try:
                    spec["duration_s"] += float(case.get("time") or 0)
                except ValueError:
                    pass
                name = case.get("name") or "?"
                failure = case.find("failure")
                error = case.find("error")
                if failure is not None:
                    spec["failed"] += 1
                    spec["failures"].append({"test": name, "message": _message(failure), "kind": "failure"})
                elif error is not None:
                    spec["errors"] += 1
                    spec["failures"].append({"test": name, "message": _message(error), "kind": "error"})
                elif case.find("skipped") is not None:
                    spec["skipped"] += 1
                else:
                    spec["passed"] += 1
    for spec in specs.values():
        spec["duration_s"] = round(spec["duration_s"], 3)
    return specs


# --- report assembly ----------------------------------------------------------------------------------------------
def apply_skips(report: dict[str, Any], skips: list[dict[str, Any]]) -> None:
    applied: dict[int, dict[str, Any]] = {}
    unexcused = 0
    for spec in report["specs"]:
        for failure in spec["failures"]:
            excused_by = None
            if report["target"] == "rdx":
                for i, skip in enumerate(skips):
                    if skip_matches(skip, spec["class"], failure["test"]):
                        excused_by = i
                        break
            if excused_by is None:
                failure["excused"] = False
                unexcused += 1
            else:
                failure["excused"] = True
                entry = applied.setdefault(excused_by, {**skips[excused_by], "matched": []})
                entry["matched"].append(f"{spec['class']}#{failure['test']}")
    report["known_skips_applied"] = [applied[i] for i in sorted(applied)]
    report["totals"]["unexcused_failures"] = unexcused


def totals_of(specs: list[dict[str, Any]]) -> dict[str, Any]:
    keys = ("tests", "passed", "failed", "errors", "skipped")
    totals: dict[str, Any] = {"specs": len(specs)}
    for k in keys:
        totals[k] = sum(int(s[k]) for s in specs)
    totals["duration_s"] = round(sum(float(s["duration_s"]) for s in specs), 3)
    totals["unexcused_failures"] = 0
    return totals


def build_report(args: argparse.Namespace, root: Path) -> dict[str, Any]:
    xml_paths = [Path(p) for p in args.inputs]
    missing = [str(p) for p in xml_paths if not p.is_file()]
    if missing:
        raise SystemExit(f"JUnit XML not found: {missing}")
    specs = sorted(parse_junit(xml_paths).values(), key=lambda s: s["class"])
    report: dict[str, Any] = {
        "schema": SCHEMA,
        "target": args.target,
        "image": args.image,
        "commit": args.commit or git_commit(root),
        "task": args.task,
        "filter": args.filter or "",
        "started": args.started or utc_now(),
        "finished": args.finished or utc_now(),
        "run_url": run_url(),
        "gradle_exit": args.gradle_exit,
        "specs": specs,
        "totals": totals_of(specs),
        "known_skips_applied": [],
    }
    skips = load_skips(Path(args.skips), root) if args.skips and Path(args.skips).is_file() else []
    apply_skips(report, skips)
    return report


def merge_reports(args: argparse.Namespace, root: Path) -> dict[str, Any]:
    reports = []
    for p in args.inputs:
        with open(p, encoding="utf-8") as fh:
            data = json.load(fh)
        if data.get("schema") != SCHEMA:
            raise SystemExit(f"{p}: expected schema {SCHEMA}, got {data.get('schema')!r}")
        reports.append(data)
    if not reports:
        raise SystemExit("--merge needs at least one JSON report")
    for key in ("target", "task"):
        values = {r.get(key) for r in reports}
        if len(values) != 1:
            raise SystemExit(f"cannot merge reports with different {key}: {sorted(map(str, values))}")
    by_class: dict[str, dict[str, Any]] = {}
    for r in reports:
        for spec in r["specs"]:
            if spec["class"] in by_class:
                raise SystemExit(f"spec {spec['class']} appears in more than one report; matrix legs must not overlap")
            by_class[spec["class"]] = {k: v for k, v in spec.items()}
            for f in by_class[spec["class"]]["failures"]:
                f.pop("excused", None)
    specs = sorted(by_class.values(), key=lambda s: s["class"])
    filters = sorted({r.get("filter") or "" for r in reports} - {""})
    exits = [r.get("gradle_exit") for r in reports if r.get("gradle_exit") is not None]
    merged: dict[str, Any] = {
        "schema": SCHEMA,
        "target": reports[0]["target"],
        "image": reports[0]["image"] if len({r["image"] for r in reports}) == 1 else sorted({r["image"] for r in reports}),
        "commit": reports[0]["commit"] if len({r["commit"] for r in reports}) == 1 else sorted({r["commit"] for r in reports}),
        "task": reports[0]["task"],
        "filter": ",".join(filters),
        "started": min(r["started"] for r in reports),
        "finished": max(r["finished"] for r in reports),
        "run_url": run_url() or reports[0].get("run_url"),
        "gradle_exit": max(exits) if exits else None,
        "merged_from": len(reports),
        "specs": specs,
        "totals": totals_of(specs),
        "known_skips_applied": [],
    }
    skips = load_skips(Path(args.skips), root) if args.skips and Path(args.skips).is_file() else []
    apply_skips(merged, skips)
    return merged


# --- Markdown -----------------------------------------------------------------------------------------------------
def markdown(report: dict[str, Any]) -> str:
    t = report["totals"]
    lines = [
        f"## Parity report — target `{report['target']}`, task `{report['task']}`",
        "",
        f"- image: `{report['image']}` · commit `{str(report['commit'])[:12]}` · filter: `{report['filter'] or '(all)'}`",
        f"- started {report['started']} · finished {report['finished']}"
        + (f" · [run]({report['run_url']})" if report.get("run_url") else ""),
        f"- **{t['passed']}/{t['tests']} passed**, {t['failed']} failed, {t['errors']} errors, {t['skipped']} skipped,"
        f" {t['specs']} specs, {t['duration_s']:.1f}s — unexcused failures: **{t['unexcused_failures']}**",
    ]
    if t["tests"] == 0:
        lines.append("- **no test ran** — this is an infrastructure failure, not a pass")
    lines += ["", "| spec | tests | passed | failed | errors | skipped | s |", "|---|---:|---:|---:|---:|---:|---:|"]
    for s in report["specs"]:
        short = s["class"].replace("org.rundeck.tests.functional.api.", "")
        lines.append(f"| `{short}` | {s['tests']} | {s['passed']} | {s['failed']} | {s['errors']} | {s['skipped']} | {s['duration_s']:.1f} |")
    failures = [(s["class"], f) for s in report["specs"] for f in s["failures"]]
    if failures:
        lines += ["", "### Failures", ""]
        for cls, f in failures:
            tag = " _(excused)_" if f.get("excused") else ""
            msg = f["message"].replace("|", "\\|").replace("\n", " ")[:200]
            lines.append(f"- `{cls.rsplit('.', 1)[-1]}` › {f['test']} — {f['kind']}: {msg}{tag}")
    if report["known_skips_applied"]:
        lines += ["", "### Known skips applied (tests/parity-skips.toml)", ""]
        for k in report["known_skips_applied"]:
            lines.append(f"- `{k['spec']}` / `{k['test']}` — {k['status']} ({k['ref']}): {k['reason']} → {len(k['matched'])} matched")
    return "\n".join(lines) + "\n"


# --- CLI --------------------------------------------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="parity-report.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("inputs", nargs="+", metavar="INPUT", help="JUnit XML files (build) or JSON reports (--merge)")
    parser.add_argument("--merge", action="store_true", help="merge JSON reports instead of reading JUnit XML")
    parser.add_argument("--out", help="write the JSON report here (omit to only print --markdown)")
    parser.add_argument("--markdown", action="store_true", help="print a Markdown summary to stdout")
    parser.add_argument("--gate", action="store_true", help="exit 1 on unexcused failures or when no test ran")
    parser.add_argument("--target", choices=("legacy", "rdx"), help="(build) server under test")
    parser.add_argument("--image", help="(build) image or binary identifier of the server under test")
    parser.add_argument("--task", help="(build) Gradle test task, e.g. apiTest")
    parser.add_argument("--filter", default="", help="(build) filter given to parity.sh")
    parser.add_argument("--started", help="(build) ISO-8601 start time")
    parser.add_argument("--finished", help="(build) ISO-8601 end time")
    parser.add_argument("--commit", help="(build) git commit (default: git rev-parse HEAD)")
    parser.add_argument("--gradle-exit", type=int, default=None, help="(build) exit code of the Gradle run")
    parser.add_argument("--skips", default=None, help="tests/parity-skips.toml (default: <root>/tests/parity-skips.toml)")
    parser.add_argument("--root", default=None, help="repository root (default: parent of this script's directory)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent.parent
    if args.skips is None:
        args.skips = str(root / "tests" / "parity-skips.toml")
    if not args.out and not args.markdown:
        parser.error("nothing to do: pass --out and/or --markdown")

    if args.merge:
        report = merge_reports(args, root)
    else:
        for required in ("target", "image", "task"):
            if not getattr(args, required):
                parser.error(f"--{required} is required to build a report from JUnit XML")
        report = build_report(args, root)

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, sort_keys=False)
            fh.write("\n")
        print(f"wrote {out}", file=sys.stderr)
    if args.markdown:
        sys.stdout.write(markdown(report))

    if args.gate:
        t = report["totals"]
        if t["tests"] == 0:
            print("gate: FAIL — no test ran", file=sys.stderr)
            return 1
        if t["unexcused_failures"] > 0:
            print(f"gate: FAIL — {t['unexcused_failures']} unexcused failure(s)", file=sys.stderr)
            return 1
        print(f"gate: PASS — {t['passed']}/{t['tests']} passed, {len(report['known_skips_applied'])} known skip(s) applied", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
