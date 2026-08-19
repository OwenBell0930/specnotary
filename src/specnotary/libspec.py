#!/usr/bin/env python3
"""SpecNotary rule pipeline: FAIL | WARN | Pending.

Disk I/O lives in spec_io.py; the human view lives in spec_render.py.
This module is the deterministic gate — schema, structure, evidence, prototype.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None

from .spec_io import (  # noqa: F401 — re-exported public API
    SCHEMA_PATH,
    DuplicateKeyError,
    default_human_path,
    dump_spec,
    expected_human_path,
    file_sha256,
    find_repo_root,
    human_body_hash,
    load_project,
    load_project_for,
    load_schema,
    load_spec,
    parse_human_header,
    relpath_from_root,
    spec_hash,
    split_human_markdown,
)
from .spec_render import RENDERER_VERSION, mermaid_lifecycle, render_human  # noqa: F401

REQUIRED_TOP = ["spec_version", "id", "title", "status", "behaviors", "acceptance"]
# Scaffold residue. CJK markers are matched with a negative lookahead so
# 「待补充材料」 is not killed as the template token 「待补」.
_PLACEHOLDER_CJK = ("占位", "示例内容", "lorem ipsum")
_PLACEHOLDER_TOKEN = re.compile(r"(?<![a-z0-9_])(todo|tbd|placeholder|xxx)(?![a-z0-9_])")
VAGUE = (
    "体验好",
    "尽量快",
    "智能化",
    "智能搜索",
    "智能推荐",
    "足够智能",
    "智能地",
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
    "形成闭环",
    "业务闭环",
    "管理闭环",
    "治理体系",
    "完善治理",
    "赋能",
    "抓手",
    "拉通",
)
# Known empty-talk phrases — not a general observability oracle.
UNOBSERVABLE_AC = (
    "体验好",
    "功能正常",
    "功能符合预期",
    "界面足够美观",
    "good ux",
    "as fast",
    "works correctly",
    "the feature works",
    "users are satisfied",
    "形成闭环",
    "治理体系",
    "完善治理",
    "赋能",
    "抓手",
)
CLAIM_DISPOSITIONS = {
    "covered",
    "omitted",
    "assumption",
    "conflict",
    "out_of_scope",
    "pending",
}
OPEN_CONFLICT = {"", "open", "unresolved", "待确认", "tbd"}



def _lang(node: Any, lang: str = "zh") -> str:
    if isinstance(node, dict):
        if lang in node and node[lang]:
            return str(node[lang])
        if "zh" in node:
            return str(node["zh"])
        if "en" in node:
            return str(node["en"])
        # An empty/shape-only mapping carries no text; stringifying it would
        # yield a literal "{}" that later emptiness checks would accept.
        return "" if not node else str(node)
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


def _is_placeholder(text: str) -> bool:
    """Scaffold text that survived into a ready spec.

    Scanned on the raw string, deliberately: the vague-wording rule exempts
    「…」 spans so a real button named 「智能识别」 passes, but the template
    writes its filler as 「占位」…, so sharing that exemption let every
    template-derived shell through. Placeholder markers are scaffold residue,
    never UI copy. 「待补」 is a template token; 「待补充」 is a real status.
    """
    raw = text.strip().lower()
    if any(marker in raw for marker in _PLACEHOLDER_CJK):
        return True
    if re.search(r"待补(?!充)", raw):
        return True
    return bool(_PLACEHOLDER_TOKEN.search(raw))


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
            fail.append(f"{kind} item must be an object, got {type(item).__name__}")
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



def warning_id(msg: str) -> str:
    """Stable id for a WARN so it can be accepted without matching the full sentence."""
    m = re.match(r"source_claim (\S+): assumption\b", msg)
    if m:
        return f"assumption:{m.group(1)}"
    m = re.match(r"permission (\S+): can=(\S+) is not an action", msg)
    if m:
        return f"permission:{m.group(1)}:{m.group(2)}"
    m = re.match(r"behavior (\S+): prefer step_id", msg)
    if m:
        return f"step_id:{m.group(1)}"
    m = re.match(r"unknown top-level field ['\"]?([^'\"]+)['\"]?", msg)
    if m:
        return f"unknown:{m.group(1)}"
    m = re.match(r"dangling reference: (\S+)", msg)
    if m:
        return f"dangling:{m.group(1)}"
    m = re.match(r"source (\S+): no path\b", msg)
    if m:
        return f"source-path:{m.group(1)}"
    m = re.match(r"source (\S+): no content_hash\b", msg)
    if m:
        return f"source-hash:{m.group(1)}"
    if msg.startswith("prototype manifest not found"):
        return "prototype:skipped"
    if msg.startswith("overview missing"):
        return "overview:missing"
    if msg.startswith("empty_states missing"):
        return "empty_states:missing"
    if msg.startswith("ui block missing"):
        return "ui:missing"
    if msg.startswith("states block missing"):
        return "states:missing"
    if "cancel_matrix is legacy" in msg:
        return "legacy:cancel_matrix"
    if msg.startswith("pending item should carry"):
        return "pending:fields"
    return "warn:" + hashlib.sha256(msg.encode("utf-8")).hexdigest()[:12]


def _accepted_ok(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    return all(str(item.get(k) or "").strip() for k in ("id", "by", "date", "reason"))


def _apply_accepted_warnings(data: dict, fail: list[str], warn: list[str]) -> list[str]:
    """Drop WARNs that have a complete acceptance record; flag stale records.

    Returns the ids of WARNs that remain (unaccepted).
    """
    records = data.get("accepted_warnings") or []
    if not isinstance(records, list):
        records = []
    accepted: dict[str, dict] = {}
    for item in records:
        if not isinstance(item, dict):
            fail.append("accepted_warnings item must be an object")
            continue
        if not _accepted_ok(item):
            msg = (
                f"accepted_warnings {item.get('id') or '?'}: need id, by, date, reason"
            )
            if data.get("status") == "ready":
                fail.append(msg)
            else:
                warn.append(msg)
            continue
        accepted[str(item["id"]).strip()] = item

    remaining: list[str] = []
    remaining_ids: list[str] = []
    current_ids: set[str] = set()
    for msg in warn:
        code = warning_id(msg)
        current_ids.add(code)
        if code in accepted:
            continue
        remaining.append(msg)
        remaining_ids.append(code)
    warn[:] = remaining
    for code, rec in accepted.items():
        if code not in current_ids:
            msg = (
                f"accepted_warnings {code} no longer applies — remove it "
                f"(accepted by {rec.get('by')} on {rec.get('date')})"
            )
            if data.get("status") == "ready":
                fail.append(msg)
            else:
                warn.append(msg)
                remaining_ids.append(warning_id(msg))
    return remaining_ids


# Evidence locators look like "ops-note.zh.txt:L2" / "cs-faq.zh.txt:Q3".
# Free-form evidence (e.g. 推导) is left alone — only file-shaped ones are matched.
_EVIDENCE_FILE = re.compile(r"^([\w.\-]+\.[A-Za-z0-9]+)\s*[:：]")


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
        if not path:
            # Evidence monotonicity: deleting the file pointer must not be
            # easier than submitting a file whose hash does not match.
            if status == "ready":
                fail.append(
                    f"source {src.get('id')}: missing path — ready requires every source "
                    "to be a real file with a content snapshot (removing path cannot pass the gate)"
                )
            else:
                warn.append(
                    f"source {src.get('id')}: no path — claims are not pinned to a file"
                )
            continue
        resolved = _resolve_source_path(str(path), spec_path)
        if resolved is None:
            warn.append(f"source {src.get('id')}: path not verified (no spec file context)")
        elif not resolved.is_file():
            fail.append(f"source {src.get('id')}: path missing: {path}")
        else:
            # Claims are only as trustworthy as the material they cite.
            # Pinning the source content hash turns "原料没漏" from pure
            # self-report into a snapshot claim: touch the source file and
            # every claim on it goes stale until re-reviewed.
            recorded = str(src.get("content_hash") or "").replace("sha256:", "").strip()
            if recorded:
                actual = file_sha256(resolved)
                if recorded != actual:
                    fail.append(
                        f"source {src.get('id')}: content changed since claims were written "
                        f"({recorded[:12]}… != {actual[:12]}…) — re-review claims and update content_hash"
                    )
            elif status == "ready":
                # PASS is defined as "claims rest on an unchanged source
                # snapshot" (docs/proof-boundary.md). An unpinned source on a
                # ready spec would make that definition false, so it must
                # block rather than warn.
                fail.append(
                    f"source {src.get('id')}: no content_hash — ready requires claims pinned to a "
                    f"source snapshot (sha256 of {Path(str(path)).name})"
                )
            else:
                warn.append(
                    f"source {src.get('id')}: no content_hash — claims not pinned to source content"
                )
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
        else:
            # content_hash proves "that file did not change"; it cannot prove
            # "path still points at the same file". Cross-checking the evidence
            # locator against the source filename closes the swap: repointing a
            # source at a different file leaves every evidence string stranded.
            evidence = str(claim.get("evidence") or "")
            src_obj = next(
                (s for s in (sources if isinstance(sources, list) else []) if isinstance(s, dict) and str(s.get("id")) == str(sref)),
                None,
            )
            src_name = Path(str((src_obj or {}).get("path") or "")).name
            if evidence and src_name and _EVIDENCE_FILE.match(evidence):
                cited = _EVIDENCE_FILE.match(evidence).group(1)
                if cited != src_name:
                    fail.append(
                        f"source_claim {cid}: evidence cites {cited} but {sref} points at {src_name} "
                        "— source was repointed or evidence is stale"
                    )
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


def _read_human_text(human_path: Path, fail: list[str]) -> str | None:
    try:
        return human_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        fail.append(f"human spec not utf-8: {human_path.name}")
        return None
    except OSError as exc:
        fail.append(f"human spec unreadable: {human_path} ({exc})")
        return None


def _validate_human_stale(
    data: dict, human_path: Path, fail: list[str], warn: list[str]
) -> None:
    text = _read_human_text(human_path, fail)
    if text is None:
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
    actual_hash = human_body_hash(body)
    if actual_hash != human_body_hash(expected_body):
        fail.append(f"human spec stale: body edited or not regenerated — {human_path.name}")
    recorded_body_hash = (meta.get("body_hash") or "").replace("sha256:", "").strip()
    if recorded_body_hash and recorded_body_hash != actual_hash:
        fail.append(
            f"human spec header body_hash does not match the body — {human_path.name}"
        )
    recorded_mode = (meta.get("gate_mode") or "").strip()
    forced = (meta.get("forced") or "").strip()
    if recorded_mode:
        if forced and recorded_mode != "degraded":
            fail.append(
                f"human spec header gate_mode={recorded_mode} with forced must be degraded"
            )
        elif not forced and recorded_mode != "hard":
            fail.append(
                f"human spec header gate_mode={recorded_mode} is not hard and not forced"
            )


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


KNOWN_TOP_LEVEL = frozenset(
    {
        "spec_version", "id", "title", "status", "baseline", "in_scope", "out_of_scope",
        "open_questions", "actors", "permissions", "defaults", "states", "ui",
        "empty_states", "object_ai", "behaviors", "acceptance", "pending",
        "project_hint", "sources", "source_claims", "overview", "architecture",
        "responsibilities", "data_contracts", "error_codes", "decisions",
        "content_hash", "accepted_warnings", "review",
    }
)


def _warn_unknown_top_level(data: dict, warn: list[str]) -> None:
    """Unknown top-level keys are consumed by nothing.

    The schema allows extensions on purpose, but a typo (`bizRuls:`) silently
    evaporates a business rule the author believed they had written down.
    """
    for key in data:
        if key not in KNOWN_TOP_LEVEL and not str(key).startswith("x_"):
            warn.append(
                f"unknown top-level field {key!r} — nothing consumes it (prefix with x_ to mark it intentional)"
            )


def _text_key(node: Any) -> str:
    """Normalized comparison key for a bilingual-or-plain text item."""
    if isinstance(node, dict):
        return " ".join(str(node.get(k, "")).strip() for k in ("zh", "en")).strip()
    return str(node or "").strip()


def _check_new_object_integrity(data: dict, fail: list[str], warn: list[str]) -> None:
    """Uniqueness / closure / non-contradiction for the v3 object family.

    The older objects (behaviors, acceptance, controls…) already had this rule
    family; overview/responsibilities/data_contracts/error_codes/decisions were
    added later and only got existence checks. An external audit found the gap.
    """
    scope_in = {_text_key(x) for x in (data.get("in_scope") or []) if _text_key(x)}
    for item in data.get("out_of_scope") or []:
        key = _text_key(item)
        if key and key in scope_in:
            fail.append(f"scope contradiction: {key!r} is both in_scope and out_of_scope")

    seen_states: set[str] = set()
    for s in (data.get("states") or {}).get("lifecycle") or []:
        if str(s) in seen_states:
            fail.append(f"duplicate lifecycle state: {s}")
        seen_states.add(str(s))

    for r in data.get("responsibilities") or []:
        if not isinstance(r, dict):
            continue
        owns = {_text_key(x) for x in (r.get("owns") or []) if _text_key(x)}
        for item in r.get("not_owns") or []:
            key = _text_key(item)
            if key and key in owns:
                fail.append(f"responsibility contradiction: {r.get('role')} both owns and disowns {key!r}")

    seen_codes: set[str] = set()
    for e in data.get("error_codes") or []:
        if not isinstance(e, dict):
            continue
        code = str(e.get("code") or "")
        if not code:
            fail.append("error_code item missing code")
            continue
        if code in seen_codes:
            fail.append(f"duplicate error_code: {code}")
        seen_codes.add(code)

    for dc in data.get("data_contracts") or []:
        if not isinstance(dc, dict):
            continue
        seen_fields: set[str] = set()
        for f in dc.get("fields") or []:
            if not isinstance(f, dict):
                continue
            name = str(f.get("name") or "")
            if not name:
                fail.append(f"data_contract {dc.get('id')}: field missing name")
                continue
            if name in seen_fields:
                fail.append(f"data_contract {dc.get('id')}: duplicate field: {name}")
            seen_fields.add(name)

    for d in data.get("decisions") or []:
        if not isinstance(d, dict):
            continue
        options = [o for o in (d.get("options") or []) if isinstance(o, dict)]
        option_ids = {str(o.get("id")) for o in options if o.get("id")}
        chosen = str(d.get("chosen") or "").strip()
        if chosen and option_ids and chosen not in option_ids:
            fail.append(
                f"decision {d.get('id')}: chosen={chosen} is not one of its options ({', '.join(sorted(option_ids))})"
            )
        elif chosen and not option_ids:
            warn.append(f"decision {d.get('id')}: chosen recorded without options to choose from")


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
    ac_ids = _collect_ids(fail, acceptance if isinstance(acceptance, list) else [], "acceptance")
    control_ids = _collect_ids(fail, (data.get("ui") or {}).get("controls") or [], "control")
    _collect_ids(fail, data.get("pending") or [], "pending")
    contract_ids = _collect_ids(fail, data.get("data_contracts") or [], "data_contract")
    decision_ids = _collect_ids(fail, data.get("decisions") or [], "decision")

    # IDs are referenced by bare name across object kinds (spec_refs, prototype
    # markers, free text), so a name may only mean one thing spec-wide.
    named: dict[str, str] = {}
    for kind, ids in (
        ("behavior", behavior_ids), ("acceptance", ac_ids), ("control", control_ids),
        ("actor", actor_ids), ("data_contract", contract_ids), ("decision", decision_ids),
    ):
        for i in ids:
            if i in named and named[i] != kind:
                fail.append(f"id collision across kinds: {i} is both {named[i]} and {kind}")
            named[i] = kind

    matrix_actions = {
        str(r.get("action")) for r in action_matrix_rows(data.get("states") or {}) if r.get("action")
    }
    for p in data.get("permissions") or []:
        if not isinstance(p, dict):
            fail.append(f"permission item must be an object, got {type(p).__name__}")
            continue
        actor = p.get("actor")
        if actor and str(actor) not in actor_ids:
            fail.append(f"permission references missing actor: {actor}")
        # `can` entries are sometimes coarser capability labels (data scope) and
        # sometimes literal matrix actions. Flag the divergence so a reviewer
        # decides, but do not fail legitimate two-layer modelling.
        for act in p.get("can") or []:
            if matrix_actions and str(act) not in matrix_actions:
                warn.append(
                    f"permission {actor}: can={act} is not an action in states.action_matrix "
                    "— confirm it is a capability label, not a state-machine action"
                )

    _check_new_object_integrity(data, fail, warn)
    _warn_unknown_top_level(data, warn)

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
    has_modern_matrix = isinstance(states, dict) and bool(states.get("action_matrix"))
    seen_pairs: dict[tuple[str, str], object] = {}
    for row in matrix:
        st = row.get("state")
        act = row.get("action")
        if lifecycle and st and str(st) not in lifecycle:
            fail.append(f"action_matrix state not in lifecycle: {st}")
        if not act:
            fail.append(f"action_matrix row for state={st} missing action")
            continue
        if has_modern_matrix and "allowed" not in row:
            fail.append(f"action_matrix {st}/{act}: missing allowed — the matrix is the single source of truth")
        pair = (str(st), str(act))
        if pair in seen_pairs:
            if seen_pairs[pair] != row.get("allowed"):
                fail.append(f"action_matrix conflict: {st}/{act} declared both allowed and denied")
            else:
                warn.append(f"action_matrix duplicate row: {st}/{act}")
        else:
            seen_pairs[pair] = row.get("allowed")
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
    if not (_lang(data.get("title"), "zh") or _lang(data.get("title"), "en")).strip():
        fail.append("status=ready requires a non-empty title")
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
        if not (_lang(b.get("name"), "zh") or _lang(b.get("name"), "en")).strip():
            fail.append(f"behavior {bid}: missing name — the human view would render an unnamed step")
        for field in ("given", "when", "then"):
            clause = (_lang(b.get(field), "zh") + " " + _lang(b.get(field), "en")).strip()
            if not clause:
                fail.append(f"behavior {bid}: {field} is empty")
            elif any(v in _strip_ui_literals(clause).lower() for v in VAGUE):
                fail.append(f"behavior {bid}: {field}-clause too vague for ready")
            elif _is_placeholder(clause):
                fail.append(f"behavior {bid}: {field} is still placeholder text")
    for a in acceptance if isinstance(acceptance, list) else []:
        if not isinstance(a, dict):
            continue
        if not str(a.get("behavior") or "").strip():
            fail.append(f"acceptance {a.get('id')}: missing behavior link — every AC must verify a behavior")
        text = (_lang(a, "zh") + " " + _lang(a, "en")).strip()
        if not text:
            fail.append(f"acceptance {a.get('id')}: missing observable zh/en text")
        elif any(v in _strip_ui_literals(text).lower() for v in UNOBSERVABLE_AC):
            fail.append(f"acceptance {a.get('id')}: not observable")
        elif _is_placeholder(text):
            fail.append(f"acceptance {a.get('id')}: is still placeholder text")
    overview_summary = (
        _lang((data.get("overview") or {}).get("summary"), "zh")
        + " "
        + _lang((data.get("overview") or {}).get("summary"), "en")
    ).strip()
    if overview_summary and _is_placeholder(overview_summary):
        fail.append("overview.summary is still placeholder text")
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
        st = str(d.get("status") or "").strip()
        chosen = str(d.get("chosen") or "").strip()
        if st == "decided" and not chosen:
            fail.append(
                f"decision {d.get('id')} marked decided but has no chosen option"
            )
        else:
            undecided = st == "pending" or (not chosen and st != "decided")
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
            if not isinstance(b, dict):
                continue
            if not b.get("step_id"):
                warn.append(f"behavior {b.get('id')}: prefer step_id for numbered main path")
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


def _validate_human_provenance(
    spec_path: Path | None, human_path: Path, fail: list[str], warn: list[str]
) -> None:
    """The `generated_from` header is a provenance claim; verify it resolves to
    the spec being checked, so a human view cannot misstate its own origin."""
    if spec_path is None:
        return
    text = _read_human_text(human_path, fail)
    if text is None:
        return
    meta = parse_human_header(text)
    declared = str(meta.get("generated_from") or "").strip()
    if not declared:
        warn.append(f"human spec {human_path.name}: no generated_from provenance")
        return
    root = find_repo_root(spec_path)
    candidates = {
        (root / declared).resolve(),
        (human_path.parent / declared).resolve(),
        Path(declared).resolve() if Path(declared).is_absolute() else None,
    }
    if spec_path.resolve() in {c for c in candidates if c is not None}:
        return
    if Path(declared).name == spec_path.name:
        # Same filename but a different base: the case directory was moved or
        # copied. Content proofs still hold, so nudge rather than block.
        warn.append(
            f"human spec provenance unresolved: generated_from={declared} — regenerate after moving the case"
        )
        return
    fail.append(
        f"human spec provenance mismatch: generated_from={declared} is not {spec_path.name}"
    )


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
        _validate_human_provenance(spec_path, resolved_human, fail, warn)
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


# Keys the rule layers dereference; wrong shapes must degrade to a FAIL,
# never to a traceback — a gate that crashes on bad input is not a gate.
_DICT_KEYS = ("title", "states", "ui", "defaults", "empty_states", "object_ai",
              "overview", "architecture", "project_hint", "review")
_LIST_KEYS = ("behaviors", "acceptance", "actors", "permissions", "pending",
              "in_scope", "out_of_scope", "open_questions", "sources",
              "source_claims", "responsibilities", "data_contracts",
              "error_codes", "decisions", "accepted_warnings")


def _sanitize_shapes(data: dict, fail: list[str]) -> dict:
    """Return a copy where wrongly-typed top-level containers are emptied,
    each recorded as a FAIL. Downstream layers can then rely on shapes."""
    safe = dict(data)
    for key in _DICT_KEYS:
        if key in safe and safe[key] is not None and not isinstance(safe[key], dict):
            fail.append(f"{key} must be an object, got {type(safe[key]).__name__}")
            safe[key] = {}
    for key in _LIST_KEYS:
        if key in safe and safe[key] is not None and not isinstance(safe[key], list):
            fail.append(f"{key} must be an array, got {type(safe[key]).__name__}")
            safe[key] = []
    return safe


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
    object-AI → source coverage → human staleness → prototype consistency.

    Nested illegal input must become a structured FAIL, never a traceback.
    """
    try:
        return _validate_inner(
            data,
            project,
            spec_path=spec_path,
            human_path=human_path,
            manifest_path=manifest_path,
            check_human=check_human,
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "fail": [f"illegal input: {type(exc).__name__}: {exc}"],
            "warn": [],
            "warn_ids": [],
        }


def _validate_inner(
    data: Any,
    project: dict | None = None,
    *,
    spec_path: Path | None = None,
    human_path: Path | None = None,
    manifest_path: Path | None = None,
    check_human: bool = True,
) -> dict[str, list[str]]:
    fail: list[str] = []
    warn: list[str] = []
    if not isinstance(data, dict):
        return {"fail": ["root must be an object"], "warn": [], "warn_ids": []}

    _layer_schema(data, fail)
    data = _sanitize_shapes(data, fail)
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
    warn_ids = _apply_accepted_warnings(data, fail, warn)
    return {"fail": fail, "warn": warn, "warn_ids": warn_ids}


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



