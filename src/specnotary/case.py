#!/usr/bin/env python3
"""Start a spec case from raw material, or attach more sources (thin adapter)."""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

from .libspec import dump_spec, file_sha256, load_spec

USAGE_NEW = (
    "Usage: specnotary new <case-dir> --from <raw-file> "
    "[--id SPEC-FOO-001] [--kind ops|prd|faq|speckit|ticket|raw]"
)
USAGE_INGEST = (
    "Usage: specnotary ingest <raw-file> --spec <machine-spec.yaml> "
    "[--kind ops|prd|faq|speckit|ticket|raw]"
)
KINDS = {"ops", "prd", "faq", "speckit", "ticket", "raw"}


def _find_repo_with_templates() -> Path | None:
    here = Path(__file__).resolve()
    candidates = [Path.cwd(), *Path.cwd().parents]
    if len(here.parents) >= 2:
        candidates.append(here.parents[2])
    for candidate in candidates:
        if (candidate / "templates" / "machine" / "spec.template.yaml").is_file():
            return candidate
    return None


def _templates() -> Path:
    root = _find_repo_with_templates()
    if root is None:
        return Path("templates/machine/spec.template.yaml")
    return root / "templates" / "machine" / "spec.template.yaml"


def _parse_kv(argv: list[str]) -> tuple[list[str], dict[str, str]]:
    positional: list[str] = []
    flags: dict[str, str] = {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in {"--from", "--id", "--kind", "--spec"}:
            if i + 1 >= len(argv):
                raise ValueError(f"{a} needs a value")
            flags[a] = argv[i + 1]
            i += 2
            continue
        if a.startswith("-"):
            raise ValueError(f"unknown flag {a}")
        positional.append(a)
        i += 1
    return positional, flags


def _slug_id(name: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", Path(name).stem).strip("-").upper() or "FEATURE"
    return f"SPEC-{slug[:40]}-001"


def _copy_raw(raw: Path, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / raw.name
    if dest.resolve() != raw.resolve():
        shutil.copy2(raw, dest)
    return dest


def new_main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        positional, flags = _parse_kv(argv)
    except ValueError as exc:
        print(f"FAIL: {exc}")
        print(USAGE_NEW)
        return 2
    if len(positional) != 1 or "--from" not in flags:
        print(USAGE_NEW)
        return 2
    raw = Path(flags["--from"])
    if not raw.is_file():
        print(f"FAIL: raw file not found: {raw}")
        return 2
    kind = flags.get("--kind", "raw")
    if kind not in KINDS:
        print(f"FAIL: kind must be one of {sorted(KINDS)}")
        return 2
    case = Path(positional[0])
    if case.exists() and any(case.iterdir()):
        print(f"FAIL: {case} already exists and is not empty")
        return 2
    spec_id = flags.get("--id") or _slug_id(case.name)
    tpl_spec = _templates()
    if not tpl_spec.is_file():
        print(f"FAIL: template missing: {tpl_spec}")
        return 2

    input_dir = case / "input"
    copied = _copy_raw(raw, input_dir)
    digest = file_sha256(copied)
    text = tpl_spec.read_text(encoding="utf-8")
    text = text.replace("SPEC-XXX-001", spec_id)
    sources_block = (
        "sources:\n"
        f"  - id: SRC-001\n"
        f"    kind: {kind}\n"
        f"    path: ../input/{copied.name}\n"
        f"    content_hash: {digest}\n"
        f"    status: registered\n"
        f"    zh: 原始需求原料\n"
    )
    if "sources: []" not in text:
        print("FAIL: template no longer has `sources: []` to fill")
        return 2
    text = text.replace("sources: []", sources_block.rstrip())
    (case / "machine").mkdir(parents=True, exist_ok=True)
    (case / "human").mkdir(parents=True, exist_ok=True)
    (case / "prototype").mkdir(parents=True, exist_ok=True)
    (case / "reports").mkdir(parents=True, exist_ok=True)
    spec_path = case / "machine" / "spec.yaml"
    spec_path.write_text(text, encoding="utf-8")
    html = (
        "<!DOCTYPE html>\n<html lang=\"zh-CN\"><head><meta charset=\"utf-8\"/>"
        f"<title>{spec_id}</title></head>\n<body>\n"
        "<p>静态原型占位。Agent 起草时按机读控件补 data-spec-id。</p>\n"
        "</body></html>\n"
    )
    (case / "prototype" / "main.html").write_text(html, encoding="utf-8")
    print(f"wrote: {spec_path}")
    print(f"source: {copied} (sha256:{digest[:12]}… kind={kind})")
    print("NEXT: Agent/Skill 按 skills/specnotary/SKILL.md 起草机读、人读与原型；用户只确认结果并拿报告去评审。")
    print(f"  specnotary check {spec_path} --explain")
    return 0


def ingest_main(argv: list[str] | None = None) -> int:
    """Register another raw file as a source (GitHub spec-kit / OpenSpec markdown included)."""
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        positional, flags = _parse_kv(argv)
    except ValueError as exc:
        print(f"FAIL: {exc}")
        print(USAGE_INGEST)
        return 2
    if len(positional) != 1 or "--spec" not in flags:
        print(USAGE_INGEST)
        return 2
    raw = Path(positional[0])
    spec_path = Path(flags["--spec"])
    kind = flags.get("--kind", "raw")
    if kind not in KINDS:
        print(f"FAIL: kind must be one of {sorted(KINDS)}")
        return 2
    if not raw.is_file():
        print(f"FAIL: raw file not found: {raw}")
        return 2
    if not spec_path.is_file():
        print(f"FAIL: spec not found: {spec_path}")
        return 2
    try:
        data = load_spec(spec_path)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        return 2
    if not isinstance(data, dict):
        print("FAIL: spec root must be an object")
        return 1
    case_input = spec_path.resolve().parent.parent / "input"
    copied = _copy_raw(raw, case_input)
    digest = file_sha256(copied)
    sources = list(data.get("sources") or [])
    existing_ids = {str(s.get("id")) for s in sources if isinstance(s, dict)}
    n = 1
    while f"SRC-{n:03d}" in existing_ids:
        n += 1
    sid = f"SRC-{n:03d}"
    rel = f"../input/{copied.name}"
    sources.append(
        {
            "id": sid,
            "kind": kind,
            "path": rel,
            "content_hash": digest,
            "status": "registered",
            "zh": f"{kind} 原料",
        }
    )
    data["sources"] = sources
    dump_spec(spec_path, data)
    print(f"ingested: {copied} as {sid} (sha256:{digest[:12]}… kind={kind})")
    print(f"wrote: {spec_path}")
    print("NOTE: claims are not invented here — Agent 继续拆 SourceClaim；用户确认后再评审。")
    return 0


if __name__ == "__main__":
    raise SystemExit(new_main())
