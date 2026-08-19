#!/usr/bin/env python3
"""Write the product-manager self-check report from a machine spec."""
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
from .pm_view import (
    disposition_label,
    disposition_meaning,
    format_landing,
    humanize_finding,
    humanize_warning_id,
    proto_bucket_label,
    proto_bucket_meaning,
    status_label,
)

USAGE = "Usage: specnotary report <machine-spec> [out.md]"

DISPOSITION_ORDER = (
    "covered",
    "omitted",
    "assumption",
    "conflict",
    "out_of_scope",
    "pending",
    "undisposed",
)
PROTO_ORDER = ("missing", "extra", "stale", "mismatch", "unverified")


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
    must_fix = list(result.get("fail") or [])
    needs_call = list(result.get("warn") or [])
    spec_id = data.get("id") or "—"
    title = ""
    raw_title = data.get("title")
    if isinstance(raw_title, dict):
        title = str(raw_title.get("zh") or raw_title.get("en") or "").strip()
    elif raw_title:
        title = str(raw_title).strip()

    lines = [
        "# 输出自检报告",
        "",
        "这份报告给产品经理开会用：对照原始需求说明，看规格写了什么、猜了什么、哪里打架、可点页面稿有没有对不上。",
        "结构检查的结论在文末。**这份报告本身不是检查工具**；有必须改的问题，由助手改规格，你不用操作内部文件。",
        "",
        "## 这份规格是哪一份",
        "",
        f"- 规格名称：{title or '（未写中文名称）'}",
        f"- 规格编号：`{spec_id}`（内部对账用，不是界面上的编号）",
        f"- 当前进度：{status_label(str(data.get('status') or ''))}",
        f"- 说明书：`{relpath_from_root(human_path, root)}`" if human_path else "- 说明书：还没有生成",
        f"- 内部规格文件：`{relpath_from_root(spec_path, root)}`（给开发和检查用，开会时看说明书即可）",
        f"- 内容指纹：`{digest}`（用来确认开会时看的是同一版，不是给人读的）",
        f"- 可点页面稿清单：`{relpath_from_root(manifest_path, root)}`"
        if manifest_path
        else "- 可点页面稿清单：还没有提供",
        "",
        "## 结构检查两档，不要混",
        "",
        "| 档 | 条数 | 意思 | 你要做什么 |",
        "|----|------|------|------------|",
        (
            f"| 必须改 | {len(must_fix)} |"
            " 有一条就不能当终稿交出。"
            " 开发和检查工具里对应英文 FAIL。"
            " | 不用你改内部文件；让助手改到这一档为 0。 |"
        ),
        (
            f"| 需要你拍板 | {len(needs_call)} |"
            " 规格里写了原始说明没有的猜测，或可点页面稿还没核实。"
            " 不挡「结构过关」，但业务上你还没认。"
            " 开发和检查工具里对应英文 WARN。"
            " | 认或不认。认了由助手记下是谁、哪天、为什么。 |"
        ),
        "",
        "下文如果出现英文 PASS / FAIL，只是给开发和检查工具对账；对人一律用上表的中文。",
        "",
    ]
    review = data.get("review") if isinstance(data.get("review"), dict) else {}
    if review.get("confirmed_by"):
        lines += [
            f"- 最近一次确认人：{review.get('confirmed_by')} · 日期：{review.get('confirmed_at') or '—'}",
            "",
        ]
    accepted = [x for x in (data.get("accepted_warnings") or []) if isinstance(x, dict)]
    if accepted:
        lines += [
            "## 已经拍过板的提醒",
            "",
            "这些曾经需要你拍板，已经记下是谁认的。开会时可以抽查理由，不需要再认一遍。",
            "",
            "| 提醒编号 | 确认人 | 日期 | 理由 |",
            "|----------|--------|------|------|",
        ]
        for item in accepted:
            lines.append(
                f"| {humanize_warning_id(str(item.get('id') or ''))} | {item.get('by') or '—'} | {item.get('date') or '—'} | {item.get('reason') or '—'} |"
            )
        lines.append("")
    lines += [
        "## 原始说明落到规格里了吗（汇总）",
        "",
        "每一条都来自原始需求说明。处理结果用中文；英文词只在内部文件里出现。",
        "",
        "| 处理结果 | 这条是什么意思 | 条数 |",
        "|----------|----------------|------|",
    ]
    for key in DISPOSITION_ORDER:
        count = len(buckets.get(key) or [])
        lines.append(
            f"| {disposition_label(key)} | {disposition_meaning(key)} | {count} |"
        )
    lines += [
        "",
        "## 逐条明细",
        "",
        "**原料条目编号**是从原始需求说明里拆出来的每一条（例如 `SRC-CLM-001`）。",
        "这个编号只用来和内部规格对账，**不是**页面上的编号，也**不是**功能编号。",
        "",
    ]
    claims = data.get("source_claims") or []
    if not claims:
        lines.append("还没有从原始说明拆出条目。终稿要求至少拆出并写进规格一条，否则结构检查不会通过。")
    else:
        lines.append("| 原料条目编号 | 处理结果 | 这条在说什么 | 落到说明书的哪一段 |")
        lines.append("|--------------|----------|--------------|--------------------|")
        for c in claims:
            if not isinstance(c, dict):
                continue
            cid = c.get("id") or "—"
            disp = str(c.get("disposition") or "").strip()
            summary = c.get("quote_or_summary") or c.get("evidence") or "—"
            landing = format_landing(c, data)
            lines.append(
                f"| `{cid}` | {disposition_label(disp)} | {summary} | {landing} |"
            )
    proto = classify_proto_issues(must_fix, needs_call)
    proto_fail = [e for e in must_fix if e.startswith("prototype")]
    if proto_fail or any(proto[k] for k in proto):
        lines += [
            "",
            "## 可点页面稿对得上吗",
            "",
            "| 情况 | 这条是什么意思 | 条数 |",
            "|------|----------------|------|",
        ]
        for key in PROTO_ORDER:
            lines.append(
                f"| {proto_bucket_label(key)} | {proto_bucket_meaning(key)} | {len(proto[key])} |"
            )
        details = []
        for key in PROTO_ORDER:
            for item in proto[key]:
                if item.startswith("prototype") or "unverified" in item:
                    details.append(f"- {proto_bucket_label(key)}：{humanize_finding(item)}")
        if details:
            lines += ["", "明细：", ""]
            lines += details
    lines += ["", "## 结构检查结论", ""]
    if must_fix:
        lines.append(
            f"**结论：结构未通过。RESULT: FAIL** 有 {len(must_fix)} 条必须先改掉，还不能当终稿交出。"
        )
        lines.append("")
        for e in must_fix:
            lines.append(f"- 必须改：{humanize_finding(e)}")
    else:
        lines.append(
            "**结论：结构通过。RESULT: PASS** 规格在既定规则里自洽，可以拿去开会。"
            "这不表示业务已经拍板，也不表示页面已经验收。"
        )
    if needs_call:
        lines.append("")
        lines.append("还需要你拍板：")
        for w in needs_call:
            lines.append(f"- {humanize_finding(w)}")
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
