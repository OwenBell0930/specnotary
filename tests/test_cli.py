#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "cli" / "run-check.sh"
sys.path.insert(0, str(ROOT / "src"))
from specnotary.libproto import classify_proto_issues, validate_prototype  # noqa: E402
from specnotary.libspec import load_spec, ready_gap, render_human, spec_hash, validate  # noqa: E402


def run(path: Path, *args: str) -> tuple[int, str]:
    """Gate a spec in-process and capture its report.

    Spawning bash + a fresh interpreter per assertion cost the suite minutes;
    the wrapper script itself is covered end-to-end by
    test_wrapper_scripts_end_to_end.
    """
    import contextlib
    import io

    from specnotary.check import main as check_main

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = check_main([str(path), *args])
    return code, buf.getvalue()


def test_wrapper_scripts_end_to_end():
    """The bash wrappers must stay runnable (PYTHONPATH wiring, exit codes)."""
    ok = subprocess.run(
        ["bash", str(CHECK), str(RAW)], capture_output=True, text=True
    )
    assert ok.returncode == 0, ok.stdout + ok.stderr
    assert "RESULT: PASS" in ok.stdout
    bad = subprocess.run(
        ["bash", str(CHECK), str(ROOT / "examples/case-order-cancel-bad/machine/spec.yaml")],
        capture_output=True, text=True,
    )
    assert bad.returncode == 1, bad.stdout + bad.stderr
    assert "RESULT: FAIL" in bad.stdout


def test_order_raw_pass():
    code, out = run(ROOT / "examples/case-order-cancel-raw/machine/spec.yaml")
    assert code == 0, out
    assert "RESULT: PASS" in out
    assert "FAIL_COUNT: 0" in out


def test_order_bad_fail():
    code, out = run(ROOT / "examples/case-order-cancel-bad/machine/spec.yaml")
    assert code == 1, out
    assert "RESULT: FAIL" in out
    assert "FAIL:" in out


def test_order_fixed_pass():
    code, out = run(ROOT / "examples/case-order-cancel-bad/machine/spec.fixed.yaml")
    assert code == 0, out
    assert "RESULT: PASS" in out


def test_order_faq_pass():
    code, out = run(ROOT / "examples/case-order-cancel-ops-faq/machine/spec.yaml")
    assert code == 0, out
    assert "RESULT: PASS" in out


def test_list_search_pass():
    code, out = run(ROOT / "examples/case-list-search/machine/spec.yaml")
    assert code == 0, out
    assert "RESULT: PASS" in out


def test_status_banana_fail():
    text = (ROOT / "examples/case-list-search/machine/spec.yaml").read_text(encoding="utf-8")
    text = text.replace("status: ready", "status: banana", 1)
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        f.write(text)
        path = Path(f.name)
    try:
        code, out = run(path)
        assert code == 1, out
        assert "FAIL" in out
        assert "banana" in out.lower() or "schema" in out.lower() or "status" in out.lower()
    finally:
        path.unlink(missing_ok=True)


def test_missing_behavior_ref_fail():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    data["acceptance"][0]["behavior"] = "B-NOT-EXIST"
    result = validate(data, {})
    assert any("behavior ref missing" in e for e in result["fail"]), result


def test_missing_actor_ref_fail():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    data["permissions"][0]["actor"] = "ghost_role"
    result = validate(data, {})
    assert any("missing actor" in e for e in result["fail"]), result


def test_generate_human_has_wireframe_and_controls():
    src = ROOT / "examples/case-order-cancel-raw/machine/spec.yaml"
    out = ROOT / "examples/case-order-cancel-raw/human/spec.md"
    p = subprocess.run(
        ["bash", str(ROOT / "cli" / "run-generate-human.sh"), str(src), str(out)],
        capture_output=True,
        text=True,
    )
    assert p.returncode == 0, p.stdout + p.stderr
    text = out.read_text(encoding="utf-8")
    assert "线框" in text or "wireframe" in text.lower() or "订单详情" in text
    assert "控件" in text
    assert "AC-01" in text
    assert "Pending" in text or "待闭合" in text
    assert "action" in text.lower() or "允许动作" in text


def test_generate_human_refuses_fail_without_flag():
    src = ROOT / "examples/case-order-cancel-bad/machine/spec.yaml"
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "out.md"
        p = subprocess.run(
            ["bash", str(ROOT / "cli" / "run-generate-human.sh"), str(src), str(out)],
            capture_output=True,
            text=True,
        )
        assert p.returncode == 1, p.stdout + p.stderr
        assert not out.exists()
        assert "refuse" in (p.stdout + p.stderr).lower() or "FAIL" in (p.stdout + p.stderr)


def test_omitted_claim_fail():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    data["source_claims"] = list(data.get("source_claims") or []) + [
        {
            "id": "SRC-CLM-OMIT",
            "source_ref": "SRC-LS-001",
            "quote_or_summary": "必须支持部分取消",
            "disposition": "omitted",
        }
    ]
    result = validate(data, {})
    assert any("omitted" in e for e in result["fail"]), result


def test_assumption_claim_warn():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    result = validate(data, {})
    assert result["fail"] == [], result
    assert any("assumption" in w for w in result["warn"]), result


def test_conflict_unclosed_fail():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    data["source_claims"] = list(data.get("source_claims") or []) + [
        {
            "id": "SRC-CLM-CF",
            "source_ref": "SRC-LS-001",
            "quote_or_summary": "原料A说回券，原料B说不回券",
            "disposition": "conflict",
        }
    ]
    result = validate(data, {})
    assert any("conflict" in e for e in result["fail"]), result


def test_covered_without_refs_fail():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    data["source_claims"] = [
        {
            "id": "SRC-CLM-EMPTY",
            "source_ref": "SRC-LS-001",
            "quote_or_summary": "要能搜",
            "disposition": "covered",
            "spec_refs": [],
        }
    ]
    result = validate(data, {})
    assert any("spec_refs is empty" in e for e in result["fail"]), result


def test_human_stale_after_hand_edit():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    with tempfile.TemporaryDirectory() as td:
        human = Path(td) / "spec.md"
        human.write_text(render_human(data, source="mem"), encoding="utf-8")
        ok = validate(data, {}, human_path=human)
        assert ok["fail"] == [], ok
        human.write_text(human.read_text(encoding="utf-8") + "\n<!-- tamper -->\n", encoding="utf-8")
        data2 = dict(data)
        data2["defaults"] = {**(data.get("defaults") or {}), "page_size": 99}
        stale = validate(data2, {}, human_path=human)
        assert any("stale" in e for e in stale["fail"]), stale


def test_human_body_edit_fail():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    with tempfile.TemporaryDirectory() as td:
        human = Path(td) / "spec.md"
        text = render_human(data, source="mem")
        assert "本期做" in text
        human.write_text(text.replace("本期做", "本期做（手改）", 1), encoding="utf-8")
        result = validate(data, {}, human_path=human)
        assert any("body" in e for e in result["fail"]), result


def test_ready_empty_claims_fail():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    data["source_claims"] = []
    result = validate(data, {})
    assert any("source_claims missing" in e for e in result["fail"]), result


