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

_CLIP = 36


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


def _clip(text: str, n: int = _CLIP) -> str:
    text = " ".join((text or "").split())
    if len(text) <= n:
        return text
    return text[: n - 1] + "…"


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
                return f"验收句「{_clip(body)}」（`{token}`）"
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
                return f"已拍板事项「{_clip(q)}」（`{token}`）"
            return f"已拍板事项（`{token}`）"

    for p in data.get("pending") or []:
        if isinstance(p, dict) and str(p.get("id") or "") == token:
            q = _text(p.get("question"), lang) or _text(p.get("missing"), lang)
            if q:
                return f"未决事项「{_clip(q)}」（`{token}`）"
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


def humanize_finding(msg: str) -> str:
    """Translate a gate finding into a sentence a product manager can act on."""
    text = str(msg or "").strip()
    patterns: list[tuple[re.Pattern[str], object]] = [
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
