#!/usr/bin/env python3
"""Documentation-vs-implementation consistency gate.

A tool that sells drift detection must not drift. Two audits caught exactly
that: a hand-copied test count, then a capability-table line still promising
the old `sync` semantics after the semantics changed. Both were invisible to
the test suite because nothing compared prose against code.

These checks fail the build when the docs claim something the code does not do.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from specnotary.cli import COMMANDS  # noqa: E402
from specnotary.libspec import RENDERER_VERSION  # noqa: E402

DOCS = [
    ROOT / "README.md",
    ROOT / "README.en.md",
    ROOT / "docs/gate-modes.md",
    ROOT / "docs/proof-boundary.md",
    ROOT / "docs/positioning.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "skills/SKILL.md",
]
BRAND = "SpecNotary"
PACKAGE = "specnotary"


def _doc_text() -> dict[Path, str]:
    return {p: p.read_text(encoding="utf-8") for p in DOCS if p.is_file()}


def test_documented_subcommands_exist():
    """Every `specnotary <verb>` mentioned in docs must be a real command."""
    unknown: list[str] = []
    for path, text in _doc_text().items():
        # Same-line only: YAML frontmatter (`name: specnotary`) must not glue
        # onto the next key.
        for verb in re.findall(rf"{PACKAGE}[ \t]+([a-z][a-z-]+)", text):
            if verb in {"gate", "check-spec"}:  # prose words, not subcommands
                continue
            if verb not in COMMANDS:
                unknown.append(f"{path.name}: '{PACKAGE} {verb}'")
    assert not unknown, "docs reference non-existent subcommands: " + "; ".join(sorted(set(unknown)))


def test_documented_flags_exist():
    """Flags promised in prose must be accepted by the code that implements them."""
    sources = {
        "--json": ROOT / "src/specnotary/check.py",
        "--explain": ROOT / "src/specnotary/check.py",
        "--lang": ROOT / "src/specnotary/generate_human.py",
        "--allow-invalid": ROOT / "src/specnotary/generate_human.py",
        "--attest-prototype": ROOT / "src/specnotary/sync.py",
    }
    documented = set()
    for text in _doc_text().values():
        documented |= set(re.findall(r"--[a-z][a-z-]+", text))
    missing = []
    for flag in documented & set(sources):
        if flag not in sources[flag].read_text(encoding="utf-8"):
            missing.append(flag)
    assert not missing, f"documented flags absent from implementation: {missing}"
    # And the reverse: implemented flags must be documented somewhere.
    undocumented = [f for f in sources if f not in documented]
    assert not undocumented, f"implemented flags missing from docs: {undocumented}"


def test_renderer_version_matches_docs():
    """No doc may cite a renderer version other than the current one."""
    wrong = []
    for path, text in _doc_text().items():
        for cited in re.findall(r"渲染器\s*v(\d+)|renderer\s*v(\d+)", text, re.IGNORECASE):
            num = cited[0] or cited[1]
            if num != RENDERER_VERSION:
                wrong.append(f"{path.name}: renderer v{num} (current: v{RENDERER_VERSION})")
    assert not wrong, "stale renderer version in docs: " + "; ".join(wrong)


def test_sync_semantics_not_misstated():
    """`sync` must never be described as refreshing the prototype hash on its own.

    This is the exact line an audit caught: attestation is an explicit action,
    and prose implying otherwise manufactures false confidence.
    """
    offenders = []
    for path, text in _doc_text().items():
        for line in text.splitlines():
            if PACKAGE + " sync" not in line and "sync`" not in line and "sync：" not in line:
                continue
            mentions_refresh = ("刷新原型" in line) or ("refresh" in line.lower() and "prototype" in line.lower())
            if mentions_refresh and "attest" not in line:
                offenders.append(f"{path.name}: {line.strip()[:100]}")
    assert not offenders, "sync described as auto-refreshing the prototype hash: " + "; ".join(offenders)


def test_no_hardcoded_test_counts():
    """Docs must not hand-copy test counts — they go stale by construction."""
    offenders = []
    # A count *claim*, not an invocation: `python3 tests/...` must not match.
    pattern = re.compile(r"(\d+)\s*(?:项|个)\s*(?:回归|测试|用例)|(\d+)\+?\s+(?:regression\s+)?tests?\b", re.IGNORECASE)
    for path, text in _doc_text().items():
        for line in text.splitlines():
            if re.search(r"python3?\s+tests/", line):
                continue
            m = pattern.search(line)
            if m:
                offenders.append(f"{path.name}: '{m.group(0).strip()}'")
    assert not offenders, (
        "hard-coded test counts drift; cite the command instead: " + "; ".join(offenders)
    )


def test_capability_table_commands_runnable():
    """Commands in the README capability table must exist as files/verbs."""
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for script in re.findall(r"`\./(cli/run-[a-z-]+\.sh)`", text):
        assert (ROOT / script).is_file(), f"README cites missing script: {script}"


def test_brand_is_consistent():
    """Old brands may only appear in explicit naming-history sentences."""
    history_markers = ("曾用名", "Formerly", "原工作名", "更名", "命名")
    stale = []
    for path, text in _doc_text().items():
        for i, line in enumerate(text.splitlines(), 1):
            if re.search(r"SpecAnvil|specanvil|Spec Kit(?!\s*/)", line) and not any(
                m in line for m in history_markers
            ):
                stale.append(f"{path.name}:{i}")
    assert not stale, f"old brand outside naming-history context: {stale}"


TESTS = [
    test_documented_subcommands_exist,
    test_documented_flags_exist,
    test_renderer_version_matches_docs,
    test_sync_semantics_not_misstated,
    test_no_hardcoded_test_counts,
    test_capability_table_commands_runnable,
    test_brand_is_consistent,
]

if __name__ == "__main__":
    failed = 0
    for t in TESTS:
        try:
            t()
            print(f"OK  {t.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {t.__name__}: {exc}")
    sys.exit(1 if failed else 0)