def test_spec_ref_must_be_spec_entity():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    data["source_claims"] = [
        {
            "id": "SRC-CLM-BADREF",
            "source_ref": "SRC-LS-001",
            "quote_or_summary": "covered via source id",
            "disposition": "covered",
            "spec_refs": ["SRC-LS-001"],
        }
    ]
    result = validate(data, {})
    assert any("not a spec entity" in e for e in result["fail"]), result


def test_explicit_missing_human_fail():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    result = validate(data, {}, human_path=Path("/tmp/specnotary-no-such-human.md"))
    assert any("human spec missing" in e for e in result["fail"]), result


def test_node_runtime_refuses_hard_pass():
    env = {**os.environ, "SPECNOTARY_RUNTIME": "node"}
    p = subprocess.run(
        ["bash", str(CHECK), str(ROOT / "examples/case-list-search/machine/spec.yaml")],
        capture_output=True,
        text=True,
        env=env,
    )
    out = p.stdout + p.stderr
    assert p.returncode == 3, out
    assert "RESULT: PASS" not in out
    assert "gate_mode: hard" not in out
    assert "Deferred" in out or "cannot produce a hard PASS" in out


def test_human_missing_hash_fail():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    with tempfile.TemporaryDirectory() as td:
        human = Path(td) / "spec.md"
        human.write_text("# handmade\n\nno hash\n", encoding="utf-8")
        result = validate(data, {}, human_path=human)
        assert any("missing spec_hash" in e for e in result["fail"]), result


def test_report_lists_dispositions():
    src = ROOT / "examples/case-list-search/machine/spec.yaml"
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "report.md"
        p = subprocess.run(
            ["bash", str(ROOT / "cli" / "run-report.sh"), str(src), str(out)],
            capture_output=True,
            text=True,
        )
        assert p.returncode == 0, p.stdout + p.stderr
        text = out.read_text(encoding="utf-8")
        assert "输出自检报告" in text
        assert "已写入规格" in text
        assert "原文没写、规格补了猜测" in text
        assert "| covered |" not in text
        assert "| assumption |" not in text
        assert spec_hash(load_spec(src)) in text


def test_self_check_report_is_pm_readable():
    """The report a product manager takes to review must not lead with machine English."""
    from specnotary.report import build_report

    md, result = build_report(RAW)
    assert md.lstrip().startswith("# 输出自检报告"), md.splitlines()[0]
    assert "需要你拍板" in md
    assert "必须改" in md
    assert "原料条目编号" in md
    assert "处理结果" in md
    assert "落到说明书的哪一段" in md
    assert "结构通过。RESULT: PASS" in md
    assert "已写入规格" in md
    assert "原文没写、规格补了猜测" in md
    assert "页面控件「取消订单」" in md
    assert "功能「取消待支付订单」" in md
    assert "| covered |" not in md
    assert "| assumption |" not in md
    assert "| omitted |" not in md
    assert "WARN:" not in md
    assert "FAIL：" not in md  # Chinese fullwidth mixed with FAIL as a row label
    assert not result["fail"]


def test_generate_list_search_human():
    src = ROOT / "examples/case-list-search/machine/spec.yaml"
    out = ROOT / "examples/case-list-search/human/spec.md"
    p = subprocess.run(
        ["bash", str(ROOT / "cli" / "run-generate-human.sh"), str(src), str(out)],
        capture_output=True,
        text=True,
    )
    assert p.returncode == 0, p.stdout + p.stderr
    text = out.read_text(encoding="utf-8")
    assert "submit_search" in text
    assert "状态与允许动作" in text
    assert "已写入规格" in text
    assert "| `assumption` |" not in text
    assert "已定稿" in text


RAW = ROOT / "examples/case-order-cancel-raw/machine/spec.yaml"
ALIGN = ROOT / "examples/case-order-cancel-raw/prototype/prototype.manifest.yaml"
DRIFT = ROOT / "examples/case-order-cancel-raw/prototype-drift/prototype.manifest.yaml"


def test_aligned_prototype_pass():
    data = load_spec(RAW)
    result = validate(data, {}, spec_path=RAW, manifest_path=ALIGN)
    proto_fails = [e for e in result["fail"] if e.startswith("prototype")]
    assert proto_fails == [], result
    code, out = run(RAW)
    assert code == 0, out
    assert "prototype:" in out


def test_drift_missing_required_control():
    data = load_spec(RAW)
    result = validate(data, {}, spec_path=RAW, manifest_path=DRIFT)
    assert any("required control not mapped: btn_cancel" in e for e in result["fail"]), result


def test_drift_unknown_spec_ref():
    data = load_spec(RAW)
    result = validate(data, {}, spec_path=RAW, manifest_path=DRIFT)
    assert any("CTRL-NOT-EXIST" in e for e in result["fail"]), result


def test_drift_stale_hash():
    data = load_spec(RAW)
    result = validate(data, {}, spec_path=RAW, manifest_path=DRIFT)
    assert any("prototype stale" in e for e in result["fail"]), result


def test_drift_extra_business_action():
    data = load_spec(RAW)
    result = validate(data, {}, spec_path=RAW, manifest_path=DRIFT)
    assert any("PROTO-PAYOUT" in e or "PROTO-FLOW-PAYOUT" in e for e in result["fail"]), result


def test_decoration_without_refs_ok():
    data = load_spec(RAW)
    manifest = load_spec(ALIGN)
    result = validate_prototype(data, manifest, manifest_path=ALIGN)
    assert not any("PROTO-DECO" in e or "decoration" in e.lower() for e in result["fail"]), result


def test_semantic_warning_is_warn():
    data = load_spec(RAW)
    result = validate(data, {}, spec_path=RAW, manifest_path=DRIFT)
    assert any("unverified" in w for w in result["warn"]), result
    buckets = classify_proto_issues(result["fail"], result["warn"])
    assert buckets["unverified"]
    assert buckets["stale"]
    assert buckets["missing"]
    assert buckets["extra"]


def test_ready_placeholder_ui_fail():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    data["ui"] = {"_": 1}
    result = validate(data, {})
    assert any("ui.wireframe" in e or "ui.controls" in e for e in result["fail"]), result


def test_ready_empty_then_fail():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    data["behaviors"][0]["then"] = {"zh": ""}
    result = validate(data, {})
    assert any("then is empty" in e for e in result["fail"]), result


def test_html_comment_not_a_hit():
    data = load_spec(RAW)
    manifest = load_spec(ALIGN)
    with tempfile.TemporaryDirectory() as td:
        html = Path(td) / "order-detail.html"
        html.write_text("<!-- <button data-spec-id='btn_cancel'></button> -->\n<div></div>\n", encoding="utf-8")
        man = Path(td) / "prototype.manifest.yaml"
        man.write_text(ALIGN.read_text(encoding="utf-8"), encoding="utf-8")
        result = validate_prototype(data, manifest, manifest_path=man)
        assert any("not found in html" in e for e in result["fail"]), result


def test_role_escape_extra_fail():
    data = load_spec(RAW)
    manifest = load_spec(ALIGN)
    screens = manifest.get("screens") or []
    screens[0].setdefault("controls", []).append(
        {"id": "PROTO-GHOST-BTN", "role": "primary_button", "spec_refs": []}
    )
    result = validate_prototype(data, manifest, manifest_path=ALIGN)
    assert any("PROTO-GHOST-BTN" in e and "extra" in e for e in result["fail"]), result


