#!/usr/bin/env python3
"""Product-manager wording for derived views (self-check report, human appendix).

Machine YAML still stores English enumerations. Anything a product manager reads
must lead with Chinese; machine ids stay in parentheses for reconciling only.
"""
from __future__ import annotations

import re

# (short label, one-line meaning) — meaning is for summary tables / legends.
DISPOSITION_ZH: dict[str, tuple[str, str]] = {
    "covered": (
        "已写入规格",
        "原始说明里的这条，已经写进说明书对应条目",
    ),
    "omitted": (
        "原文有、规格没写",
        "原始说明要求了，说明书里没有对应写法，也没有说明为什么不写",
    ),
    "assumption": (
        "原文没写、规格补了猜测",
        "原始说明没写死，起草时补上了；结构检查不挡，但需要你认或不认",
    ),
    "conflict": (
        "原文互相打架",
        "同一份原始说明前后说法不一致，必须先拍板才能当终稿",
    ),
    "out_of_scope": (
        "本期不做",
        "已经明确不在这一期做",
    ),
    "pending": (
        "还没定",
        "已经登记为未决事项，终稿前必须收口",
    ),
    "undisposed": (
        "还没登记怎么处理",
        "从原始说明拆出来了，但还没标明怎么处理",
    ),
}

DISPOSITION_EN: dict[str, tuple[str, str]] = {
    "covered": ("Written into the spec", "This source item landed on spec entities"),
    "omitted": ("In the source, missing from the spec", "Required by source, not in the spec, and unexplained"),
    "assumption": ("Guess filled in; source was silent", "Needs the product manager to accept or reject"),
    "conflict": ("Source contradicts itself", "Must be decided before a final spec"),
    "out_of_scope": ("Out of this slice", "Explicitly not in this delivery"),
    "pending": ("Still open", "Must be closed before a final spec"),
    "undisposed": ("Not filed yet", "Extracted but no handling recorded"),
}

PROTO_BUCKET_ZH: dict[str, tuple[str, str]] = {
    "missing": ("规格有、页面稿没有", "说明书要求了这个控件或功能，可点页面稿里找不到"),
    "extra": ("页面稿有、规格没有", "可点页面稿多出来的东西，说明书没写"),
    "stale": ("规格改过了、页面稿还是旧版", "说明书已经改过，可点页面稿还按旧版对账"),
    "mismatch": ("对不上", "说明书和可点页面稿对不上号"),
    "unverified": ("还没核实", "页面怎么排、按钮怎么放，还是起草时的假设，原文没有写死"),
}

STATUS_ZH = {
    "draft": "草稿，还不能当终稿",
    "ready": "已定稿，结构已过关，可以开会",
    "deprecated": "已停用",
}
STATUS_EN = {
    "draft": "Draft, not a final spec yet",
    "ready": "Final for this slice; structure passed, can go to review",
    "deprecated": "Deprecated",
}

_KIND_ZH = {
    "behavior": "功能",
    "behaviors": "功能",
    "acceptance": "验收句",
    "ac": "验收句",
    "control": "页面控件",
    "controls": "页面控件",
}

def _text(node, lang: str = "zh") -> str:
    if isinstance(node, dict):
        if lang in node and node[lang]:
            return str(node[lang]).strip()
        if "zh" in node and node["zh"]:
            return str(node["zh"]).strip()
        if "en" in node and node["en"]:
            return str(node["en"]).strip()
        return ""
    if node is None:
        return ""
    return str(node).strip()


def _inline(text: str) -> str:
    """Keep the complete wording while making it safe for one Markdown row."""
    return " ".join((text or "").split())


def _drop_ascii_paren(text: str) -> str:
    """Drop a trailing English parenthetical left in by drafting notes."""
    return re.sub(r"\s+\([^)]*[A-Za-z][^)]*\)\s*$", "", text or "").strip()


def disposition_label(key: str, lang: str = "zh") -> str:
    table = DISPOSITION_ZH if lang != "en" else DISPOSITION_EN
    pair = table.get(str(key or "").strip())
    return pair[0] if pair else str(key or "—")


def disposition_meaning(key: str, lang: str = "zh") -> str:
    table = DISPOSITION_ZH if lang != "en" else DISPOSITION_EN
    pair = table.get(str(key or "").strip())
    return pair[1] if pair else ""


