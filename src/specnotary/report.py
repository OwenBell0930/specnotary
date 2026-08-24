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
    ready_gap,
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


def _plain_text(value) -> str:
    if isinstance(value, dict):
        for key in ("zh", "en", "label", "name", "text", "question", "missing", "id"):
            if value.get(key):
                return _plain_text(value[key])
        return ""
    if value is None:
        return ""
    return " ".join(str(value).split())


def _table_cell(value) -> str:
    return _plain_text(value).replace("|", "\\|") or "—"


def _display_path(path: Path, root: Path) -> str:
    """Use portable repo paths in shipped samples, absolute paths in ad-hoc cases."""
    if (root / ".git").exists() or (root / "project.yaml").is_file():
        return relpath_from_root(path, root)
    return str(path.resolve())


def _review_items(data: dict) -> list[str]:
    """Business questions that belong in the PM review, not hidden in draft state."""
    items: list[str] = []
    closed = {"closed", "resolved", "done", "decided"}
    for pending in data.get("pending") or []:
        if not isinstance(pending, dict):
            continue
        if str(pending.get("status") or "").strip().lower() in closed:
            continue
        pid = pending.get("id") or "未编号"
        missing = _plain_text(pending.get("missing")) or "未写清要补什么"
        impact = _plain_text(pending.get("impact"))
        owner = _plain_text(pending.get("owner"))
        detail = f"未决事项 {pid}：{missing}"
        if impact:
            detail += f"；不拍板的影响：{impact}"
        if owner:
            detail += f"；拍板人：{owner}"
        items.append(detail)
    for decision in data.get("decisions") or []:
        if not isinstance(decision, dict):
            continue
        if str(decision.get("status") or "").strip().lower() == "decided" and decision.get("chosen"):
            continue
        did = decision.get("id") or "未编号"
        question = _plain_text(decision.get("question")) or "未写清要决定什么"
        options = " / ".join(
            _plain_text(option) for option in (decision.get("options") or []) if _plain_text(option)
        )
        items.append(f"待拍板 {did}：{question}" + (f"；可选：{options}" if options else ""))
    for claim in data.get("source_claims") or []:
        if not isinstance(claim, dict):
            continue
        disposition = str(claim.get("disposition") or "").strip()
        resolution = _plain_text(claim.get("resolution"))
        if disposition == "conflict" and resolution.lower() not in {"", "open", "pending", "tbd", "待确认", "未决"}:
            continue
        if disposition not in {"omitted", "conflict", "pending"}:
            continue
        cid = claim.get("id") or "未编号"
        summary = _plain_text(claim.get("quote_or_summary") or claim.get("evidence")) or "未写摘要"
        label = {
            "omitted": "原料有但规格没写",
            "conflict": "原料互相打架",
            "pending": "原料处理方式还没定",
        }[disposition]
        items.append(f"原料条目 {cid}（{label}）：{summary}")
    return list(dict.fromkeys(items))