def test_source_path_missing_fail():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    data["sources"][0]["path"] = "../input/no-such-file.txt"
    result = validate(
        data, {}, spec_path=ROOT / "examples/case-list-search/machine/spec.yaml"
    )
    assert any("path missing" in e for e in result["fail"]), result


def test_ready_no_covered_fail():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    data["source_claims"] = [
        {
            "id": "SRC-CLM-ONLY-ASSUME",
            "source_ref": "SRC-LS-001",
            "quote_or_summary": "先猜一个默认分页",
            "disposition": "assumption",
            "spec_refs": ["defaults.page_size"],
        }
    ]
    result = validate(data, {})
    assert any("at least one covered" in e for e in result["fail"]), result


def test_uncovered_behavior_fail():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    for claim in data.get("source_claims") or []:
        refs = [r for r in (claim.get("spec_refs") or []) if r != "B2"]
        claim["spec_refs"] = refs
    result = validate(data, {})
    assert any("coverage missing for behavior B2" in e for e in result["fail"]), result


def test_node_generate_refuses_hard_stamp():
    p = subprocess.run(
        ["node", str(ROOT / "cli" / "node" / "generate_human.js"), str(RAW)],
        capture_output=True,
        text=True,
    )
    out = p.stdout + p.stderr
    assert p.returncode == 3, out
    assert "gate_mode: hard" not in out or "cannot stamp" in out


def test_template_draft_passes_gate():
    code, out = run(ROOT / "templates/machine/spec.template.yaml")
    assert code == 0, out
    assert "RESULT: PASS" in out


def test_renderer_version_stale():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    with tempfile.TemporaryDirectory() as td:
        human = Path(td) / "spec.md"
        text = render_human(data, source="mem")
        text = text.replace("<!-- renderer_version: ", "<!-- renderer_version: 0", 1)
        human.write_text(text, encoding="utf-8")
        result = validate(data, {}, human_path=human)
        assert any("renderer v" in e for e in result["fail"]), result


def test_explain_ready_gap():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    data["status"] = "draft"
    data["defaults"] = {}
    gap = ready_gap(data, {})
    assert any("defaults" in g for g in gap), gap
    result = validate(data, {})
    assert result["fail"] == [], result


def test_explain_flag_prints_gap():
    with tempfile.TemporaryDirectory() as td:
        case = Path(td) / "case"
        shutil.copytree(ROOT / "examples/case-list-search", case)
        shutil.rmtree(case / "human")
        spec = case / "machine" / "spec.yaml"
        text = spec.read_text(encoding="utf-8")
        spec.write_text(text.replace("status: ready", "status: draft", 1), encoding="utf-8")
        p = subprocess.run(
            ["bash", str(CHECK), str(spec), "--explain"],
            capture_output=True,
            text=True,
        )
        out = p.stdout + p.stderr
        assert p.returncode == 0, out
        assert "READY_GAP_COUNT:" in out
        assert "READY-GAP:" in out


def test_in_scope_required_for_ready():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    data["in_scope"] = []
    result = validate(data, {})
    assert any("in_scope" in e for e in result["fail"]), result


def test_interaction_broken_link_fail():
    data = load_spec(RAW)
    manifest = load_spec(ALIGN)
    manifest["interactions"][0]["trigger"] = "PROTO-GHOST-TRIGGER"
    result = validate_prototype(data, manifest, manifest_path=ALIGN)
    assert any("link broken" in e for e in result["fail"]), result


def test_sync_roundtrip_requires_attest():
    with tempfile.TemporaryDirectory() as td:
        case = Path(td) / "case"
        shutil.copytree(ROOT / "examples/case-order-cancel-raw", case)
        spec = case / "machine" / "spec.yaml"
        text = spec.read_text(encoding="utf-8")
        assert "refund_path: original" in text
        spec.write_text(text.replace("refund_path: original", "refund_path: original_channel", 1), encoding="utf-8")
        stale_code, stale_out = run(spec)
        assert stale_code == 1, stale_out
        assert "stale" in stale_out
        # Plain sync regenerates the human but must NOT re-certify the prototype.
        # Asserting only the exit code once let a real bug hide here: the human
        # view was not regenerated at all. Assert the artifact, not just the code.
        human = case / "human" / "spec.md"
        p = subprocess.run(
            ["bash", str(ROOT / "cli" / "run-sync.sh"), str(spec)],
            capture_output=True,
            text=True,
        )
        assert p.returncode == 1, p.stdout + p.stderr
        assert "NOT refreshed" in p.stdout + p.stderr
        assert "original_channel" in human.read_text(encoding="utf-8"), (
            "plain sync must regenerate the human view — a stale prototype is a "
            "separate concern and must not block the derivation"
        )
        assert "needs re-attestation" in p.stdout
        code, out = run(spec)
        assert code == 1, out
        assert "prototype stale" in out
        # Explicit attestation is the only way to re-certify.
        p2 = subprocess.run(
            ["bash", str(ROOT / "cli" / "run-sync.sh"), str(spec), "--attest-prototype"],
            capture_output=True,
            text=True,
        )
        assert p2.returncode == 0, p2.stdout + p2.stderr
        assert "attested" in p2.stdout + p2.stderr
        code2, out2 = run(spec)
        assert code2 == 0, out2
        assert "RESULT: PASS" in out2


def test_quoted_ui_label_not_vague():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    data["behaviors"][0]["when"] = {"zh": "点击「智能识别」按钮"}
    result = validate(data, {})
    assert not any("too vague" in e for e in result["fail"]), result
    data["behaviors"][0]["when"] = {"zh": "智能地快速搜索"}
    result2 = validate(data, {})
    assert any("too vague" in e for e in result2["fail"]), result2


def test_dangling_ref_fail_on_ready():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    data["states"]["action_matrix"][0]["zh"] = "可提交关键词（二次确认见 P-99）"
    result = validate(data, {})
    assert any("dangling reference: P-99" in e for e in result["fail"]), result
    data["status"] = "draft"
    result2 = validate(data, {})
    assert any("dangling reference: P-99" in w for w in result2["warn"]), result2


def test_declared_ref_in_text_ok():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    data["states"]["action_matrix"][0]["zh"] = "可提交关键词（对应 AC-01）"
    result = validate(data, {})
    assert not any("dangling" in e for e in result["fail"]), result


def test_spa_source_markers_and_comments():
    from specnotary.libproto import _html_spec_ids
    from specnotary.markers import scan_markers
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "Toc.tsx"
        src.write_text(
            '// data-spec-id="ghost_line"\n'
            '/* <button data-spec-id="ghost_block" /> */\n'
            'export const B = () => (<button data-spec-id="btn_search">搜</button>);\n',
            encoding="utf-8",
        )
        ids = _html_spec_ids(src)
        assert ids == {"btn_search"}, ids
        found = scan_markers(Path(td))
        assert "btn_search" in found and "ghost_line" not in found, found


