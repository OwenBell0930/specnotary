#!/usr/bin/env python3
"""Shared machine-spec load/validate/render for Spec Kit CLI."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


REQUIRED_TOP = ["spec_version", "id", "title", "status", "behaviors", "acceptance"]


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


def _lang_text(node: Any, lang: str) -> str:
    if isinstance(node, dict):
        if lang in node and node[lang]:
            return str(node[lang])
        if "zh" in node:
            return str(node["zh"])
        if "en" in node:
            return str(node["en"])
        return str(node)
    return "" if node is None else str(node)


def validate(data: Any, project: dict | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["root must be an object"]

    for key in REQUIRED_TOP:
        if key not in data:
            errors.append(f"missing required field: {key}")

    behaviors = data.get("behaviors") or []
    acceptance = data.get("acceptance") or []
    if not isinstance(behaviors, list) or len(behaviors) < 1:
        errors.append("behaviors must have at least 1 item")
    if not isinstance(acceptance, list) or len(acceptance) < 1:
        errors.append("acceptance must have at least 1 item")

    status = data.get("status")
    open_qs = data.get("open_questions") or []
    if status == "ready" and open_qs:
        errors.append("status=ready but open_questions is not empty")

    # Stronger rules when claiming ready
    if status == "ready":
        if not data.get("actors"):
            errors.append("status=ready requires actors")
        if not data.get("defaults"):
            errors.append("status=ready requires defaults")
        vague = ("体验好", "尽量快", "智能", "good ux", "quickly", "尽快")
        for b in behaviors if isinstance(behaviors, list) else []:
            then = (
                _lang_text((b or {}).get("then"), "zh")
                + " "
                + _lang_text((b or {}).get("then"), "en")
            ).lower()
            if any(v in then for v in vague):
                errors.append(
                    f"behavior {(b or {}).get('id')}: then-clause looks too vague for ready"
                )

    weight = (project or {}).get("object_ai_weight", "medium")
    obj = data.get("object_ai") or {}
    if weight == "high":
        if not obj or not obj.get("enabled"):
            errors.append("object_ai_weight=high requires object_ai.enabled=true")
        else:
            for key in ("tools_boundary", "failure_fallback", "human_takeover_when"):
                if not obj.get(key):
                    errors.append(f"object_ai_weight=high requires object_ai.{key}")

    return errors


def render_human(data: dict, source: str, gate_mode: str = "hard") -> str:
    title_zh = _lang_text(data.get("title"), "zh")
    title_en = _lang_text(data.get("title"), "en")
    lines = [
        f"<!-- generated_from: {source} -->",
        f"<!-- gate_mode: {gate_mode} -->",
        f"<!-- DO NOT long-term edit without updating machine source -->",
        "",
        f"# {title_zh}",
        f"# {title_en}" if title_en and title_en != title_zh else "",
        "",
        f"- **ID:** `{data.get('id')}`",
        f"- **Status:** `{data.get('status')}`",
        f"- **Spec version:** `{data.get('spec_version')}`",
        "",
        "## Scope / 范围",
        "",
        "### In scope / 范围内",
        "",
    ]
    for item in data.get("in_scope") or []:
        lines.append(f"- {_lang_text(item, 'zh')} / {_lang_text(item, 'en')}".rstrip(" /"))
    lines += ["", "### Out of scope / 范围外", ""]
    for item in data.get("out_of_scope") or []:
        lines.append(f"- {_lang_text(item, 'zh')} / {_lang_text(item, 'en')}".rstrip(" /"))
    lines += ["", "### Open questions / 待决", ""]
    oq = data.get("open_questions") or []
    if not oq:
        lines.append("- （无 / none）")
    for q in oq:
        qid = (q or {}).get("id", "")
        lines.append(f"- `{qid}` {_lang_text(q, 'zh')} / {_lang_text(q, 'en')}".rstrip(" /"))

    lines += ["", "## Actors & permissions / 角色与权限", ""]
    for a in data.get("actors") or []:
        lines.append(f"- `{a.get('id')}`: {_lang_text(a, 'zh')} / {_lang_text(a, 'en')}".rstrip(" /"))
    for p in data.get("permissions") or []:
        lines.append(f"- `{p.get('actor')}` can `{', '.join(p.get('can') or [])}`")

    lines += ["", "## Defaults & empty states / 默认值与空态", ""]
    defaults = data.get("defaults") or {}
    if defaults:
        lines.append("```yaml")
        lines.append(yaml.dump(defaults, allow_unicode=True).rstrip() if yaml else str(defaults))
        lines.append("```")
    else:
        lines.append("- （未声明 / not declared）")
    empty = data.get("empty_states") or {}
    for key, val in empty.items():
        lines.append(f"- **{key}:** {_lang_text(val, 'zh')} / {_lang_text(val, 'en')}".rstrip(" /"))

    lines += ["", "## Object AI / 对象 AI", ""]
    obj = data.get("object_ai") or {}
    lines.append(f"- enabled: `{obj.get('enabled', False)}`")
    if obj.get("enabled"):
        lines.append(f"- failure_fallback: {_lang_text(obj.get('failure_fallback'), 'zh')}")
        lines.append(f"- confidence_threshold: `{obj.get('confidence_threshold', '')}`")
        lines.append("- tools_boundary:")
        for t in obj.get("tools_boundary") or []:
            lines.append(f"  - {_lang_text(t, 'zh')} / {_lang_text(t, 'en')}".rstrip(" /"))
        lines.append("- human_takeover_when:")
        for t in obj.get("human_takeover_when") or []:
            lines.append(f"  - {_lang_text(t, 'zh')} / {_lang_text(t, 'en')}".rstrip(" /"))

    lines += ["", "## Behaviors / 行为", ""]
    for b in data.get("behaviors") or []:
        lines.append(f"### `{b.get('id')}` {_lang_text(b.get('name'), 'zh')}")
        lines.append("")
        lines.append(f"- **Given:** {_lang_text(b.get('given'), 'zh')} / {_lang_text(b.get('given'), 'en')}".rstrip(" /"))
        lines.append(f"- **When:** {_lang_text(b.get('when'), 'zh')} / {_lang_text(b.get('when'), 'en')}".rstrip(" /"))
        lines.append(f"- **Then:** {_lang_text(b.get('then'), 'zh')} / {_lang_text(b.get('then'), 'en')}".rstrip(" /"))
        lines.append("")

    lines += ["## Acceptance / 验收", ""]
    for a in data.get("acceptance") or []:
        lines.append(
            f"- `{a.get('id')}` ({a.get('behavior')}): {_lang_text(a, 'zh')} / {_lang_text(a, 'en')}".rstrip(" /")
        )
    lines.append("")
    return "\n".join([ln for ln in lines if ln is not None])


def load_project(root: Path) -> dict:
    for name in ("project.yaml", "project.example.yaml"):
        p = root / name
        if p.exists() and yaml is not None:
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            if isinstance(data, dict):
                return data
    return {}
