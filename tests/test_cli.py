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
from specanvil.libproto import classify_proto_issues, validate_prototype  # noqa: E402
from specanvil.libspec import load_spec, ready_gap, render_human, spec_hash, validate  # noqa: E402


def run(path: Path) -> tuple[int, str]:
    p = subprocess.run(["bash", str(CHECK), str(path)], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


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
    result = validate(data, {}, human_path=Path("/tmp/specanvil-no-such-human.md"))
    assert any("human spec missing" in e for e in result["fail"]), result


def test_node_runtime_refuses_hard_pass():
    env = {**os.environ, "SPECANVIL_RUNTIME": "node"}
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
        assert "assumption" in text
        assert "covered" in text
        assert spec_hash(load_spec(src)) in text


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
        p = subprocess.run(
            ["bash", str(ROOT / "cli" / "run-sync.sh"), str(spec)],
            capture_output=True,
            text=True,
        )
        assert p.returncode == 1, p.stdout + p.stderr
        assert "NOT refreshed" in p.stdout + p.stderr
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
    from specanvil.libproto import _html_spec_ids
    from specanvil.markers import scan_markers
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
            [sys.executable, "-m", "specanvil.markers",
             str(ROOT / "examples/case-list-search/machine/spec.yaml"), td],
            capture_output=True, text=True, env=env,
        )
        out = p.stdout + p.stderr
        assert p.returncode == 0, out
        assert "ok inp_keyword" in out
        assert "?? not_in_spec" in out
        assert "btn_search" in out  # required but unmarked


def test_v3_toc_overview_and_diagrams():
    text = (ROOT / "examples/case-order-cancel-raw/human/spec.md").read_text(encoding="utf-8")
    assert "## 目录" in text
    assert "概览" in text and "设计原则" in text
    assert text.count("```mermaid") >= 2  # architecture + lifecycle
    # v4: no auto main-path chain — behaviors are often branches, not a sequence
    assert "flowchart TD" not in text
    assert "非流程图" in text
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


def test_ready_missing_content_hash_warn():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    data["sources"][0].pop("content_hash")
    result = validate(
        data, {}, spec_path=ROOT / "examples/case-list-search/machine/spec.yaml"
    )
    assert any("not pinned" in w for w in result["warn"]), result


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
            [sys.executable, "-m", "specanvil.generate_human", str(case / "machine" / "spec.yaml")],
            capture_output=True, text=True, env=env,
        )
        assert p.returncode == 0, p.stdout + p.stderr
        assert (case / "human" / "spec.md").is_file(), p.stdout


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
            [sys.executable, "-m", "specanvil.cli", "check", str(spec)],
            capture_output=True, text=True, env=env,
        )
        assert cli.returncode == 1, cli.stdout
        req = _json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {
            "name": "review_report", "arguments": {"path": str(spec)}}}) + "\n"
        mcp = subprocess.run(
            [sys.executable, "-m", "specanvil.cli", "mcp"],
            input=req, capture_output=True, text=True, env=env, timeout=60,
        )
        body = _json.loads(mcp.stdout.splitlines()[0])["result"]["content"][0]["text"]
        assert "RESULT: FAIL" in body, body[:400]
        assert "object_ai" in body


def test_json_output():
    import json as _json
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    p = subprocess.run(
        [sys.executable, "-m", "specanvil.cli", "check", str(RAW), "--json"],
        capture_output=True, text=True, env=env,
    )
    assert p.returncode == 0, p.stdout + p.stderr
    verdict = _json.loads(p.stdout)
    assert verdict["result"] == "PASS" and verdict["fail"] == []
    assert verdict["summary"]["behaviors"] >= 4
    assert "spec_hash" in verdict


def test_precommit_multi():
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    p = subprocess.run(
        [sys.executable, "-m", "specanvil.cli", "precommit",
         str(RAW), str(ROOT / "examples/case-list-search/machine/spec.yaml")],
        capture_output=True, text=True, env=env,
    )
    assert p.returncode == 0, p.stdout + p.stderr
    assert p.stdout.count("PASS ") == 2
    bad = subprocess.run(
        [sys.executable, "-m", "specanvil.cli", "precommit",
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
        [sys.executable, "-m", "specanvil.cli", "mcp"],
        input=reqs, capture_output=True, text=True, env=env, timeout=60,
    )
    lines = [_json.loads(x) for x in p.stdout.splitlines() if x.strip()]
    by_id = {o["id"]: o for o in lines}
    assert by_id[1]["result"]["serverInfo"]["name"] == "specanvil"
    names = [t["name"] for t in by_id[2]["result"]["tools"]]
    assert names == ["check_spec", "ready_gap", "review_report"]
    assert "PASS" in by_id[3]["result"]["content"][0]["text"]


def test_cli_module_entry():
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    p = subprocess.run(
        [sys.executable, "-m", "specanvil.cli", "check", str(RAW)],
        capture_output=True,
        text=True,
        env=env,
    )
    out = p.stdout + p.stderr
    assert p.returncode == 0, out
    assert "RESULT: PASS" in out
    v = subprocess.run(
        [sys.executable, "-m", "specanvil.cli", "--version"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert v.returncode == 0
    assert v.stdout.strip()


if __name__ == "__main__":
    failed = 0
    for t in [
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
        test_ready_missing_content_hash_warn,
        test_allow_invalid_stamps_degraded,
        test_human_default_out_standard_layout,
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
        test_v3_toc_overview_and_diagrams,
        test_v3_data_contract_error_codes_decisions,
        test_decision_undecided_blocks_ready,
        test_decision_decided_passes,
        test_overview_missing_warns_on_ready,
        test_data_contract_claimable,
        test_json_output,
        test_precommit_multi,
        test_en_human_roundtrip,
        test_en_vague_calibration,
        test_mcp_server_smoke,
        test_cli_module_entry,
    ]:
        try:
            t()
            print(f"OK  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
    sys.exit(1 if failed else 0)