def test_markers_command_reconciles():
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "page.html").write_text(
            '<button data-spec-id="inp_keyword"></button>'
            '<div data-spec-id="not_in_spec"></div>',
            encoding="utf-8",
        )
        env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
        p = subprocess.run(
            [sys.executable, "-m", "specnotary.markers",
             str(ROOT / "examples/case-list-search/machine/spec.yaml"), td],
            capture_output=True, text=True, env=env,
        )
        out = p.stdout + p.stderr
        assert p.returncode == 0, out
        assert "ok inp_keyword" in out
        assert "?? not_in_spec" in out
        assert "btn_search" in out  # required but unmarked


def test_human_view_toc_overview_and_diagrams():
    text = (ROOT / "examples/case-order-cancel-raw/human/spec.md").read_text(encoding="utf-8")
    assert "## 目录" in text
    assert "概览" in text and "设计原则" in text
    assert text.count("```mermaid") >= 2  # architecture + state set
    # v4: no auto main-path chain — behaviors are often branches, not a sequence
    assert "flowchart TD" not in text
    # v5: the state diagram lists states without asserting transitions
    assert "不表示转移" in text
    state_block = text.split("```mermaid")[2].split("```")[0]
    assert "-->" not in state_block, "state set diagram must not draw transitions"
    assert "职责边界" in text and "不负责" in text


def test_v3_data_contract_error_codes_decisions():
    text = (ROOT / "examples/case-order-cancel-raw/human/spec.md").read_text(encoding="utf-8")
    assert "CancelRequest" in text and "数据契约" in text
    assert "CANCEL_NOT_ALLOWED" in text and "错误码" in text
    assert "决策记录" in text and "D-01" in text


def test_decision_undecided_blocks_ready():
    data = load_spec(RAW)
    data["decisions"] = list(data.get("decisions") or []) + [
        {"id": "D-99", "question": {"zh": "还没拍板的问题"}, "status": "pending"}
    ]
    result = validate(data, {})
    assert any("D-99 undecided" in e for e in result["fail"]), result


def test_decision_decided_passes():
    data = load_spec(RAW)
    result = validate(data, {})
    assert not any("undecided" in e for e in result["fail"]), result


def test_overview_missing_warns_on_ready():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    data.pop("overview", None)
    result = validate(data, {})
    assert any("overview missing" in w for w in result["warn"]), result


def test_data_contract_claimable():
    data = load_spec(RAW)
    data["source_claims"] = list(data.get("source_claims") or []) + [
        {
            "id": "SRC-CLM-DC",
            "source_ref": "SRC-001",
            "quote_or_summary": "取消请求需幂等",
            "disposition": "covered",
            "spec_refs": ["CancelRequest"],
        }
    ]
    result = validate(data, {})
    assert not any("not a spec entity" in e for e in result["fail"]), result


def test_malformed_shapes_never_crash():
    base = {
        "spec_version": "0.1", "id": "X", "title": {"zh": "t"}, "status": "draft",
        "behaviors": [{"id": "B1"}], "acceptance": [{"id": "AC-01"}],
    }
    mutations = [
        {"ui": "字符串"}, {"states": [1, 2]}, {"behaviors": {"id": "B1"}},
        {"defaults": "str"}, {"object_ai": 3}, {"overview": ["x"]},
        {"acceptance": "nope"}, {"pending": {"id": "P-01"}}, {"title": ["l"]},
        {"behaviors": ["oops-not-an-object"]},
    ]
    for m in mutations:
        data = {**base, **m}
        result = validate(data, {})  # must not raise
        assert result["fail"], m
        render_human(data, source="mem")  # must not raise either


def test_ac_missing_behavior_link_fail():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    data["acceptance"][0].pop("behavior")
    result = validate(data, {})
    assert any("missing behavior link" in e for e in result["fail"]), result


def test_matrix_missing_allowed_and_conflict_fail():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    data["states"]["action_matrix"][0].pop("allowed")
    data["states"]["action_matrix"].append(
        {"state": "idle", "action": "submit_search", "allowed": False, "zh": "矛盾"}
    )
    result = validate(data, {})
    assert any("missing allowed" in e for e in result["fail"]), result
    assert any("conflict" in e for e in result["fail"]), result


def test_source_content_hash_pins_material():
    with tempfile.TemporaryDirectory() as td:
        case = Path(td) / "case"
        shutil.copytree(ROOT / "examples/case-list-search", case)
        spec = case / "machine" / "spec.yaml"
        code, out = run(spec)
        assert code == 0, out
        # Silently appending a requirement to the source material must break PASS.
        note = case / "input" / "ops-note.zh.txt"
        note.write_text(note.read_text(encoding="utf-8") + "\n新增：还要支持按价格区间筛选。\n", encoding="utf-8")
        code2, out2 = run(spec)
        assert code2 == 1, out2
        assert "content changed" in out2


def test_ready_missing_content_hash_fails_draft_warns():
    """PASS is defined as resting on a pinned snapshot, so ready must enforce it."""
    spec = ROOT / "examples/case-list-search/machine/spec.yaml"
    data = load_spec(spec)
    data["sources"][0].pop("content_hash")
    ready = validate(data, {}, spec_path=spec, check_human=False)
    assert any("ready requires claims pinned" in e for e in ready["fail"]), ready
    data["status"] = "draft"
    draft = validate(data, {}, spec_path=spec, check_human=False)
    assert not any("content_hash" in e for e in draft["fail"]), draft
    assert any("not pinned" in w for w in draft["warn"]), draft


def test_stale_prototype_does_not_block_human_regen():
    """Regression: prototype attestation state must not gate the derivation."""
    with tempfile.TemporaryDirectory() as td:
        case = Path(td) / "case"
        shutil.copytree(ROOT / "examples/case-order-cancel-raw", case)
        spec = case / "machine" / "spec.yaml"
        human = case / "human" / "spec.md"
        spec.write_text(spec.read_text(encoding="utf-8").replace("2 小时", "30 天"), encoding="utf-8")
        env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
        p = subprocess.run(
            [sys.executable, "-m", "specnotary.generate_human", str(spec)],
            capture_output=True, text=True, env=env,
        )
        assert p.returncode == 0, p.stdout + p.stderr
        text = human.read_text(encoding="utf-8")
        assert "30 天" in text
        assert "<!-- gate_mode: hard -->" in text  # machine itself is clean
        assert "re-attestation" in p.stdout


def test_allow_invalid_stamps_degraded():
    src = ROOT / "examples/case-order-cancel-bad/machine/spec.yaml"
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "out.md"
        p = subprocess.run(
            ["bash", str(ROOT / "cli" / "run-generate-human.sh"), str(src), str(out), "--allow-invalid"],
            capture_output=True, text=True,
        )
        assert p.returncode == 0, p.stdout + p.stderr
        text = out.read_text(encoding="utf-8")
        assert "<!-- gate_mode: degraded -->" in text
        assert "gate_mode: hard" not in text
        assert "forced: --allow-invalid" in text


