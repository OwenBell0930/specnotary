#!/usr/bin/env python3
"""Load / dump / hash / paths — the machine spec as bytes on disk.

Kept separate from the rule pipeline and the human renderer so a change to
how YAML is read cannot silently rewrite how FAIL is decided, and vice versa.
"""
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

SCHEMA_PATH = Path(__file__).resolve().parent / "schemas" / "machine-spec.schema.json"
# Process ledger — not product content. Accepting a WARN must not stale
# the human view or prototype endorsement.
_HASH_EXCLUDE = frozenset({"content_hash", "accepted_warnings", "review"})


class DuplicateKeyError(RuntimeError):
    """A mapping declared the same key twice — the source of truth is ambiguous."""


class _StrictLoader(getattr(yaml, "SafeLoader", object) if yaml else object):
    """SafeLoader that refuses duplicate mapping keys.

    Plain YAML silently keeps the last value, so `status: banana` followed by
    `status: ready` parses as ready with no warning. A file that means two
    different things cannot be a single source of truth.
    """


def _no_duplicate_keys(loader, node, deep=False):  # pragma: no cover - thin shim
    mapping: dict = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise DuplicateKeyError(
                f"duplicate key {key!r} at line {key_node.start_mark.line + 1} "
                "— the machine source must be unambiguous"
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


if yaml is not None:
    _StrictLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        lambda loader, node: _no_duplicate_keys(loader, node, deep=False),
    )


def _reject_duplicate_pairs(pairs):
    """Same contract as YAML: a key must mean one thing."""
    mapping: dict = {}
    for key, value in pairs:
        if key in mapping:
            raise DuplicateKeyError(
                f"duplicate key {key!r} — the machine source must be unambiguous"
            )
        mapping[key] = value
    return mapping


def load_spec(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError(
                "PyYAML missing. Install: pip install pyyaml  OR use JSON  OR degraded Skill mode."
            )
        return yaml.load(text, Loader=_StrictLoader)  # noqa: S506 - strict SafeLoader subclass
    if suffix == ".json":
        return json.loads(text, object_pairs_hook=_reject_duplicate_pairs)
    raise RuntimeError(f"unsupported suffix {suffix} (use .yaml/.yml/.json)")


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def spec_hash(data: dict) -> str:
    """SHA-256 of canonical machine spec (excludes process-ledger fields)."""
    payload = {k: v for k, v in data.items() if k not in _HASH_EXCLUDE}
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


_CHROME_HINT = (
    "generated_from",
    "spec_id:",
    "spec_version:",
    "spec_hash",
    "body_hash",
    "renderer_version",
    "lang:",
    "gate_mode",
    "forced:",
    "以机读 YAML",
    "Machine YAML is the single",
)


def parse_human_header(text: str) -> dict[str, str]:
    """Read chrome comments anywhere in the file.

    Trailer placement keeps Markdown preview free of blank comment lines.
    One key per comment, or several `key: value` pairs separated by `;`.
    """
    meta: dict[str, str] = {}
    for block in re.findall(r"<!--(.*?)-->", text, flags=re.DOTALL):
        for m in re.finditer(r"([a-z_]+)\s*:\s*([^\s;]+(?:\s+[^\s;]+)*)", block):
            meta[m.group(1)] = m.group(2).strip()
    return meta


def _strip_chrome_comments(text: str) -> str:
    def keep_or_drop(match: re.Match[str]) -> str:
        return "" if any(h in match.group(0) for h in _CHROME_HINT) else match.group(0)

    out = re.sub(r"<!--.*?-->", keep_or_drop, text, flags=re.DOTALL)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip() + "\n"


def expected_human_path(spec_path: Path | None) -> Path | None:
    """Standard layout: machine/spec.yaml ↔ human/spec.md.

    Alternate machine files in the same folder (e.g. spec.fixed.yaml) are not
    that pair — attaching the sibling human would fail provenance.
    """
    if spec_path is None:
        return None
    if spec_path.name not in {"spec.yaml", "spec.yml", "spec.json"}:
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
    return meta, _strip_chrome_comments(text)


def human_body_hash(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump_spec(path: Path, data: dict) -> None:
    """Write a machine spec. Comment-preserving round-trip is not promised."""
    if yaml is None:
        raise RuntimeError("PyYAML missing — cannot write YAML")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )


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
