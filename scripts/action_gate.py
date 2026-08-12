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

from specanvil.check import gate


def main() -> int:
    pattern = sys.argv[1] if len(sys.argv) > 1 else "**/machine/spec.yaml"
    explain = len(sys.argv) > 2 and sys.argv[2].lower() == "true"
    files = sorted(glob.glob(pattern, recursive=True))
    if not files:
        print(f"::notice::SpecAnvil: no spec files matched {pattern!r}")
        return 0
    worst = 0
    for raw in files:
        verdict = gate(Path(raw), explain=explain)
        fails, warns = verdict["fail"], verdict["warn"]
        print(f"::group::SpecAnvil {raw} — {verdict['result']} (FAIL {len(fails)} / WARN {len(warns)})")
        for e in fails:
            print(f"::error file={raw},line=1::{e}")
        for w in warns:
            print(f"::warning file={raw},line=1::{w}")
        for g in verdict.get("ready_gap") or []:
            print(f"::notice file={raw},line=1::READY-GAP: {g}")
        print("::endgroup::")
        worst = max(worst, 1 if fails else 0)
    print(f"SpecAnvil gated {len(files)} spec(s); result: {'FAIL' if worst else 'PASS'}")
    return worst


if __name__ == "__main__":
    sys.exit(main())
