#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "cli" / "run-check.sh"
sys.path.insert(0, str(ROOT / "cli" / "python"))
from libspec import load_spec, validate  # noqa: E402


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
    ]:
        try:
            t()
            print(f"OK  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
    sys.exit(1 if failed else 0)
