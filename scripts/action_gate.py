#!/usr/bin/env python3
"""GitHub Action entry: gate every matched spec, emit workflow annotations.

FAILs surface as ::error annotations on the spec file (file-level — the gate
does not track YAML line numbers), WARNs as ::warning. Exits 1 if any spec
fails, so the check blocks the PR.
"""
from __future__ import annotations

import glob
import sys
from pathlib import Path

from specnotary.check import gate


def main() -> int:
    pattern = sys.argv[1] if len(sys.argv) > 1 else "**/machine/spec.yaml"
    explain = len(sys.argv) > 2 and sys.argv[2].lower() == "true"
    files = sorted(glob.glob(pattern, recursive=True))
    if not files:
        print(f"::notice::SpecNotary: no spec files matched {pattern!r}")
        return 0
    worst = 0
    for raw in files:
        verdict = gate(Path(raw), explain=explain)
        fails, warns = verdict["fail"], verdict["warn"]
        layers = verdict.get("fail_by_layer") or {}
        summary = " ".join(f"{k}={len(v)}" for k, v in layers.items()) or "clean"
        print(f"::group::SpecNotary {raw} — {verdict['result']} [{summary}]")
        # Reviewers need to know which artifact to touch, not just that it failed.
        FIX = {
            "machine": "edit the machine spec",
            "source": "re-review SourceClaims / update content_hash",
            "human": "run: specnotary sync <spec>",
            "prototype": "re-verify the prototype, then: specnotary sync <spec> --attest-prototype",
        }
        for layer, items in layers.items():
            print(f"::notice file={raw},line=1::{len(items)} {layer} finding(s) — {FIX.get(layer, '')}")
        for e in fails:
            print(f"::error file={raw},line=1::{e}")
        for w in warns:
            print(f"::warning file={raw},line=1::{w}")
        for g in verdict.get("ready_gap") or []:
            print(f"::notice file={raw},line=1::READY-GAP: {g}")
        print("::endgroup::")
        worst = max(worst, 1 if fails else 0)
    print(f"SpecNotary gated {len(files)} spec(s); result: {'FAIL' if worst else 'PASS'}")
    return worst


if __name__ == "__main__":
    sys.exit(main())
