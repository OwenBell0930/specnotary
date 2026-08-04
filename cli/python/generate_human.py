#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from libspec import load_spec, render_human, validate  # noqa: E402


def main() -> int:
    if len(sys.argv) not in {2, 3}:
        print("Usage: generate_human.py <machine-spec> [out.md]")
        return 2
    src = Path(sys.argv[1])
    if not src.exists():
        print(f"FAIL: file not found: {src}")
        return 2
    out = Path(sys.argv[2]) if len(sys.argv) == 3 else src.with_suffix(".human.md")
    try:
        data = load_spec(src)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        return 4 if "PyYAML" in str(exc) else 2
    if not isinstance(data, dict):
        print("FAIL: root must be object")
        return 1
    result = validate(data, {})
    md = render_human(data, source=str(src), gate_mode="hard")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print(f"wrote: {out}")
    if result["fail"]:
        print("NOTE: source has FAIL items; human view still generated")
        for e in result["fail"]:
            print(f"FAIL: {e}")
    for w in result["warn"]:
        print(f"WARN: {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
