#!/usr/bin/env python3
"""Write a review-readiness report from a machine spec."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from libproto import classify_proto_issues, default_manifest_path  # noqa: E402
from libspec import (  # noqa: E402
    claim_summary,
    default_human_path,
    load_project,
    load_spec,
    relpath_from_root,
    spec_hash,
    validate,
)


def render_report(
    data: dict,
    result: dict,
    spec_path: Path,
    human_path: Path | None,
    manifest_path: Path | None = None,
) -> str:
    buckets = claim_summary(data)
    digest = spec_hash(data)
    lines = [
        "# 评审就绪报告 / Review-readiness report",
        "",
        f"- 机读：`{relpath_from_root(spec_path, ROOT)}`",
        f"- 规格 ID：`{data.get('id')}` · 状态：`{data.get('status')}`",
        f"- 机读哈希：`{digest}`",
        f"- 人读：`{relpath_from_root(human_path, ROOT)}`" if human_path else "- 人读：未提供",
        f"- 原型：`{relpath_from_root(manifest_path, ROOT)}`" if manifest_path else "- 原型：未提供",
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


def main() -> int:
    if len(sys.argv) not in {2, 3}:
        print("Usage: report.py <machine-spec> [out.md]")
        return 2
    spec_path = Path(sys.argv[1])
    if not spec_path.exists():
        print(f"FAIL: file not found: {spec_path}")
        return 2
    out = Path(sys.argv[2]) if len(sys.argv) == 3 else spec_path.parent.parent / "reports" / "review-readiness.md"
    try:
        data = load_spec(spec_path)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        return 2
    if not isinstance(data, dict):
        print("FAIL: root must be object")
        return 1
    project = load_project(ROOT)
    if isinstance(data.get("project_hint"), dict):
        project = {**project, **data["project_hint"]}
    human = default_human_path(spec_path)
    manifest = default_manifest_path(spec_path)
    result = validate(
        data, project, spec_path=spec_path, human_path=human, manifest_path=manifest
    )
    md = render_report(data, result, spec_path, human, manifest)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print(f"wrote: {out}")
    print(f"FAIL_COUNT: {len(result['fail'])}")
    print(f"WARN_COUNT: {len(result['warn'])}")
    return 1 if result["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())