def proto_bucket_label(key: str) -> str:
    pair = PROTO_BUCKET_ZH.get(str(key or "").strip())
    return pair[0] if pair else str(key or "—")


def proto_bucket_meaning(key: str) -> str:
    pair = PROTO_BUCKET_ZH.get(str(key or "").strip())
    return pair[1] if pair else ""


def status_label(status: str, lang: str = "zh") -> str:
    raw = str(status or "").strip()
    table = STATUS_ZH if lang != "en" else STATUS_EN
    zh = table.get(raw)
    if zh and raw:
        return f"{zh} (`{raw}`)" if lang == "en" else f"{zh}（`{raw}`）"
    return f"`{raw}`" if raw else "—"


def format_spec_ref(data: dict, ref: str, lang: str = "zh") -> str:
    """Turn a machine spec_ref into a Chinese phrase with the id in parentheses."""
    token = str(ref or "").strip()
    if not token:
        return "—"

    if token.startswith("defaults."):
        key = token.split(".", 1)[1]
        return f"默认值「{key}」（`{token}`）"
    if token.startswith("empty_states."):
        key = token.split(".", 1)[1]
        empty = data.get("empty_states") if isinstance(data.get("empty_states"), dict) else {}
        zh = _text(empty.get(key), lang)
        if zh:
            return f"界面提示「{zh}」（`{token}`）"
        return f"界面提示（`{token}`）"

    for b in data.get("behaviors") or []:
        if isinstance(b, dict) and str(b.get("id") or "") == token:
            name = _text(b.get("name"), lang) or _text(b, lang)
            if name:
                return f"功能「{name}」（`{token}`）"
            return f"功能（`{token}`）"

    for a in data.get("acceptance") or []:
        if isinstance(a, dict) and str(a.get("id") or "") == token:
            body = _text(a, lang) or _text(a.get("text"), lang)
            if body:
                return f"验收句「{_inline(body)}」（`{token}`）"
            return f"验收句（`{token}`）"

    ui = data.get("ui") if isinstance(data.get("ui"), dict) else {}
    for c in ui.get("controls") or []:
        if isinstance(c, dict) and str(c.get("id") or "") == token:
            zh = _text(c, lang)
            if zh:
                return f"页面控件「{zh}」（`{token}`）"
            return f"页面控件（`{token}`）"

    for d in data.get("decisions") or []:
        if isinstance(d, dict) and str(d.get("id") or "") == token:
            q = _text(d.get("question"), lang)
            if q:
                return f"已拍板事项「{_inline(q)}」（`{token}`）"
            return f"已拍板事项（`{token}`）"

    for p in data.get("pending") or []:
        if isinstance(p, dict) and str(p.get("id") or "") == token:
            q = _text(p.get("question"), lang) or _text(p.get("missing"), lang)
            if q:
                return f"未决事项「{_inline(q)}」（`{token}`）"
            return f"未决事项（`{token}`）"

    return f"`{token}`"


def format_landing(claim: dict, data: dict, lang: str = "zh") -> str:
    refs = [str(r) for r in (claim.get("spec_refs") or []) if str(r).strip()]
    if refs:
        return "；".join(format_spec_ref(data, r, lang) for r in refs)
    resolution = str(claim.get("resolution") or "").strip()
    if resolution:
        return resolution
    disp = str(claim.get("disposition") or "").strip()
    if disp == "out_of_scope":
        return "本期不做，不落到说明书具体条目"
    if disp == "conflict":
        return "原文打架，还没有拍板结论"
    if disp == "omitted":
        return "规格里没有对应写法"
    if disp == "pending":
        return "还没定，未落到说明书具体条目"
    return "—"


def _kind_zh(kind: str) -> str:
    return _KIND_ZH.get(str(kind or "").lower(), str(kind or "条目"))


def humanize_warning_id(wid: str) -> str:
    token = str(wid or "").strip()
    m = re.match(r"^assumption:(.+)$", token)
    if m:
        return f"原文没写、规格补了猜测（原料条目 `{m.group(1)}`）"
    m = re.match(r"^step_id:(.+)$", token)
    if m:
        return f"功能步骤编号待补（`{m.group(1)}`）"
    m = re.match(r"^permission:(.+)$", token)
    if m:
        return f"权限写法待核对（`{m.group(1)}`）"
    if token.startswith("warn:"):
        return f"其他提醒（内部编号 `{token}`）"
    return f"`{token}`" if token else "—"