def test_human_default_out_standard_layout():
    with tempfile.TemporaryDirectory() as td:
        case = Path(td) / "case"
        shutil.copytree(ROOT / "examples/case-list-search", case)
        shutil.rmtree(case / "human")
        env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
        p = subprocess.run(
            [sys.executable, "-m", "specnotary.generate_human", str(case / "machine" / "spec.yaml")],
            capture_output=True, text=True, env=env,
        )
        assert p.returncode == 0, p.stdout + p.stderr
        written = case / "human" / "spec.md"
        assert written.is_file(), p.stdout
        # Existence is not correctness: assert the artifact carries this spec.
        text = written.read_text(encoding="utf-8")
        assert "SPEC-LIST-SEARCH-001" in text
        assert "<!-- renderer_version:" in text and "## 目录" in text
        assert text.lstrip().startswith("# "), text.splitlines()[:12]
        toc = text.find("## 目录")
        assert toc > 0 and "<!--" not in text[:toc], "chrome comments must not sit before the TOC"


def test_commands_actually_perform_their_side_effect():
    """Every writing command must change its artifact, not just exit 0.

    The sync bug hid behind an exit-code-only assertion: the command reported
    a status while silently skipping the write it advertises. Assert content
    movement for each writer.
    """
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    with tempfile.TemporaryDirectory() as td:
        case = Path(td) / "case"
        shutil.copytree(ROOT / "examples/case-order-cancel-raw", case)
        spec = case / "machine" / "spec.yaml"
        human = case / "human" / "spec.md"
        report = case / "reports" / "review-readiness.md"
        marker = "取消订单（审计标记）"
        spec.write_text(spec.read_text(encoding="utf-8").replace("取消订单", marker, 1), encoding="utf-8")

        # human: content must land in the artifact
        before = human.read_text(encoding="utf-8")
        subprocess.run([sys.executable, "-m", "specnotary.generate_human", str(spec)],
                       capture_output=True, text=True, env=env, check=True)
        after = human.read_text(encoding="utf-8")
        assert after != before and marker in after, "generate_human did not write the new content"

        # report: regenerated and reflects the current hash
        subprocess.run([sys.executable, "-m", "specnotary.report", str(spec), str(report)],
                       capture_output=True, text=True, env=env)
        from specnotary.libspec import load_spec as _load, spec_hash as _hash
        assert _hash(_load(spec)) in report.read_text(encoding="utf-8"), "report is not current"

        # sync --attest-prototype: the manifest hash must actually move
        manifest = case / "prototype" / "prototype.manifest.yaml"
        old_manifest = manifest.read_text(encoding="utf-8")
        subprocess.run([sys.executable, "-m", "specnotary.sync", str(spec), "--attest-prototype"],
                       capture_output=True, text=True, env=env)
        assert manifest.read_text(encoding="utf-8") != old_manifest, "attestation did not refresh the hash"
        code, out = run(spec)
        assert code == 0, out

        from contextlib import redirect_stdout
        import io as _io
        from specnotary.confirm import main as confirm_main
        buf = _io.StringIO()
        with redirect_stdout(buf):
            rc = confirm_main([str(spec), "--by", "qa", "--reason", "side-effect", "--accept-all-warn"])
        assert rc == 0, buf.getvalue()
        stamped = spec.read_text(encoding="utf-8")
        assert "accepted_warnings" in stamped and "qa" in stamped, "confirm did not write the ledger"


def test_mcp_report_matches_cli():
    import json as _json
    with tempfile.TemporaryDirectory() as td:
        case = Path(td) / "case"
        shutil.copytree(ROOT / "examples/case-list-search", case)
        spec = case / "machine" / "spec.yaml"
        # project_hint raises the bar; spec has no object_ai block → must FAIL everywhere
        text = spec.read_text(encoding="utf-8")
        spec.write_text(text + "\nproject_hint:\n  object_ai_weight: high\n", encoding="utf-8")
        env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
        cli = subprocess.run(
            [sys.executable, "-m", "specnotary.cli", "check", str(spec)],
            capture_output=True, text=True, env=env,
        )
        assert cli.returncode == 1, cli.stdout
        req = _json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {
            "name": "review_report", "arguments": {"path": str(spec)}}}) + "\n"
        mcp = subprocess.run(
            [sys.executable, "-m", "specnotary.cli", "mcp"],
            input=req, capture_output=True, text=True, env=env, timeout=60,
        )
        body = _json.loads(mcp.stdout.splitlines()[0])["result"]["content"][0]["text"]
        assert "RESULT: FAIL" in body, body[:400]
        assert "object_ai" in body


def test_json_output():
    import json as _json
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    p = subprocess.run(
        [sys.executable, "-m", "specnotary.cli", "check", str(RAW), "--json"],
        capture_output=True, text=True, env=env,
    )
    assert p.returncode == 0, p.stdout + p.stderr
    verdict = _json.loads(p.stdout)
    assert verdict["result"] == "PASS" and verdict["fail"] == []
    assert verdict["summary"]["behaviors"] >= 4
    assert "spec_hash" in verdict


def test_json_findings_are_layered():
    """Integrations must not have to parse message prefixes to know what broke."""
    import json as _json

    from specnotary.check import classify_findings

    grouped = classify_findings([
        "prototype stale: hash abc… != machine def…",
        "human spec stale: body edited or not regenerated — spec.md",
        "source SRC-001: path missing: ../input/x.txt",
        "behavior B1: then is empty",
    ])
    assert set(grouped) == {"prototype", "human", "source", "machine"}, grouped
    assert len(grouped["machine"]) == 1

    with tempfile.TemporaryDirectory() as td:
        case = Path(td) / "case"
        shutil.copytree(ROOT / "examples/case-order-cancel-raw", case)
        spec = case / "machine" / "spec.yaml"
        spec.write_text(spec.read_text(encoding="utf-8").replace("2 小时", "30 天"), encoding="utf-8")
        env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
        subprocess.run([sys.executable, "-m", "specnotary.generate_human", str(spec)],
                       capture_output=True, text=True, env=env)
        p = subprocess.run([sys.executable, "-m", "specnotary.cli", "check", str(spec), "--json"],
                           capture_output=True, text=True, env=env)
        verdict = _json.loads(p.stdout)
        # Only the endorsement is stale: the machine layer must be clean.
        assert verdict["result"] == "FAIL"
        assert list(verdict["fail_by_layer"]) == ["prototype"], verdict["fail_by_layer"]


def test_precommit_multi():
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    p = subprocess.run(
        [sys.executable, "-m", "specnotary.cli", "precommit",
         str(RAW), str(ROOT / "examples/case-list-search/machine/spec.yaml")],
        capture_output=True, text=True, env=env,
    )
    assert p.returncode == 0, p.stdout + p.stderr
    assert p.stdout.count("PASS ") == 2
    bad = subprocess.run(
        [sys.executable, "-m", "specnotary.cli", "precommit",
         str(ROOT / "examples/case-order-cancel-bad/machine/spec.yaml")],
        capture_output=True, text=True, env=env,
    )
    assert bad.returncode == 1


def test_en_human_roundtrip():
    data = load_spec(RAW)
    md = render_human(data, source="mem", lang="en")
    assert "Table of Contents" in md
    assert "States & Allowed Actions" in md
    assert "Decision Log" in md and "| Owns | Does not own |" in md
    assert "<!-- lang: en -->" in md
    with tempfile.TemporaryDirectory() as td:
        human = Path(td) / "spec.md"
        human.write_text(md, encoding="utf-8")
        result = validate(data, {}, human_path=human)
        assert not any("stale" in e for e in result["fail"]), result


