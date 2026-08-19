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
    ROOT / "docs/empty-talk-corpus.md",
    ROOT / "docs/release-checklist.md",
    ROOT / "docs/human-view.md",
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
        "--from": ROOT / "src/specnotary/case.py",
        "--id": ROOT / "src/specnotary/case.py",
        "--kind": ROOT / "src/specnotary/case.py",
        "--spec": ROOT / "src/specnotary/case.py",
        "--by": ROOT / "src/specnotary/confirm.py",
        "--reason": ROOT / "src/specnotary/confirm.py",
        "--accept-all-warn": ROOT / "src/specnotary/confirm.py",
        "--accept": ROOT / "src/specnotary/confirm.py",
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
# Distinguishing "discussing the phrasing" from "promising the behavior" needs
# structure, not a keyword list: an earlier version exempted any line containing
# 不, which is so common in Chinese that a promise like
# 「一条命令刷新原型哈希，不必手动改」 slipped straight through. Two structural
# signals only: the phrase is quoted (being cited), or a negation sits
# immediately against it.
_QUOTED = (("「", "」"), ("“", "”"), ("`", "`"), ('"', '"'))
_NEGATORS = ("不会", "不再", "不自动", "不是", "并不", "从不", "never", "no longer",
             "does not", "do not", "doesn't", "don't", "without", "NOT")


def _is_cited(line: str, start: int, end: int) -> bool:
    """The match lies inside a quoted span — the text names the phrase.

    Span containment, not adjacency: a doc may quote a whole sentence as a
    counter-example (「刷新原型哈希，不必手动改」), and the offending words sit
    in the middle of it.
    """
    for open_q, close_q in _QUOTED:
        cursor = 0
        while True:
            open_at = line.find(open_q, cursor)
            if open_at == -1:
                break
            close_at = line.find(close_q, open_at + len(open_q))
            if close_at == -1:
                break
            if open_at < start and end <= close_at:
                return True
            cursor = close_at + len(close_q)
    return False


def _strip_emphasis(text: str) -> str:
    """Drop markdown emphasis so `**不**自动刷新` reads as `不自动刷新`."""
    return re.sub(r"[*_`]+", "", text)


def _is_negated(line: str, start: int, end: int) -> bool:
    """A negation bound to this phrase, not merely present on the line.

    Chinese 不 is only honoured immediately to the left, where it negates the
    matched verb. On the right it usually governs a different clause — that is
    how 「刷新原型哈希，不必手动改」 once escaped as a false promise.
    """
    left = _strip_emphasis(line[max(0, start - 14): start])
    right = _strip_emphasis(line[end: end + 16])
    if any(n in left or n in right for n in _NEGATORS):
        return True
    return left.rstrip().endswith("不") or left.rstrip().endswith("未")


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
            for pattern in _AUTO_REFRESH_CLAIMS:
                m = pattern.search(line)
                if not m:
                    continue
                window = "\n".join(lines[max(0, i - 2): i + 3])
                if "sync" not in window:
                    continue  # a claim about some other command
                # Qualification must be on the same line as the claim. A nearby
                # correct line does not fix a wrong one — and readers often see
                # only one of the two.
                if "attest" in line:
                    continue
                if _is_cited(line, m.start(), m.end()) or _is_negated(line, m.start(), m.end()):
                    continue  # naming or denying the phrase, not promising it
                offenders.append(f"{path.name}:{i + 1}: {line.strip()[:90]}")
                break
    assert not offenders, "sync described as auto-refreshing the prototype hash: " + "; ".join(offenders)


def test_sync_semantics_detector_is_calibrated():
    """The exemption must not swallow real promises.

    Every gate needs its own negative test: the first exemption here keyed on
    any line containing 不, which let 「刷新原型哈希，不必手动改」 pass. A rule
    is only as good as the false-negatives it is proven to reject.
    """
    def flags(line: str) -> bool:
        for pattern in _AUTO_REFRESH_CLAIMS:
            m = pattern.search(line)
            if not m:
                continue
            if "attest" in line:
                return False
            if _is_cited(line, m.start(), m.end()) or _is_negated(line, m.start(), m.end()):
                return False
            return True
        return False

    must_flag = [
        "改完机读后一条命令刷新原型哈希，不必手动改。",
        "sync 会自动刷新原型哈希，不需要额外操作。",
        "# sync 会自动刷新原型哈希，不需要额外操作：",  # shell comment above a correct command
        "sync refreshes the prototype hash so you do not need to think about it.",
        "一条命令同步人读与原型哈希。",
        "specnotary sync：重生成人读 + 刷新原型哈希 + 复跑门禁",
    ]
    must_not_flag = [
        "原型 manifest 哈希**不**自动刷新，须复核后显式背书。",
        "措辞变体（「自动刷新」）也要被检测到。",
        "sync does not refresh the prototype hash on its own.",
        "sync 默认不再刷新原型哈希。",
        "NOTE: prototype hash NOT refreshed — sync does not regenerate the prototype.",
        "改完机读后重新生成人读；原型须显式 `--attest-prototype` 刷新原型哈希。",
        # A whole sentence quoted as a counter-example: the offending words are
        # deep inside the quotes, not adjacent to them.
        "导致「刷新原型哈希，不必手动改」这类真承诺全部漏过。",
    ]
    missed = [s for s in must_flag if not flags(s)]
    false_alarms = [s for s in must_not_flag if flags(s)]
    assert not missed, f"detector misses real false promises: {missed}"
    assert not false_alarms, f"detector flags rule discussion: {false_alarms}"


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
    """Abandoned working names must not appear on the public surface."""
    patterns = (
        re.compile(r"曾用名"),
        re.compile(r"\bFormerly\b"),
        re.compile(r"原工作名"),
        re.compile(r"SpecAnvil"),
        re.compile(r"specanvil", re.I),
        re.compile(r"Spec Kit"),
        re.compile(r"spec-kit-node"),
    )
    stale = []
    scanned = dict(_doc_text())
    lock = ROOT / "cli/node/package-lock.json"
    if lock.is_file():
        scanned[lock] = lock.read_text(encoding="utf-8")
    for path, text in scanned.items():
        for i, line in enumerate(text.splitlines(), 1):
            if any(p.search(line) for p in patterns):
                stale.append(f"{path.name}:{i}")
                break
    assert not stale, "abandoned brand or rename history: " + "; ".join(stale)


