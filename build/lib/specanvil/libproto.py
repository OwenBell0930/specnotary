#!/usr/bin/env python3
"""Deterministic prototype-manifest checks (P2)."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None

from .libspec import known_entity_ids, load_spec, spec_hash

SCHEMA_PATH = Path(__file__).resolve().parent / "schemas" / "prototype-manifest.schema.json"
EXTRA_EXEMPT_ROLES = {"decoration", "visual"}


def expected_manifest_path(spec_path: Path | None) -> Path | None:
    if spec_path is None:
        return None
    return spec_path.resolve().parent.parent / "prototype" / "prototype.manifest.yaml"


def default_manifest_path(spec_path: Path | None) -> Path | None:
    sibling = expected_manifest_path(spec_path)
    return sibling if sibling is not None and sibling.is_file() else None


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _iter_controls(manifest: dict) -> list[tuple[dict, dict | None]]:
    out: list[tuple[dict, dict | None]] = []
    for screen in manifest.get("screens") or []:
        if not isinstance(screen, dict):
            continue
        for ctrl in screen.get("controls") or []:
            if isinstance(ctrl, dict):
                out.append((ctrl, screen))
    return out


def _html_spec_ids(html_path: Path) -> set[str]:
    if not html_path.is_file():
        return set()
    text = re.sub(r"<!--.*?-->", "", html_path.read_text(encoding="utf-8"), flags=re.DOTALL)
    return set(re.findall(r'data-spec-id=["\']([^"\']+)["\']', text))


def _required_spec_controls(data: dict) -> list[str]:
    ids = []
    for c in (data.get("ui") or {}).get("controls") or []:
        if not isinstance(c, dict) or not c.get("id"):
            continue
        if c.get("prototype_optional") is True:
            continue
        ids.append(str(c["id"]))
    return ids


def _required_behaviors(data: dict) -> list[str]:
    ids = []
    for b in data.get("behaviors") or []:
        if not isinstance(b, dict) or not b.get("id"):
            continue
        if b.get("prototype_optional") is True:
            continue
        ids.append(str(b["id"]))
    return ids


def classify_proto_issues(fail: list[str], warn: list[str]) -> dict[str, list[str]]:
    buckets = {"missing": [], "extra": [], "stale": [], "mismatch": [], "unverified": []}
    for e in fail:
        if not str(e).startswith("prototype"):
            continue
        low = e.lower()
        if "stale" in low or "hash" in low:
            buckets["stale"].append(e)
        elif "missing" in low or "not mapped" in low or "未映射" in e:
            buckets["missing"].append(e)
        elif "extra" in low or "no spec_refs" in low or "擅自" in e:
            buckets["extra"].append(e)
        elif "mismatch" in low or "not found in html" in low or "schema" in low:
            buckets["mismatch"].append(e)
        else:
            buckets["mismatch"].append(e)
    for w in warn:
        if str(w).startswith("prototype") or "unverified" in str(w).lower():
            buckets["unverified"].append(w)
    return buckets


def validate_prototype(
    data: dict,
    manifest: dict,
    *,
    manifest_path: Path | None = None,
) -> dict[str, list[str]]:
    fail: list[str] = []
    warn: list[str] = []
    if not isinstance(manifest, dict):
        return {"fail": ["prototype: manifest root must be an object"], "warn": []}

    if jsonschema is None:
        fail.append("prototype schema: jsonschema not installed — cannot claim hard gate")
    else:
        try:
            jsonschema.validate(instance=manifest, schema=_load_schema())
        except jsonschema.ValidationError as exc:
            path = ".".join(str(p) for p in exc.absolute_path) or "(root)"
            fail.append(f"prototype schema: {exc.message} at {path}")

    meta = manifest.get("generated_from_spec") or {}
    expected = spec_hash(data)
    recorded = str(meta.get("hash") or "").replace("sha256:", "").strip()
    if meta.get("id") and str(meta.get("id")) != str(data.get("id")):
        fail.append(f"prototype stale: spec id {meta.get('id')} != {data.get('id')}")
    if not recorded:
        fail.append("prototype stale: generated_from_spec.hash missing")
    elif recorded != expected:
        fail.append(
            f"prototype stale: hash {recorded[:12]}… != machine {expected[:12]}… — regenerate"
        )

    entities = known_entity_ids(data)
    behavior_ids = {str((b or {}).get("id")) for b in (data.get("behaviors") or []) if (b or {}).get("id")}
    spec_control_ids = {
        str(c["id"])
        for c in ((data.get("ui") or {}).get("controls") or [])
        if isinstance(c, dict) and c.get("id")
    }
    mapped_controls: set[str] = set()
    mapped_behaviors: set[str] = set()
    proto_ids: set[str] = set()

    declared_ids: set[str] = set()
    for screen in manifest.get("screens") or []:
        if not isinstance(screen, dict):
            continue
        if screen.get("id"):
            declared_ids.add(str(screen["id"]))
        for ctrl in screen.get("controls") or []:
            if isinstance(ctrl, dict) and ctrl.get("id"):
                declared_ids.add(str(ctrl["id"]))
    for item in manifest.get("interactions") or []:
        if isinstance(item, dict) and item.get("id"):
            declared_ids.add(str(item["id"]))

    for screen in manifest.get("screens") or []:
        if not isinstance(screen, dict):
            continue
        sid = screen.get("id")
        if sid:
            if sid in proto_ids:
                fail.append(f"prototype duplicate id: {sid}")
            proto_ids.add(str(sid))
        for ref in screen.get("spec_refs") or []:
            if str(ref) not in entities:
                fail.append(f"prototype screen {sid}: spec_ref missing: {ref}")
        if screen.get("required") is True and not screen.get("path"):
            fail.append(f"prototype screen {sid}: required but has no path")
        html_ids: set[str] = set()
        rel = screen.get("path")
        if rel and manifest_path is not None:
            html_path = (manifest_path.parent / rel).resolve()
            if not html_path.is_file():
                fail.append(f"prototype screen {sid}: html missing: {rel}")
            else:
                html_ids = _html_spec_ids(html_path)

        for ctrl, _scr in [(c, screen) for c in (screen.get("controls") or []) if isinstance(c, dict)]:
            cid = ctrl.get("id")
            if cid:
                if cid in proto_ids:
                    fail.append(f"prototype duplicate id: {cid}")
                proto_ids.add(str(cid))
            refs = [str(r) for r in (ctrl.get("spec_refs") or [])]
            role = str(ctrl.get("role") or "control")
            if not refs and role not in EXTRA_EXEMPT_ROLES:
                fail.append(f"prototype extra: control {cid} has no spec_refs")
            for ref in refs:
                if ref not in entities:
                    fail.append(f"prototype control {cid}: spec_ref missing: {ref}")
                mapped_controls.add(ref)
                if ref in behavior_ids:
                    mapped_behaviors.add(ref)
            selector = str(ctrl.get("selector") or "")
            mark = None
            m = re.search(r"data-spec-id=['\"]([^'\"]+)['\"]", selector)
            if m:
                mark = m.group(1)
            if mark and rel and manifest_path is not None:
                html_file = (manifest_path.parent / rel).resolve()
                if html_file.is_file() and mark not in html_ids:
                    fail.append(
                        f"prototype mismatch: {cid} data-spec-id={mark} not found in html"
                    )
            elif mark and not rel:
                fail.append(f"prototype mismatch: {cid} has data-spec-id but screen has no path")
            if rel and html_ids:
                for ref in refs:
                    if ref in spec_control_ids and ref not in html_ids:
                        fail.append(
                            f"prototype mismatch: mapped control {ref} not found in html"
                        )

    for item in manifest.get("interactions") or []:
        if not isinstance(item, dict):
            continue
        iid = item.get("id")
        if iid:
            if iid in proto_ids:
                fail.append(f"prototype duplicate id: {iid}")
            proto_ids.add(str(iid))
        refs = [str(r) for r in (item.get("spec_refs") or [])]
        role = str(item.get("role") or "flow")
        if not refs and role not in EXTRA_EXEMPT_ROLES:
            fail.append(f"prototype extra: interaction {iid} has no spec_refs")
        for ref in refs:
            if ref not in entities:
                fail.append(f"prototype interaction {iid}: spec_ref missing: {ref}")
            if ref in behavior_ids:
                mapped_behaviors.add(ref)
        for link in ("from", "to", "trigger"):
            target = item.get(link)
            if target and str(target) not in declared_ids:
                fail.append(f"prototype link broken: {iid} {link}={target} not declared")

    for deco in manifest.get("decorations") or []:
        if not isinstance(deco, dict):
            continue
        # decoration without spec_refs is allowed
        for ref in deco.get("spec_refs") or []:
            if str(ref) not in entities:
                fail.append(f"prototype decoration {deco.get('id')}: spec_ref missing: {ref}")

    for copy in manifest.get("copy_refs") or []:
        if not isinstance(copy, dict):
            continue
        for ref in copy.get("spec_refs") or []:
            if str(ref) not in entities:
                fail.append(f"prototype copy {copy.get('id')}: spec_ref missing: {ref}")

    for cid in _required_spec_controls(data):
        if cid not in mapped_controls:
            fail.append(f"prototype missing: required control not mapped: {cid}")

    for bid in _required_behaviors(data):
        if bid not in mapped_behaviors:
            fail.append(f"prototype missing: required behavior not mapped: {bid}")

    for sw in manifest.get("semantic_warnings") or []:
        if not isinstance(sw, dict):
            continue
        ev = sw.get("evidence") or "no-evidence"
        note = sw.get("note") or "possible semantic mismatch"
        conf = sw.get("confidence") or "low"
        warn.append(f"prototype unverified [{conf}] {sw.get('target')}: {note} ({ev})")

    return {"fail": fail, "warn": warn}


def load_and_validate_prototype(
    data: dict,
    manifest_path: Path,
) -> dict[str, list[str]]:
    try:
        manifest = load_spec(manifest_path)
    except Exception as exc:  # noqa: BLE001
        return {"fail": [f"prototype: cannot load {manifest_path}: {exc}"], "warn": []}
    if not isinstance(manifest, dict):
        return {"fail": ["prototype: manifest root must be an object"], "warn": []}
    return validate_prototype(data, manifest, manifest_path=manifest_path)