_READY_REQUIREMENTS_ZH = {
    "actors": "参与角色（谁使用、谁负责、谁可以操作）",
    "non-empty in_scope": "本期范围",
    "a non-empty title": "需求标题",
    "defaults with at least one real key": "真实默认值",
    "ui (wireframe or non-empty controls)": "页面入口、控件或线框",
    "ui.wireframe or non-empty ui.controls": "页面线框或控件清单",
    "states (lifecycle / allowed actions)": "状态变化和允许动作",
    "states.action_matrix (lifecycle alone is not enough)": "状态与动作对应关系",
    "product/information architecture (architecture.mermaid)": "产品与信息架构",
    "product module responsibilities": "产品模块职责边界",
    "product data contracts": "业务数据契约",
    "product error definitions": "用户可见的错误定义",
}


def _ready_requirement_zh(requirement: str) -> str:
    raw = str(requirement or "").strip()
    if raw.startswith("D-PROTOTYPE:"):
        return "终稿还缺少原型决策：请说明是否需要可交互原型，以及原型放在哪里。"
    if raw.startswith("regenerate human/prototype"):
        return "状态切换后需要重新生成方案文档和原型，避免内容指纹失效。"
    meaning = _READY_REQUIREMENTS_ZH.get(raw)
    if meaning:
        return f"终稿还缺少{meaning}。"
    return f"终稿还缺少必填内容：{raw}。"


def _behavior_field_zh(field: str) -> str:
    return {
        "given": "前置条件",
        "when": "用户动作",
        "then": "预期结果",
    }.get(str(field or "").strip(), str(field or "步骤"))


