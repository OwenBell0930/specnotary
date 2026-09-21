#!/usr/bin/env python3
"""Human review view — derived from the machine spec, never authored here.

Rule pipeline stays in libspec.py; disk I/O stays in spec_io.py. This module
only lays out fields the machine source already holds.
"""
from __future__ import annotations

import re

from .pm_view import disposition_label, format_landing, status_label
from .spec_io import human_body_hash, spec_hash, split_human_markdown

RENDERER_VERSION = "14"


def _rules():
    """Late import: libspec loads this module while defining the gate."""
    from . import libspec as L
    return L

def _allowed_label(row: dict, lang: str = "zh") -> str:
    if "allowed" in row:
        val = row.get("allowed")
        if isinstance(val, bool):
            if lang == "en":
                return "allowed" if val else "denied"
            return "允许" if val else "禁止"
        return str(val)
    if "buyer_self_cancel" in row:  # legacy cancel_matrix
        return str(row.get("buyer_self_cancel"))
    return "—"


# zh literals are canonical (zh output stays byte-identical); en is a lookup layer.
_EN = {
    "目录": "Table of Contents",
    "概览": "Overview",
    "范围": "Scope",
    "产品与信息架构": "Product & Information Architecture",
    "页面与消费者视图": "Surfaces & Consumer Views",
    "功能说明": "Features",
    "职责边界": "Responsibilities",
    "数据契约": "Data Contracts",
    "对象契约": "Object Contracts",
    "角色与权限": "Roles & Permissions",
    "权限规则矩阵": "Permission Rule Matrix",
    "状态与允许动作": "States & Allowed Actions",
    "页面与交互": "Pages & Interactions",
    "主路径（编号）": "Main Path (numbered)",
    "默认值与提示文案": "Defaults & Copy",
    "错误码": "Error Codes",
    "验收标准（AC）": "Acceptance Criteria (AC)",
    "信息待闭合项（Pending）": "Pending Items",
    "决策记录": "Decision Log",
    "对象 AI": "Object AI",
    "原料落在规格里的情况": "Where source items landed",
    "> **文档类型**：评审就绪的标准需求规格说明书（人读评审稿）<br>": "> **Document type**: review-ready requirements specification (human review view)<br>",
    "> **规格编号**：`{sid}` · **进度**：{status} · **版本**：`{ver}`  ": "> **Spec id**: `{sid}` · **Progress**: {status} · **Version**: `{ver}`  ",
    "> **机读哈希**：`{digest}…`<br>": "> **Machine hash**: `{digest}…`<br>",
    "> **怎么读：** 先看「功能说明」判断本期方案；「主路径」用 Given/When/Then 逐条核对结果；「状态与允许动作」说明按钮何时可点；「页面与交互」说明按钮文案和失败提示。": "> **How to read:** Features frame the proposal; Main Path reviews observable outcomes in Given/When/Then form; States explain when controls are available; Pages define labels and failure copy.",
    "**设计原则：**": "**Design principles:**",
    "**环境与约束：**": "**Environment & constraints:**",
    "**本期做：**": "**In scope:**",
    "**本期不做（白名单外，不展开）：**": "**Out of scope (whitelist only, not elaborated):**",
    "**对照基线：** {baseline}": "**Baseline:** {baseline}",
    "本章按模块划分方案边界。每个模块先写中文名称；括号里的机读 ID 给助手和检查工具对账，不是菜单原文。「负责」是该模块包含的界面或能力，「不负责」是明确不做的事。": "This chapter splits the proposal by module. The machine ID is for the assistant and deterministic checks, not a menu label. Owns = what the module includes; does not own = explicitly excluded.",
    "这是**{kind}**（机读 ID：`{role}`）。": "This is a **{kind}** (machine ID: `{role}`).",
    "页面": "page",
    "后台引擎": "backend engine",
    "服务": "service",
    "模块": "module",
    "本章列出本期要做的功能。每条的验收写法（Given/When/Then）见后面「主路径」同编号步骤。": "This chapter lists features in this slice. The Given/When/Then form of each item is in Main Path under the same number.",
    "**要做到：** {v}": "**Done when:** {v}",
    "**对应：** 步骤 {step} · `{bid}`": "**Maps to:** step {step} · `{bid}`",
    "本章回答两件事：①现在处于哪个状态（哪个页面/哪条任务）；②该状态下哪些动作允许、哪些禁止。下图按对象分组，方框之间没有箭头——允许的转移只看下面的表，不从图上猜。": "This chapter answers two questions: (1) which state the page or task is in; (2) which actions are allowed in that state. Boxes are grouped by subject and are not connected — do not infer flow from the diagram; the table is the source of truth.",
    "| 负责 | 不负责 |": "| Owns | Does not own |",
    "共 {n} 个数据实体。每个对象一张字段表，用于评审时对齐业务含义、输入输出和关键规则；不在这里规定开发语言或测试方案。": "{n} data entities. Each table aligns business meaning, inputs, outputs, and key rules during review; it does not prescribe implementation language or a test plan.",
    "| 字段 | 中文 | 类型 | 说明 |": "| Field | Label | Type | Notes |",
    "**规则：**": "**Rules:**",
    "下面是**登录身份**（谁在操作系统），不是页面名称。可执行动作是业务动作（和下一章「动作」列对应），不是接口路径，也不是数据库字段。": "These are **login identities** (who operates the system), not page names. Allowed actions are business actions (same column as the next chapter), not API paths or database fields.",
    "| 身份 | 机读 ID | 可执行动作 |": "| Identity | Machine ID | Allowed actions |",
    "共 {s} 个状态、{a} 类动作，其中明确禁止 {d} 项。前端按钮显隐与置灰以下表为唯一准据。": "{s} states × {a} action kinds, {d} explicitly denied. The table below is the single source of truth for enabling/hiding controls.",
    "已声明的状态集合（不表示转移；允许的转移以下表为准）：": "Declared state set (no transitions implied; allowed transitions are governed by the table below):",
    "**按对象列出的状态（编号只为对照，不是流转顺序）：**": "**States by subject (numbers are for reference, not a flow order):**",
    "### {subject}": "### {subject}",
    "| 状态 | 动作 | 是否允许 | 说明 |": "| State | Action | Allowed | Notes |",
    "共 {n} 步。这是「功能说明」的可观察结果写法，供评审逐条核对；编号不是用户操作顺序。": "{n} steps. These observable outcomes let reviewers inspect each feature; numbers are not a user sequence.",
    "| （机读未提供 action_matrix） | — | — | — |": "| (machine source has no action_matrix) | — | — | — |",
    "**入口：** {entry}": "**Entry:** {entry}",
    "### 线框": "### Wireframe",
    "### 控件规格": "### Control Spec",
    "共 {n} 个控件，其中 {f} 个定义了失败反馈文案。": "{n} controls, {f} of them with explicit failure-feedback copy.",
    "| 按钮文案 | 机读 ID | 显示条件 | 交互 | 失败反馈 |": "| Label | Machine ID | Visible when | Interaction | Failure feedback |",
    "本章是页面上用户能点到的按钮和输入框。按钮文案是界面上的字；机读 ID 给规格与原型对账。": "This chapter lists on-screen buttons and fields. Labels are user-visible copy; machine IDs reconcile the spec and prototype.",
    "共 {n} 步；每步用 Given/When/Then 说明前提、动作和可见结果，供需求评审逐条判断。步骤为编号清单，非执行顺序。": "{n} steps; each Given/When/Then states the precondition, action, and visible outcome for requirements review. Steps are numbered, not sequential.",
    "### 步骤 {step} · {name}": "### Step {step} · {name}",
    "- **Given：** {v}": "- **Given:** {v}",
    "- **When：** {v}": "- **When:** {v}",
    "- **Then：** {v}": "- **Then:** {v}",
    "- **连带结果：**": "- **Side effects:**",
    "### 默认值": "### Defaults",
    "| 项 | 值 |": "| Key | Value |",
    "（无）": "(none)",
    "### 空态 / 拦截文案（须与界面一致）": "### Empty-state / Blocking Copy (must match UI verbatim)",
    "| 场景 | 文案 |": "| Scenario | Copy |",
    "评审时用一张表统一错误含义、触发条件、是否可重试和用户看到的文案。": "Use one review table to align error meaning, trigger, retry policy, and user-visible copy.",
    "| 错误码 | 含义 | 触发场景 | 可重试 | 用户文案 |": "| Code | Meaning | Trigger | Retryable | User copy |",
    "是": "yes",
    "否": "no",
    "共 {n} 条；逐条可执行，已知空话／占位词会被门禁否决。": "{n} criteria; each one executable — known empty-talk / placeholder phrasing is rejected by the gate.",
    "- **{aid}**（行为 `{bid}`）：{text}": "- **{aid}** (behavior `{bid}`): {text}",
    "无。": "None.",
    "| ID | 缺失信息 | 影响范围 | 责任人 | 状态 |": "| ID | Missing | Impact | Owner | Status |",
    "| ID | 类型 | 问题 / 缺失事实 | 影响范围 | 选项与建议 | 责任人 | 状态 |": "| ID | Type | Question / missing fact | Impact | Options & recommendation | Owner | Status |",
    "事实缺口": "fact gap",
    "产品取舍": "product decision",
    "共 {n} 项，已拍板 {d} 项，待定 {u} 项。「为什么是这样」的存档，新人不必考古聊天记录。": "{n} decisions — {d} settled, {u} open. The archive of why things are this way; no chat-log archaeology needed.",
    "| ID | 问题 | 选定 | 日期 | 备注 |": "| ID | Question | Chosen | Date | Note |",
    "| 页面 / 入口 | 类型 | 回答的用户问题 | 读取 | 修改 | 跳转 | 权威状态来源 |": "| Surface / entry | Kind | User question | Reads | Writes | Links | Authoritative state source |",
    "| 规则 | 角色 | 动作 | 对象 | 状态 | 结果 | 生效面 | 执行位置 |": "| Rule | Actor | Action | Object | States | Effect | Surfaces | Enforcement |",
    "**目标：** {v}": "**Goal:** {v}",
    "**入口：** `{v}`": "**Entry:** `{v}`",
    "**参与角色：** {v}": "**Actors:** {v}",
    "**读取 / 修改：** {reads} / {writes}": "**Reads / writes:** {reads} / {writes}",
    "**权限规则：** {v}": "**Permission rules:** {v}",
    "**幂等口径：** {v}": "**Idempotency:** {v}",
    "**恢复方式：** {v}": "**Recovery:** {v}",
    "**异常与恢复：**": "**Exceptions & recovery:**",
    "| 异常 | 触发条件 | 用户看到 | 已保存事实 | 重试 / 恢复 |": "| Exception | Trigger | Visible result | Preserved facts | Retry / recovery |",
    "**对象类型：** `{kind}`  ": "**Object kind:** `{kind}`  ",
    "**职责与归属：** {purpose}；{ownership}  ": "**Purpose & ownership:** {purpose}; {ownership}  ",
    "**唯一性：** {identity}  ": "**Identity:** {identity}  ",
    "**历史与当前：** {boundary}": "**History vs current:** {boundary}",
    "**关系：**": "**Relationships:**",
    "**待定**": "**undecided**",
    "- 失败兜底: {v}": "- Failure fallback: {v}",
    "- 工具边界:": "- Tool boundary:",
    "- 人工接管:": "- Human takeover:",
    "下面逐条对照原始需求说明。处理结果用中文；括号里的编号给助手和检查工具对账。已写入规格 {c} 条 · 原文没写、规格补了猜测 {a} 条 · 本期不做 {o} 条 · 其他 {r} 条。完整性需要开会时抽查。": "Each row is a source item. Handling is in plain language; ids are for the assistant and deterministic checks. Written into the spec: {c}. Guess filled in: {a}. Out of this slice: {o}. Other: {r}. Spot-check completeness in review.",
    "| 原料条目编号 | 处理结果 | 这条在说什么 | 落到说明书的哪一段 |": "| Source item id | Handling | What this says | Where it landed |",
    "**EN title:** {t}": "**Title (zh):** {t}",
    "<!-- 以机读 YAML 为唯一准据；禁止长期只改本文件 -->": "<!-- Machine YAML is the single source of truth; do not hand-edit this file long-term -->",
}


