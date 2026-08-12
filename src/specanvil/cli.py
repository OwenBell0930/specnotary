#!/usr/bin/env python3
"""SpecAnvil unified CLI: check / human / report / sync."""
from __future__ import annotations

import sys

from . import __version__
from .check import main as check_main
from .generate_human import main as human_main
from .report import main as report_main
from .sync import main as sync_main

COMMANDS = {
    "check": (check_main, "Hard gate: schema + rules + evidence chain (--explain for ready gap)"),
    "human": (human_main, "Generate human construction-grade view from machine source"),
    "report": (report_main, "Write review-readiness report (coverage + prototype buckets)"),
    "sync": (sync_main, "Regenerate human + refresh prototype hash after machine edits"),
}


def _usage() -> str:
    lines = [f"specanvil {__version__} — forge dev-ready specs on a hard gate", "", "Commands:"]
    for name, (_fn, help_text) in COMMANDS.items():
        lines.append(f"  specanvil {name:<8} {help_text}")
    lines.append("")
    lines.append("Run `specanvil <command>` with no args for per-command usage.")
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