def test_en_vague_calibration():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    data["behaviors"][0]["then"] = {"zh": "点击后返回结果", "en": "Clicking Search returns items whose title contains the keyword, newest first"}
    result = validate(data, {})
    assert not any("too vague" in e for e in result["fail"]), result
    data["behaviors"][0]["then"] = {"en": "The experience is seamless and intuitive"}
    result2 = validate(data, {})
    assert any("too vague" in e for e in result2["fail"]), result2


def test_mcp_server_smoke():
    import json as _json
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    reqs = "\n".join([
        _json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}),
        _json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
        _json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
            "name": "check_spec", "arguments": {"path": str(RAW)}}}),
    ]) + "\n"
    p = subprocess.run(
        [sys.executable, "-m", "specnotary.cli", "mcp"],
        input=reqs, capture_output=True, text=True, env=env, timeout=60,
    )
    lines = [_json.loads(x) for x in p.stdout.splitlines() if x.strip()]
    by_id = {o["id"]: o for o in lines}
    assert by_id[1]["result"]["serverInfo"]["name"] == "specnotary"
    names = [t["name"] for t in by_id[2]["result"]["tools"]]
    assert names == ["check_spec", "ready_gap", "review_report"]
    assert "PASS" in by_id[3]["result"]["content"][0]["text"]