def _prototype_summary(data: dict) -> str:
    decision = next(
        (
            item
            for item in (data.get("decisions") or [])
            if isinstance(item, dict) and str(item.get("id") or "") == "D-PROTOTYPE"
        ),
        None,
    )
    if not decision or str(decision.get("status") or "") != "decided" or not decision.get("chosen"):
        return "待产品经理拍板是否制作及采用何种载体"
    chosen = str(decision.get("chosen"))
    option = next(
        (
            item
            for item in (decision.get("options") or [])
            if isinstance(item, dict) and str(item.get("id") or "") == chosen
        ),
        None,
    )
    label = _plain_text(option) or chosen
    return f"{label}（内部选项 `{chosen}`）"


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
    draft_gap = list(result.get("ready_gap") or [])
    review_items = _review_items(data)
    call_items = list(dict.fromkeys([humanize_finding(w) for w in needs_call] + review_items))
    status = str(data.get("status") or "")
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
        "这份报告给产品经理做需求评审：对照原始需求说明，看方案写了什么、猜了什么、哪里打架、可点页面稿有没有对不上。",
        "结构检查的结论在文末。**这份报告本身不是检查工具**；有必须改的问题，由助手改规格，你不用操作内部文件。",
        "",
        "## 这份规格是哪一份",
        "",
        f"- 规格名称：{title or '（未写中文名称）'}",
        f"- 规格编号：`{spec_id}`（内部对账用，不是界面上的编号）",
        f"- 当前进度：{status_label(str(data.get('status') or ''))}",
        f"- 说明书：`{_display_path(human_path, root)}`" if human_path else "- 说明书：还没有生成",
        f"- 内部规格文件：`{_display_path(spec_path, root)}`（给助手和检查工具用，开会时看说明书即可）",
        f"- 内容指纹：`{digest}`（用来确认开会时看的是同一版，不是给人读的）",
        f"- 可交互原型方案：{_prototype_summary(data)}",
        f"- 可点页面稿清单：`{_display_path(manifest_path, root)}`"
        if manifest_path
        else (
            "- 可点页面稿清单：不适用（已决定不制作原型）"
            if "`no_prototype`" in _prototype_summary(data)
            else "- 可点页面稿清单：还没有提供"
        ),
        "",
        "## 三类信号，不要混",
        "",
        "| 档 | 条数 | 意思 | 你要做什么 |",
        "|----|------|------|------------|",
        (
            f"| 必须改 | {len(must_fix)} |"
            " 有一条就不能当终稿交出。"
            " 检查工具里对应英文 FAIL。"
            " | 不用你改内部文件；让助手改到这一档为 0。 |"
        ),
        (
            f"| 需要你拍板 | {len(call_items)} |"
            " 原料冲突、未决事项、规格补的猜测，或可点页面稿还没核实。"
            " 不一定挡结构检查，但评审会上必须说清。"
            " | 认或不认。认了由助手记下是谁、哪天、为什么。 |"
        ),
        (
            f"| 终稿差距 | {len(draft_gap)} |"
            " 仅草稿有：现在若改成定稿，仍会触发的检查问题。"
            " | 由助手补齐；不要求你处理内部字段。 |"
        ),
        "",
        "DRAFT 表示可以带着问题评审，但不是终稿；只有标为 ready 且结构闭合时，结论才会显示 PASS。",
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
                f"| {_table_cell(humanize_warning_id(str(item.get('id') or '')))} | {_table_cell(item.get('by'))} | {_table_cell(item.get('date'))} | {_table_cell(item.get('reason'))} |"
            )
        lines.append("")
    lines += ["## 本次评审需要拍板或补充", ""]
    if call_items:
        for item in call_items:
            lines.append(f"- {item}")
    else:
        lines.append("没有已登记的业务未决、原料冲突或待确认假设。")
    if status != "ready":
        lines += ["", "## 变成终稿前还差什么", ""]
        if draft_gap:
            for item in draft_gap:
                lines.append(f"- 由助手补齐：{humanize_finding(item)}")
        else:
            lines.append("结构上没有新增差距；确认评审内容后，由助手把状态改为 ready 并复查。")
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
                f"| `{cid}` | {_table_cell(disposition_label(disp))} | {_table_cell(summary)} | {_table_cell(landing)} |"
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
    elif status == "draft":
        lines.append(
            "**结论：草稿结构可用。RESULT: DRAFT** 可以带着上面的待拍板事项去评审，"
            "但不能把它当成已经收口的终稿。"
        )
    elif status == "deprecated":
        lines.append("**结论：该规格已停用。RESULT: DEPRECATED** 仅供追溯，不应作为当前评审材料。")
    else:
        lines.append(
            "**结论：结构通过。RESULT: PASS** 规格在既定规则里自洽，可以拿去开会。"
            "这不表示业务已经拍板，也不表示页面已经验收。"
        )
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
    if data.get("status") != "ready":
        result["ready_gap"] = ready_gap(
            data,
            project,
            spec_path=spec_path,
            human_path=human,
            manifest_path=manifest,
        )
    result["review_state"] = "blocked" if result["fail"] else data.get("status")
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
    if result["fail"]:
        final = "FAIL"
    elif result.get("review_state") == "draft":
        final = "DRAFT"
    elif result.get("review_state") == "deprecated":
        final = "DEPRECATED"
    else:
        final = "PASS"
    print(f"RESULT: {final}")
    return 1 if result["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())
