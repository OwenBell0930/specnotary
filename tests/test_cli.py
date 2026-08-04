#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "cli" / "run-check.sh"


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


if __name__ == "__main__":
    failed = 0
    for t in [
        test_order_raw_pass,
        test_order_bad_fail,
        test_order_fixed_pass,
        test_order_faq_pass,
        test_generate_human_has_wireframe_and_controls,
    ]:
        try:
            t()
            print(f"OK  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
    sys.exit(1 if failed else 0)
