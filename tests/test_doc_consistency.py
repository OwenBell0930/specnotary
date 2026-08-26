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
from specnotary.pm_view import humanize_finding  # noqa: E402

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
    ROOT / "docs/product-quality-model.md",
    ROOT / "docs/product-review-contract.md",
    ROOT / "docs/product-review-corpus.md",
    ROOT / "docs/skill-boundary.md",
    ROOT / "docs/release-checklist.md",
    ROOT / "docs/human-view.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "CHANGELOG.md",
    ROOT / "SECURITY.md",
    ROOT / "skills/specnotary/SKILL.md",
    ROOT / "skills/specnotary-draft/SKILL.md",
    ROOT / "skills/specnotary-review/SKILL.md",
    ROOT / "skills/specnotary-gate/SKILL.md",
    ROOT / "commands/write-spec.md",
    ROOT / "commands/draft-spec.md",
    ROOT / "commands/review-spec.md",
    ROOT / "commands/gate-spec.md",
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


def test_front_door_states_audience_and_tools():
    """Audience and recommended tools must be visible above the first thematic break."""
    specs = (
        ("README.md", "产品经理", ("Cursor", "Codex", "github.com/OwenBell0930/specnotary", "工作区")),
        ("README.en.md", "product manager", ("Cursor", "Codex", "github.com/OwenBell0930/specnotary", "workspace")),
    )
    missing = []
    for name, audience, tools in specs:
        head = (ROOT / name).read_text(encoding="utf-8").split("\n---\n", 1)[0]
        if audience.lower() not in head.lower():
            missing.append(f"{name} top must name {audience}")
        for tool in tools:
            if tool not in head:
                missing.append(f"{name} top must name {tool}")
    assert not missing, "; ".join(missing)


def test_public_positioning_stays_review_ready():
    """Public surfaces must not drift back into implementation/test hand-off claims."""
    paths = (
        ROOT / "README.md",
        ROOT / "README.en.md",
        ROOT / "docs/assets/hero-banner.svg",
        ROOT / "docs/assets/ipo-flow.svg",
    )
    forbidden = (
        "Dev-ready specs",
        "Construction-grade human",
        "Construction view",
        "build from this table",
        "按这张表开发",
    )
    stale = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for phrase in forbidden:
            if phrase in text:
                stale.append(f"{path.name}: {phrase}")
    assert not stale, "public positioning crossed the PM review boundary: " + "; ".join(stale)


def test_playground_does_not_mislabel_draft_as_pass():
    """The zero-install demo must preserve the CLI's FAIL/DRAFT/PASS semantics."""
    text = (ROOT / "playground/index.html").read_text(encoding="utf-8")
    assert '"result": verdict' in text
    assert 'v.result === "DRAFT"' in text
    assert "RESULT: DRAFT" in text
    assert "评审就绪的方案示例" in text
    assert 'review: "../examples/case-order-cancel-ops-faq/machine/spec.yaml"' in text
    assert "#btn-human{margin-left:auto}" in text
    assert "checkCurrentSource" in text
    assert "还没有可检查的需求" in text
    assert 'id="human-preview"' in text
    assert 'id="human-edit"' in text
    assert "renderMarkdown" in text
    assert "body.human-mode #source-panel" in text
    assert '"ready_gap": [humanize_finding(g) for g in gap]' in text
    assert "终稿还缺少参与角色" in humanize_finding("status=ready requires actors")
    assert "功能 B1 的预期结果太笼统" in humanize_finding(
        "behavior B1: then-clause too vague for ready"
    )
    assert "原型决策" in humanize_finding(
        "status=ready requires D-PROTOTYPE: decide whether an interactive prototype is needed and choose its carrier"
    )


