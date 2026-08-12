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
        human.write_text(text.replace("## 1. 范围", "## 1. 范围（手改）", 1), encoding="utf-8")
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


def test_sync_roundtrip():
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
        p = subprocess.run(
            ["bash", str(ROOT / "cli" / "run-sync.sh"), str(spec)],
            capture_output=True,
            text=True,
        )
        assert p.returncode == 0, p.stdout + p.stderr
        code, out = run(spec)
        assert code == 0, out
        assert "RESULT: PASS" in out


def test_quoted_ui_label_not_vague():
    data = load_spec(ROOT / "examples/case-list-search/machine/spec.yaml")
    data["behaviors"][0]["when"] = {"zh": "点击「智能识别」按钮"}
    result = validate(data, {})
    assert not any("too vague" in e for e in result["fail"]), result
    data["behaviors"][0]["when"] = {"zh": "智能地快速搜索"}
    result2 = validate(data, {})
    assert any("too vague" in e for e in result2["fail"]), result2


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
        test_sync_roundtrip,
        test_quoted_ui_label_not_vague,
        test_cli_module_entry,
    ]:
        try:
            t()
            print(f"OK  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
    sys.exit(1 if failed else 0)
