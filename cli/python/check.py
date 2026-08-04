#!/usr/bin/env python3
"""Minimal hard-gate checker for machine specs (YAML/JSON)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None


REQUIRED_TOP = ["spec_version", "id", "title", "status", "behaviors", "acceptance"]


def load(path: Path):
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            print("FAIL: PyYAML not installed. pip install pyyaml  OR use JSON spec  OR degraded Skill mode.")
            sys.exit(4)
        return yaml.safe_load(text)
    if path.suffix.lower() == ".json":
        return json.loads(text)
    print(f"FAIL: unsupported suffix {path.suffix} (use .yaml/.yml/.json)")
    sys.exit(2)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: check.py <machine-spec>")
        return 2
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"FAIL: file not found: {path}")
        return 2
    data = load(path)
    if not isinstance(data, dict):
        print("FAIL: root must be an object")
        return 1
    errors = []
    for key in REQUIRED_TOP:
        if key not in data:
            errors.append(f"missing required field: {key}")
    behaviors = data.get("behaviors") or []
    acceptance = data.get("acceptance") or []
    if isinstance(behaviors, list) and len(behaviors) < 1:
        errors.append("behaviors must have at least 1 item")
    if isinstance(acceptance, list) and len(acceptance) < 1:
        errors.append("acceptance must have at least 1 item")
    open_qs = data.get("open_questions") or []
    if data.get("status") == "ready" and open_qs:
        errors.append("status=ready but open_questions is not empty")

    print("gate_mode: hard")
    print(f"runtime: python")
    print(f"file: {path}")
    if errors:
        print("RESULT: FAIL")
        for e in errors:
            print(f"- {e}")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
