#!/usr/bin/env python3
"""Retrofit reconciliation: diff data-spec-id markers in a source tree
against spec entities.

Existing projects were built without markers; before they can use the
prototype gate they need data-spec-id retrofitted into their DOM/JSX.
This command answers: which markers already exist, which are unknown to
the spec, and which required controls/behaviors are still unmarked.
Informational only — it is not a gate and always exits 0 on success.
"""
from __future__ import annotations

import sys
from pathlib import Path

from .libproto import _CODE_SUFFIXES, _html_spec_ids, _required_behaviors, _required_spec_controls
from .libspec import known_entity_ids, load_spec

USAGE = "Usage: specanvil markers <machine-spec.yaml|json> <source-dir>"
SCAN_SUFFIXES = {".html", ".htm"} | _CODE_SUFFIXES
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "coverage", "__pycache__"}


def scan_markers(source_dir: Path) -> dict[str, list[str]]:
    """marker id -> files (relative) that declare it, comments excluded."""
    found: dict[str, list[str]] = {}
    for path in sorted(source_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            ids = _html_spec_ids(path)
        except (OSError, UnicodeDecodeError):
            continue
        rel = str(path.relative_to(source_dir))
        for marker in ids:
            found.setdefault(marker, []).append(rel)
    return found


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print(USAGE)
        return 2
    spec_path, source_dir = Path(argv[0]), Path(argv[1])
    if not spec_path.is_file():
        print(f"FAIL: file not found: {spec_path}")
        return 2
    if not source_dir.is_dir():
        print(f"FAIL: directory not found: {source_dir}")
        return 2
    try:
        data = load_spec(spec_path)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        return 4 if "PyYAML" in str(exc) else 2
    if not isinstance(data, dict):
        print("FAIL: root must be object")
        return 1

    entities = known_entity_ids(data)
    found = scan_markers(source_dir)
    matched = {m: fs for m, fs in found.items() if m in entities}
    unknown = {m: fs for m, fs in found.items() if m not in entities}
    required = sorted(set(_required_spec_controls(data)) | set(_required_behaviors(data)))
    unmarked = [rid for rid in required if rid not in found]

    print(f"spec: {spec_path}")
    print(f"source: {source_dir}")
    print(f"MARKERS_FOUND: {len(found)}")
    print(f"MATCHED: {len(matched)}")
    for m, fs in sorted(matched.items()):
        print(f"  ok {m}  ({fs[0]}{' +' + str(len(fs) - 1) if len(fs) > 1 else ''})")
    print(f"UNKNOWN: {len(unknown)}")
    for m, fs in sorted(unknown.items()):
        print(f"  ?? {m}  ({fs[0]}) — not a spec entity")
    print(f"REQUIRED_UNMARKED: {len(unmarked)}")
    for rid in unmarked:
        print(f"  .. {rid} — add data-spec-id=\"{rid}\" to its element")
    if not found:
        print("NOTE: no markers yet — retrofit data-spec-id first, then write prototype.manifest.yaml")
    return 0


if __name__ == "__main__":
    sys.exit(main())
