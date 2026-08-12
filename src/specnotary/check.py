#!/usr/bin/env python3
"""Hard gate: schema + deterministic rules + evidence chain."""
from __future__ import annotations

import json
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

USAGE = "Usage: specnotary check <machine-spec.yaml|json> [human.md] [prototype.manifest.yaml] [--explain] [--json]"


def gate(
    path: Path,
    human: Path | None = None,
    manifest: Path | None = None,
    *,
    explain: bool = False,
) -> dict:
    """Run the gate and return a machine-readable verdict.

    Single source for CLI text output, --json, the pre-commit hook, the
    GitHub Action and the MCP server — integrations must never re-implement
    gate semantics.
    """
    verdict: dict = {
        "gate_mode": "hard",
        "runtime": "python",
        "file": str(path),
        "result": "ERROR",
        "exit_code": 2,
        "fail": [],
        "warn": [],
    }
    if not path.exists():
        verdict["fail"] = [f"file not found: {path}"]
        return verdict
    resolved_human = human if human is not None else default_human_path(path)
    resolved_manifest = manifest if manifest is not None else default_manifest_path(path)
    try:
        data = load_spec(path)
    except Exception as exc:  # noqa: BLE001
        verdict["fail"] = [str(exc)]
        verdict["exit_code"] = 4 if "PyYAML" in str(exc) else 2
        return verdict

    project = load_project_for(path)
    if isinstance(data, dict) and isinstance(data.get("project_hint"), dict):
        project = {**project, **data["project_hint"]}

    result = validate(
        data, project, spec_path=path, human_path=resolved_human, manifest_path=resolved_manifest
    )
    verdict.update(
        {
            "human": str(resolved_human) if resolved_human is not None else None,
            "prototype": str(resolved_manifest) if resolved_manifest is not None else None,
            "fail": result["fail"],
            "warn": result["warn"],
        }
    )
    if isinstance(data, dict):
        verdict["spec_hash"] = spec_hash(data)
        verdict["summary"] = {
            "status": data.get("status"),
            "behaviors": len(data.get("behaviors") or []),
            "acceptance": len(data.get("acceptance") or []),
            "claims": len(data.get("source_claims") or []),
            "pending": len(data.get("pending") or []),
        }
        if project.get("object_ai_weight"):
            verdict["object_ai_weight"] = project.get("object_ai_weight")
        if explain and data.get("status") != "ready":
            verdict["ready_gap"] = ready_gap(
                data,
                project,
                spec_path=path,
                human_path=resolved_human,
                manifest_path=resolved_manifest,
            )
    verdict["result"] = "FAIL" if result["fail"] else "PASS"
    verdict["exit_code"] = 1 if result["fail"] else 0
    return verdict


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    explain = "--explain" in argv
    as_json = "--json" in argv
    argv = [a for a in argv if a not in {"--explain", "--json"}]
    if len(argv) not in {1, 2, 3}:
        print(USAGE)
        return 2
    path = Path(argv[0])
    human = Path(argv[1]) if len(argv) >= 2 else None
    manifest = Path(argv[2]) if len(argv) == 3 else None

    verdict = gate(path, human, manifest, explain=explain)

    if as_json:
        print(json.dumps(verdict, ensure_ascii=False, indent=2))
        return int(verdict["exit_code"])

    if verdict["result"] == "ERROR":
        for e in verdict["fail"]:
            print(f"FAIL: {e}")
        return int(verdict["exit_code"])

    print("gate_mode: hard")
    print("runtime: python")
    print(f"file: {verdict['file']}")
    if verdict.get("human"):
        print(f"human: {verdict['human']}")
    if verdict.get("prototype"):
        print(f"prototype: {verdict['prototype']}")
    if verdict.get("spec_hash"):
        print(f"spec_hash: {verdict['spec_hash']}")
    if verdict.get("summary"):
        s = verdict["summary"]
        print(
            "SUMMARY: status={} behaviors={} acceptance={} claims={} pending={}".format(
                s["status"], s["behaviors"], s["acceptance"], s["claims"], s["pending"]
            )
        )
    if verdict.get("object_ai_weight"):
        print(f"object_ai_weight: {verdict['object_ai_weight']}")
    print(f"FAIL_COUNT: {len(verdict['fail'])}")
    print(f"WARN_COUNT: {len(verdict['warn'])}")
    for e in verdict["fail"]:
        print(f"FAIL: {e}")
    for w in verdict["warn"]:
        print(f"WARN: {w}")
    if "ready_gap" in verdict:
        gap = verdict["ready_gap"]
        print(f"READY_GAP_COUNT: {len(gap)}")
        for g in gap:
            print(f"READY-GAP: {g}")
        if not gap and not verdict["fail"]:
            print("NOTE: no gap — this draft would pass as ready right now")
    if verdict["result"] == "FAIL":
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    if verdict["warn"]:
        print("NOTE: PASS with WARN — resolve or accept explicitly before treating as review-ready")
    return 0


if __name__ == "__main__":
    sys.exit(main())
