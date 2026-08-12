#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from libproto import default_manifest_path  # noqa: E402
from libspec import default_human_path, load_project, load_spec, spec_hash, validate  # noqa: E402


def main() -> int:
    if len(sys.argv) not in {2, 3, 4}:
        print("Usage: check.py <machine-spec.yaml|json> [human.md] [prototype.manifest.yaml]")
        return 2
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"FAIL: file not found: {path}")
        return 2
    human = Path(sys.argv[2]) if len(sys.argv) >= 3 else default_human_path(path)
    manifest = Path(sys.argv[3]) if len(sys.argv) == 4 else default_manifest_path(path)
    try:
        data = load_spec(path)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        return 4 if "PyYAML" in str(exc) else 2

    project = load_project(ROOT)
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
        print("NOTE: PASS with WARN — resolve or accept explicitly before treating as review-ready")
    return 0


if __name__ == "__main__":
    sys.exit(main())
