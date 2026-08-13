#!/usr/bin/env python3
"""Mutation matrix: systematic negative coverage for the gate.

Two audits found holes that ad-hoc tests missed, because "which rules exist"
was never measured — only "do the samples still pass". This file enumerates
mutation operators (break one thing on purpose) crossed with spec objects, and
asserts each mutant is rejected. The pass rate is printed as KILL_RATE so a
regression in coverage is visible instead of silent.

Adding a spec object without adding its mutants here is the failure mode this
file exists to prevent: every object family below must have at least one
uniqueness, one closure and one contradiction mutant where applicable.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from specnotary.libspec import load_spec, render_human, validate  # noqa: E402

BASE_SPEC = ROOT / "examples/case-list-search/machine/spec.yaml"
RICH_SPEC = ROOT / "examples/case-order-cancel-raw/machine/spec.yaml"


def _walk(node, parts):
    """Follow a dotted path; numeric segments index into lists."""
    for p in parts:
        node = node[int(p)] if p.isdigit() else node[p]
    return node


def _set(path: str, value):
    """Mutation that assigns a dotted path, e.g. 'ui.controls'."""
    def apply(d):
        parts = path.split(".")
        node = _walk(d, parts[:-1])
        key = parts[-1]
        node[int(key) if key.isdigit() else key] = value
        return d
    return apply


def _append(path: str, value):
    def apply(d):
        _walk(d, path.split(".")).append(copy.deepcopy(value))
        return d
    return apply


# (id, object family, operator class, base spec, mutation, expected substring)
MUTANTS = [
    # ---- shape robustness: wrong container types must FAIL, never crash ----
    ("shape-ui", "ui", "type", BASE_SPEC, _set("ui", "字符串"), "must be an object"),
    ("shape-states", "states", "type", BASE_SPEC, _set("states", [1, 2]), "must be an object"),
    ("shape-behaviors", "behaviors", "type", BASE_SPEC, _set("behaviors", {"id": "B1"}), "must be an array"),
    ("shape-defaults", "defaults", "type", BASE_SPEC, _set("defaults", "s"), "must be an object"),
    ("shape-acceptance", "acceptance", "type", BASE_SPEC, _set("acceptance", "s"), "must be an array"),
    ("shape-decisions", "decisions", "type", RICH_SPEC, _set("decisions", "s"), "must be an array"),
    ("shape-contracts", "data_contracts", "type", RICH_SPEC, _set("data_contracts", {}), "must be an array"),

    # ---- uniqueness ----
    ("uniq-behavior", "behaviors", "uniqueness", BASE_SPEC,
     _append("behaviors", {"id": "B1", "name": {"zh": "dup"}, "given": {"zh": "g"}, "when": {"zh": "w"}, "then": {"zh": "t"}}),
     "duplicate behavior id"),
    ("uniq-acceptance", "acceptance", "uniqueness", BASE_SPEC,
     _append("acceptance", {"id": "AC-01", "behavior": "B1", "zh": "dup"}), "duplicate acceptance id"),
    ("uniq-control", "ui.controls", "uniqueness", BASE_SPEC,
     _append("ui.controls", {"id": "btn_search", "zh": "dup"}), "duplicate control id"),
    ("uniq-lifecycle", "states.lifecycle", "uniqueness", BASE_SPEC,
     _append("states.lifecycle", "idle"), "duplicate lifecycle state"),
    ("uniq-errorcode", "error_codes", "uniqueness", RICH_SPEC,
     _append("error_codes", {"code": "CANCEL_NOT_ALLOWED", "zh": "dup"}), "duplicate error_code"),
    ("uniq-contract-field", "data_contracts", "uniqueness", RICH_SPEC,
     _append("data_contracts.0.fields", {"name": "order_id", "zh": "dup"}), "duplicate field"),
    ("uniq-decision", "decisions", "uniqueness", RICH_SPEC,
     _append("decisions", {"id": "D-01", "question": {"zh": "dup"}, "chosen": "A", "status": "decided"}),
     "duplicate decision id"),
    ("uniq-cross-kind", "ids", "uniqueness", BASE_SPEC,
     _append("ui.controls", {"id": "B1", "zh": "collide"}), "id collision across kinds"),

    # ---- reference closure ----
    ("ref-ac-behavior", "acceptance", "closure", BASE_SPEC,
     _set("acceptance.0.behavior", "B-GHOST"), "behavior ref missing"),
    ("ref-ac-unlinked", "acceptance", "closure", BASE_SPEC,
     lambda d: (d["acceptance"][0].pop("behavior"), d)[1], "missing behavior link"),
    ("ref-permission-actor", "permissions", "closure", BASE_SPEC,
     lambda d: (d["permissions"][0].__setitem__("actor", "ghost"), d)[1], "missing actor"),
    ("ref-claim-source", "source_claims", "closure", BASE_SPEC,
     lambda d: (d["source_claims"][0].__setitem__("source_ref", "SRC-GHOST"), d)[1], "source_ref missing"),
    ("ref-claim-specref", "source_claims", "closure", BASE_SPEC,
     lambda d: (d["source_claims"][0].__setitem__("spec_refs", ["SRC-LS-001"]), d)[1], "not a spec entity"),
    ("ref-decision-chosen", "decisions", "closure", RICH_SPEC,
     lambda d: (d["decisions"][0].__setitem__("chosen", "Z"), d)[1], "not one of its options"),
    ("ref-dangling-text", "free text", "closure", BASE_SPEC,
     lambda d: (d["states"]["action_matrix"][0].__setitem__("zh", "见 P-99"), d)[1], "dangling reference"),
    ("ref-matrix-lifecycle", "states", "closure", BASE_SPEC,
     lambda d: (d["states"]["action_matrix"][0].__setitem__("state", "ghost_state"), d)[1], "not in lifecycle"),

    # ---- contradiction ----
    ("contra-scope", "in/out_scope", "contradiction", BASE_SPEC,
     _append("out_of_scope", {"zh": "按商品 ID 精确匹配"}), "scope contradiction"),
    ("contra-matrix", "states", "contradiction", BASE_SPEC,
     _append("states.action_matrix", {"state": "idle", "action": "submit_search", "allowed": False, "zh": "x"}),
     "action_matrix conflict"),
    ("contra-responsibility", "responsibilities", "contradiction", RICH_SPEC,
     lambda d: (d["responsibilities"][0].__setitem__("not_owns", copy.deepcopy(d["responsibilities"][0]["owns"])), d)[1],
     "responsibility contradiction"),

    # ---- ready completeness (placeholders and empty talk) ----
    ("ready-vague-then", "behaviors", "completeness", BASE_SPEC,
     lambda d: (d["behaviors"][0].__setitem__("then", {"zh": "体验好就行"}), d)[1], "too vague"),
    ("ready-empty-then", "behaviors", "completeness", BASE_SPEC,
     lambda d: (d["behaviors"][0].__setitem__("then", {"zh": ""}), d)[1], "then is empty"),
    ("ready-unobservable-ac", "acceptance", "completeness", BASE_SPEC,
     lambda d: (d["acceptance"][0].__setitem__("zh", "功能正常"), d)[1], "not observable"),
    ("ready-placeholder-ui", "ui", "completeness", BASE_SPEC, _set("ui", {"_": 1}),
     "requires ui"),
    ("ready-placeholder-defaults", "defaults", "completeness", BASE_SPEC, _set("defaults", {"_": 1}),
     "defaults with at least one real key"),
    ("ready-no-matrix", "states", "completeness", BASE_SPEC, _set("states", {"lifecycle": ["a", "b"]}),
     "requires states.action_matrix"),
    ("ready-matrix-no-allowed", "states", "completeness", BASE_SPEC,
     lambda d: (d["states"]["action_matrix"][0].pop("allowed"), d)[1], "missing allowed"),
    ("ready-empty-scope", "in_scope", "completeness", BASE_SPEC, _set("in_scope", []),
     "requires non-empty in_scope"),
    ("ready-open-pending", "pending", "completeness", BASE_SPEC,
     _set("pending", [{"id": "P-1", "missing": "m", "impact": "i", "owner": "o", "status": "open"}]),
     "still open"),
    ("ready-undecided", "decisions", "completeness", RICH_SPEC,
     _append("decisions", {"id": "D-99", "question": {"zh": "未拍板"}, "status": "pending"}), "undecided"),

    # ---- evidence ledger ----
    ("evid-no-claims", "source_claims", "evidence", BASE_SPEC, _set("source_claims", []),
     "source_claims missing"),
    ("evid-all-assumption", "source_claims", "evidence", BASE_SPEC,
     lambda d: ([c.__setitem__("disposition", "assumption") for c in d["source_claims"]], d)[1],
     "at least one covered"),
    ("evid-omitted", "source_claims", "evidence", BASE_SPEC,
     _append("source_claims", {"id": "SRC-CLM-X", "source_ref": "SRC-LS-001",
                               "quote_or_summary": "漏了的要求", "disposition": "omitted"}), "omitted"),
    ("evid-open-conflict", "source_claims", "evidence", BASE_SPEC,
     _append("source_claims", {"id": "SRC-CLM-C", "source_ref": "SRC-LS-001",
                               "quote_or_summary": "两处冲突", "disposition": "conflict"}), "conflict not closed"),
    ("evid-uncovered-entity", "source_claims", "evidence", BASE_SPEC,
     lambda d: ([c.__setitem__("spec_refs", [r for r in (c.get("spec_refs") or []) if r != "B2"])
                 for c in d["source_claims"]], d)[1], "coverage missing for behavior B2"),
    ("evid-evidence-swap", "sources", "evidence", BASE_SPEC,
     lambda d: (d["source_claims"][0].__setitem__("evidence", "other-file.txt:L2"), d)[1],
     "evidence cites"),
    ("evid-source-status", "sources", "evidence", BASE_SPEC,
     lambda d: (d["sources"][0].__setitem__("status", "bogus"), d)[1], "registered|superseded"),
]


def _apply(mutation, data):
    out = mutation(copy.deepcopy(data))
    return out if isinstance(out, dict) else data


def run_matrix(verbose: bool = True) -> tuple[int, int, list[str]]:
    cache: dict[Path, dict] = {}
    survivors: list[str] = []
    for mid, family, klass, spec_path, mutation, expected in MUTANTS:
        if spec_path not in cache:
            cache[spec_path] = load_spec(spec_path)
        mutated = _apply(mutation, cache[spec_path])
        try:
            result = validate(mutated, {}, spec_path=spec_path, check_human=False)
            render_human(mutated, source="mutation")  # must not raise either
        except Exception as exc:  # noqa: BLE001
            survivors.append(f"{mid} [{klass}/{family}] CRASHED: {type(exc).__name__}: {exc}")
            continue
        if not any(expected in e for e in result["fail"]):
            survivors.append(
                f"{mid} [{klass}/{family}] SURVIVED: expected {expected!r}, got {result['fail'][:2] or 'no FAIL'}"
            )
        elif verbose:
            print(f"  killed {mid:26} [{klass}/{family}]")
    return len(MUTANTS) - len(survivors), len(MUTANTS), survivors


def test_mutation_matrix_full_kill():
    killed, total, survivors = run_matrix(verbose=False)
    assert not survivors, "surviving mutants:\n  " + "\n  ".join(survivors)
    assert killed == total


def test_matrix_covers_every_object_family():
    """Guard against adding a spec object without adding its mutants."""
    families = {m[1] for m in MUTANTS}
    required = {
        "behaviors", "acceptance", "ui.controls", "states", "permissions",
        "source_claims", "sources", "decisions", "data_contracts",
        "error_codes", "responsibilities", "in_scope", "pending",
    }
    missing = required - families
    assert not missing, f"object families with no mutation coverage: {sorted(missing)}"


def test_matrix_covers_every_operator_class():
    classes = {m[2] for m in MUTANTS}
    assert {"type", "uniqueness", "closure", "contradiction", "completeness", "evidence"} <= classes


if __name__ == "__main__":
    killed, total, survivors = run_matrix()
    print()
    for s in survivors:
        print(f"  SURVIVED {s}")
    rate = killed / total * 100
    print(f"\nMUTANTS: {total}")
    print(f"KILLED: {killed}")
    print(f"KILL_RATE: {rate:.1f}%")
    for t in (test_matrix_covers_every_object_family, test_matrix_covers_every_operator_class):
        t()
        print(f"OK  {t.__name__}")
    sys.exit(1 if survivors else 0)
