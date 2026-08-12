#!/usr/bin/env python3
"""Write a review-readiness report from a machine spec."""
from __future__ import annotations

import sys
from pathlib import Path

from .libproto import classify_proto_issues, default_manifest_path
from .libspec import (
    claim_summary,
    default_human_path,
    find_repo_root,
    load_project_for,
    load_spec,
    relpath_from_root,
    spec_hash,
    validate,
)

USAGE = "Usage: specnotary report <machine-spec> [out.md]"


def render_report(
    data: dict,
    result: dict,
    spec_path: Path,
    human_path: Path | None,
    manifest_path: Path | None = None,
) -> str:
    root = find_repo_root(spec_path)
    buckets = claim_summary(data)
    digest = spec_hash(data)
    lines = [
        "# 评审就绪报告 / Review-readiness report",
        "",
        f"- 机读：`{relpath_from_root(spec_path, root)}`",
        f"- 规格 ID：`{data.get('id')}` · 状态：`{data.get('status')}`",
        f"- 机读哈希：`{digest}`",
        f"- 人读：`{relpath_from_root(human_path, root)}`" if human_path else "- 人读：未提供",
        f"- 原型：`{relpath_from_root(manifest_path, root)}`" if manifest_path else "- 原型：未提供",
        f"- FAIL：{len(result['fail'])} · WARN：{len(result['warn'])}",
        "",
        "## 原料覆盖汇总",
        "",
        "| 处置 | 条数 |",
        "|------|------|",
    ]
    for key in ("covered", "omitted", "assumption", "conflict", "out_of_scope", "pending", "undisposed"):
        lines.append(f"| `{key}` | {len(buckets.get(key) or [])} |")
    lines += ["", "## 明细", ""]
    claims = data.get("source_claims") or []
    if not claims:
        lines.append("无 SourceClaim。覆盖未证明（`status: ready` 为 FAIL）。")
    else:
        lines.append("| ID | 处置 | 摘要 | 引用 / 闭合 |")
        lines.append("|----|------|------|-------------|")
        for c in claims:
            if not isinstance(c, dict):
                continue
            extra = ", ".join(c.get("spec_refs") or []) or (c.get("resolution") or "—")
            lines.append(
                f"| {c.get('id')} | {c.get('disposition')} | {c.get('quote_or_summary') or '—'} | {extra} |"
            )
    proto = classify_proto_issues(result["fail"], result["warn"])
    proto_fail = [e for e in result["fail"] if e.startswith("prototype")]
    if proto_fail or any(proto[k] for k in proto):
        lines += ["", "## 原型一致性", ""]
        lines.append("| 类型 | 条数 |")
        lines.append("|------|------|")
        for key in ("missing", "extra", "stale", "mismatch", "unverified"):
            lines.append(f"| `{key}` | {len(proto[key])} |")
        for key in ("missing", "extra", "stale", "mismatch", "unverified"):
            for item in proto[key]:
                if item.startswith("prototype") or "unverified" in item:
                    lines.append(f"- `{key}`: {item}")
    lines += ["", "## 门禁", ""]
    if result["fail"]:
        lines.append("**RESULT: FAIL**")
        for e in result["fail"]:
            lines.append(f"- FAIL: {e}")
    else:
        lines.append("**RESULT: PASS**")
    for w in result["warn"]:
        lines.append(f"- WARN: {w}")
    lines.append("")
    return "\n".join(lines)


def build_report(spec_path: Path) -> tuple[str, dict]:
    """Shared assembly for CLI and MCP — one resolution path, one verdict.

    The external audit caught the MCP outlet skipping the project_hint merge
    and diverging from the CLI; every outlet must go through here.
    """
    data = load_spec(spec_path)
    if not isinstance(data, dict):
        raise ValueError("root must be object")
    project = load_project_for(spec_path)
    if isinstance(data.get("project_hint"), dict):
        project = {**project, **data["project_hint"]}
    human = default_human_path(spec_path)
    manifest = default_manifest_path(spec_path)
    result = validate(
        data, project, spec_path=spec_path, human_path=human, manifest_path=manifest
    )
    md = render_report(data, result, spec_path, human, manifest)
    return md, result


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) not in {1, 2}:
        print(USAGE)
        return 2
    spec_path = Path(argv[0])
    if not spec_path.exists():
        print(f"FAIL: file not found: {spec_path}")
        return 2
    out = Path(argv[1]) if len(argv) == 2 else spec_path.parent.parent / "reports" / "review-readiness.md"
    try:
        md, result = build_report(spec_path)
    except ValueError as exc:
        print(f"FAIL: {exc}")
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        return 2
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print(f"wrote: {out}")
    print(f"FAIL_COUNT: {len(result['fail'])}")
    print(f"WARN_COUNT: {len(result['warn'])}")
    return 1 if result["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())
