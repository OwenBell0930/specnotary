#!/usr/bin/env python3
"""Spec Kit shared load / validate (FAIL|WARN|Pending) / render human spec."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

REQUIRED_TOP = ["spec_version", "id", "title", "status", "behaviors", "acceptance"]
VAGUE = ("体验好", "尽量快", "智能", "方便地", "good ux", "quickly", "尽快", "尽量")


def load_spec(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError(
                "PyYAML missing. Install: pip install pyyaml  OR use JSON  OR degraded Skill mode."
            )
        return yaml.safe_load(text)
    if suffix == ".json":
        return json.loads(text)
    raise RuntimeError(f"unsupported suffix {suffix} (use .yaml/.yml/.json)")


def _lang(node: Any, lang: str = "zh") -> str:
    if isinstance(node, dict):
        if lang in node and node[lang]:
            return str(node[lang])
        if "zh" in node:
            return str(node["zh"])
        if "en" in node:
            return str(node["en"])
        return str(node)
    return "" if node is None else str(node)


def _pending_ok(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    return all(item.get(k) not in (None, "") for k in ("id", "missing", "impact", "owner", "status"))


def validate(data: Any, project: dict | None = None) -> dict[str, list[str]]:
    """Return {fail, warn} lists. Pending rules apply when status=ready."""
    fail: list[str] = []
    warn: list[str] = []
    if not isinstance(data, dict):
        return {"fail": ["root must be an object"], "warn": []}

    for key in REQUIRED_TOP:
        if key not in data:
            fail.append(f"missing required field: {key}")

    behaviors = data.get("behaviors") or []
    acceptance = data.get("acceptance") or []
    if not isinstance(behaviors, list) or len(behaviors) < 1:
        fail.append("behaviors must have at least 1 item")
    if not isinstance(acceptance, list) or len(acceptance) < 1:
        fail.append("acceptance must have at least 1 item")

    # AC ids unique
    ac_ids = []
    for a in acceptance if isinstance(acceptance, list) else []:
        aid = (a or {}).get("id")
        if aid:
            if aid in ac_ids:
                fail.append(f"duplicate acceptance id: {aid}")
            ac_ids.append(aid)

    status = data.get("status")
    pending = data.get("pending") or []
    open_qs = data.get("open_questions") or []

    if status == "ready":
        if open_qs:
            fail.append("status=ready but open_questions is not empty — move to pending with owner or resolve")
        if not data.get("actors"):
            fail.append("status=ready requires actors")
        if not data.get("defaults"):
            fail.append("status=ready requires defaults")
        if not data.get("ui"):
            fail.append("status=ready requires ui (entry, wireframe or controls)")
        if not data.get("states"):
            fail.append("status=ready requires states (lifecycle / allowed actions)")
        for b in behaviors if isinstance(behaviors, list) else []:
            then = (_lang((b or {}).get("then"), "zh") + " " + _lang((b or {}).get("then"), "en")).lower()
            if any(v in then for v in VAGUE):
                fail.append(f"behavior {(b or {}).get('id')}: then-clause too vague for ready")
        for a in acceptance if isinstance(acceptance, list) else []:
            text = (_lang(a, "zh") + " " + _lang(a, "en")).lower()
            if any(v in text for v in ("体验好", "功能正常", "good ux", "as fast")):
                fail.append(f"acceptance {(a or {}).get('id')}: not observable")
        for p in pending if isinstance(pending, list) else []:
            if not _pending_ok(p):
                fail.append(
                    "pending item missing four fields: id, missing, impact, owner, status"
                )
            elif str((p or {}).get("status", "")).lower() in {"open", "待确认", "tbd"}:
                fail.append(
                    f"pending {(p or {}).get('id')} still open — cannot mark status=ready"
                )

    # WARN tier (always useful)
    if not data.get("ui"):
        warn.append("ui block missing — human spec will lack wireframe/controls")
    if not data.get("states"):
        warn.append("states block missing — lifecycle/actions unclear")
    if not data.get("empty_states") and not (data.get("ui") or {}).get("empty_states"):
        warn.append("empty_states missing — empty/error copy may be invented downstream")
    if isinstance(behaviors, list):
        for b in behaviors:
            if not (b or {}).get("step_id"):
                warn.append(f"behavior {(b or {}).get('id')}: prefer step_id for numbered main path")
    if pending and status != "ready":
        for p in pending:
            if not _pending_ok(p):
                warn.append("pending item should use four fields: id/missing/impact/owner/status")

    weight = (project or {}).get("object_ai_weight", "medium")
    obj = data.get("object_ai") or {}
    if weight == "high":
        if not obj or not obj.get("enabled"):
            fail.append("object_ai_weight=high requires object_ai.enabled=true")
        else:
            for key in ("tools_boundary", "failure_fallback", "human_takeover_when"):
                if not obj.get(key):
                    fail.append(f"object_ai_weight=high requires object_ai.{key}")

    return {"fail": fail, "warn": warn}


def render_human(data: dict, source: str, gate_mode: str = "hard") -> str:
    """Render 可开发的需求规格说明书 (human view) from machine source."""
    title_zh = _lang(data.get("title"), "zh")
    title_en = _lang(data.get("title"), "en")
    ui = data.get("ui") or {}
    states = data.get("states") or {}
    lines: list[str] = [
        f"<!-- generated_from: {source} -->",
        f"<!-- gate_mode: {gate_mode} -->",
        "<!-- 机读为主源；禁止长期只改本文件 -->",
        "",
        f"# {title_zh}",
        "",
        f"> **文档类型**：可开发的需求规格说明书（人读视图）  ",
        f"> **规格 ID**：`{data.get('id')}` · **状态**：`{data.get('status')}` · **版本**：`{data.get('spec_version')}`",
        "",
    ]
    if title_en and title_en != title_zh:
        lines += [f"**EN title:** {title_en}", ""]

    # 1 范围
    lines += ["## 1. 范围", "", "### 1.1 本期做", ""]
    for item in data.get("in_scope") or []:
        lines.append(f"- {_lang(item, 'zh')}")
    lines += ["", "### 1.2 本期不做（白名单外，不展开）", ""]
    for item in data.get("out_of_scope") or []:
        lines.append(f"- {_lang(item, 'zh')}")
    if data.get("baseline"):
        lines += ["", f"**对照基线：** {_lang(data.get('baseline'), 'zh')}", ""]

    # 2 角色权限
    lines += ["## 2. 角色与权限", "", "| 角色 | 说明 | 可执行动作 |", "|------|------|------------|"]
    perm_map = {(p or {}).get("actor"): (p or {}).get("can") or [] for p in (data.get("permissions") or [])}
    for a in data.get("actors") or []:
        aid = (a or {}).get("id")
        cans = ", ".join(perm_map.get(aid) or [])
        lines.append(f"| `{aid}` | {_lang(a, 'zh')} | {cans or '—'} |")
    lines.append("")

    # 3 状态
    lines += ["## 3. 订单状态与可取消性", ""]
    if states.get("lifecycle"):
        lines.append("**生命周期（编号供流程对照）：**")
        for i, s in enumerate(states.get("lifecycle") or [], 1):
            lines.append(f"{i}. `{s}`")
        lines.append("")
    lines += [
        "| 状态 | 买家自助取消 | 说明 |",
        "|------|--------------|------|",
    ]
    for row in states.get("cancel_matrix") or []:
        lines.append(
            f"| `{(row or {}).get('state')}` | {(row or {}).get('buyer_self_cancel')} | {_lang(row, 'zh')} |"
        )
    if not states.get("cancel_matrix"):
        lines.append("| （机读未提供 cancel_matrix） | — | — |")
    lines.append("")

    # 4 UI
    lines += ["## 4. 页面与交互", ""]
    if ui.get("entry"):
        lines.append(f"**入口：** {_lang(ui.get('entry'), 'zh')}")
        lines.append("")
    if ui.get("wireframe"):
        lines.append("### 4.1 线框")
        lines.append("")
        lines.append("```text")
        lines.append(str(ui.get("wireframe")).rstrip())
        lines.append("```")
        lines.append("")
    controls = ui.get("controls") or []
    if controls:
        lines.append("### 4.2 控件规格")
        lines.append("")
        lines.append("| 控件 | 文案/占位 | 显示条件 | 交互 | 失败反馈 |")
        lines.append("|------|-----------|----------|------|----------|")
        for c in controls:
            lines.append(
                "| {name} | {label} | {when} | {action} | {fail} |".format(
                    name=(c or {}).get("id", ""),
                    label=_lang(c, "zh"),
                    when=_lang((c or {}).get("visible_when"), "zh") or "—",
                    action=_lang((c or {}).get("action"), "zh") or "—",
                    fail=_lang((c or {}).get("fail_feedback"), "zh") or "—",
                )
            )
        lines.append("")

    # 5 主路径
    lines += ["## 5. 主路径（编号）", ""]
    for b in data.get("behaviors") or []:
        step = (b or {}).get("step_id") or (b or {}).get("id")
        lines.append(f"### 步骤 {step} · {_lang((b or {}).get('name'), 'zh')}")
        lines.append("")
        lines.append(f"- **Given：** {_lang((b or {}).get('given'), 'zh')}")
        lines.append(f"- **When：** {_lang((b or {}).get('when'), 'zh')}")
        lines.append(f"- **Then：** {_lang((b or {}).get('then'), 'zh')}")
        if (b or {}).get("side_effects"):
            lines.append("- **连带结果：**")
            for s in (b or {}).get("side_effects") or []:
                lines.append(f"  - {_lang(s, 'zh')}")
        lines.append("")

    # 6 默认与空态
    lines += ["## 6. 默认值与提示文案", "", "### 6.1 默认值", ""]
    defaults = data.get("defaults") or {}
    if defaults:
        lines.append("| 项 | 值 |")
        lines.append("|----|----|")
        for k, v in defaults.items():
            lines.append(f"| `{k}` | `{v}` |")
    else:
        lines.append("（无）")
    lines += ["", "### 6.2 空态 / 拦截文案（须与界面一致）", ""]
    empty = data.get("empty_states") or ui.get("empty_states") or {}
    if empty:
        lines.append("| 场景 | 文案 |")
        lines.append("|------|------|")
        for k, v in empty.items():
            lines.append(f"| `{k}` | {_lang(v, 'zh')} |")
    else:
        lines.append("（无）")
    lines.append("")

    # 7 AC
    lines += ["## 7. 验收标准（AC）", ""]
    for a in data.get("acceptance") or []:
        lines.append(
            f"- **{(a or {}).get('id')}**（行为 `{(a or {}).get('behavior')}`）：{_lang(a, 'zh')}"
        )
    lines.append("")

    # 8 Pending
    lines += ["## 8. 信息待闭合项（Pending）", ""]
    pending = data.get("pending") or []
    if not pending:
        lines.append("无。")
    else:
        lines.append("| ID | 缺失信息 | 影响范围 | 责任人 | 状态 |")
        lines.append("|----|----------|----------|--------|------|")
        for p in pending:
            lines.append(
                f"| {(p or {}).get('id')} | {(p or {}).get('missing')} | {(p or {}).get('impact')} | {(p or {}).get('owner')} | {(p or {}).get('status')} |"
            )
    lines.append("")

    # 9 object AI
    obj = data.get("object_ai") or {}
    lines += ["## 9. 对象 AI", "", f"- enabled: `{obj.get('enabled', False)}`"]
    if obj.get("enabled"):
        lines.append(f"- 失败兜底: {_lang(obj.get('failure_fallback'), 'zh')}")
        lines.append("- 工具边界:")
        for t in obj.get("tools_boundary") or []:
            lines.append(f"  - {_lang(t, 'zh')}")
        lines.append("- 人工接管:")
        for t in obj.get("human_takeover_when") or []:
            lines.append(f"  - {_lang(t, 'zh')}")
    lines.append("")
    return "\n".join(lines)


def load_project(root: Path) -> dict:
    for name in ("project.yaml", "project.example.yaml"):
        p = root / name
        if p.exists() and yaml is not None:
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            if isinstance(data, dict):
                return data
    return {}