def test_cli_module_entry():
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    p = subprocess.run(
        [sys.executable, "-m", "specnotary.cli", "check", str(RAW)],
        capture_output=True,
        text=True,
        env=env,
    )
    out = p.stdout + p.stderr
    assert p.returncode == 0, out
    assert "RESULT: PASS" in out
    v = subprocess.run(
        [sys.executable, "-m", "specnotary.cli", "--version"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert v.returncode == 0
    assert v.stdout.strip()


def test_ready_source_without_path_fails():
    """Deleting the file pointer must not be easier than submitting a bad hash."""
    spec = ROOT / "examples/case-list-search/machine/spec.yaml"
    data = load_spec(spec)
    data["sources"][0].pop("path", None)
    data["sources"][0].pop("content_hash", None)
    ready = validate(data, {}, spec_path=spec, check_human=False)
    assert any("missing path" in e for e in ready["fail"]), ready
    data["status"] = "draft"
    draft = validate(data, {}, spec_path=spec, check_human=False)
    assert not any("missing path" in e for e in draft["fail"]), draft
    assert any("no path" in w for w in draft["warn"]), draft


def test_json_duplicate_key_rejected():
    import json as _json

    payload = {
        "spec_version": "0.1",
        "id": "X",
        "title": {"zh": "t"},
        "status": "draft",
        "behaviors": [{"id": "B1", "name": {"zh": "n"}, "given": {"zh": "g"}, "when": {"zh": "w"}, "then": {"zh": "t"}}],
        "acceptance": [{"id": "AC-01", "behavior": "B1", "zh": "ok"}],
    }
    raw = _json.dumps(payload).replace(
        '"status": "draft"', '"status": "banana", "status": "draft"', 1
    )
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        fh.write(raw)
        path = Path(fh.name)
    try:
        from specnotary.libspec import DuplicateKeyError, load_spec as _load

        try:
            _load(path)
            raise AssertionError("duplicate JSON keys must not load")
        except DuplicateKeyError as exc:
            assert "duplicate key" in str(exc)
    finally:
        path.unlink(missing_ok=True)


def test_minimal_manifest_without_file_fails():
    """A self-reported mapping is not a landing. No file → no prototype PASS."""
    data = load_spec(RAW)
    required = ["btn_cancel", "btn_cancel_disabled", "dlg_confirm_title", "dlg_confirm_ok", "dlg_confirm_cancel"]
    behaviors = ["B1", "B2", "B3", "B4"]
    manifest = {
        "prototype_version": "0.1",
        "generated_from_spec": {"id": data["id"], "hash": spec_hash(data)},
        "screens": [
            {
                "id": "SCREEN-FAKE",
                "controls": [
                    {
                        "id": "CLAIM-EVERYTHING",
                        "role": "control",
                        "spec_refs": required + behaviors,
                    }
                ],
            }
        ],
    }
    result = validate_prototype(data, manifest, manifest_path=ALIGN)
    assert result["fail"], result
    assert any("no verifiable file" in e or "not mapped" in e for e in result["fail"]), result


def test_prototype_source_id_cannot_witness_ui():
    data = load_spec(RAW)
    manifest = load_spec(ALIGN)
    screens = manifest.get("screens") or []
    screens[0].setdefault("controls", []).append(
        {"id": "PROTO-DELETE-ACCOUNT", "role": "control", "spec_refs": ["SRC-001"]}
    )
    result = validate_prototype(data, manifest, manifest_path=ALIGN)
    assert any("not a mappable spec entity" in e for e in result["fail"]), result


def test_marker_in_script_string_is_not_a_landing():
    from specnotary.libproto import _html_spec_ids

    with tempfile.TemporaryDirectory() as td:
        html = Path(td) / "order-detail.html"
        html.write_text(
            "<div></div><script>const auditOnly = ['data-spec-id=\"btn_cancel\"'];</script>\n",
            encoding="utf-8",
        )
        assert _html_spec_ids(html) == set()
        data = load_spec(RAW)
        manifest = load_spec(ALIGN)
        man = Path(td) / "prototype.manifest.yaml"
        man.write_text(ALIGN.read_text(encoding="utf-8"), encoding="utf-8")
        result = validate_prototype(data, manifest, manifest_path=man)
        assert any("not found in html" in e for e in result["fail"]), result


def test_human_view_expands_status_enums_and_copy_keys():
    """Human prose must not leak raw enum/copy ids when the machine has labels.

    v9 expanded empty_states and prefixed lifecycle ids, then stopped —
    `terminated` / `created` in Then/AC/controls/defaults stayed English.
    """
    data = {
        "spec_version": "0.1",
        "id": "SPEC-EXPAND-001",
        "title": {"zh": "展开测试"},
        "status": "draft",
        "in_scope": [{"zh": "导入"}],
        "actors": [
            {"id": "corpus_admin", "zh": "语料管理员"},
            {"id": "system", "zh": "后台任务引擎"},
        ],
        "empty_states": {
            "file_too_large": {"zh": "单个文件不能超过 50MB"},
            "audit_failed": {"zh": "稽核失败，请稍后重试"},
        },
        "defaults": {
            "status_update_allowed": ["created", "running", "succeeded", "failed", "terminated"],
            "max_upload_file_mb": 50,
        },
        "states": {
            "lifecycle": [
                "import_created",
                "import_running",
                "import_succeeded",
                "import_failed",
                "import_terminated",
            ],
            "labels": {
                "import_created": {"zh": "已创建", "of": "导入任务"},
                "import_running": {"zh": "执行中", "of": "导入任务"},
                "import_succeeded": {"zh": "已成功", "of": "导入任务"},
                "import_failed": {"zh": "已失败", "of": "导入任务"},
                "import_terminated": {"zh": "已终止", "of": "导入任务"},
            },
            "action_labels": {"terminate_import_task": {"zh": "终止导入任务"}},
            "action_matrix": [
                {
                    "state": "import_created",
                    "action": "terminate_import_task",
                    "allowed": True,
                    "zh": "未执行完可终止",
                }
            ],
        },
        "ui": {
            "controls": [
                {
                    "id": "btn_terminate",
                    "zh": "终止任务",
                    "visible_when": {"zh": "corpus_admin 且状态∈{created,running}"},
                    "action": {"zh": "状态改为 terminated"},
                    "fail_feedback": {"zh": "—"},
                }
            ]
        },
        "data_contracts": [
            {
                "id": "ImportTask",
                "zh": "导入任务",
                "fields": [
                    {"name": "created_at", "zh": "创建时间", "type": "datetime", "desc": {"zh": "创建时写入"}},
                    {
                        "name": "status",
                        "zh": "状态",
                        "type": "enum",
                        "desc": {"zh": "created/running/succeeded/failed/terminated"},
                    },
                ],
            }
        ],
        "behaviors": [
            {
                "id": "B1",
                "step_id": 1,
                "name": {"zh": "终止导入任务"},
                "given": {"zh": "选中任务状态∈{created,running}"},
                "when": {"zh": "system 将任务置为 terminated"},
                "then": {
                    "zh": "状态变为 terminated。若状态为 succeeded/failed/terminated，"
                    "展示 file_too_large；执行异常展示 audit_failed"
                },
            }
        ],
        "acceptance": [
            {
                "id": "AC-01",
                "behavior": "B1",
                "zh": "Given 任务状态=running When 点终止 Then 状态=terminated",
            }
        ],
    }
    md = render_human(data, source="mem")
    leaked = []
    for token in (
        "状态变为 terminated",
        "状态改为 terminated",
        "状态=terminated",
        "状态=running",
        "状态为 succeeded/failed/terminated",
        "展示 file_too_large",
        "展示 audit_failed",
        "corpus_admin 且",
        "system 将任务",
    ):
        if token in md:
            leaked.append(token)
    assert not leaked, f"human view still shows raw machine ids: {leaked}"
    assert "已终止" in md
    assert "已创建" in md
    assert "已成功" in md
    assert "「单个文件不能超过 50MB」" in md
    assert "「稽核失败，请稍后重试」" in md
    assert "语料管理员" in md
    assert "后台任务引擎" in md
    assert "终止导入任务" in md
    assert "`created_at`" in md
    assert "created_at" in md and "已创建_at" not in md


def test_human_header_gate_mode_cannot_be_forged():
    import re as _re

    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    md = render_human(data, source="machine/spec.yaml", gate_mode="hard")
    forged = md.replace("<!-- gate_mode: hard -->", "<!-- gate_mode: degraded -->", 1)
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "spec.md"
        path.write_text(forged, encoding="utf-8")
        result = validate(data, {}, spec_path=None, human_path=path, check_human=True)
        assert any("gate_mode" in e for e in result["fail"]), result
    lied = _re.sub(r"(<!-- body_hash: )[0-9a-f]+", r"\1deadbeef", md, count=1)
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "spec.md"
        path.write_text(lied, encoding="utf-8")
        result = validate(data, {}, spec_path=None, human_path=path, check_human=True)
        assert any("body_hash does not match" in e for e in result["fail"]), result


def test_known_empty_talk_ac_fails():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    data["acceptance"][0]["zh"] = "功能符合预期"
    result = validate(data, {}, check_human=False)
    assert any("not observable" in e for e in result["fail"]), result
    data["acceptance"][0]["zh"] = "Users are satisfied"
    result2 = validate(data, {}, check_human=False)
    assert any("not observable" in e for e in result2["fail"]), result2
    data["acceptance"][0]["zh"] = "形成闭环"
    result3 = validate(data, {}, check_human=False)
    assert any("not observable" in e for e in result3["fail"]), result3
    data["behaviors"][0]["then"] = {"zh": "形成闭环"}
    result4 = validate(data, {}, check_human=False)
    assert any("too vague" in e for e in result4["fail"]), result4
    data["behaviors"][0]["then"] = {"zh": "本模块治理到位"}
    result5 = validate(data, {}, check_human=False)
    assert not any("too vague" in e for e in result5["fail"]), result5


def _parse_empty_talk_corpus(path: Path) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    must: list[tuple[str, str]] = []
    must_not: list[tuple[str, str]] = []
    section = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## ") and "必须拦" in line:
            section = "fail"
            continue
        if line.startswith("## ") and "不得拦" in line:
            section = "pass"
            continue
        if line.startswith("## "):
            section = None
            continue
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        loc, sentence = cells[0], cells[1]
        if loc in {"位置", "loc"} or set(loc) <= {"-", ":"}:
            continue
        if loc not in {"ac", "then"}:
            continue
        if section == "fail":
            must.append((loc, sentence))
        elif section == "pass":
            must_not.append((loc, sentence))
    return must, must_not


def test_empty_talk_corpus():
    """Public calibration set — known phrases, not a general observability oracle."""
    corpus = ROOT / "docs/empty-talk-corpus.md"
    must, must_not = _parse_empty_talk_corpus(corpus)
    assert must and must_not, "corpus tables are empty"
    baseline = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")

    def replay(loc: str, sentence: str):
        data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
        if loc == "ac":
            data["acceptance"][0]["zh"] = sentence
        else:
            then = data["behaviors"][0].get("then")
            if isinstance(then, dict):
                then["zh"] = sentence
            else:
                data["behaviors"][0]["then"] = {"zh": sentence}
        return validate(data, {}, spec_path=None, check_human=False)

    talk_marks = ("not observable", "too vague", "placeholder")
    missed = []
    for loc, sentence in must:
        result = replay(loc, sentence)
        if not any(any(m in e for m in talk_marks) for e in result["fail"]):
            missed.append(f"{loc}: {sentence}")
    assert not missed, "corpus must-fail sentences were not blocked: " + "; ".join(missed)

    false_hits = []
    for loc, sentence in must_not:
        result = replay(loc, sentence)
        hits = [e for e in result["fail"] if any(m in e for m in talk_marks)]
        if hits:
            false_hits.append(f"{loc}: {sentence} → {hits}")
    assert not false_hits, "corpus must-not-fail sentences were blocked: " + "; ".join(false_hits)
    assert baseline["acceptance"][0]["zh"]  # sanity: parser did not mutate the file


def _copy_case(td: str, name: str = "case-order-cancel-raw") -> Path:
    dest = Path(td) / name
    shutil.copytree(ROOT / "examples" / name, dest)
    return dest / "machine" / "spec.yaml"


def test_new_and_ingest_pin_source():
    import io
    from contextlib import redirect_stdout

    from specnotary.case import ingest_main, new_main
    from specnotary.libspec import file_sha256

    with tempfile.TemporaryDirectory() as td:
        raw = Path(td) / "ops-note.txt"
        raw.write_text("未发货订单允许买家自助取消\n", encoding="utf-8")
        case = Path(td) / "my-feat"
        buf = io.StringIO()
        with redirect_stdout(buf):
            assert new_main([str(case), "--from", str(raw), "--kind", "ops", "--id", "SPEC-NEW-001"]) == 0
        spec = case / "machine" / "spec.yaml"
        assert spec.is_file()
        copied = case / "input" / "ops-note.txt"
        assert copied.is_file()
        data = load_spec(spec)
        assert data["id"] == "SPEC-NEW-001"
        assert data["sources"][0]["kind"] == "ops"
        assert data["sources"][0]["content_hash"] == file_sha256(copied)
        result = validate(data, {}, spec_path=spec, check_human=False)
        assert not result["fail"], result

        kit = Path(td) / "spec.md"
        kit.write_text("# Feature\n\nGitHub spec-kit placeholder spec.\n", encoding="utf-8")
        with redirect_stdout(buf):
            assert ingest_main([str(kit), "--spec", str(spec), "--kind", "speckit"]) == 0
        data2 = load_spec(spec)
        kinds = [s.get("kind") for s in data2["sources"]]
        assert "speckit" in kinds
        assert (case / "input" / "spec.md").is_file()


def test_confirm_warn_ledger():
    """Accepting a WARN silences it; incomplete/stale ledger fails ready; hash chain stays."""
    import io
    from contextlib import redirect_stdout

    from specnotary.confirm import main as confirm_main
    from specnotary.libspec import spec_hash
    from specnotary.report import build_report

    with tempfile.TemporaryDirectory() as td:
        spec = _copy_case(td)
        before = load_spec(spec)
        digest = spec_hash(before)
        code, out = run(spec)
        assert code == 0, out
        assert "WARN:" in out
        from specnotary.check import gate
        warn_ids = list(gate(spec).get("warn_ids") or [])
        assert warn_ids, "flagship fixture should still carry assumption WARNs"

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = confirm_main(
                [str(spec), "--by", "alice", "--reason", "ops signed off", "--accept-all-warn"]
            )
        assert rc == 0, buf.getvalue()
        after = load_spec(spec)
        assert spec_hash(after) == digest, "ledger fields must not move spec_hash"
        accepted = {x["id"] for x in after.get("accepted_warnings") or []}
        assert set(warn_ids) <= accepted
        assert after["review"]["confirmed_by"] == "alice"

        code2, out2 = run(spec)
        assert code2 == 0, out2
        assert "WARN: source_claim" not in out2, out2

        md, result = build_report(spec)
        assert "已经拍过板的提醒" in md
        assert "alice" in md
        assert not result["fail"]

        after["accepted_warnings"].append(
            {"id": "assumption:SRC-CLM-GHOST", "by": "alice", "date": "2026-08-14", "reason": "stale"}
        )
        stale = validate(after, {}, spec_path=spec, check_human=True)
        assert any("no longer applies" in e for e in stale["fail"]), stale

        after["accepted_warnings"] = [{"id": warn_ids[0], "by": "alice"}]
        incomplete = validate(after, {}, spec_path=spec, check_human=True)
        assert any("need id, by, date, reason" in e for e in incomplete["fail"]), incomplete


def test_confirm_refuses_fail():
    import io
    from contextlib import redirect_stdout
    from specnotary.confirm import main as confirm_main

    spec = ROOT / "examples/case-order-cancel-bad/machine/spec.yaml"
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = confirm_main([str(spec), "--by", "bob", "--reason", "nope", "--accept-all-warn"])
    assert rc == 1
    assert "cannot confirm" in buf.getvalue()


if __name__ == "__main__":
    failed = 0
    for t in [
        test_wrapper_scripts_end_to_end,
        test_order_raw_pass,
        test_order_bad_fail,
        test_order_fixed_pass,
        test_order_faq_pass,
        test_list_search_pass,
        test_status_banana_fail,
        test_missing_behavior_ref_fail,
        test_missing_actor_ref_fail,
        test_generate_human_has_wireframe_and_controls,
        test_generate_human_refuses_fail_without_flag,
        test_generate_list_search_human,
        test_omitted_claim_fail,
        test_assumption_claim_warn,
        test_conflict_unclosed_fail,
        test_covered_without_refs_fail,
        test_human_stale_after_hand_edit,
        test_human_body_edit_fail,
        test_ready_empty_claims_fail,
        test_spec_ref_must_be_spec_entity,
        test_explicit_missing_human_fail,
        test_node_runtime_refuses_hard_pass,
        test_human_missing_hash_fail,
        test_report_lists_dispositions,
        test_self_check_report_is_pm_readable,
        test_aligned_prototype_pass,
        test_drift_missing_required_control,
        test_drift_unknown_spec_ref,
        test_drift_stale_hash,
        test_drift_extra_business_action,
        test_decoration_without_refs_ok,
        test_semantic_warning_is_warn,
        test_malformed_shapes_never_crash,
        test_ac_missing_behavior_link_fail,
        test_matrix_missing_allowed_and_conflict_fail,
        test_source_content_hash_pins_material,
        test_ready_missing_content_hash_fails_draft_warns,
        test_stale_prototype_does_not_block_human_regen,
        test_allow_invalid_stamps_degraded,
        test_human_default_out_standard_layout,
        test_commands_actually_perform_their_side_effect,
        test_mcp_report_matches_cli,
        test_ready_placeholder_ui_fail,
        test_ready_empty_then_fail,
        test_html_comment_not_a_hit,
        test_role_escape_extra_fail,
        test_source_path_missing_fail,
        test_ready_no_covered_fail,
        test_uncovered_behavior_fail,
        test_node_generate_refuses_hard_stamp,
        test_template_draft_passes_gate,
        test_renderer_version_stale,
        test_explain_ready_gap,
        test_explain_flag_prints_gap,
        test_in_scope_required_for_ready,
        test_interaction_broken_link_fail,
        test_sync_roundtrip_requires_attest,
        test_quoted_ui_label_not_vague,
        test_dangling_ref_fail_on_ready,
        test_declared_ref_in_text_ok,
        test_spa_source_markers_and_comments,
        test_markers_command_reconciles,
        test_human_view_toc_overview_and_diagrams,
        test_v3_data_contract_error_codes_decisions,
        test_decision_undecided_blocks_ready,
        test_decision_decided_passes,
        test_overview_missing_warns_on_ready,
        test_data_contract_claimable,
        test_json_output,
        test_json_findings_are_layered,
        test_precommit_multi,
        test_en_human_roundtrip,
        test_en_vague_calibration,
        test_mcp_server_smoke,
        test_cli_module_entry,
        test_ready_source_without_path_fails,
        test_json_duplicate_key_rejected,
        test_minimal_manifest_without_file_fails,
        test_prototype_source_id_cannot_witness_ui,
        test_marker_in_script_string_is_not_a_landing,
        test_human_view_expands_status_enums_and_copy_keys,
        test_human_header_gate_mode_cannot_be_forged,
        test_known_empty_talk_ac_fails,
        test_empty_talk_corpus,
        test_new_and_ingest_pin_source,
        test_confirm_warn_ledger,
        test_confirm_refuses_fail,
    ]:
        try:
            t()
            print(f"OK  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
    sys.exit(1 if failed else 0)