def _tt(lang: str):
    if lang == "en":
        return lambda s: _EN.get(s, s)
    return lambda s: s


def _anchor(title: str) -> str:
    """Markdown heading anchor (GitHub-style: lowercase, punctuation dropped, CJK kept)."""
    t = re.sub(r"[^\w\- ]", "", title.strip().lower(), flags=re.UNICODE)
    return t.replace(" ", "-")


def _mermaid_label(text: str) -> str:
    return str(text).replace('"', "'").replace("\n", " ").strip()


_ROLE_KIND = {
    "page": "页面",
    "screen": "页面",
    "engine": "后台引擎",
    "service": "服务",
    "module": "模块",
}


def _label_node(states: dict, sid: str) -> tuple[str, str]:
    labels = states.get("labels") if isinstance(states.get("labels"), dict) else {}
    node = labels.get(sid)
    if isinstance(node, dict):
        return str(node.get("zh") or "").strip(), str(node.get("of") or node.get("subject") or "").strip()
    if isinstance(node, str) and node.strip():
        return node.strip(), ""
    return "", ""


def _action_label(states: dict, action: str) -> str:
    labels = states.get("action_labels") if isinstance(states.get("action_labels"), dict) else {}
    node = labels.get(action)
    if isinstance(node, dict):
        return str(node.get("zh") or "").strip()
    if isinstance(node, str):
        return node.strip()
    return ""


