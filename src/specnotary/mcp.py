#!/usr/bin/env python3
"""Minimal MCP (Model Context Protocol) stdio server.

Exposes the gate to agents as tools — check_spec / ready_gap / review_report.
Newline-delimited JSON-RPC 2.0 over stdio, zero extra dependencies. The
server is a thin adapter: all semantics live in check.gate / libspec, so an
agent calling this can never get a different verdict than the CLI.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import __version__
from .check import gate
from .libspec import load_project_for, load_spec, ready_gap

PROTOCOL_VERSION = "2024-11-05"

TOOLS = [
    {
        "name": "check_spec",
        "description": (
            "Run the deterministic hard gate on a machine spec file "
            "(schema, rules, source coverage, human staleness, prototype consistency). "
            "Returns FAIL/WARN lists and the verdict."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Path to machine spec YAML/JSON"}},
            "required": ["path"],
        },
    },
    {
        "name": "ready_gap",
        "description": "For a draft spec: list which FAILs would appear if status flipped to ready right now.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Path to machine spec YAML/JSON"}},
            "required": ["path"],
        },
    },
    {
        "name": "review_report",
        "description": "Render the review-readiness report (source coverage + prototype buckets) as markdown.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Path to machine spec YAML/JSON"}},
            "required": ["path"],
        },
    },
]


def _tool_check_spec(path: str) -> str:
    return json.dumps(gate(Path(path)), ensure_ascii=False, indent=2)


def _tool_ready_gap(path: str) -> str:
    p = Path(path)
    data = load_spec(p)
    if not isinstance(data, dict):
        return json.dumps({"error": "root must be object"})
    project = load_project_for(p)
    if isinstance(data.get("project_hint"), dict):
        project = {**project, **data["project_hint"]}
    gap = ready_gap(data, project, spec_path=p)
    return json.dumps(
        {"status": data.get("status"), "ready_gap": gap, "count": len(gap)},
        ensure_ascii=False,
        indent=2,
    )


def _tool_review_report(path: str) -> str:
    from .report import build_report  # noqa: PLC0415

    md, _result = build_report(Path(path))
    return md


def _handle(req: dict) -> dict | None:
    method = req.get("method")
    rid = req.get("id")
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": rid,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "specnotary", "version": __version__},
            },
        }
    if method in {"notifications/initialized", "initialized"}:
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = req.get("params") or {}
        name = params.get("name")
        args = params.get("arguments") or {}
        handlers = {
            "check_spec": _tool_check_spec,
            "ready_gap": _tool_ready_gap,
            "review_report": _tool_review_report,
        }
        if name not in handlers:
            return {
                "jsonrpc": "2.0",
                "id": rid,
                "error": {"code": -32602, "message": f"unknown tool: {name}"},
            }
        try:
            text = handlers[name](str(args.get("path", "")))
            is_error = False
        except Exception as exc:  # noqa: BLE001
            text = f"tool error: {exc}"
            is_error = True
        return {
            "jsonrpc": "2.0",
            "id": rid,
            "result": {"content": [{"type": "text", "text": text}], "isError": is_error},
        }
    if rid is not None:
        return {
            "jsonrpc": "2.0",
            "id": rid,
            "error": {"code": -32601, "message": f"method not found: {method}"},
        }
    return None


def main(argv: list[str] | None = None) -> int:  # noqa: ARG001
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = _handle(req)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
