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

# User-facing prose. CLI help and the Action manifest count: an audit found the
# stale `sync` promise living in `cli.py`'s help string, which users read more
# often than any markdown file.
DOCS = [
    ROOT / "README.md",
    ROOT / "README.en.md",
    ROOT / "docs/gate-modes.md",
    ROOT / "docs/proof-boundary.md",
    ROOT / "docs/positioning.md",
    ROOT / "docs/release-checklist.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "CHANGELOG.md",
    ROOT / "SECURITY.md",
    ROOT / "skills/SKILL.md",
    ROOT / "src/specnotary/cli.py",
    ROOT / "src/specnotary/sync.py",
    ROOT / "action.yml",
    ROOT / "playground/index.html",
]
BRAND = "SpecNotary"
PACKAGE = "specnotary"


def _doc_text() -> dict[Path, str]:
    """Doc bodies, with released CHANGELOG entries trimmed off.

    A shipped changelog entry is a historical record: it may legitimately cite
    the renderer version or semantics of its own release. Only the newest
    (still-shipping) section is held to current truth.
    """
    out: dict[Path, str] = {}
    for p in DOCS:
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8")
        if p.name == "CHANGELOG.md":
            sections = re.split(r"^## \[", text, flags=re.MULTILINE)
            text = sections[0] + ("## [" + sections[1] if len(sections) > 1 else "")
        out[p] = text
    return out


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


# Ways prose has claimed the prototype hash refreshes itself. The first audit's
# regex only knew 刷新原型 / refresh…prototype on the *same line* as the command,
# so a comment one line above the command, a Python help string, and the wording
# 自动刷新 all slipped through. Match the claim, not one phrasing of it.
_AUTO_REFRESH_CLAIMS = (
    re.compile(r"刷新原型"),
    re.compile(r"自动刷新"),
    re.compile(r"同步.{0,6}原型.{0,4}哈希"),
    re.compile(r"refresh(?:es|ing)?\s+(?:the\s+)?prototype", re.IGNORECASE),
    re.compile(r"prototype\s+hash.{0,20}refresh", re.IGNORECASE),
)
# A line that *discusses* the forbidden phrasing (a changelog entry about the
# rule, a doc explaining what is not allowed) is not itself a false promise.
_DISCUSSING_THE_RULE = (
    "不", "no longer", "not ", "须", "必须", "改为", "曾", "盲区", "误判",
    "「自动刷新」", "措辞变体", "NOT refreshed",
)


def test_sync_semantics_not_misstated():
    """`sync` must never be described as refreshing the prototype hash on its own.

    Attestation is an explicit action; prose implying otherwise manufactures
    false confidence. Scanned in a sliding window because the claim and the
    command are often on adjacent lines (a shell comment above its command).
    """
    offenders = []
    for path, text in _doc_text().items():
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if not any(p.search(line) for p in _AUTO_REFRESH_CLAIMS):
                continue
            window = "\n".join(lines[max(0, i - 2): i + 3])
            if "sync" not in window:
                continue  # a claim about some other command
            if "attest" in window:
                continue  # correctly qualified
            if any(cue in line for cue in _DISCUSSING_THE_RULE):
                continue  # describing the rule, not promising the behavior
            offenders.append(f"{path.name}:{i + 1}: {line.strip()[:90]}")
    assert not offenders, "sync described as auto-refreshing the prototype hash: " + "; ".join(offenders)


def test_version_is_single_sourced():
    """Package, CLI and release plan must cite one version."""
    from specnotary import __version__

    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
    assert m, "pyproject has no version"
    assert m.group(1) == __version__, f"pyproject {m.group(1)} != package {__version__}"
    wrong = []
    for path, text in _doc_text().items():
        for tag in re.findall(r"tag\s+`?v(\d+\.\d+\.\d+)`?", text):
            if tag != __version__:
                wrong.append(f"{path.name}: tag v{tag} (package {__version__})")
    assert not wrong, "release tag disagrees with package version: " + "; ".join(wrong)


def test_lifecycle_diagram_declares_no_transitions():
    """The state-set diagram must not draw arrows between lifecycle entries."""
    from specnotary.libspec import mermaid_lifecycle

    diagram = mermaid_lifecycle({"lifecycle": ["a", "b", "c"]}) or ""
    assert "-->" not in diagram, (
        "lifecycle diagram must not imply transitions; declaration order is not a flow"
    )


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
    test_version_is_single_sourced,
    test_lifecycle_diagram_declares_no_transitions,
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
