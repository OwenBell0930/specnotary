#!/usr/bin/env python3
"""Hard gate: schema + deterministic rules + evidence chain."""
from __future__ import annotations

import sys
from pathlib import Path

from .libproto import default_manifest_path
from .libspec import (
    default_human_path,
    load_project_for,
    load_spec,
    ready_gap,
    spec_hash,
    validate,
)

USAGE = "Usage: specanvil check <machine-spec.yaml|json> [human.md] [prototype.manifest.yaml] [--explain]"


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    explain = "--explain" in argv
    argv = [a for a in argv if a != "--explain"]
    if len(argv) not in {1, 2, 3}:
        print(USAGE)
        return 2
    path = Path(argv[0])
    if not path.exists():
        print(f"FAIL: file not found: {path}")
        return 2
    human = Path(argv[1]) if len(argv) >= 2 else default_human_path(path)
    manifest = Path(argv[2]) if len(argv) == 3 else default_manifest_path(path)
    try:
        data = load_spec(path)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        return 4 if "PyYAML" in str(exc) else 2

    project = load_project_for(path)
    if isinstance(data, dict) and isinstance(data.get("project_hint"), dict):
        project = {**project, **data["project_hint"]}

    result = validate(
        data, project, spec_path=path, human_path=human, manifest_path=manifest
    )
    fails = result["fail"]
    warns = result["warn"]

    print("gate_mode: hard")
    print("runtime: python")
    print(f"file: {path}")
    if human is not None:
        print(f"human: {human}")
    if manifest is not None:
        print(f"prototype: {manifest}")
    if isinstance(data, dict):
        print(f"spec_hash: {spec_hash(data)}")
        print(
            "SUMMARY: status={} behaviors={} acceptance={} claims={} pending={}".format(
                data.get("status"),
                len(data.get("behaviors") or []),
                len(data.get("acceptance") or []),
                len(data.get("source_claims") or []),
                len(data.get("pending") or []),
            )
        )
    if project.get("object_ai_weight"):
        print(f"object_ai_weight: {project.get('object_ai_weight')}")
    print(f"FAIL_COUNT: {len(fails)}")
    print(f"WARN_COUNT: {len(warns)}")
    for e in fails:
        print(f"FAIL: {e}")
    for w in warns:
        print(f"WARN: {w}")

    if explain and isinstance(data, dict) and data.get("status") != "ready":
        gap = ready_gap(
            data, project, spec_path=path, human_path=human, manifest_path=manifest
        )
        print(f"READY_GAP_COUNT: {len(gap)}")
        for g in gap:
            print(f"READY-GAP: {g}")
        if not gap and not fails:
            print("NOTE: no gap — this draft would pass as ready right now")

    if fails:
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    if warns:
        print("NOTE: PASS with WARN — resolve or accept explicitly before treating as review-ready")
    return 0


if __name__ == "__main__":
    sys.exit(main())