def _fmt_action(states: dict, action: str) -> str:
    act = str(action or "")
    zh = _action_label(states, act)
    return f"{zh}（`{act}`）" if zh and act else (f"`{act}`" if act else "—")


def _fmt_labelled(zh: str, key: str) -> str:
    return f"{zh}（`{key}`）" if zh and key else (f"`{key}`" if key else "—")


def _map_zh(node, lang: str) -> str:
    L = _rules()
    return L._lang(node, lang).strip()


# Suffix aliases shorter than this are too generic (`ui`, `id`, `idle`).
_MIN_VALUE_ALIAS = 5
_SKIP_ACTOR_IDS = frozenset(
    {"and", "the", "for", "not", "any", "all", "yes", "no", "or", "to", "of"}
)


def _human_id_pairs(data: dict, lang: str) -> list[tuple[str, str]]:
    """Machine id → human phrase. Longer keys win at replace time.

    Families (all of them — leaving one out is how `terminated` leaked as
    raw English after `file_too_large` was already expanded):
    - empty_states → 「界面原文」
    - lifecycle / action / actor / control / value_labels → 中文（`id`）
    - lifecycle `prefix_value` also aliases `value` when value is long enough
      (`import_terminated` → `terminated` → 已终止)
    """
    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add(key: str, repl: str) -> None:
        k = str(key or "")
        if not k or not repl or k in seen:
            return
        seen.add(k)
        pairs.append((k, repl))

    empty = data.get("empty_states") or {}
    if isinstance(empty, dict):
        for key, val in empty.items():
            zh = _map_zh(val, lang)
            if zh:
                add(str(key), f"「{zh}」")

    states = data.get("states") if isinstance(data.get("states"), dict) else {}
    for sid in states.get("lifecycle") or []:
        sid_s = str(sid)
        zh, _of = _label_node(states, sid_s)
        if zh:
            add(sid_s, _fmt_labelled(zh, sid_s))
    action_labels = states.get("action_labels") if isinstance(states.get("action_labels"), dict) else {}
    for action, node in action_labels.items():
        zh = _map_zh(node, lang) if not isinstance(node, str) else node.strip()
        if not zh and isinstance(node, dict):
            zh = str(node.get("zh") or "").strip()
        if zh:
            add(str(action), _fmt_labelled(zh, str(action)))
    value_labels = states.get("value_labels") if isinstance(states.get("value_labels"), dict) else {}
    for vid, node in value_labels.items():
        zh = _map_zh(node, lang) if not isinstance(node, str) else node.strip()
        if not zh and isinstance(node, dict):
            zh = str(node.get("zh") or "").strip()
        if zh:
            add(str(vid), _fmt_labelled(zh, str(vid)))
    for sid in states.get("lifecycle") or []:
        sid_s = str(sid)
        zh, _of = _label_node(states, sid_s)
        if not zh or "_" not in sid_s:
            continue
        alias = sid_s.split("_", 1)[1]
        if len(alias) < _MIN_VALUE_ALIAS or alias in seen:
            continue
        add(alias, _fmt_labelled(zh, alias))

    ui = data.get("ui") if isinstance(data.get("ui"), dict) else {}
    for ctrl in ui.get("controls") or []:
        if not isinstance(ctrl, dict) or not ctrl.get("id"):
            continue
        cid = str(ctrl["id"])
        zh = _map_zh(ctrl, lang)
        if zh and ("_" in cid or cid.startswith(("btn", "tbl", "inp"))):
            add(cid, _fmt_labelled(zh, cid))

    for actor in data.get("actors") or []:
        if not isinstance(actor, dict) or not actor.get("id"):
            continue
        aid = str(actor["id"])
        if aid.lower() in _SKIP_ACTOR_IDS or len(aid) < 3:
            continue
        zh = _map_zh(actor, lang)
        if zh:
            add(aid, _fmt_labelled(zh, aid))

    pairs.sort(key=lambda x: len(x[0]), reverse=True)
    return pairs


