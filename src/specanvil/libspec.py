#!/usr/bin/env python3
"""SpecAnvil shared load / validate (FAIL|WARN|Pending) / render human spec."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None

REQUIRED_TOP = ["spec_version", "id", "title", "status", "behaviors", "acceptance"]
VAGUE = (
    "体验好",
    "尽量快",
    "智能",
    "方便地",
    "尽快",
    "尽量",
    "good ux",
    "quickly",
    "seamless",
    "intuitive",
    "user-friendly",
    "user friendly",
    "as fast as possible",
    "blazingly fast",
    "best-in-class",
)
RENDERER_VERSION = "3"
SCHEMA_PATH = Path(__file__).resolve().parent / "schemas" / "machine-spec.schema.json"
CLAIM_DISPOSITIONS = {
    "covered",
    "omitted",
    "assumption",
    "conflict",
    "out_of_scope",
    "pending",
}
OPEN_CONFLICT = {"", "open", "unresolved", "待确认", "tbd"}


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


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


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


REF_TOKEN = re.compile(r"\b(?:P|AC|SRC|D)-[A-Za-z0-9][A-Za-z0-9_-]*\b")


def dangling_refs(data: dict) -> list[str]:
    """ID-shaped tokens mentioned anywhere in the spec that are not declared.

    Catches stale free-text cross-references like 「见 P-01」 after P-01 was
    resolved. Only unambiguous spec-owned prefixes (P- / AC- / SRC-) are
    scanned; bare B1/C1 style tokens collide with real-world names (区域 C1,
    型号 B2) and are deliberately left alone.
    """
    blob = json.dumps(data, ensure_ascii=False, default=str)
    known = known_entity_ids(data)
    return sorted({tok for tok in REF_TOKEN.findall(blob) if tok not in known})


def _strip_ui_literals(text: str) -> str:
    """Drop 「…」 spans before the vague-wording scan.

    CJK corner brackets mark literal UI copy (button labels, toast text).
    A real feature named 「智能识别」 must not trip the 智能 empty-talk rule;
    unquoted slogans like 支持智能搜索 still fail.
    """
    return re.sub(r"「[^」]*」", "", text)


def _pending_ok(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    return all(item.get(k) not in (None, "") for k in ("id", "missing", "impact", "owner", "status"))


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
    "架构总览": "Architecture",
    "职责边界": "Responsibilities",
    "数据契约": "Data Contracts",
    "角色与权限": "Roles & Permissions",
    "状态与允许动作": "States & Allowed Actions",
    "页面与交互": "Pages & Interactions",
    "主路径（编号）": "Main Path (numbered)",
    "默认值与提示文案": "Defaults & Copy",
    "错误码": "Error Codes",
    "验收标准（AC）": "Acceptance Criteria (AC)",
    "信息待闭合项（Pending）": "Pending Items",
    "决策记录": "Decision Log",
    "对象 AI": "Object AI",
    "原料覆盖（SourceClaim）": "Source Coverage (SourceClaim)",
    "> **文档类型**：可开发的需求规格说明书（人读视图）  ": "> **Document type**: dev-ready specification (human view)  ",
    "> **规格 ID**：`{sid}` · **状态**：`{status}` · **版本**：`{ver}`  ": "> **Spec ID**: `{sid}` · **Status**: `{status}` · **Version**: `{ver}`  ",
    "> **机读哈希**：`{digest}…`": "> **Machine hash**: `{digest}…`",
    "**设计原则：**": "**Design principles:**",
    "**环境与约束：**": "**Environment & constraints:**",
    "**本期做：**": "**In scope:**",
    "**本期不做（白名单外，不展开）：**": "**Out of scope (whitelist only, not elaborated):**",
    "**对照基线：** {baseline}": "**Baseline:** {baseline}",
    "谁负责什么、明确不负责什么，开工前先对齐边界。": "Who owns what — and explicitly what they do not — settled before work starts.",
    "| 负责 | 不负责 |": "| Owns | Does not own |",
    "共 {n} 个数据实体；字段即前后端接口与存储的对齐口径。": "{n} data entities; the fields are the alignment contract between frontend, backend and storage.",
    "| 字段 | 中文 | 类型 | 说明 |": "| Field | Label | Type | Notes |",
    "**规则：**": "**Rules:**",
    "{n} 类角色；可执行动作与状态矩阵联动。": "{n} actor roles; allowed actions tie back to the state matrix.",
    "| 角色 | 说明 | 可执行动作 |": "| Role | Description | Allowed actions |",
    "{s} 个状态 × {a} 类动作，其中明确禁止 {d} 项。前端显隐与置灰以下表为唯一准据。": "{s} states × {a} action kinds, {d} explicitly denied. The table below is the single source of truth for enabling/hiding controls.",
    "生命周期顺序（示意）：": "Lifecycle order (indicative):",
    "**生命周期（编号供流程对照）：**": "**Lifecycle (numbered for flow reference):**",
    "| 状态 | 动作 | 是否允许 | 说明 |": "| State | Action | Allowed | Notes |",
    "| （机读未提供 action_matrix） | — | — | — |": "| (machine source has no action_matrix) | — | — | — |",
    "**入口：** {entry}": "**Entry:** {entry}",
    "### 线框": "### Wireframe",
    "### 控件规格": "### Control Spec",
    "共 {n} 个控件，其中 {f} 个定义了失败反馈文案。": "{n} controls, {f} of them with explicit failure-feedback copy.",
    "| 控件 | 文案/占位 | 显示条件 | 交互 | 失败反馈 |": "| Control | Label/placeholder | Visible when | Interaction | Failure feedback |",
    "共 {n} 步；每步的 Given/When/Then 同时是测试的验收输入。": "{n} steps; every Given/When/Then doubles as test acceptance input.",
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
    "开发按码实现分支，测试按码构造用例，客服按文案答复——一张表三方共用。": "Developers branch on the code, testers derive cases from it, support answers with the copy — one table, three consumers.",
    "| 错误码 | 含义 | 触发场景 | 可重试 | 用户文案 |": "| Code | Meaning | Trigger | Retryable | User copy |",
    "是": "yes",
    "否": "no",
    "共 {n} 条；逐条可执行，不可观察的表述会被门禁否决。": "{n} criteria; each one executable — unobservable wording is rejected by the gate.",
    "- **{aid}**（行为 `{bid}`）：{text}": "- **{aid}** (behavior `{bid}`): {text}",
    "无。": "None.",
    "| ID | 缺失信息 | 影响范围 | 责任人 | 状态 |": "| ID | Missing | Impact | Owner | Status |",
    "共 {n} 项，已拍板 {d} 项，待定 {u} 项。「为什么是这样」的存档，新人不必考古聊天记录。": "{n} decisions — {d} settled, {u} open. The archive of why things are this way; no chat-log archaeology needed.",
    "| ID | 问题 | 选定 | 日期 | 备注 |": "| ID | Question | Chosen | Date | Note |",
    "**待定**": "**undecided**",
    "- 失败兜底: {v}": "- Failure fallback: {v}",
    "- 工具边界:": "- Tool boundary:",
    "- 人工接管:": "- Human takeover:",
    "覆盖账本（附录）：原料每句话的下落。covered {c} · assumption {a} · out_of_scope {o} · 其他 {r}。": "Coverage ledger (appendix): where every source statement landed. covered {c} · assumption {a} · out_of_scope {o} · other {r}.",
    "| ID | 处置 | 摘要 | 规格引用 |": "| ID | Disposition | Summary | Spec refs |",
    "**EN title:** {t}": "**Title (zh):** {t}",
    "<!-- 以机读 YAML 为唯一准据；禁止长期只改本文件 -->": "<!-- Machine YAML is the single source of truth; do not hand-edit this file long-term -->",
}


def _tt(lang: str):
    if lang == "en":
        return lambda s: _EN.get(s, s)
    return lambda s: s


def action_matrix_rows(states: dict) -> list[dict]:
    """Prefer action_matrix; fall back to legacy cancel_matrix."""
    if not isinstance(states, dict):
        return []
    rows = states.get("action_matrix")
    if isinstance(rows, list) and rows:
        return [r for r in rows if isinstance(r, dict)]
    legacy = states.get("cancel_matrix")
    if isinstance(legacy, list) and legacy:
        out = []
        for r in legacy:
            if not isinstance(r, dict):
                continue
            out.append(
                {
                    **r,
                    "action": r.get("action") or "buyer_self_cancel",
                    "allowed": r.get("allowed", r.get("buyer_self_cancel")),
                }
            )
        return out
    return []


def _collect_ids(fail: list[str], items: list, kind: str) -> set[str]:
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        iid = item.get("id")
        if not iid:
            fail.append(f"{kind} item missing id")
            continue
        sid = str(iid)
        if sid in seen:
            fail.append(f"duplicate {kind} id: {sid}")
        seen.add(sid)
    return seen


def spec_hash(data: dict) -> str:
    """SHA-256 of canonical machine spec (excludes content_hash if present)."""
    payload = {k: v for k, v in data.items() if k != "content_hash"}
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def parse_human_header(text: str) -> dict[str, str]:
    meta: dict[str, str] = {}
    for raw in text.splitlines()[:40]:
        m = re.match(r"^<!--\s*([a-z_]+)\s*:\s*(.*?)\s*-->\s*$", raw.strip())
        if m:
            meta[m.group(1)] = m.group(2)
    return meta


def expected_human_path(spec_path: Path | None) -> Path | None:
    if spec_path is None:
        return None
    return spec_path.resolve().parent.parent / "human" / "spec.md"


def default_human_path(spec_path: Path | None) -> Path | None:
    sibling = expected_human_path(spec_path)
    return sibling if sibling is not None and sibling.is_file() else None


def relpath_from_root(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return path.name


def split_human_markdown(text: str) -> tuple[dict[str, str], str]:
    meta = parse_human_header(text)
    lines = text.splitlines()
    i = 0
    while i < len(lines) and (lines[i].startswith("<!--") or lines[i].strip() == ""):
        i += 1
    body = "\n".join(lines[i:]).strip() + "\n"
    return meta, body


def human_body_hash(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def claim_spec_ref_ids(data: dict) -> set[str]:
    """Whitelist for SourceClaim.spec_refs — spec entities only, not sources/claims/lifecycle names."""
    ids: set[str] = set()
    for items in (
        data.get("behaviors") or [],
        data.get("acceptance") or [],
        (data.get("ui") or {}).get("controls") or [],
        data.get("data_contracts") or [],
        data.get("decisions") or [],
    ):
        for item in items:
            if isinstance(item, dict) and item.get("id"):
                ids.add(str(item.get("id")))
    for key in data.get("defaults") or {}:
        ids.add(f"defaults.{key}")
    for key in data.get("empty_states") or {}:
        ids.add(f"empty_states.{key}")
    return ids


def known_entity_ids(data: dict) -> set[str]:
    ids: set[str] = set()
    for kind, items in (
        ("actor", data.get("actors") or []),
        ("behavior", data.get("behaviors") or []),
        ("acceptance", data.get("acceptance") or []),
        ("pending", data.get("pending") or []),
        ("control", (data.get("ui") or {}).get("controls") or []),
        ("source", data.get("sources") or []),
        ("claim", data.get("source_claims") or []),
        ("data_contract", data.get("data_contracts") or []),
        ("decision", data.get("decisions") or []),
    ):
        del kind
        for item in items:
            if isinstance(item, dict) and item.get("id"):
                ids.add(str(item.get("id")))
    states = data.get("states") or {}
    if isinstance(states, dict):
        for s in states.get("lifecycle") or []:
            ids.add(str(s))
        for row in action_matrix_rows(states):
            if row.get("action"):
                ids.add(str(row.get("action")))
    for ec in data.get("error_codes") or []:
        if isinstance(ec, dict) and ec.get("code"):
            ids.add(str(ec["code"]))
    for key in data.get("defaults") or {}:
        ids.add(f"defaults.{key}")
        ids.add(str(key))
    for key in data.get("empty_states") or {}:
        ids.add(f"empty_states.{key}")
        ids.add(str(key))
    return ids


def claim_summary(data: dict) -> dict[str, list[dict]]:
    buckets: dict[str, list[dict]] = {k: [] for k in CLAIM_DISPOSITIONS}
    buckets["undisposed"] = []
    for claim in data.get("source_claims") or []:
        if not isinstance(claim, dict):
            continue
        disp = str(claim.get("disposition") or "").strip()
        if disp in buckets:
            buckets[disp].append(claim)
        else:
            buckets["undisposed"].append(claim)
    return buckets


def _resolve_source_path(raw: str, spec_path: Path | None) -> Path | None:
    p = Path(raw)
    if p.is_absolute():
        return p
    if spec_path is None:
        return None
    return (spec_path.parent / p).resolve()


def _covered_spec_refs(claims: list) -> set[str]:
    refs: set[str] = set()
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        if str(claim.get("disposition") or "").strip() != "covered":
            continue
        for ref in claim.get("spec_refs") or []:
            refs.add(str(ref))
    return refs


def _validate_source_layer(
    data: dict, fail: list[str], warn: list[str], spec_path: Path | None = None
) -> None:
    sources = data.get("sources") or []
    claims = data.get("source_claims") or []
    source_ids = _collect_ids(fail, sources if isinstance(sources, list) else [], "source")
    _collect_ids(fail, claims if isinstance(claims, list) else [], "source_claim")
    status = data.get("status")

    if status == "ready" and not claims:
        fail.append("source_claims missing — ready requires coverage evidence")

    for src in sources if isinstance(sources, list) else []:
        if not isinstance(src, dict):
            continue
        path = src.get("path")
        if path:
            resolved = _resolve_source_path(str(path), spec_path)
            if resolved is None:
                warn.append(f"source {src.get('id')}: path not verified (no spec file context)")
            elif not resolved.is_file():
                fail.append(f"source {src.get('id')}: path missing: {path}")
        st = src.get("status")
        if st and st not in {"registered", "superseded"}:
            fail.append(f"source {src.get('id')}: status must be registered|superseded")

    for claim in claims if isinstance(claims, list) else []:
        if not isinstance(claim, dict):
            continue
        cid = claim.get("id") or "?"
        disp = str(claim.get("disposition") or "").strip()
        if not disp:
            fail.append(f"source_claim {cid}: missing disposition")
            continue
        if disp not in CLAIM_DISPOSITIONS:
            fail.append(f"source_claim {cid}: invalid disposition {disp!r}")
            continue
        if not claim.get("quote_or_summary") and not claim.get("evidence"):
            fail.append(f"source_claim {cid}: need quote_or_summary or evidence")
        sref = claim.get("source_ref")
        if not sref:
            fail.append(f"source_claim {cid}: source_ref is required")
        elif str(sref) not in source_ids:
            fail.append(f"source_claim {cid}: source_ref missing: {sref}")
        refs = claim.get("spec_refs") or []
        allowed_refs = claim_spec_ref_ids(data)
        if disp == "covered":
            if not refs:
                fail.append(f"source_claim {cid}: covered but spec_refs is empty")
            for ref in refs:
                if str(ref) not in allowed_refs:
                    fail.append(f"source_claim {cid}: spec_ref not a spec entity: {ref}")
        if disp == "omitted" and status == "ready":
            fail.append(f"source_claim {cid}: omitted — unexplained gap blocks ready")
        if disp == "conflict":
            resolution = str(claim.get("resolution") or "").strip().lower()
            if resolution in OPEN_CONFLICT and status == "ready":
                fail.append(f"source_claim {cid}: conflict not closed (need resolution)")
        if disp == "pending" and status == "ready":
            fail.append(f"source_claim {cid}: pending disposition cannot stay on ready")
        if disp == "assumption":
            warn.append(f"source_claim {cid}: assumption — confirm with product owner")

    if status == "ready" and isinstance(claims, list) and claims:
        if not any(
            isinstance(c, dict) and str(c.get("disposition") or "").strip() == "covered"
            for c in claims
        ):
            fail.append("source_claims: ready requires at least one covered claim")
        covered = _covered_spec_refs(claims)
        for kind, items in (
            ("behavior", data.get("behaviors") or []),
            ("acceptance", data.get("acceptance") or []),
            ("control", (data.get("ui") or {}).get("controls") or []),
        ):
            for item in items if isinstance(items, list) else []:
                if not isinstance(item, dict) or not item.get("id"):
                    continue
                if item.get("coverage_optional") is True:
                    continue
                iid = str(item["id"])
                if iid not in covered:
                    fail.append(f"source_claim coverage missing for {kind} {iid}")


def _validate_human_stale(
    data: dict, human_path: Path, fail: list[str], warn: list[str]
) -> None:
    try:
        text = human_path.read_text(encoding="utf-8")
    except OSError as exc:
        fail.append(f"human spec unreadable: {human_path} ({exc})")
        return
    meta, body = split_human_markdown(text)
    expected = spec_hash(data)
    recorded = (meta.get("spec_hash") or "").replace("sha256:", "").strip()
    if not recorded:
        fail.append(f"human spec stale: {human_path.name} missing spec_hash — regenerate")
        return
    if recorded != expected:
        fail.append(
            f"human spec stale: hash {recorded[:12]}… != machine {expected[:12]}… — regenerate"
        )
    sid = meta.get("spec_id")
    if sid and sid != str(data.get("id")):
        fail.append(f"human spec id mismatch: {sid} != {data.get('id')}")
    recorded_rv = (meta.get("renderer_version") or "").strip()
    if recorded_rv != RENDERER_VERSION:
        # Renderer upgrades change body layout without changing meaning;
        # give a targeted message instead of a confusing body-hash mismatch.
        fail.append(
            f"human spec stale: renderer v{recorded_rv or '?'} != v{RENDERER_VERSION}"
            " — regenerate (spec content unchanged)"
        )
        return
    recorded_lang = (meta.get("lang") or "zh").strip() or "zh"
    expected_body = split_human_markdown(
        render_human(data, source=meta.get("generated_from") or str(human_path), lang=recorded_lang)
    )[1]
    if human_body_hash(body) != human_body_hash(expected_body):
        fail.append(f"human spec stale: body edited or not regenerated — {human_path.name}")


def _layer_schema(data: dict, fail: list[str]) -> None:
    """Layer 1 — JSON Schema (types, enums, required)."""
    if jsonschema is None:
        fail.append("schema: jsonschema not installed — cannot claim hard gate (pip install jsonschema)")
        for key in REQUIRED_TOP:
            if key not in data:
                fail.append(f"missing required field: {key}")
        status = data.get("status")
        if status is not None and status not in {"draft", "ready", "deprecated"}:
            fail.append(f"status invalid (schema): {status!r} — allowed: draft|ready|deprecated")
        return
    try:
        jsonschema.validate(instance=data, schema=load_schema())
    except jsonschema.ValidationError as exc:
        path = ".".join(str(p) for p in exc.absolute_path) or "(root)"
        fail.append(f"schema: {exc.message} at {path}")
    except Exception as exc:  # noqa: BLE001
        fail.append(f"schema validation error: {exc}")


def _layer_structure(data: dict, fail: list[str], warn: list[str]) -> list[dict]:
    """Layer 2 — ID uniqueness, cross-references, action matrix. Returns matrix rows."""
    behaviors = data.get("behaviors") or []
    acceptance = data.get("acceptance") or []
    if not isinstance(behaviors, list) or len(behaviors) < 1:
        fail.append("behaviors must have at least 1 item")
    if not isinstance(acceptance, list) or len(acceptance) < 1:
        fail.append("acceptance must have at least 1 item")

    actor_ids = _collect_ids(fail, data.get("actors") or [], "actor")
    behavior_ids = _collect_ids(fail, behaviors if isinstance(behaviors, list) else [], "behavior")
    _collect_ids(fail, acceptance if isinstance(acceptance, list) else [], "acceptance")
    _collect_ids(fail, (data.get("ui") or {}).get("controls") or [], "control")
    _collect_ids(fail, data.get("pending") or [], "pending")

    for p in data.get("permissions") or []:
        if not isinstance(p, dict):
            continue
        actor = p.get("actor")
        if actor and str(actor) not in actor_ids:
            fail.append(f"permission references missing actor: {actor}")

    for a in acceptance if isinstance(acceptance, list) else []:
        if not isinstance(a, dict):
            continue
        bid = a.get("behavior")
        if bid and str(bid) not in behavior_ids:
            fail.append(f"acceptance {a.get('id')}: behavior ref missing: {bid}")

    states = data.get("states") or {}
    lifecycle = set(states.get("lifecycle") or []) if isinstance(states, dict) else set()
    matrix = action_matrix_rows(states if isinstance(states, dict) else {})
    if isinstance(states, dict) and states.get("cancel_matrix") and not states.get("action_matrix"):
        warn.append("states.cancel_matrix is legacy — prefer states.action_matrix (state/action/allowed)")
    for row in matrix:
        st = row.get("state")
        if lifecycle and st and str(st) not in lifecycle:
            fail.append(f"action_matrix state not in lifecycle: {st}")
        if not row.get("action"):
            fail.append(f"action_matrix row for state={st} missing action")
    return matrix


def _layer_ready(data: dict, matrix: list[dict], fail: list[str]) -> None:
    """Layer 3 — dev-ready completeness. Placeholders do not count."""
    if data.get("status") != "ready":
        return
    behaviors = data.get("behaviors") or []
    acceptance = data.get("acceptance") or []
    pending = data.get("pending") or []
    if data.get("open_questions"):
        fail.append("status=ready but open_questions is not empty — move to pending with owner or resolve")
    if not data.get("actors"):
        fail.append("status=ready requires actors")
    if not [s for s in (data.get("in_scope") or []) if _lang(s, "zh") or _lang(s, "en")]:
        fail.append("status=ready requires non-empty in_scope")
    defaults = data.get("defaults") or {}
    real_defaults = [
        k
        for k in (defaults if isinstance(defaults, dict) else {})
        if str(k).strip() not in {"_", "-", "todo", "placeholder"}
        and not str(k).startswith("_")
    ]
    if not real_defaults:
        fail.append("status=ready requires defaults with at least one real key")
    ui = data.get("ui") if isinstance(data.get("ui"), dict) else {}
    wire = str((ui or {}).get("wireframe") or "").strip()
    real_controls = [
        c for c in ((ui or {}).get("controls") or []) if isinstance(c, dict) and c.get("id")
    ]
    if not ui:
        fail.append("status=ready requires ui (wireframe or non-empty controls)")
    elif not wire and not real_controls:
        fail.append("status=ready requires ui.wireframe or non-empty ui.controls")
    states_obj = data.get("states") if isinstance(data.get("states"), dict) else {}
    if not states_obj:
        fail.append("status=ready requires states (lifecycle / allowed actions)")
    elif not matrix:
        fail.append("status=ready requires states.action_matrix (lifecycle alone is not enough)")
    for b in behaviors if isinstance(behaviors, list) else []:
        if not isinstance(b, dict):
            continue
        bid = b.get("id")
        for field in ("given", "when", "then"):
            clause = (_lang(b.get(field), "zh") + " " + _lang(b.get(field), "en")).strip()
            if not clause:
                fail.append(f"behavior {bid}: {field} is empty")
            elif any(v in _strip_ui_literals(clause).lower() for v in VAGUE):
                fail.append(f"behavior {bid}: {field}-clause too vague for ready")
    for a in acceptance if isinstance(acceptance, list) else []:
        if not isinstance(a, dict):
            continue
        text = (_lang(a, "zh") + " " + _lang(a, "en")).strip()
        if not text:
            fail.append(f"acceptance {a.get('id')}: missing observable zh/en text")
        elif any(
            v in _strip_ui_literals(text).lower()
            for v in ("体验好", "功能正常", "good ux", "as fast")
        ):
            fail.append(f"acceptance {a.get('id')}: not observable")
    for p in pending if isinstance(pending, list) else []:
        if not _pending_ok(p):
            fail.append(
                "pending item missing required fields: id, missing, impact, owner, status"
            )
        elif str((p or {}).get("status", "")).strip().lower() in {"open", "待确认", "tbd"}:
            fail.append(
                f"pending {(p or {}).get('id')} still open — cannot mark status=ready"
            )
    for d in data.get("decisions") or []:
        if not isinstance(d, dict):
            continue
        undecided = str(d.get("status") or "").strip() == "pending" or (
            not d.get("chosen") and str(d.get("status") or "") != "decided"
        )
        if undecided:
            fail.append(
                f"decision {d.get('id')} undecided — decide it or move to pending with owner"
            )


def _layer_quality_warn(data: dict, warn: list[str]) -> None:
    """Layer 4 — quality debt that does not block PASS."""
    behaviors = data.get("behaviors") or []
    pending = data.get("pending") or []
    if data.get("status") == "ready" and not data.get("overview"):
        warn.append("overview missing — readers get no orientation before detail sections")
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
    if pending and data.get("status") != "ready":
        for p in pending:
            if not _pending_ok(p):
                warn.append("pending item should carry: id/missing/impact/owner/status")


def _layer_object_ai(data: dict, project: dict | None, fail: list[str]) -> None:
    weight = (project or {}).get("object_ai_weight", "medium")
    obj = data.get("object_ai") or {}
    if weight == "high":
        if not obj or not obj.get("enabled"):
            fail.append("object_ai_weight=high requires object_ai.enabled=true")
        else:
            for key in ("tools_boundary", "failure_fallback", "human_takeover_when"):
                if not obj.get(key):
                    fail.append(f"object_ai_weight=high requires object_ai.{key}")


def _layer_human(
    data: dict,
    spec_path: Path | None,
    human_path: Path | None,
    fail: list[str],
    warn: list[str],
) -> None:
    explicit_human = human_path is not None
    resolved_human = human_path if explicit_human else expected_human_path(spec_path)
    if resolved_human is not None and resolved_human.is_file():
        _validate_human_stale(data, resolved_human, fail, warn)
    elif resolved_human is not None and (explicit_human or data.get("status") == "ready"):
        fail.append(f"human spec missing: {resolved_human}")


def _layer_prototype(
    data: dict,
    spec_path: Path | None,
    manifest_path: Path | None,
    fail: list[str],
    warn: list[str],
) -> None:
    from .libproto import default_manifest_path, expected_manifest_path, load_and_validate_prototype  # noqa: PLC0415

    explicit_manifest = manifest_path is not None
    resolved_manifest = manifest_path if explicit_manifest else default_manifest_path(spec_path)
    if resolved_manifest is not None and resolved_manifest.is_file():
        proto = load_and_validate_prototype(data, resolved_manifest)
        fail.extend(proto["fail"])
        warn.extend(proto["warn"])
    elif explicit_manifest and resolved_manifest is not None and not resolved_manifest.is_file():
        fail.append(f"prototype manifest missing: {resolved_manifest}")
    elif (
        not explicit_manifest
        and spec_path is not None
        and data.get("status") == "ready"
        and expected_manifest_path(spec_path) is not None
        and not expected_manifest_path(spec_path).is_file()
    ):
        warn.append("prototype manifest not found — prototype consistency skipped")


def validate(
    data: Any,
    project: dict | None = None,
    *,
    spec_path: Path | None = None,
    human_path: Path | None = None,
    manifest_path: Path | None = None,
    check_human: bool = True,
) -> dict[str, list[str]]:
    """Return {fail, warn}. Pipeline: schema → structure → ready → warn →
    object-AI → source coverage → human staleness → prototype consistency."""
    fail: list[str] = []
    warn: list[str] = []
    if not isinstance(data, dict):
        return {"fail": ["root must be an object"], "warn": []}

    _layer_schema(data, fail)
    matrix = _layer_structure(data, fail, warn)
    for tok in dangling_refs(data):
        msg = f"dangling reference: {tok} mentioned in text but not declared"
        if data.get("status") == "ready":
            fail.append(msg)
        else:
            warn.append(msg)
    _layer_ready(data, matrix, fail)
    _layer_quality_warn(data, warn)
    _layer_object_ai(data, project, fail)
    _validate_source_layer(data, fail, warn, spec_path=spec_path)
    if check_human:
        _layer_human(data, spec_path, human_path, fail, warn)
    _layer_prototype(data, spec_path, manifest_path, fail, warn)

    return {"fail": fail, "warn": warn}


def ready_gap(
    data: dict,
    project: dict | None = None,
    *,
    spec_path: Path | None = None,
    human_path: Path | None = None,
    manifest_path: Path | None = None,
) -> list[str]:
    """What extra FAILs would appear if status were flipped to ready right now.

    Deterministic dry-run for drafts: answers 「距 ready 还差什么」without
    forcing authors to flip the flag and read a wall of FAILs.
    """
    if not isinstance(data, dict) or data.get("status") == "ready":
        return []
    current = validate(
        data, project, spec_path=spec_path, human_path=human_path, manifest_path=manifest_path
    )
    simulated_data = json.loads(json.dumps(data, ensure_ascii=False, default=str))
    simulated_data["status"] = "ready"
    simulated = validate(
        simulated_data,
        project,
        spec_path=spec_path,
        human_path=human_path,
        manifest_path=manifest_path,
    )
    seen = set(current["fail"])
    gap: list[str] = []
    regen_noted = False
    for e in simulated["fail"]:
        if e in seen:
            continue
        # Flipping status changes spec_hash, so hash-stale entries are a given;
        # collapse them into one actionable line instead of noise.
        if "stale: hash" in e or "renderer v" in e:
            if not regen_noted:
                gap.append("regenerate human/prototype after flipping status (hash will change)")
                regen_noted = True
            continue
        gap.append(e)
    return gap


def _anchor(title: str) -> str:
    """Markdown heading anchor (GitHub-style: lowercase, punctuation dropped, CJK kept)."""
    t = re.sub(r"[^\w\- ]", "", title.strip().lower(), flags=re.UNICODE)
    return t.replace(" ", "-")


def _mermaid_label(text: str) -> str:
    return str(text).replace('"', "'").replace("\n", " ").strip()


def mermaid_lifecycle(states: dict) -> str | None:
    """Deterministic lifecycle-order diagram from states.lifecycle."""
    chain = [str(s) for s in (states.get("lifecycle") or []) if s]
    if len(chain) < 2:
        return None
    nodes = " --> ".join(f'S{i}["{_mermaid_label(s)}"]' for i, s in enumerate(chain))
    return "flowchart LR\n  " + nodes


def mermaid_main_path(behaviors: list, lang: str = "zh") -> str | None:
    """Deterministic step-chain diagram from behaviors order."""
    steps = []
    for b in behaviors or []:
        if not isinstance(b, dict):
            continue
        sid = b.get("step_id") or b.get("id")
        name = _lang(b.get("name"), lang) or str(b.get("id") or "")
        steps.append(f"{sid}. {name}".strip())
    if len(steps) < 2:
        return None
    nodes = " --> ".join(f'B{i}["{_mermaid_label(s)}"]' for i, s in enumerate(steps))
    return "flowchart TD\n  " + nodes


def render_human(data: dict, source: str, gate_mode: str = "hard", lang: str = "zh") -> str:
    """Render 可开发的需求规格说明书 (human view) from machine source.

    Reading arc (v3): orient first — overview, scope, architecture,
    responsibilities, data contracts — then zoom into rules, interactions and
    evidence. Sections render only when the machine source holds them, and
    numbering is assigned after selection so the arc stays contiguous.
    Every diagram is either stored in or derived from the machine source;
    nothing here is authored at render time. `lang` swaps chrome strings and
    field-language preference; zh output is byte-stable.
    """
    t = _tt(lang)
    title_zh = _lang(data.get("title"), "zh")
    title_en = _lang(data.get("title"), "en")
    title_main = title_en if lang == "en" and title_en else title_zh
    title_alt = title_zh if lang == "en" else title_en
    ui = data.get("ui") or {}
    states = data.get("states") or {}
    behaviors = data.get("behaviors") or []
    acceptance = data.get("acceptance") or []
    digest = spec_hash(data)
    sections: list[tuple[str, list[str]]] = []

    # ---- 概览（作者在机读里写的全局视角；渲染器只摆放） ----
    overview = data.get("overview") or {}
    if overview:
        sec: list[str] = []
        summary = _lang(overview.get("summary"), lang)
        if summary:
            sec += [summary, ""]
        principles = overview.get("design_principles") or []
        if principles:
            sec += [t("**设计原则：**"), ""]
            for i, p in enumerate(principles, 1):
                sec.append(f"{i}. {_lang(p, lang)}")
            sec.append("")
        constraints = overview.get("environment_constraints") or []
        if constraints:
            sec += [t("**环境与约束：**"), ""]
            for c in constraints:
                sec.append(f"- {_lang(c, lang)}")
            sec.append("")
        sections.append(("概览", sec))

    # ---- 范围 ----
    sec = [t("**本期做：**"), ""]
    for item in data.get("in_scope") or []:
        sec.append(f"- {_lang(item, lang)}")
    sec += ["", t("**本期不做（白名单外，不展开）：**"), ""]
    for item in data.get("out_of_scope") or []:
        sec.append(f"- {_lang(item, lang)}")
    if data.get("baseline"):
        sec += ["", t("**对照基线：** {baseline}").format(baseline=_lang(data.get("baseline"), lang))]
    sec.append("")
    sections.append(("范围", sec))

    # ---- 架构总览（机读持有 mermaid 源码） ----
    arch = data.get("architecture") or {}
    if arch.get("mermaid"):
        sec = []
        note = _lang(arch.get("note"), lang)
        if note:
            sec += [note, ""]
        sec += ["```mermaid", str(arch["mermaid"]).rstrip(), "```", ""]
        sections.append(("架构总览", sec))

    # ---- 职责边界 ----
    resp = [r for r in (data.get("responsibilities") or []) if isinstance(r, dict)]
    if resp:
        sec = [t("谁负责什么、明确不负责什么，开工前先对齐边界。"), ""]
        for r in resp:
            zh = _lang(r, lang)
            sec.append(f"### {r.get('role')}" + (f" · {zh}" if zh else ""))
            sec.append("")
            owns = r.get("owns") or []
            nots = r.get("not_owns") or []
            sec += [t("| 负责 | 不负责 |"), "|------|--------|"]
            for i in range(max(len(owns), len(nots), 1)):
                left = _lang(owns[i], lang) if i < len(owns) else ""
                right = _lang(nots[i], lang) if i < len(nots) else ""
                sec.append(f"| {left or '—'} | {right or '—'} |")
            sec.append("")
        sections.append(("职责边界", sec))

    # ---- 数据契约 ----
    contracts = [c for c in (data.get("data_contracts") or []) if isinstance(c, dict)]
    if contracts:
        sec = [t("共 {n} 个数据实体；字段即前后端接口与存储的对齐口径。").format(n=len(contracts)), ""]
        for dc in contracts:
            zh = _lang(dc, lang)
            sec.append(f"### {dc.get('id')}" + (f" · {zh}" if zh else ""))
            sec.append("")
            fields = [f for f in (dc.get("fields") or []) if isinstance(f, dict)]
            if fields:
                sec += [t("| 字段 | 中文 | 类型 | 说明 |"), "|------|------|------|------|"]
                for f in fields:
                    sec.append(
                        f"| `{f.get('name')}` | {f.get('zh') or '—'} | `{f.get('type') or '—'}` | {_lang(f.get('desc'), lang) or '—'} |"
                    )
                sec.append("")
            if dc.get("example_json"):
                sec += ["```json", str(dc["example_json"]).rstrip(), "```", ""]
            rules = dc.get("rules") or []
            if rules:
                sec.append(t("**规则：**"))
                sec.append("")
                for rule in rules:
                    sec.append(f"- {_lang(rule, lang)}")
                sec.append("")
        sections.append(("数据契约", sec))

    # ---- 角色与权限 ----
    actors = data.get("actors") or []
    sec = [t("{n} 类角色；可执行动作与状态矩阵联动。").format(n=len(actors)), ""]
    sec += [t("| 角色 | 说明 | 可执行动作 |"), "|------|------|------------|"]
    perm_map = {(p or {}).get("actor"): (p or {}).get("can") or [] for p in (data.get("permissions") or [])}
    for a in actors:
        aid = (a or {}).get("id")
        cans = ", ".join(perm_map.get(aid) or [])
        sec.append(f"| `{aid}` | {_lang(a, lang)} | {cans or '—'} |")
    sec.append("")
    sections.append(("角色与权限", sec))

    # ---- 状态与允许动作 ----
    matrix = action_matrix_rows(states)
    lifecycle = states.get("lifecycle") or []
    denied = sum(1 for r in matrix if r.get("allowed") is False)
    action_kinds = len({str(r.get("action")) for r in matrix if r.get("action")})
    sec = []
    if matrix:
        sec += [
            t("{s} 个状态 × {a} 类动作，其中明确禁止 {d} 项。前端显隐与置灰以下表为唯一准据。").format(
                s=len(lifecycle), a=action_kinds, d=denied
            ),
            "",
        ]
    life_mermaid = mermaid_lifecycle(states)
    if life_mermaid:
        sec += [t("生命周期顺序（示意）："), "", "```mermaid", life_mermaid, "```", ""]
    if lifecycle:
        sec.append(t("**生命周期（编号供流程对照）：**"))
        for i, s in enumerate(lifecycle, 1):
            sec.append(f"{i}. `{s}`")
        sec.append("")
    sec += [t("| 状态 | 动作 | 是否允许 | 说明 |"), "|------|------|----------|------|"]
    for row in matrix:
        sec.append(
            f"| `{(row or {}).get('state')}` | `{(row or {}).get('action')}` | {_allowed_label(row, lang)} | {_lang(row, lang)} |"
        )
    if not matrix:
        sec.append(t("| （机读未提供 action_matrix） | — | — | — |"))
    sec.append("")
    sections.append(("状态与允许动作", sec))

    # ---- 页面与交互 ----
    sec = []
    if ui.get("entry"):
        sec += [t("**入口：** {entry}").format(entry=_lang(ui.get("entry"), lang)), ""]
    if ui.get("wireframe"):
        sec += [t("### 线框"), "", "```text", str(ui.get("wireframe")).rstrip(), "```", ""]
    controls = ui.get("controls") or []
    if controls:
        with_fail = sum(
            1 for c in controls if isinstance(c, dict) and _lang(c.get("fail_feedback"), lang) not in ("", "—")
        )
        sec += [
            t("### 控件规格"),
            "",
            t("共 {n} 个控件，其中 {f} 个定义了失败反馈文案。").format(n=len(controls), f=with_fail),
            "",
            t("| 控件 | 文案/占位 | 显示条件 | 交互 | 失败反馈 |"),
            "|------|-----------|----------|------|----------|",
        ]
        for c in controls:
            sec.append(
                "| {name} | {label} | {when} | {action} | {fail} |".format(
                    name=(c or {}).get("id", ""),
                    label=_lang(c, lang),
                    when=_lang((c or {}).get("visible_when"), lang) or "—",
                    action=_lang((c or {}).get("action"), lang) or "—",
                    fail=_lang((c or {}).get("fail_feedback"), lang) or "—",
                )
            )
        sec.append("")
    sections.append(("页面与交互", sec))

    # ---- 主路径（编号） ----
    sec = [t("共 {n} 步；每步的 Given/When/Then 同时是测试的验收输入。").format(n=len(behaviors)), ""]
    path_mermaid = mermaid_main_path(behaviors, lang)
    if path_mermaid:
        sec += ["```mermaid", path_mermaid, "```", ""]
    for b in behaviors:
        step = (b or {}).get("step_id") or (b or {}).get("id")
        sec += [
            t("### 步骤 {step} · {name}").format(step=step, name=_lang((b or {}).get("name"), lang)),
            "",
            t("- **Given：** {v}").format(v=_lang((b or {}).get("given"), lang)),
            t("- **When：** {v}").format(v=_lang((b or {}).get("when"), lang)),
            t("- **Then：** {v}").format(v=_lang((b or {}).get("then"), lang)),
        ]
        if (b or {}).get("side_effects"):
            sec.append(t("- **连带结果：**"))
            for s in (b or {}).get("side_effects") or []:
                sec.append(f"  - {_lang(s, lang)}")
        sec.append("")
    sections.append(("主路径（编号）", sec))

    # ---- 默认值与提示文案 ----
    sec = [t("### 默认值"), ""]
    defaults = data.get("defaults") or {}
    if defaults:
        sec += [t("| 项 | 值 |"), "|----|----|"]
        for k, v in defaults.items():
            sec.append(f"| `{k}` | `{v}` |")
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
            t("开发按码实现分支，测试按码构造用例，客服按文案答复——一张表三方共用。"),
            "",
            t("| 错误码 | 含义 | 触发场景 | 可重试 | 用户文案 |"),
            "|--------|------|----------|--------|----------|",
        ]
        for e in error_codes:
            retry = t("是") if e.get("retryable") else t("否")
            sec.append(
                f"| `{e.get('code')}` | {e.get('zh') or '—'} | {_lang(e.get('trigger'), lang) or '—'} | {retry} | {_lang(e.get('user_copy'), lang) or '—'} |"
            )
        sec.append("")
        sections.append(("错误码", sec))

    # ---- 验收标准（AC） ----
    sec = [t("共 {n} 条；逐条可执行，不可观察的表述会被门禁否决。").format(n=len(acceptance)), ""]
    for a in acceptance:
        sec.append(
            t("- **{aid}**（行为 `{bid}`）：{text}").format(
                aid=(a or {}).get("id"), bid=(a or {}).get("behavior"), text=_lang(a, lang)
            )
        )
    sec.append("")
    sections.append(("验收标准（AC）", sec))

    # ---- Pending ----
    sec = []
    pending = data.get("pending") or []
    if not pending:
        sec.append(t("无。"))
    else:
        sec += [t("| ID | 缺失信息 | 影响范围 | 责任人 | 状态 |"), "|----|----------|----------|--------|------|"]
        for p in pending:
            sec.append(
                f"| {(p or {}).get('id')} | {(p or {}).get('missing')} | {(p or {}).get('impact')} | {(p or {}).get('owner')} | {(p or {}).get('status')} |"
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
            sec.append(
                f"| {d.get('id')} | {_lang(d.get('question'), lang)} | {chosen} | {d.get('date') or '—'} | {_lang(d.get('note'), lang) or '—'} |"
            )
        sec.append("")
        sections.append(("决策记录", sec))

    # ---- 对象 AI ----
    obj = data.get("object_ai") or {}
    sec = [f"- enabled: `{obj.get('enabled', False)}`"]
    if obj.get("enabled"):
        sec.append(t("- 失败兜底: {v}").format(v=_lang(obj.get("failure_fallback"), lang)))
        sec.append(t("- 工具边界:"))
        for item in obj.get("tools_boundary") or []:
            sec.append(f"  - {_lang(item, lang)}")
        sec.append(t("- 人工接管:"))
        for item in obj.get("human_takeover_when") or []:
            sec.append(f"  - {_lang(item, lang)}")
    sec.append("")
    sections.append(("对象 AI", sec))

    # ---- 原料覆盖（附录） ----
    claims = data.get("source_claims") or []
    if claims:
        buckets = claim_summary(data)
        sec = [
            t("覆盖账本（附录）：原料每句话的下落。covered {c} · assumption {a} · out_of_scope {o} · 其他 {r}。").format(
                c=len(buckets.get("covered") or []),
                a=len(buckets.get("assumption") or []),
                o=len(buckets.get("out_of_scope") or []),
                r=len(claims)
                - len(buckets.get("covered") or [])
                - len(buckets.get("assumption") or [])
                - len(buckets.get("out_of_scope") or []),
            ),
            "",
            t("| ID | 处置 | 摘要 | 规格引用 |"),
            "|----|------|------|----------|",
        ]
        for c in claims:
            if not isinstance(c, dict):
                continue
            refs = ", ".join(f"`{r}`" for r in (c.get("spec_refs") or [])) or "—"
            sec.append(
                f"| `{c.get('id')}` | `{c.get('disposition')}` | {c.get('quote_or_summary') or c.get('evidence') or '—'} | {refs} |"
            )
        sec.append("")
        sections.append(("原料覆盖（SourceClaim）", sec))

    # ---- 组装：标题块 → 目录 → 编号章节 ----
    numbered = [(f"{i}. {t(title)}", body) for i, (title, body) in enumerate(sections, 1)]
    lines: list[str] = [
        f"# {title_main}",
        "",
        t("> **文档类型**：可开发的需求规格说明书（人读视图）  "),
        t("> **规格 ID**：`{sid}` · **状态**：`{status}` · **版本**：`{ver}`  ").format(
            sid=data.get("id"), status=data.get("status"), ver=data.get("spec_version")
        ),
        t("> **机读哈希**：`{digest}…`").format(digest=digest[:16]),
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
    headers = [
        f"<!-- generated_from: {source} -->",
        f"<!-- spec_id: {data.get('id')} -->",
        f"<!-- spec_version: {data.get('spec_version')} -->",
        f"<!-- spec_hash: {digest} -->",
        f"<!-- body_hash: {human_body_hash(body_text)} -->",
        f"<!-- renderer_version: {RENDERER_VERSION} -->",
        f"<!-- lang: {lang} -->",
        f"<!-- gate_mode: {gate_mode} -->",
        t("<!-- 以机读 YAML 为唯一准据；禁止长期只改本文件 -->"),
        "",
    ]
    return "\n".join(headers) + body_text


def load_project(root: Path) -> dict:
    """Load only project.yaml. Never auto-load project.example.yaml."""
    p = root / "project.yaml"
    if p.exists() and yaml is not None:
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        if isinstance(data, dict):
            return data
    return {}


def find_repo_root(start: Path) -> Path:
    """Walk up from a spec file to the enclosing repo/project root."""
    cur = start.resolve()
    if cur.is_file():
        cur = cur.parent
    for candidate in (cur, *cur.parents):
        if (candidate / ".git").exists() or (candidate / "project.yaml").is_file():
            return candidate
    return cur


def load_project_for(spec_path: Path) -> dict:
    """Load project.yaml from the spec file's own repo, not the tool's."""
    return load_project(find_repo_root(spec_path))
