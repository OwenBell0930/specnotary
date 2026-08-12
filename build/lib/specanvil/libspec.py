#!/usr/bin/env python3
"""Spec Kit shared load / validate (FAIL|WARN|Pending) / render human spec."""
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
VAGUE = ("体验好", "尽量快", "智能", "方便地", "good ux", "quickly", "尽快", "尽量")
RENDERER_VERSION = "2"
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


def _pending_ok(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    return all(item.get(k) not in (None, "") for k in ("id", "missing", "impact", "owner", "status"))


def _allowed_label(row: dict) -> str:
    if "allowed" in row:
        val = row.get("allowed")
        if isinstance(val, bool):
            return "允许" if val else "禁止"
        return str(val)
    if "buyer_self_cancel" in row:  # legacy cancel_matrix
        return str(row.get("buyer_self_cancel"))
    return "—"


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
    expected_body = split_human_markdown(render_human(data, source=meta.get("generated_from") or str(human_path)))[1]
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
            elif any(v in clause.lower() for v in VAGUE):
                fail.append(f"behavior {bid}: {field}-clause too vague for ready")
    for a in acceptance if isinstance(acceptance, list) else []:
        if not isinstance(a, dict):
            continue
        text = (_lang(a, "zh") + " " + _lang(a, "en")).strip()
        if not text:
            fail.append(f"acceptance {a.get('id')}: missing observable zh/en text")
        elif any(v in text.lower() for v in ("体验好", "功能正常", "good ux", "as fast")):
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


def _layer_quality_warn(data: dict, warn: list[str]) -> None:
    """Layer 4 — quality debt that does not block PASS."""
    behaviors = data.get("behaviors") or []
    pending = data.get("pending") or []
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


def render_human(data: dict, source: str, gate_mode: str = "hard") -> str:
    """Render 可开发的需求规格说明书 (human view) from machine source."""
    title_zh = _lang(data.get("title"), "zh")
    title_en = _lang(data.get("title"), "en")
    ui = data.get("ui") or {}
    states = data.get("states") or {}
    digest = spec_hash(data)
    lines: list[str] = [
        f"# {title_zh}",
        "",
        f"> **文档类型**：可开发的需求规格说明书（人读视图）  ",
        f"> **规格 ID**：`{data.get('id')}` · **状态**：`{data.get('status')}` · **版本**：`{data.get('spec_version')}`  ",
        f"> **机读哈希**：`{digest[:16]}…`",
        "",
    ]
    if title_en and title_en != title_zh:
        lines += [f"**EN title:** {title_en}", ""]

    lines += ["## 1. 范围", "", "### 1.1 本期做", ""]
    for item in data.get("in_scope") or []:
        lines.append(f"- {_lang(item, 'zh')}")
    lines += ["", "### 1.2 本期不做（白名单外，不展开）", ""]
    for item in data.get("out_of_scope") or []:
        lines.append(f"- {_lang(item, 'zh')}")
    if data.get("baseline"):
        lines += ["", f"**对照基线：** {_lang(data.get('baseline'), 'zh')}", ""]

    lines += ["## 2. 角色与权限", "", "| 角色 | 说明 | 可执行动作 |", "|------|------|------------|"]
    perm_map = {(p or {}).get("actor"): (p or {}).get("can") or [] for p in (data.get("permissions") or [])}
    for a in data.get("actors") or []:
        aid = (a or {}).get("id")
        cans = ", ".join(perm_map.get(aid) or [])
        lines.append(f"| `{aid}` | {_lang(a, 'zh')} | {cans or '—'} |")
    lines.append("")

    lines += ["## 3. 状态与允许动作", ""]
    if states.get("lifecycle"):
        lines.append("**生命周期（编号供流程对照）：**")
        for i, s in enumerate(states.get("lifecycle") or [], 1):
            lines.append(f"{i}. `{s}`")
        lines.append("")
    lines += [
        "| 状态 | 动作 | 是否允许 | 说明 |",
        "|------|------|----------|------|",
    ]
    matrix = action_matrix_rows(states)
    for row in matrix:
        lines.append(
            f"| `{(row or {}).get('state')}` | `{(row or {}).get('action')}` | {_allowed_label(row)} | {_lang(row, 'zh')} |"
        )
    if not matrix:
        lines.append("| （机读未提供 action_matrix） | — | — | — |")
    lines.append("")

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

    lines += ["## 7. 验收标准（AC）", ""]
    for a in data.get("acceptance") or []:
        lines.append(
            f"- **{(a or {}).get('id')}**（行为 `{(a or {}).get('behavior')}`）：{_lang(a, 'zh')}"
        )
    lines.append("")

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

    claims = data.get("source_claims") or []
    if claims:
        lines += ["## 10. 原料覆盖（SourceClaim）", ""]
        lines.append("| ID | 处置 | 摘要 | 规格引用 |")
        lines.append("|----|------|------|----------|")
        for c in claims:
            if not isinstance(c, dict):
                continue
            refs = ", ".join(f"`{r}`" for r in (c.get("spec_refs") or [])) or "—"
            lines.append(
                f"| `{c.get('id')}` | `{c.get('disposition')}` | {c.get('quote_or_summary') or c.get('evidence') or '—'} | {refs} |"
            )
        lines.append("")
    body = "\n".join(lines)
    if not body.endswith("\n"):
        body += "\n"
    headers = [
        f"<!-- generated_from: {source} -->",
        f"<!-- spec_id: {data.get('id')} -->",
        f"<!-- spec_version: {data.get('spec_version')} -->",
        f"<!-- spec_hash: {digest} -->",
        f"<!-- body_hash: {human_body_hash(body)} -->",
        f"<!-- renderer_version: {RENDERER_VERSION} -->",
        f"<!-- gate_mode: {gate_mode} -->",
        "<!-- 以机读 YAML 为唯一准据；禁止长期只改本文件 -->",
        "",
    ]
    return "\n".join(headers) + body


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
