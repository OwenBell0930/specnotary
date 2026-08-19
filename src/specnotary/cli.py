#!/usr/bin/env python3
"""SpecNotary unified CLI: check / human / report / sync."""
from __future__ import annotations

import sys

from . import __version__
from .case import ingest_main, new_main
from .check import gate
from .check import main as check_main
from .confirm import main as confirm_main
from .generate_human import main as human_main
from .markers import main as markers_main
from .mcp import main as mcp_main
from .report import main as report_main
from .sync import main as sync_main


def precommit_main(argv: list[str] | None = None) -> int:
    """pre-commit entry: every argument is a machine spec; aggregate verdicts."""
    import sys as _sys
    from pathlib import Path

    argv = list(_sys.argv[1:] if argv is None else argv)
    if not argv:
        print("Usage: specnotary precommit <machine-spec> [...]")
        return 2
    worst = 0
    for raw in argv:
        verdict = gate(Path(raw))
        mark = "PASS" if verdict["result"] == "PASS" else "FAIL"
        print(f"{mark} {raw} (FAIL {len(verdict['fail'])} / WARN {len(verdict['warn'])})")
        for e in verdict["fail"]:
            print(f"  FAIL: {e}")
        worst = max(worst, int(verdict["exit_code"]))
    return worst


COMMANDS = {
    "new": (new_main, "Start a case from raw material: copy source, pin hash, scaffold draft YAML"),
    "ingest": (ingest_main, "Register another raw file as a source (GitHub spec-kit / OpenSpec markdown included)"),
    "check": (check_main, "Hard gate: schema + rules + evidence chain (--explain, --json)"),
    "human": (human_main, "Generate human construction-grade view (--lang zh|en)"),
    "report": (report_main, "Write the product-manager self-check report"),
    "confirm": (confirm_main, "Record who accepted remaining WARNs and stamp review confirmation"),
    "sync": (sync_main, "Regenerate the human view after machine edits (prototype needs --attest-prototype)"),
    "markers": (markers_main, "Diff data-spec-id markers in a source tree against spec entities (retrofit helper)"),
    "precommit": (precommit_main, "Gate multiple specs at once (pre-commit hook entry)"),
    "mcp": (mcp_main, "Run the stdio MCP server exposing check/gap/report to agents"),
}


def _usage() -> str:
    lines = [f"specnotary {__version__} — forge dev-ready specs on a hard gate", "", "Commands:"]
    for name, (_fn, help_text) in COMMANDS.items():
        lines.append(f"  specnotary {name:<8} {help_text}")
    lines.append("")
    lines.append("Run `specnotary <command>` with no args for per-command usage.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in {"-h", "--help", "help"}:
        print(_usage())
        return 0
    if argv[0] in {"-V", "--version", "version"}:
        print(__version__)
        return 0
    cmd = argv[0]
    if cmd not in COMMANDS:
        print(f"ERROR: unknown command {cmd!r}")
        print(_usage())
        return 2
    return COMMANDS[cmd][0](argv[1:])


if __name__ == "__main__":
    sys.exit(main())
