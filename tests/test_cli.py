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


def test_case01_pass():
    code, out = run(ROOT / "examples/case-01-raw-material/machine/spec.yaml")
    assert code == 0, out
    assert "RESULT: PASS" in out


def test_case02_bad_fail():
    code, out = run(ROOT / "examples/case-02-bad-prd/machine/spec.yaml")
    assert code == 1, out
    assert "RESULT: FAIL" in out


def test_case02_fixed_pass():
    code, out = run(ROOT / "examples/case-02-bad-prd/machine/spec.fixed.yaml")
    assert code == 0, out
    assert "RESULT: PASS" in out


def test_case03_ai_high_pass():
    code, out = run(ROOT / "examples/case-03-reverse-manual/machine/spec.yaml")
    assert code == 0, out
    assert "RESULT: PASS" in out


def test_generate_human():
    src = ROOT / "examples/case-01-raw-material/machine/spec.yaml"
    out = ROOT / "examples/case-01-raw-material/human/spec.md"
    p = subprocess.run(
        ["bash", str(ROOT / "cli/run-generate-human.sh"), str(src), str(out)],
        capture_output=True,
        text=True,
    )
    assert p.returncode == 0, p.stdout + p.stderr
    text = out.read_text(encoding="utf-8")
    assert "generated_from" in text
    assert "书架助手" in text


if __name__ == "__main__":
    tests = [
        test_case01_pass,
        test_case02_bad_fail,
        test_case02_fixed_pass,
        test_case03_ai_high_pass,
        test_generate_human,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"OK  {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"ERR  {t.__name__}: {e}")
    sys.exit(1 if failed else 0)