def test_english_readme_has_front_door_sections():
    """The English front door must keep the same section anchors as the Chinese one."""
    zh = (ROOT / "README.md").read_text(encoding="utf-8")
    en = (ROOT / "README.en.md").read_text(encoding="utf-8")
    missing = []
    for anchor in ("value", "overview", "demo", "quick-start", "gates", "examples", "structure", "docs"):
        needle = f'id="{anchor}"'
        if needle not in zh:
            missing.append(f"README.md #{anchor}")
        if needle not in en:
            missing.append(f"README.en.md #{anchor}")
    assert not missing, "front-door section missing: " + "; ".join(missing)


def test_no_process_theater():
    """First public surface must not narrate audit rounds or release choreography."""
    forbidden = re.compile(
        r"第[一二三四五六七八九十\d]+轮|红队修复|外部审计发现|九步复核|发布前建设|P0-P2"
    )
    stale = []
    extra = [ROOT / "docs/assets/architecture.svg", ROOT / "scripts/gen_diagrams.py"]
    scanned = dict(_doc_text())
    for path in extra:
        if path.is_file():
            scanned[path] = path.read_text(encoding="utf-8")
    for path, text in scanned.items():
        for i, line in enumerate(text.splitlines(), 1):
            if forbidden.search(line):
                stale.append(f"{path.name}:{i}")
    archive = ROOT / "docs/archive"
    if archive.exists() and any(p.is_file() for p in archive.rglob("*")):
        stale.append("docs/archive must not ship")
    assert not stale, "process narrative on public surface: " + "; ".join(stale)


def test_schema_and_known_top_level_agree():
    """Adding a schema field must show up as a known top-level key, and vice versa.

    `content_hash` is a legacy root alias excluded from the schema on purpose.
    """
    from specnotary.libspec import KNOWN_TOP_LEVEL, load_schema

    schema_keys = set(load_schema().get("properties") or {})
    code_only = {"content_hash"}
    missing_in_known = schema_keys - KNOWN_TOP_LEVEL
    missing_in_schema = KNOWN_TOP_LEVEL - schema_keys - code_only
    assert not missing_in_known, f"schema properties not in KNOWN_TOP_LEVEL: {sorted(missing_in_known)}"
    assert not missing_in_schema, f"KNOWN_TOP_LEVEL not in schema: {sorted(missing_in_schema)}"


def test_shape_sanitizer_matches_schema_containers():
    """Wrong-shape FAIL keys must be the schema's objects and arrays."""
    from specnotary.libspec import _DICT_KEYS, _LIST_KEYS, load_schema

    props = load_schema().get("properties") or {}

    def types_of(key: str) -> set[str]:
        spec = props.get(key) or {}
        raw = spec.get("type")
        if isinstance(raw, list):
            return {str(x) for x in raw}
        return {str(raw)} if raw else set()

    for key in _DICT_KEYS:
        assert key in props, f"_DICT_KEYS {key} is not a schema property"
        assert "object" in types_of(key), f"_DICT_KEYS {key} is not a schema object"
    for key in _LIST_KEYS:
        assert key in props, f"_LIST_KEYS {key} is not a schema property"
        assert "array" in types_of(key), f"_LIST_KEYS {key} is not a schema array"


def test_security_support_matches_package_minor():
    """SECURITY.md '当前 x.y.x' must be this package's minor line."""
    from specnotary import __version__

    text = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    m = re.search(r"当前\s+(\d+\.\d+)\.x", text)
    assert m, "SECURITY.md must declare the supported minor as 当前 N.N.x"
    minor = ".".join(__version__.split(".")[:2])
    assert m.group(1) == minor, f"SECURITY supports {m.group(1)}.x but package is {__version__}"


TESTS = [
    test_documented_subcommands_exist,
    test_documented_flags_exist,
    test_renderer_version_matches_docs,
    test_sync_semantics_not_misstated,
    test_sync_semantics_detector_is_calibrated,
    test_version_is_single_sourced,
    test_lifecycle_diagram_declares_no_transitions,
    test_no_hardcoded_test_counts,
    test_capability_table_commands_runnable,
    test_brand_is_consistent,
    test_english_readme_has_front_door_sections,
    test_no_process_theater,
    test_schema_and_known_top_level_agree,
    test_shape_sanitizer_matches_schema_containers,
    test_security_support_matches_package_minor,
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