def _expand_machine_ids(text: str, data: dict, lang: str) -> str:
    """Show Chinese in the human view; keep machine keys out of prose."""
    if not text:
        return text
    pairs = _human_id_pairs(data, lang)
    if not pairs:
        return text
    out = text
    for key, repl in pairs:
        out = re.sub(rf"(?<![「`])\b{re.escape(key)}\b(?![」`])", repl, out)
    return out


def _fmt_default_value(value, data: dict, lang: str) -> str:
    if isinstance(value, list):
        if not value:
            return "（无）"
        return "、".join(_fmt_default_value(v, data, lang) for v in value)
    if isinstance(value, bool):
        return "是" if value else "否" if lang != "en" else ("yes" if value else "no")
    raw = str(value)
    expanded = _expand_machine_ids(raw, data, lang)
    if expanded != raw:
        return expanded
    return f"`{raw}`"


# Back-compat alias used by older call sites / tests.
_expand_empty_copy = _expand_machine_ids


def mermaid_lifecycle(states: dict) -> str | None:
    """Render the declared states as an unconnected set, never as a chain.

    v5: arrows previously chained lifecycle entries in declaration order,
    which asserted transitions the machine source never declared — the
    order-cancel sample rendered `completed --> cancelled`, which is simply
    wrong. Transition truth lives in action_matrix; the diagram only shows
    which states exist. v8 groups boxes by `labels.of` when present.
    """
    chain = [str(s) for s in (states.get("lifecycle") or []) if s]
    if len(chain) < 2:
        return None
    groups: list[tuple[str, list[str]]] = []
    index: dict[str, int] = {}
    for sid in chain:
        _zh, of_ = _label_node(states, sid)
        key = of_ or "已声明的状态"
        if key not in index:
            index[key] = len(groups)
            groups.append((key, []))
        groups[index[key]][1].append(sid)
    lines = ["flowchart TB"]
    ni = 0
    for gi, (title, ids) in enumerate(groups):
        lines.append(f'  subgraph G{gi}["{_mermaid_label(title)}"]')
        for sid in ids:
            zh, _of = _label_node(states, sid)
            display = f"{zh}<br/>{sid}" if zh else sid
            lines.append(f'    S{ni}["{_mermaid_label(display)}"]')
            ni += 1
        lines.append("  end")
    return "\n".join(lines)


# NOTE: an auto-generated "main path" chain diagram was removed in renderer v4.
# Behaviors are frequently alternative branches, not a sequence; chaining them
# asserted flow relations the machine source never declared. A diagram that
# states false relations is worse than no diagram.


