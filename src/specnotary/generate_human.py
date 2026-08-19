#!/usr/bin/env python3
"""Generate the human construction-grade view from the machine source."""
from __future__ import annotations

import sys
from pathlib import Path

from .libspec import (
    expected_human_path,
    find_repo_root,
    load_project_for,
    load_spec,
    relpath_from_root,
    render_human,
    validate,
)

USAGE = "Usage: specnotary human <machine-spec> [out.md] [--allow-invalid] [--lang zh|en]"


def _pop_lang(argv: list[str]) -> tuple[list[str], str]:
    lang = "zh"
    out: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a.startswith("--lang="):
            lang = a.split("=", 1)[1].strip() or "zh"
        elif a == "--lang" and i + 1 < len(argv):
            lang = argv[i + 1].strip() or "zh"
            i += 1
        else:
            out.append(a)
        i += 1
    return out, lang


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    argv, lang = _pop_lang(argv)
    if lang not in {"zh", "en"}:
        print(f"FAIL: unsupported lang {lang!r} (zh|en)")
        return 2
    allow_invalid = "--allow-invalid" in argv
    args = [a for a in argv if a != "--allow-invalid"]
    if len(args) not in {1, 2}:
        print(USAGE)
        return 2
    src = Path(args[0])
    if not src.exists():
        print(f"FAIL: file not found: {src}")
        return 2
    if len(args) == 2:
        out = Path(args[1])
    elif src.resolve().parent.name == "machine":
        # Standard layout: write where the gate will look for it.
        out = expected_human_path(src) or src.with_suffix(".human.md")
    else:
        out = src.with_suffix(".human.md")
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

    # The human view derives from the machine source alone. Prototype
    # attestation is a separate, later concern — letting a stale prototype
    # block regeneration made `sync` unusable on any project with a prototype
    # and left users unable to tell "human not synced" from "prototype not
    # re-endorsed".
    blocking = [e for e in result["fail"] if not e.startswith("prototype")]
    proto_fails = [e for e in result["fail"] if e.startswith("prototype")]

    if blocking and not allow_invalid:
        print("FAIL: machine spec has FAIL items — refuse to write human view")
        print("Hint: fix FAIL first, or pass --allow-invalid to force generate")
        for e in blocking:
            print(f"FAIL: {e}")
        for w in result["warn"]:
            print(f"WARN: {w}")
        return 1

    # A human view forced past a failing gate must never carry the hard stamp.
    mode = "hard" if not blocking else "degraded"
    md = render_human(data, source=relpath_from_root(src, find_repo_root(src)), gate_mode=mode, lang=lang)
    if blocking:
        md = md.replace(
            f"<!-- gate_mode: {mode} -->",
            f"<!-- gate_mode: {mode} -->\n<!-- forced: --allow-invalid, FAIL_COUNT={len(blocking)} -->",
            1,
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print(f"wrote: {out}")
    if blocking:
        print(f"NOTE: generated with --allow-invalid despite FAIL — stamped gate_mode: {mode}")
        for e in blocking:
            print(f"FAIL: {e}")
    for e in proto_fails:
        print(f"NOTE: human view regenerated; prototype still needs re-attestation — {e}")
    for w in result["warn"]:
        print(f"WARN: {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
