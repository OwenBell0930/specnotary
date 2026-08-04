#!/usr/bin/env python3
from __future__ import annotations

import json
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
    # allow per-spec hint
    if isinstance(data, dict) and isinstance(data.get("project_hint"), dict):
        project = {**project, **data["project_hint"]}

    errors = validate(data, project)
    print("gate_mode: hard")
    print("runtime: python")
    print(f"file: {path}")
    if project.get("object_ai_weight"):
        print(f"object_ai_weight: {project.get('object_ai_weight')}")
    if errors:
        print("RESULT: FAIL")
        for e in errors:
            print(f"- {e}")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