def test_public_playground_entry_opens_the_rendered_app():
    """Public links must open Pages, and Pages must not fetch Jekyll-excluded files."""
    live = "https://owenbell0930.github.io/specnotary/playground/"
    for name in ("README.md", "README.en.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert live in text, f"{name} must link to the rendered Playground"
        assert "](playground/index.html)" not in text, f"{name} links to source instead of GUI"

    page = (ROOT / "playground/index.html").read_text(encoding="utf-8")
    sources = page.split("const SOURCES =", 1)[1].split("];", 1)[0]
    assert '"__init__.py"' not in sources, "Jekyll excludes __init__.py from Pages"
    assert 'FS.writeFile("/lib/specnotary/__init__.py", "")' in page
    assert 'href="https://github.com/OwenBell0930/specnotary"' in page


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


def test_cursor_plugin_manifest_is_valid():
    """Plugin manifest paths exist and Skill/Command frontmatter names match directories.

    This proves packaging layout and discoverable filenames for Cursor's
    skills/commands directories — not that Marketplace hosting or runtime
    injection already works for every Cursor build.
    """
    import json
    import re as _re

    manifest_path = ROOT / ".cursor-plugin" / "plugin.json"
    assert manifest_path.is_file(), "missing .cursor-plugin/plugin.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data.get("name") == "specnotary"
    skills_dir = ROOT / data.get("skills", "skills")
    commands_dir = ROOT / data.get("commands", "commands")
    assert skills_dir.is_dir(), f"manifest skills path missing: {skills_dir}"
    assert commands_dir.is_dir(), f"manifest commands path missing: {commands_dir}"
    logo = ROOT / data["logo"]
    assert logo.is_file(), f"plugin logo missing: {data['logo']}"
    assert not (ROOT / "mcp.json").is_file(), "MCP is not the product path; do not ship mcp.json in the plugin"

    def frontmatter(path: Path) -> dict[str, str]:
        text = path.read_text(encoding="utf-8")
        m = _re.match(r"^---\n(.*?)\n---\n", text, _re.DOTALL)
        assert m, f"missing YAML frontmatter: {path}"
        block = m.group(1)
        name_m = _re.search(r"^name:\s*(\S+)", block, _re.M)
        desc_m = _re.search(r"^description:\s*>?\s*(.*)", block, _re.M)
        assert name_m and desc_m, f"frontmatter needs name+description: {path}"
        desc = desc_m.group(1).strip()
        if desc_m.group(0).rstrip().endswith(">"):
            # folded block: take following indented lines until blank/non-indented
            lines = []
            after = block.split("description:", 1)[1]
            for line in after.splitlines()[1:]:
                if line.startswith("  ") or line.startswith("\t"):
                    lines.append(line.strip())
                elif line.strip() == "":
                    if lines:
                        break
                else:
                    break
            desc = " ".join(lines) if lines else desc
        assert desc, f"empty description: {path}"
        return {"name": name_m.group(1).strip(), "description": desc}

    for skill in (
        "specnotary",
        "specnotary-draft",
        "specnotary-review",
        "specnotary-gate",
    ):
        path = skills_dir / skill / "SKILL.md"
        assert path.is_file(), f"missing skill: {skill}"
        meta = frontmatter(path)
        assert meta["name"] == skill, f"skill name {meta['name']!r} != dir {skill!r}"

    for cmd in ("write-spec", "draft-spec", "review-spec", "gate-spec"):
        path = commands_dir / f"{cmd}.md"
        assert path.is_file(), f"missing command: {cmd}"
        meta = frontmatter(path)
        assert meta["name"] == cmd, f"command name {meta['name']!r} != file {cmd!r}"


def test_product_quality_model_is_single_sourced():
    """Draft/Review must point at one model doc; skills must not embed a second full copy."""
    model = ROOT / "docs/product-quality-model.md"
    assert model.is_file()
    body = model.read_text(encoding="utf-8")
    for needle in (
        "goals_and_core",
        "boundary",
        "architecture",
        "flow",
        "ux",
        "PRODUCT_REVIEW: REVISE",
        "REVIEWABLE",
        "产品方案合理",
    ):
        assert needle in body, f"quality model missing {needle}"
    assert "Structure Gate 通过" in body and "产品方案合理" in body
    for skill in (
        ROOT / "skills/specnotary-draft/SKILL.md",
        ROOT / "skills/specnotary-review/SKILL.md",
        ROOT / "skills/specnotary/SKILL.md",
    ):
        text = skill.read_text(encoding="utf-8")
        assert "product-quality-model.md" in text, f"{skill.name} must cite the shared model"
        assert text.count("goals_and_core") <= 2, f"{skill.name} looks like a duplicated model"


def test_product_review_contract_and_corpus():
    """Review contract + anti-corpus exist for Agent/human eval; not a fake LLM unit proof."""
    contract = (ROOT / "docs/product-review-contract.md").read_text(encoding="utf-8")
    corpus = (ROOT / "docs/product-review-corpus.md").read_text(encoding="utf-8")
    for field in (
        "id",
        "dimension",
        "severity",
        "observation",
        "impact",
        "direction",
        "confidence",
        "requires_decision",
        "source_fidelity",
        "unavailable",
        "content_hash",
        "source_materials",
        "validity",
        "stale",
    ):
        assert field in contract, f"contract missing {field}"
    assert "禁止" in contract and "PASS" in contract
    for anti in ("ANTI-01", "ANTI-02", "ANTI-03", "ANTI-04", "ANTI-05"):
        assert anti in corpus, f"corpus missing {anti}"
    assert "Structure Gate 通过不等于产品方案合理" in corpus


def _load_product_review_schema():
    import json

    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover
        raise AssertionError("jsonschema required") from exc
    schema = json.loads(
        (ROOT / "src/specnotary/schemas/product-review.schema.json").read_text(encoding="utf-8")
    )
    return jsonschema, schema


def _fixture_review():
    import copy

    import yaml

    raw = yaml.safe_load(
        (ROOT / "examples/product-review-fixture/reports/product-review.yaml").read_text(
            encoding="utf-8"
        )
    )
    return copy.deepcopy(raw)


def test_product_review_schema_accepts_fixture():
    """Fixture validates; negative shapes fail; MD projection matches YAML minimally."""
    import hashlib

    jsonschema, schema = _load_product_review_schema()
    fixture = _fixture_review()
    jsonschema.validate(instance=fixture, schema=schema)

    subject = ROOT / fixture["subject"]["path"]
    digest = hashlib.sha256(subject.read_bytes()).hexdigest()
    assert fixture["subject"]["content_hash"] == digest, "fixture hash must match subject file"

    md = (ROOT / "examples/product-review-fixture/reports/product-review.md").read_text(
        encoding="utf-8"
    )
    assert f"PRODUCT_REVIEW: {fixture['verdict']}" in md
    assert fixture["subject"]["content_hash"] in md
    assert fixture["gate_note"]["zh"] in md
    for finding in fixture["findings"]:
        assert finding["id"] in md, f"MD missing finding id {finding['id']}"

    def must_fail(mutator, label: str):
        bad = _fixture_review()
        mutator(bad)
        try:
            jsonschema.validate(instance=bad, schema=schema)
        except jsonschema.ValidationError:
            return
        raise AssertionError(f"schema must reject {label}")

    must_fail(lambda d: d.__setitem__("verdict", "PASS"), "verdict PASS")

    def empty_evidence(d):
        f = dict(d["findings"][0])
        f["evidence"] = ""
        f.pop("spec_refs", None)
        d["findings"] = [f]

    must_fail(empty_evidence, "empty evidence string")

    def drop_summary_zh(d):
        d["summary"] = {"en": "only english"}

    must_fail(drop_summary_zh, "missing summary.zh")

    def aligned_without_materials(d):
        d["source_fidelity"] = "aligned"
        d["source_materials"] = []

    must_fail(aligned_without_materials, "aligned without source_materials")

    def contradictory_reviewable(d):
        d["verdict"] = "REVIEWABLE"
        d["findings"] = [
            {
                **d["findings"][0],
                "severity": "blocker",
                "requires_decision": False,
            }
        ]

    must_fail(contradictory_reviewable, "REVIEWABLE with blocker")

    def revise_without_major(d):
        d["verdict"] = "REVISE"
        # keep only minor
        d["findings"] = [{**d["findings"][0], "severity": "minor", "requires_decision": False}]

    must_fail(revise_without_major, "REVISE without blocker/major")


def test_orchestrator_separates_three_verdicts():
    """Default full flow must require separate Draft / Product Review / Structure Gate status."""
    text = (ROOT / "skills/specnotary/SKILL.md").read_text(encoding="utf-8")
    for needle in (
        "DRAFT_STATUS",
        "PRODUCT_REVIEW",
        "STRUCTURE_GATE",
        "specnotary-draft",
        "specnotary-review",
        "specnotary-gate",
        "跳过 Draft",
        "重新 Review",
        "content_hash",
        "stale",
    ):
        assert needle in text, f"orchestrator missing {needle}"
    gate = (ROOT / "skills/specnotary-gate/SKILL.md").read_text(encoding="utf-8")
    assert "伪造" in gate and "Markdown" in gate, "gate skill must refuse hard PASS on plain Markdown"
    assert "不能覆盖" in gate or "不能**覆盖" in gate or "不能覆盖" in gate.replace("*", "")
    draft = (ROOT / "skills/specnotary-draft/SKILL.md").read_text(encoding="utf-8")
    assert "不跑 Product Review" in draft


def test_product_review_requires_re_review_after_change():
    """Docs/skills must bind Product Review to subject hash and require re-review after edits."""
    paths = (
        ROOT / "docs/product-review-contract.md",
        ROOT / "skills/specnotary/SKILL.md",
        ROOT / "skills/specnotary-review/SKILL.md",
        ROOT / "commands/write-spec.md",
        ROOT / "commands/review-spec.md",
    )
    required = (
        "content_hash",
        "stale",
        "重新 Review",
    )
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for needle in required:
            assert needle in text, f"{path.name} missing {needle}"
    contract = (ROOT / "docs/product-review-contract.md").read_text(encoding="utf-8")
    assert "source_materials" in contract
    assert "不能覆盖" in contract or "不能**覆盖" in contract
    proof = (ROOT / "docs/proof-boundary.md").read_text(encoding="utf-8")
    assert "独立审查" in proof
    assert "新上下文" in proof or "人工复核" in proof


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
    test_front_door_states_audience_and_tools,
    test_public_positioning_stays_review_ready,
    test_playground_does_not_mislabel_draft_as_pass,
    test_public_playground_entry_opens_the_rendered_app,
    test_english_readme_has_front_door_sections,
    test_no_process_theater,
    test_schema_and_known_top_level_agree,
    test_shape_sanitizer_matches_schema_containers,
    test_cursor_plugin_manifest_is_valid,
    test_product_quality_model_is_single_sourced,
    test_product_review_contract_and_corpus,
    test_product_review_schema_accepts_fixture,
    test_orchestrator_separates_three_verdicts,
    test_product_review_requires_re_review_after_change,
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
