#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from libspec import load_project, load_spec, validate  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: check.py <machine-spec.yaml|json>")
        return 2
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"FAIL: file not found: {path}")
        return 2
    try:
        data = load_spec(path)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        return 4 if "PyYAML" in str(exc) else 2

    project = load_project(ROOT)
    if isinstance(data, dict) and isinstance(data.get("project_hint"), dict):
        project = {**project, **data["project_hint"]}

    result = validate(data, project)
    fails = result["fail"]
    warns = result["warn"]

    print("gate_mode: hard")
    print("runtime: python")
    print(f"file: {path}")
    if project.get("object_ai_weight"):
        print(f"object_ai_weight: {project.get('object_ai_weight')}")
    print(f"FAIL_COUNT: {len(fails)}")
    print(f"WARN_COUNT: {len(warns)}")
    for e in fails:
        print(f"FAIL: {e}")
    for w in warns:
        print(f"WARN: {w}")
    if fails:
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    if warns:
        print("NOTE: PASS with WARN — resolve or accept explicitly before treating as入库级完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