def humanize_finding(msg: str) -> str:
    """Translate a gate finding into a sentence a product manager can act on."""
    text = str(msg or "").strip()
    patterns: list[tuple[re.Pattern[str], object]] = [
        (
            re.compile(r"^status=ready but open_questions is not empty — move to pending with owner or resolve$"),
            lambda _m: "终稿仍有未决事项：请补充负责人和处理状态，或先拍板解决。",
        ),
        (
            re.compile(r"^status=ready requires (.+)$"),
            lambda m: _ready_requirement_zh(m.group(1)),
        ),
        (
            re.compile(r"^behavior (\S+): missing name — the human view would render an unnamed step$"),
            lambda m: f"功能 {m.group(1)} 缺少名称，评审材料无法说明这一步要完成什么。",
        ),
        (
            re.compile(r"^behavior (\S+): (given|when|then) is empty$"),
            lambda m: f"功能 {m.group(1)} 缺少{_behavior_field_zh(m.group(2))}。",
        ),
        (
            re.compile(r"^behavior (\S+): (given|when|then)-clause too vague for ready$"),
            lambda m: f"功能 {m.group(1)} 的{_behavior_field_zh(m.group(2))}太笼统，无法据此评审或验收。",
        ),
        (
            re.compile(r"^behavior (\S+): (given|when|then) is still placeholder text$"),
            lambda m: f"功能 {m.group(1)} 的{_behavior_field_zh(m.group(2))}仍是占位内容，请补成具体说法。",
        ),
        (
            re.compile(r"^acceptance (\S+): missing behavior link — every AC must verify a behavior$"),
            lambda m: f"验收场景 {m.group(1)} 没有对应功能，无法判断它要验证哪条流程。",
        ),
        (
            re.compile(r"^acceptance (\S+): missing observable zh/en text$"),
            lambda m: f"验收场景 {m.group(1)} 缺少可观察的结果描述。",
        ),
        (
            re.compile(r"^acceptance (\S+): not observable$"),
            lambda m: f"验收场景 {m.group(1)} 仍不可观察，请写清状态、页面结果或用户能看到的反馈。",
        ),
        (
            re.compile(r"^acceptance (\S+): is still placeholder text$"),
            lambda m: f"验收场景 {m.group(1)} 仍是占位内容，请改成可以判断对错的具体结果。",
        ),
        (
            re.compile(r"^permission (\S+): can=(\S+) is not an action in states\.action_matrix — confirm it is a capability label, not a state-machine action$"),
            lambda m: f"角色「{m.group(1)}」的权限「{m.group(2)}」未出现在状态动作表中，请确认它是权限标签还是业务动作。",
        ),
        (
            re.compile(r"^source (\S+): path not verified \(no spec file context\)$"),
            lambda m: f"原料「{m.group(1)}」的文件路径尚未核实；当前试用环境没有对应原料文件可供对账。",
        ),
        (
            re.compile(r"^source (\S+): missing path — ready requires every source to have a path$"),
            lambda m: f"原料「{m.group(1)}」没有来源文件路径，无法追溯原始需求。",
        ),
        (
            re.compile(r"^source_claims missing — ready requires coverage evidence$"),
            lambda _m: "缺少原料对照记录，无法说明每条需求是如何进入方案的。",
        ),
        (
            re.compile(r"^overview missing — readers get no orientation before detail sections$"),
            lambda _m: "缺少方案概览，读者进入细节前不知道这份方案要解决什么。",
        ),
        (
            re.compile(r"^ui block missing — human spec will lack wireframe/controls$"),
            lambda _m: "缺少页面和控件说明，评审时无法讨论入口、操作和反馈。",
        ),
        (
            re.compile(r"^states block missing — lifecycle/actions unclear$"),
            lambda _m: "缺少状态和动作说明，主流程及不同状态下能否操作不清楚。",
        ),
        (
            re.compile(r"^empty_states missing — empty/error copy may be invented downstream$"),
            lambda _m: "缺少空状态和错误提示，后续容易由不同角色各自猜文案。",
        ),
        (
            re.compile(r"^behavior (\S+): prefer step_id for numbered main path$"),
            lambda m: f"功能 {m.group(1)} 建议补充主流程步骤编号，方便评审时按顺序讨论。",
        ),
        (
            re.compile(r"^scope contradiction: (.+) is both in_scope and out_of_scope$"),
            lambda m: f"范围冲突：{m.group(1)} 同时被列入本期范围和不做范围，请先统一口径。",
        ),
        (
            re.compile(r"^decision (\S+): chosen recorded without options to choose from$"),
            lambda m: f"决策「{m.group(1)}」已经写了选择结果，但没有列出可选方案，无法复核决策依据。",
        ),
        (
            re.compile(r"^source_claim (\S+): assumption — confirm with product owner$"),
            lambda m: (
                f"原料条目 {m.group(1)}：原文没写、规格补了猜测，需要你确认认不认。"
            ),
        ),
        (
            re.compile(r"^source_claim (\S+): omitted — unexplained gap blocks ready$"),
            lambda m: (
                f"原料条目 {m.group(1)}：原文有要求，规格里没写，也没说明为什么不写。"
                "终稿不能留这种缺口。"
            ),
        ),
        (
            re.compile(r"^source_claim (\S+): conflict not closed \(need resolution\)$"),
            lambda m: f"原料条目 {m.group(1)}：原文互相打架，还没有拍板结论。",
        ),
        (
            re.compile(r"^source_claim (\S+): pending disposition cannot stay on ready$"),
            lambda m: f"原料条目 {m.group(1)}：还标着「还没定」，不能当终稿。",
        ),
        (
            re.compile(r"^source_claim coverage missing for (\S+) (\S+)$"),
            lambda m: (
                f"说明书里的{_kind_zh(m.group(1))} {m.group(2)} 没有对应的原料条目，对不上账。"
            ),
        ),
        (
            re.compile(r"^prototype unverified \[(\w+)\] (\S+): (.+)$"),
            lambda m: (
                f"可点页面稿还未核实（画面 {m.group(2)}）：{_drop_ascii_paren(m.group(3))}"
            ),
        ),
    ]
    for pat, fn in patterns:
        matched = pat.match(text)
        if matched:
            return str(fn(matched))
    if text.startswith("prototype unverified"):
        rest = text.split(":", 1)[-1].strip() if ":" in text else text
        return f"可点页面稿还未核实：{_drop_ascii_paren(rest)}"
    if text.startswith("prototype"):
        return f"可点页面稿：{text}"
    if text.startswith("source_claim"):
        return f"原料对照：{text}"
    if text.startswith("human spec"):
        return f"说明书：{text}"
    return text