def render_human(data: dict, source: str, gate_mode: str = "hard", lang: str = "zh") -> str:
    """Render the review-ready requirements specification from machine source.

    Reading arc (v10): orient first — overview, scope, features,
    architecture, responsibilities, data contracts — then zoom into rules,
    interactions and evidence. Chrome comments trail the body so Markdown
    preview is not blank. Sections render only when the machine source holds
    them. Nothing here is authored at render time.
    """
    L = _rules()
    t = _tt(lang)
    data = L._sanitize_shapes(dict(data), [])
    _lang = L._lang
    action_matrix_rows = L.action_matrix_rows
    claim_summary = L.claim_summary

    def prose(node) -> str:
        return _expand_machine_ids(_lang(node, lang), data, lang)
    title_zh = _lang(data.get("title"), "zh")
    title_en = _lang(data.get("title"), "en")
    title_main = title_en if lang == "en" and title_en else title_zh
    title_alt = title_zh if lang == "en" else title_en
    ui = data.get("ui") if isinstance(data.get("ui"), dict) else {}
    states = data.get("states") if isinstance(data.get("states"), dict) else {}
    behaviors = [b for b in (data.get("behaviors") or []) if isinstance(b, dict)]
    acceptance = [a for a in (data.get("acceptance") or []) if isinstance(a, dict)]
    digest = spec_hash(data)
    sections: list[tuple[str, list[str]]] = []

    # ---- 概览（作者在机读里写的全局视角；渲染器只摆放） ----
    overview = data.get("overview") or {}
    if overview:
        sec: list[str] = []
        summary = prose(overview.get("summary"))
        if summary:
            sec += [summary, ""]
        principles = overview.get("design_principles") or []
        if principles:
            sec += [t("**设计原则：**"), ""]
            for i, p in enumerate(principles, 1):
                sec.append(f"{i}. {prose(p)}")
            sec.append("")
        constraints = overview.get("environment_constraints") or []
        if constraints:
            sec += [t("**环境与约束：**"), ""]
            for c in constraints:
                sec.append(f"- {prose(c)}")
            sec.append("")
        sections.append(("概览", sec))

    # ---- 范围 ----
    sec = [t("**本期做：**"), ""]
    for item in data.get("in_scope") or []:
        sec.append(f"- {prose(item)}")
    sec += ["", t("**本期不做（白名单外，不展开）：**"), ""]
    for item in data.get("out_of_scope") or []:
        sec.append(f"- {prose(item)}")
    if data.get("baseline"):
        sec += ["", t("**对照基线：** {baseline}").format(baseline=prose(data.get("baseline")))]
    sec.append("")
    sections.append(("范围", sec))

    # ---- 功能说明（behavior 名称 + 要做到什么；验收句子在主路径） ----
    if behaviors:
        sec = [t("本章列出本期要做的功能。每条的验收写法（Given/When/Then）见后面「主路径」同编号步骤。"), ""]
        for i, b in enumerate(behaviors, 1):
            step = b.get("step_id") or i
            name = _lang(b.get("name"), lang) or str(b.get("id") or "")
            then = prose(b.get("then"))
            sec += [f"### {i}. {name}", ""]
            if then:
                sec.append(t("**要做到：** {v}").format(v=then))
            sec.append(t("**对应：** 步骤 {step} · `{bid}`").format(step=step, bid=b.get("id") or "—"))
            sec.append("")
        sections.append(("功能说明", sec))

    # ---- 产品与信息架构（机读持有 mermaid 源码） ----
    arch = data.get("architecture") or {}
    if arch.get("mermaid"):
        sec = []
        note = prose(arch.get("note"))
        if note:
            sec += [note, ""]
        sec += ["```mermaid", str(arch["mermaid"]).rstrip(), "```", ""]
        sections.append(("产品与信息架构", sec))

    surfaces = [s for s in (arch.get("surfaces") or []) if isinstance(s, dict)]
    if surfaces:
        sec = [
            t("| 页面 / 入口 | 类型 | 回答的用户问题 | 读取 | 修改 | 跳转 | 权威状态来源 |"),
            "|-------------|------|------------------|------|------|------|--------------|",
        ]
        for s in surfaces:
            label = _lang(s, lang) or str(s.get("id") or "—")
            sid = str(s.get("id") or "")
            if sid:
                label = f"{label} (`{sid}`)"
            sec.append(
                "| {label} | {kind} | {question} | {reads} | {writes} | {links} | {source} |".format(
                    label=label,
                    kind=s.get("kind") or "—",
                    question=prose(s.get("question")) or "—",
                    reads="、".join(f"`{v}`" for v in (s.get("reads") or [])) or "—",
                    writes="、".join(f"`{v}`" for v in (s.get("writes") or [])) or "—",
                    links="、".join(f"`{v}`" for v in (s.get("links_to") or [])) or "—",
                    source=prose(s.get("state_source")) or "—",
                )
            )
        sec.append("")
        sections.append(("页面与消费者视图", sec))

    # ---- 职责边界 ----
    resp = [r for r in (data.get("responsibilities") or []) if isinstance(r, dict)]
    if resp:
        sec = [t("本章按模块划分方案边界。每个模块先写中文名称；括号里的机读 ID 给助手和检查工具对账，不是菜单原文。「负责」是该模块包含的界面或能力，「不负责」是明确不做的事。"), ""]
        for r in resp:
            zh = _lang(r, lang)
            role = str(r.get("role") or "")
            kind_raw = str(r.get("kind") or "").strip().lower()
            kind = t(_ROLE_KIND.get(kind_raw, "模块"))
            heading = zh or role
            sec.append(f"### {heading}")
            sec.append("")
            sec.append(t("这是**{kind}**（机读 ID：`{role}`）。").format(kind=kind, role=role))
            sec.append("")
            owns = r.get("owns") or []
            nots = r.get("not_owns") or []
            sec += [t("| 负责 | 不负责 |"), "|------|--------|"]
            for i in range(max(len(owns), len(nots), 1)):
                left = prose(owns[i]) if i < len(owns) else ""
                right = prose(nots[i]) if i < len(nots) else ""
                sec.append(f"| {left or '—'} | {right or '—'} |")
            sec.append("")
        sections.append(("职责边界", sec))

    # ---- 数据契约 ----
    contracts = [c for c in (data.get("data_contracts") or []) if isinstance(c, dict)]
    if contracts:
        sec = [t("共 {n} 个数据实体。每个对象一张字段表，用于评审时对齐业务含义、输入输出和关键规则；不在这里规定开发语言或测试方案。").format(n=len(contracts)), ""]
        for dc in contracts:
            zh = _lang(dc, lang)
            sec.append(f"### {dc.get('id')}" + (f" · {zh}" if zh else ""))
            sec.append("")
            if any(dc.get(k) for k in ("purpose", "ownership", "identity", "kind", "history_current_boundary")):
                sec.append(t("**对象类型：** `{kind}`  ").format(kind=dc.get("kind") or "—"))
                sec.append(
                    t("**职责与归属：** {purpose}；{ownership}  ").format(
                        purpose=prose(dc.get("purpose")) or "—",
                        ownership=prose(dc.get("ownership")) or "—",
                    )
                )
                sec.append(t("**唯一性：** {identity}  ").format(identity=prose(dc.get("identity")) or "—"))
                sec.append(
                    t("**历史与当前：** {boundary}").format(
                        boundary=prose(dc.get("history_current_boundary")) or "—"
                    )
                )
                sec.append("")
            relationships = [r for r in (dc.get("relationships") or []) if isinstance(r, dict)]
            if relationships:
                sec.append(t("**关系：**"))
                sec.append("")
                for relation in relationships:
                    sec.append(
                        f"- `{relation.get('target')}` · `{relation.get('cardinality')}`：{relation.get('zh') or '—'}"
                    )
                sec.append("")
            fields = [f for f in (dc.get("fields") or []) if isinstance(f, dict)]
            if fields:
                sec += [t("| 字段 | 中文 | 类型 | 说明 |"), "|------|------|------|------|"]
                for f in fields:
                    sec.append(
                        f"| `{f.get('name')}` | {f.get('zh') or '—'} | `{f.get('type') or '—'}` | {prose(f.get('desc')) or '—'} |"
                    )
                sec.append("")
            if dc.get("example_json"):
                sec += ["```json", str(dc["example_json"]).rstrip(), "```", ""]
            rules = dc.get("rules") or []
            if rules:
                sec.append(t("**规则：**"))
                sec.append("")
                for rule in rules:
                    sec.append(f"- {prose(rule)}")
                sec.append("")
        sections.append(("数据契约", sec))

    # ---- 角色与权限 ----
    actors = [a for a in (data.get("actors") or []) if isinstance(a, dict)]
    sec = [t("下面是**登录身份**（谁在操作系统），不是页面名称。可执行动作是业务动作（和下一章「动作」列对应），不是接口路径，也不是数据库字段。"), ""]
    sec += [t("| 身份 | 机读 ID | 可执行动作 |"), "|------|---------|------------|"]
    perm_map = {
        p.get("actor"): p.get("can") or []
        for p in (data.get("permissions") or [])
        if isinstance(p, dict)
    }
    for a in actors:
        aid = a.get("id")
        cans = "、".join(_fmt_action(states, x) for x in (perm_map.get(aid) or []))
        sec.append(f"| {_lang(a, lang) or '—'} | `{aid}` | {cans or '—'} |")
    sec.append("")
    sections.append(("角色与权限", sec))

    permission_rows = [
        (p.get("actor"), rule)
        for p in (data.get("permissions") or [])
        if isinstance(p, dict)
        for rule in (p.get("rules") or [])
        if isinstance(rule, dict)
    ]
    if permission_rows:
        sec = [
            t("| 规则 | 角色 | 动作 | 对象 | 状态 | 结果 | 生效面 | 执行位置 |"),
            "|------|------|------|------|------|------|--------|----------|",
        ]
        for actor, rule in permission_rows:
            sec.append(
                "| `{rid}` | `{actor}` | `{action}` | `{obj}` | {states} | `{effect}` | {surfaces} | {enforcement} |".format(
                    rid=rule.get("id") or "—",
                    actor=actor or "—",
                    action=rule.get("action") or "—",
                    obj=rule.get("object") or "—",
                    states="、".join(f"`{v}`" for v in (rule.get("states") or [])) or "—",
                    effect=rule.get("effect") or "—",
                    surfaces="、".join(f"`{v}`" for v in (rule.get("surfaces") or [])) or "—",
                    enforcement="、".join(str(v) for v in (rule.get("enforcement") or [])) or "—",
                )
            )
        sec.append("")
        sections.append(("权限规则矩阵", sec))

    # ---- 状态与允许动作 ----
    matrix = action_matrix_rows(states)
    lifecycle = [str(s) for s in (states.get("lifecycle") or []) if s]
    denied = sum(1 for r in matrix if r.get("allowed") is False)
    action_kinds = len({str(r.get("action")) for r in matrix if r.get("action")})
    sec = [
        t("本章回答两件事：①现在处于哪个状态（哪个页面/哪条任务）；②该状态下哪些动作允许、哪些禁止。下图按对象分组，方框之间没有箭头——允许的转移只看下面的表，不从图上猜。"),
        "",
    ]
    if matrix:
        sec += [
            t("共 {s} 个状态、{a} 类动作，其中明确禁止 {d} 项。前端按钮显隐与置灰以下表为唯一准据。").format(
                s=len(lifecycle), a=action_kinds, d=denied
            ),
            "",
        ]
    life_mermaid = mermaid_lifecycle(states)
    if life_mermaid:
        sec += [t("已声明的状态集合（不表示转移；允许的转移以下表为准）："), "", "```mermaid", life_mermaid, "```", ""]
    if lifecycle:
        sec.append(t("**按对象列出的状态（编号只为对照，不是流转顺序）：**"))
        grouped: list[tuple[str, list[str]]] = []
        gindex: dict[str, int] = {}
        for sid in lifecycle:
            zh, of_ = _label_node(states, sid)
            key = of_ or t("模块")
            if key not in gindex:
                gindex[key] = len(grouped)
                grouped.append((key, []))
            grouped[gindex[key]][1].append(sid)
        n = 1
        for subject, ids in grouped:
            sec += ["", t("### {subject}").format(subject=subject), ""]
            for sid in ids:
                zh, _of = _label_node(states, sid)
                label = f"{zh}（`{sid}`）" if zh else f"`{sid}`"
                sec.append(f"{n}. {label}")
                n += 1
        sec.append("")
    sec += [t("| 状态 | 动作 | 是否允许 | 说明 |"), "|------|------|----------|------|"]
    for row in matrix:
        st = str((row or {}).get("state") or "")
        act = str((row or {}).get("action") or "")
        st_zh, st_of = _label_node(states, st)
        act_zh = _action_label(states, act)
        st_cell = f"{st_zh}（`{st}`）" if st_zh else f"`{st}`"
        if st_of:
            st_cell = f"{st_of} · {st_cell}"
        act_cell = f"{act_zh}（`{act}`）" if act_zh else f"`{act}`"
        sec.append(
            f"| {st_cell} | {act_cell} | {_allowed_label(row, lang)} | {prose(row) or '—'} |"
        )
    if not matrix:
        sec.append(t("| （机读未提供 action_matrix） | — | — | — |"))
    sec.append("")
    sections.append(("状态与允许动作", sec))

    # ---- 页面与交互 ----
    sec = [t("本章是页面上用户能点到的按钮和输入框。按钮文案是界面上的字；机读 ID 给规格与原型对账。"), ""]
    if ui.get("entry"):
        sec += [t("**入口：** {entry}").format(entry=prose(ui.get("entry"))), ""]
    if ui.get("wireframe"):
        sec += [t("### 线框"), "", "```text", _expand_machine_ids(str(ui.get("wireframe")), data, lang).rstrip(), "```", ""]
    controls = [c for c in (ui.get("controls") or []) if isinstance(c, dict)]
    if controls:
        with_fail = sum(
            1 for c in controls if isinstance(c, dict) and _lang(c.get("fail_feedback"), lang) not in ("", "—")
        )
        sec += [
            t("### 控件规格"),
            "",
            t("共 {n} 个控件，其中 {f} 个定义了失败反馈文案。").format(n=len(controls), f=with_fail),
            "",
            t("| 按钮文案 | 机读 ID | 显示条件 | 交互 | 失败反馈 |"),
            "|----------|---------|----------|------|----------|",
        ]
        for c in controls:
            sec.append(
                "| {label} | `{name}` | {when} | {action} | {fail} |".format(
                    name=c.get("id", ""),
                    label=_lang(c, lang) or c.get("id", ""),
                    when=prose(c.get("visible_when")) or "—",
                    action=prose(c.get("action")) or "—",
                    fail=prose(c.get("fail_feedback")) or "—",
                )
            )
        sec.append("")
    sections.append(("页面与交互", sec))

    # ---- 主路径（编号） ----
    sec = [t("共 {n} 步。这是「功能说明」的可观察结果写法，供评审逐条核对；编号不是用户操作顺序。").format(n=len(behaviors)), ""]
    for b in behaviors:
        step = b.get("step_id") or b.get("id")
        sec += [
            t("### 步骤 {step} · {name}").format(step=step, name=_lang(b.get("name"), lang)),
            "",
            t("- **Given：** {v}").format(v=prose(b.get("given"))),
            t("- **When：** {v}").format(v=prose(b.get("when"))),
            t("- **Then：** {v}").format(v=prose(b.get("then"))),
        ]
        if b.get("side_effects"):
            sec.append(t("- **连带结果：**"))
            for s in b.get("side_effects") or []:
                sec.append(f"  - {prose(s)}")
        if b.get("goal"):
            sec.append(t("**目标：** {v}").format(v=prose(b.get("goal"))))
        if b.get("entry_ref"):
            sec.append(t("**入口：** `{v}`").format(v=b.get("entry_ref")))
        if b.get("actor_refs"):
            sec.append(t("**参与角色：** {v}").format(v="、".join(f"`{v}`" for v in b.get("actor_refs") or [])))
        if b.get("reads") or b.get("writes"):
            sec.append(
                t("**读取 / 修改：** {reads} / {writes}").format(
                    reads="、".join(f"`{v}`" for v in b.get("reads") or []) or "—",
                    writes="、".join(f"`{v}`" for v in b.get("writes") or []) or "—",
                )
            )
        if b.get("permission_refs"):
            sec.append(t("**权限规则：** {v}").format(v="、".join(f"`{v}`" for v in b.get("permission_refs") or [])))
        if b.get("idempotency"):
            sec.append(t("**幂等口径：** {v}").format(v=prose(b.get("idempotency"))))
        if b.get("recovery"):
            sec.append(t("**恢复方式：** {v}").format(v=prose(b.get("recovery"))))
        exceptions = [e for e in (b.get("exceptions") or []) if isinstance(e, dict)]
        if exceptions:
            sec += ["", t("**异常与恢复：**"), "", t("| 异常 | 触发条件 | 用户看到 | 已保存事实 | 重试 / 恢复 |"), "|------|----------|----------|------------|-------------|"]
            for exc in exceptions:
                retry = prose(exc.get("retry"))
                recovery = prose(exc.get("recovery"))
                retry_recovery = "；".join(v for v in (retry, recovery) if v) or "—"
                sec.append(
                    "| `{id}` | {trigger} | {visible} | {facts} | {rr} |".format(
                        id=exc.get("id") or "—",
                        trigger=prose(exc.get("trigger")) or "—",
                        visible=prose(exc.get("visible_result")) or "—",
                        facts="、".join(prose(v) for v in (exc.get("preserved_facts") or [])) or "—",
                        rr=retry_recovery,
                    )
                )
        sec.append("")
    sections.append(("主路径（编号）", sec))

    # ---- 默认值与提示文案 ----
    sec = [t("### 默认值"), ""]
    defaults = data.get("defaults") or {}
    if defaults:
        sec += [t("| 项 | 值 |"), "|----|----|"]
        for k, v in defaults.items():
            sec.append(f"| `{k}` | {_fmt_default_value(v, data, lang)} |")
    else:
        sec.append(t("（无）"))
    sec += ["", t("### 空态 / 拦截文案（须与界面一致）"), ""]
    empty = data.get("empty_states") or ui.get("empty_states") or {}
    if empty:
        sec += [t("| 场景 | 文案 |"), "|------|------|"]
        for k, v in empty.items():
            sec.append(f"| `{k}` | {_lang(v, lang)} |")
    else:
        sec.append(t("（无）"))
    sec.append("")
    sections.append(("默认值与提示文案", sec))

    # ---- 错误码 ----
    error_codes = [e for e in (data.get("error_codes") or []) if isinstance(e, dict)]
    if error_codes:
        sec = [
            t("评审时用一张表统一错误含义、触发条件、是否可重试和用户看到的文案。"),
            "",
            t("| 错误码 | 含义 | 触发场景 | 可重试 | 用户文案 |"),
            "|--------|------|----------|--------|----------|",
        ]
        for e in error_codes:
            retry = t("是") if e.get("retryable") else t("否")
            sec.append(
                f"| `{e.get('code')}` | {e.get('zh') or '—'} | {prose(e.get('trigger')) or '—'} | {retry} | {prose(e.get('user_copy')) or '—'} |"
            )
        sec.append("")
        sections.append(("错误码", sec))

    # ---- 验收标准（AC） ----
    sec = [t("共 {n} 条；逐条可执行，已知空话／占位词会被门禁否决。").format(n=len(acceptance)), ""]
    for a in acceptance:
        sec.append(
            t("- **{aid}**（行为 `{bid}`）：{text}").format(
                aid=a.get("id"), bid=a.get("behavior"), text=prose(a)
            )
        )
    sec.append("")
    sections.append(("验收标准（AC）", sec))

    # ---- Pending ----
    sec = []
    pending = [p for p in (data.get("pending") or []) if isinstance(p, dict)]
    if not pending:
        sec.append(t("无。"))
    else:
        sec += [t("| ID | 类型 | 问题 / 缺失事实 | 影响范围 | 选项与建议 | 责任人 | 状态 |"), "|----|------|-----------------|----------|------------|--------|------|"]
        for p in pending:
            kind = t("产品取舍") if p.get("kind") == "decision" else t("事实缺口")
            options = []
            for option in p.get("options") or []:
                if isinstance(option, dict):
                    options.append(f"{option.get('zh') or option.get('id') or '—'} (`{option.get('id') or '—'}`)")
                else:
                    options.append(str(option))
            recommendation = prose(p.get("recommendation"))
            tradeoff = prose(p.get("tradeoff"))
            choice = "；".join(
                v for v in (
                    " / ".join(options),
                    (f"建议：{recommendation}" if recommendation else ""),
                    (f"代价：{tradeoff}" if tradeoff else ""),
                ) if v
            ) or "—"
            sec.append(
                f"| {p.get('id')} | {kind} | {p.get('missing')} | {p.get('impact')} | {choice} | {p.get('owner')} | {p.get('status')} |"
            )
    sec.append("")
    sections.append(("信息待闭合项（Pending）", sec))

    # ---- 决策记录 ----
    decisions = [d for d in (data.get("decisions") or []) if isinstance(d, dict)]
    if decisions:
        undecided = sum(
            1
            for d in decisions
            if str(d.get("status") or "") == "pending" or (not d.get("chosen") and str(d.get("status") or "") != "decided")
        )
        sec = [
            t("共 {n} 项，已拍板 {d} 项，待定 {u} 项。「为什么是这样」的存档，新人不必考古聊天记录。").format(
                n=len(decisions), d=len(decisions) - undecided, u=undecided
            ),
            "",
            t("| ID | 问题 | 选定 | 日期 | 备注 |"),
            "|----|------|------|------|------|",
        ]
        for d in decisions:
            chosen = d.get("chosen") or t("**待定**")
            if d.get("chosen"):
                selected = next(
                    (
                        option
                        for option in (d.get("options") or [])
                        if isinstance(option, dict)
                        and str(option.get("id") or "") == str(d.get("chosen"))
                    ),
                    None,
                )
                selected_label = prose(selected) if selected else ""
                if selected_label:
                    chosen = f"{selected_label} (`{d.get('chosen')}`)"
            sec.append(
                f"| {d.get('id')} | {prose(d.get('question'))} | {chosen} | {d.get('date') or '—'} | {prose(d.get('note')) or '—'} |"
            )
        sec.append("")
        sections.append(("决策记录", sec))

    # ---- 对象 AI ----
    obj = data.get("object_ai") or {}
    sec = [f"- enabled: `{obj.get('enabled', False)}`"]
    if obj.get("enabled"):
        sec.append(t("- 失败兜底: {v}").format(v=prose(obj.get("failure_fallback"))))
        sec.append(t("- 工具边界:"))
        for item in obj.get("tools_boundary") or []:
            sec.append(f"  - {prose(item)}")
        sec.append(t("- 人工接管:"))
        for item in obj.get("human_takeover_when") or []:
            sec.append(f"  - {prose(item)}")
    sec.append("")
    sections.append(("对象 AI", sec))

    # ---- 原料落到规格（附录） ----
    claims = data.get("source_claims") or []
    if claims:
        buckets = claim_summary(data)
        sec = [
            t("下面逐条对照原始需求说明。处理结果用中文；括号里的编号给助手和检查工具对账。已写入规格 {c} 条 · 原文没写、规格补了猜测 {a} 条 · 本期不做 {o} 条 · 其他 {r} 条。完整性需要开会时抽查。").format(
                c=len(buckets.get("covered") or []),
                a=len(buckets.get("assumption") or []),
                o=len(buckets.get("out_of_scope") or []),
                r=len(claims)
                - len(buckets.get("covered") or [])
                - len(buckets.get("assumption") or [])
                - len(buckets.get("out_of_scope") or []),
            ),
            "",
            t("| 原料条目编号 | 处理结果 | 这条在说什么 | 落到说明书的哪一段 |"),
            "|--------------|----------|--------------|--------------------|",
        ]
        for c in claims:
            if not isinstance(c, dict):
                continue
            disp = str(c.get("disposition") or "").strip()
            summary = c.get("quote_or_summary") or c.get("evidence") or "—"
            sec.append(
                f"| `{c.get('id')}` | {disposition_label(disp, lang)} | {summary} | {format_landing(c, data, lang)} |"
            )
        sec.append("")
        sections.append(("原料落在规格里的情况", sec))

    # ---- 组装：标题块 → 目录 → 编号章节 ----
    numbered = [(f"{i}. {t(title)}", body) for i, (title, body) in enumerate(sections, 1)]
    lines: list[str] = [
        f"# {title_main}",
        "",
        t("> **文档类型**：评审就绪的标准需求规格说明书（人读评审稿）<br>"),
        t("> **规格编号**：`{sid}` · **进度**：{status} · **版本**：`{ver}`  ").format(
            sid=data.get("id"),
            status=status_label(str(data.get("status") or ""), lang),
            ver=data.get("spec_version"),
        ),
        t("> **机读哈希**：`{digest}…`<br>").format(digest=digest[:16]),
        t("> **怎么读：** 先看「功能说明」判断本期方案；「主路径」用 Given/When/Then 逐条核对结果；「状态与允许动作」说明按钮何时可点；「页面与交互」说明按钮文案和失败提示。"),
        "",
    ]
    if title_alt and title_alt != title_main:
        lines += [t("**EN title:** {t}").format(t=title_alt), ""]
    lines += [f"## {t('目录')}", ""]
    for heading, _body in numbered:
        lines.append(f"- [{heading}](#{_anchor(heading)})")
    lines.append("")
    for heading, body in numbered:
        lines += [f"## {heading}", ""]
        lines += body

    body_text = "\n".join(lines)
    if not body_text.endswith("\n"):
        body_text += "\n"

    def _assemble(body_digest: str) -> str:
        chrome = (
            f"<!-- generated_from: {source} -->\n"
            f"<!-- spec_id: {data.get('id')} -->\n"
            f"<!-- spec_version: {data.get('spec_version')} -->\n"
            f"<!-- spec_hash: {digest} -->\n"
            f"<!-- body_hash: {body_digest} -->\n"
            f"<!-- renderer_version: {RENDERER_VERSION} -->\n"
            f"<!-- lang: {lang} -->\n"
            f"<!-- gate_mode: {gate_mode} -->\n"
            + t("<!-- 以机读 YAML 为唯一准据；禁止长期只改本文件 -->")
        )
        # Trailer only: HTML comments between title and TOC show as blank
        # in Markdown preview.
        out = body_text.rstrip() + "\n\n" + chrome + "\n"
        return out

    draft = _assemble("0" * 64)
    return _assemble(human_body_hash(split_human_markdown(draft)[1]))
