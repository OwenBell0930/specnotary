#!/usr/bin/env python3
"""Generate the human construction-grade view from the machine source."""
from __future__ import annotations

import sys
from pathlib import Path

from .libspec import (
    find_repo_root,
    load_project_for,
    load_spec,
    relpath_from_root,
    render_human,
    validate,
)

USAGE = "Usage: specanvil human <machine-spec> [out.md] [--allow-invalid]"


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    allow_invalid = "--allow-invalid" in argv
    args = [a for a in argv if a != "--allow-invalid"]
    if len(args) not in {1, 2}:
        print(USAGE)
        return 2
    src = Path(args[0])
    if not src.exists():
        print(f"FAIL: file not found: {src}")
        return 2
    out = Path(args[1]) if len(args) == 2 else src.with_suffix(".human.md")
    try:
        data = load_spec(src)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        return 4 if "PyYAML" in str(exc) else 2
    if not isinstance(data, dict):
        print("FAIL: root must be object")
        return 1

    project = load_project_for(src)
    if isinstance(data.get("project_hint"), dict):
        project = {**project, **data["project_hint"]}
    result = validate(data, project, spec_path=src, check_human=False)

    if result["fail"] and not allow_invalid:
        print("FAIL: machine spec has FAIL items — refuse to write human view")
        print("Hint: fix FAIL first, or pass --allow-invalid to force generate")
        for e in result["fail"]:
            print(f"FAIL: {e}")
        for w in result["warn"]:
            print(f"WARN: {w}")
        return 1

    md = render_human(data, source=relpath_from_root(src, find_repo_root(src)), gate_mode="hard")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print(f"wrote: {out}")
    if result["fail"]:
        print("NOTE: generated with --allow-invalid despite FAIL")
        for e in result["fail"]:
            print(f"FAIL: {e}")
    for w in result["warn"]:
        print(f"WARN: {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
