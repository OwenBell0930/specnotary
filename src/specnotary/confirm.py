#!/usr/bin/env python3
"""Record who accepted remaining WARNs — turns a process hint into a ledger."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from .check import gate
from .libspec import dump_spec, load_spec, warning_id, _accepted_ok

USAGE = (
    "Usage: specnotary confirm <machine-spec.yaml> --by <name> --reason <text> "
    "[--accept-all-warn | --accept <id> ...]"
)


def _parse(argv: list[str]) -> tuple[Path | None, dict[str, str], list[str]]:
    spec: Path | None = None
    flags: dict[str, str] = {}
    accepts: list[str] = []
    accept_all = False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in {"--by", "--reason"}:
            if i + 1 >= len(argv):
                raise ValueError(f"{a} needs a value")
            flags[a] = argv[i + 1]
            i += 2
            continue
        if a == "--accept":
            if i + 1 >= len(argv):
                raise ValueError("--accept needs an id")
            accepts.append(argv[i + 1])
            i += 2
            continue
        if a == "--accept-all-warn":
            accept_all = True
            i += 1
            continue
        if a.startswith("-"):
            raise ValueError(f"unknown flag {a}")
        if spec is not None:
            raise ValueError("unexpected extra argument")
        spec = Path(a)
        i += 1
    flags["_accept_all"] = "1" if accept_all else ""
    return spec, flags, accepts


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        spec, flags, accepts = _parse(argv)
    except ValueError as exc:
        print(f"FAIL: {exc}")
        print(USAGE)
        return 2
    if spec is None or "--by" not in flags or "--reason" not in flags:
        print(USAGE)
        return 2
    if not spec.is_file():
        print(f"FAIL: file not found: {spec}")
        return 2
    by = flags["--by"].strip()
    reason = flags["--reason"].strip()
    if not by or not reason:
        print("FAIL: --by and --reason must be non-empty")
        return 2

    verdict = gate(spec)
    if verdict["result"] == "FAIL":
        print("FAIL: cannot confirm a spec that does not PASS the hard gate")
        for e in verdict["fail"]:
            print(f"  FAIL: {e}")
        return 1

    # Recompute ids against the unfiltered machine by loading and listing
    # remaining (already filtered) warn_ids from the gate.
    remaining = list(verdict.get("warn_ids") or [])
    if not remaining and not verdict["warn"]:
        pass
    elif not remaining:
        remaining = [warning_id(w) for w in verdict["warn"]]

    chosen: list[str]
    if flags.get("_accept_all"):
        chosen = remaining
    else:
        chosen = accepts
        unknown = [c for c in chosen if c not in remaining]
        if unknown:
            print("FAIL: --accept id is not a current WARN: " + ", ".join(unknown))
            print("current:", " ".join(remaining) or "(none)")
            return 2
        leftover = [c for c in remaining if c not in set(chosen)]
        if leftover:
            print("FAIL: unaccepted WARN remain: " + " ".join(leftover))
            print("pass --accept-all-warn or --accept each id")
            return 2

    data = load_spec(spec)
    if not isinstance(data, dict):
        print("FAIL: spec root must be an object")
        return 1
    today = date.today().isoformat()
    existing = [x for x in (data.get("accepted_warnings") or []) if isinstance(x, dict)]
    by_id = {str(x.get("id")): x for x in existing if x.get("id")}
    for code in chosen:
        by_id[code] = {"id": code, "by": by, "date": today, "reason": reason}
    data["accepted_warnings"] = [by_id[k] for k in sorted(by_id) if _accepted_ok(by_id[k]) or k in chosen]
    data["review"] = {
        "confirmed_by": by,
        "confirmed_at": today,
        "reason": reason,
    }
    dump_spec(spec, data)
    print(f"confirmed: {spec} by {by} on {today}")
    if chosen:
        print("accepted: " + " ".join(chosen))
    else:
        print("accepted: (no remaining WARN)")
    print("NEXT: specnotary report <spec>  → 拿去评审")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
