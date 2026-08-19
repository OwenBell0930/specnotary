<p align="center">
  <img src="docs/assets/hero-banner.svg" alt="SpecNotary — forge dev-ready specs" width="100%"/>
</p>

<h1 align="center">SpecNotary</h1>

<p align="center">
  <strong>Forge vague requirements into dev-ready specs — writing + a hard gate in one suite.</strong><br/>
  <strong>For product managers.</strong> You do three things: <strong>hand over raw material, confirm the result, take the pack to review.</strong><br/>
  <strong>Recommended: Cursor or Codex</strong> (can edit files and run commands). Try the playground first; for your own work, hand the <strong>local folder</strong> to the assistant. You do not operate internal tools.
</p>

<p align="center">
  <a href="README.md">简体中文</a> · English
</p>

<p align="center">
  <a href="#value">Value</a> ·
  <a href="#overview">Overview</a> ·
  <a href="#demo">Demo</a> ·
  <a href="#quick-start">Quick Start</a> ·
  <a href="#gates">Gates</a> ·
  <a href="#examples">Examples</a> ·
  <a href="#structure">Structure</a> ·
  <a href="#docs">Docs</a>
</p>

<p align="center">
  <img alt="try" src="https://img.shields.io/badge/try-browser%20playground-0B6BCB"/>
  <img alt="gate" src="https://img.shields.io/badge/gate-FAIL%20%7C%20WARN%20%7C%20Pending-DC2626"/>
  <img alt="runtime" src="https://img.shields.io/badge/hard%20gate-Python-159947"/>
  <img alt="llm" src="https://img.shields.io/badge/LLM%20in%20gate-zero-0B6BCB"/>
  <img alt="license" src="https://img.shields.io/badge/license-MIT-0B6BCB"/>
  <img alt="node" src="https://img.shields.io/badge/Node-Deferred-94A3B8"/>
  <img alt="author" src="https://img.shields.io/badge/by-OwenBell-0F172A"/>
</p>

> How this relates to workflow-style SDD tools: [`docs/positioning.md`](docs/positioning.md). Not affiliated with the CNCF Notary Project (OCI artifact signing).

---

<a id="value"></a>

## Value · the problem

**Both goals must hold:**

1. **Dev-ready** — engineering can start from the tables; QA can accept from the ACs
2. **Review-ready** — before review you can show an evidence chain: source snapshots unchanged and the coverage ledger closed, assumptions and pendings registered and blocked when they shouldn't be, human view byte-identical to the machine source, prototype markers not dangling

**One line:** forge vague PRDs / tickets / FAQs into buildable specs; slogan-grade “fake detail” fails a deterministic gate.

> What PASS does and does not prove: [`docs/proof-boundary.md`](docs/proof-boundary.md) — PASS ≠ the business is right; PASS = structure and evidence chain are closed.

| Pain | What SpecNotary does |
|------|---------------------|
| A long write-up still leaves visibility, copy, and defaults to guesswork | Human view requires wireframes · control tables · state/action matrices · numbered main paths |
| “smart / ASAP / great UX” shipped as a spec | Hard `FAIL`: vague given/when/then, known empty-talk / placeholder AC phrasing, placeholder ui/defaults |
| Human doc and machine truth drift apart | Machine YAML is the **single source of truth**; the human view is generated; hand-editing it fails the gate |
| Review cannot show which source sentence became which spec line | SourceClaim ledger: every **registered** source item has a disposition, every required entity has a claim, source bytes are hash-pinned (ledger completeness is sampled by humans — see [proof boundary](docs/proof-boundary.md)) |
| Prototype and spec evolve separately | PrototypeManifest + HTML `data-spec-id` marker check |
| Open questions pretending to be ready | `Pending` needs five fields; still open on `ready` → `FAIL` |
| No Python, so no hard gate | Skill can run a degraded check, which must be labelled `gate_mode: degraded`; Node CLI = Deferred |

<p align="center">
  <img src="docs/assets/ipo-flow.svg" alt="Input → Process → Output" width="100%"/>
</p>

### Who uses it · when

**You do three things:**

1. **Hand over raw material** — send the original write-up to an AI assistant
2. **Confirm the result** — check the spec and the page draft; assumptions that were not in the source need your yes
3. **Take it to review** — bring the assistant's self-check report to the meeting

Start with [`playground/index.html`](playground/index.html) and click the sample buttons. For your own work: hand the <strong>local folder</strong> to Cursor or Codex and ask it to install and follow [`skills/SKILL.md`](skills/SKILL.md). Product managers do not operate internal tools.

| Situation | What you do |
|-----------|-------------|
| A new request lands | Hand over the original notes, confirm the spec and page draft, take the pack to the meeting |
| Before a requirements review | Check coverage notes, confirmed assumptions, and whether fake detail was blocked |
| Hand-off to engineering | Use the buttons, states, and acceptance sentences in the spec |
| Hand-off to QA | Use the acceptance sentences and empty-state copy as case input |
| Post-mortem on a fake-detail draft | Compare `case-order-cancel-bad`: which phrasings the gate rejects |

**Not this:** not another slogan template, and not project management or multiplayer online editing. Upstream docs stay **raw material**; the formal output is a **dev-ready requirements spec** (also used to close review). Documents from other tools can be registered as sources; they are not auto-converted into SpecNotary's machine format.

### Capability status (honest tiers)

> Product managers only need the three steps above. This table is for assistants and maintainers, not a checklist for you to run.

| Capability | Status | Notes |
|------------|--------|-------|
| YAML/JSON machine validation (schema + rules) | **Available** | `specnotary check` / `./cli/run-check.sh` |
| Start a case / register another source | **Available** | `specnotary new --from` · `specnotary ingest --spec` (pins hash; does not invent claims) |
| WARN acceptance ledger | **Available** | `specnotary confirm --by --reason --accept-all-warn` (who / when / why; stale ids FAIL on ready) |
| Ready-gap report | **Available** | `specnotary check --explain` prints `READY-GAP` |
| Human construction view | **Available** | `specnotary human` (refuses to write on FAIL) |
| One-command derivative sync | **Available** | `specnotary sync`: regenerate human view + re-run the gate; prototype attestation needs explicit `--attest-prototype` |
| FAIL / WARN / Pending layers | **Available** | See `docs/gate-modes.md` |
| Generic `action_matrix` (non-order example) | **Available** | See `examples/case-list-search/` |
| Skill drafting / degraded check | **Available** | Degraded must be labelled `degraded` |
| Source coverage (SourceClaim) | **Available** | On ready every source needs a real path + content_hash; deleting path cannot bypass; required entities must be cited; `specnotary report` writes the PM self-check report |
| Global human view (TOC / overview / features / architecture / duties / data contracts / error codes / decisions) | **Available** | renderer v11; machine IDs expanded to Chinese; mermaid diagrams generated deterministically |
| Decision-log gate | **Available** | Undecided `decisions` FAIL on `ready` |
| Human hash / stale detection | **Available** | `spec_hash` + byte-identical body + `renderer_version`; editing only the body still FAILs |
| Prototype manifest consistency | **Available** | manifest hash + real-file `data-spec-id` attributes (HTML/React/Vue; script strings do not count); no manifest → skip + WARN |
| Marker retrofit on existing trees | **Available** | `specnotary markers`: listed / illegal / still-to-fill `data-spec-id` |
| Dangling-id check | **Available** | Prose mentions of `P-*`/`AC-*`/`SRC-*` must exist |
| Mutation coverage metric | **Available** | `tests/test_mutations.py`: operator × object family, prints `KILL_RATE`, runs in CI |
| Docs-do-not-drift self-check | **Available** | `tests/test_doc_consistency.py`: capability wording / version / subcommands / flags vs code |
| pip install | **Available** | After clone, `pip install .` (not on PyPI yet) |
| Machine verdict output | **Available** | `specnotary check --json` includes `fail_by_layer` (machine/source/human/prototype) |
| English human view | **Available** | `specnotary human --lang en`; Chinese output is byte-stable |
| pre-commit hook | **Maintainer optional** | The assistant can run the CLI locally. Not the product-manager path, and not team online collaboration |
| GitHub Action | **Not the product path** | Code exists. Current use: give the folder to an assistant that runs the check locally |
| MCP server | **Not the product path** | Code exists. The assistant follows the Skill and runs commands; no extra protocol required |
| Try it in the browser | **Available** | [`playground/`](playground/index.html): zero install; click to see a bad spec get rejected |
| Hand to an agent to write your own spec | **Available** | PM supplies raw material and confirms; the agent drafts and gates per the Skill |
| Node-equivalent hard gate | **Deferred** | stubs refuse; they never fake a hard PASS |
| Hosted web service | **Deferred** | — |

---

<a id="overview"></a>

## Overview · what the suite looks like

Product managers can skip this section. It describes the internals the assistant actually uses.

**Carriers:**

| Layer | What it is | Duty |
|-------|------------|------|
| **CLI** (primary · Python) | `specnotary new / ingest / check / human / report / confirm / sync` (or `cli/run-*.sh` without install) | Pin sources; hard gate; machine → human; coverage report; WARN ledger; hash-chain sync |
| **Scaffold** (primary) | `templates/` · `examples/` | Field conventions and construction-grade samples |
| **Skill** (auxiliary) | `skills/` | Draft the machine source; degraded check when no runtime |

<p align="center">
  <img src="docs/assets/flow.svg" alt="SpecNotary main flow" width="100%"/>
</p>

**Available capabilities (short)**

| Capability | In plain words |
|------------|----------------|
| Machine-first | Edit YAML/JSON; human view is generated by the CLI; default is no generate on FAIL |
| Construction-grade human | Wireframe · control table · state/action matrix · numbered main path · AC · Pending |
| Hard CLI gate | Python: `FAIL_COUNT` must be 0; schema + ID/ref checks |
| Degraded Skill | Usable without Python; the result must be labelled `degraded` |

---

<a id="demo"></a>

## Demo · speak with a real spec

<p align="center">
  <img src="docs/assets/before-after.svg" alt="Fake detail vs construction density" width="100%"/>
</p>

A slice of the “unshipped order cancel” human view — wireframe, control visibility, failure copy as written.  
People stay because they can **build from this table**, not because of slogans.

### Excerpt · controls

| Control | Copy | Shown when | Failure copy |
|---------|------|------------|--------------|
| `btn_cancel` | Cancel order | Buyer self and state ∈ {unpaid,paid_unshipped} and risk check did not block | — |
| `btn_cancel_disabled` | Cancel order (disabled) | state ∈ {fulfilling,shipped} | Current order state does not allow self-service cancel; contact support or use after-sales |
| `dlg_confirm_ok` | Confirm cancel | Dialog open | Cancel failed, try again later (network / payment channel errors) |

### Excerpt · state matrix

| State | Buyer self-cancel | Notes |
|-------|-------------------|-------|
| `unpaid` | Allowed | Close the order, release coupon, no refund ticket |
| `paid_unshipped` | Allowed | Original-path refund + restock; coupons are not auto-returned |
| `fulfilling` / `shipped` | Forbidden | `not_allowed` copy as written |

Full sample:

- Machine → [`examples/case-order-cancel-raw/machine/spec.yaml`](examples/case-order-cancel-raw/machine/spec.yaml)
- Human → [`examples/case-order-cancel-raw/human/spec.md`](examples/case-order-cancel-raw/human/spec.md)

---

<a id="quick-start"></a>

## Quick Start

**Product manager**

1. Open [`playground/index.html`](playground/index.html) and click the two sample buttons (one is rejected, one passes). No commands.
2. If it looks useful, give the **local folder** to Cursor, Codex, or another assistant that can edit files and run commands. Ask it to install and follow [`skills/SKILL.md`](skills/SKILL.md). You and engineering do not need to co-edit the spec on GitHub.
3. Send it your draft. You fill in what's missing, confirm the write-up, and take the review pack to the meeting.

Paste this to the assistant (you do not run it):

```text
Install SpecNotary from this folder (`pip install .`) and follow skills/SKILL.md strictly.
Ask me only: what raw material is still missing, whether the result is right, and where the review pack is.
Do not ask me to operate internal tools or edit internal files.
```

Steps the assistant runs are in [`skills/SKILL.md`](skills/SKILL.md). Shipped samples live in `examples/`.

**Regression:**

```bash
python3 tests/test_cli.py
```

> [!NOTE]
> **Scale:** compressing vague notes into a buildable spec is expensive — a 12-line ops note becomes a long spec. Use it for multi-state, multi-exception work; skip it for tiny tweaks.  
> If the assistant has no Python, it can only run a degraded check and must write `gate_mode: degraded`.  
> Node runtime = **Deferred**; it must not fake a formal verdict.

---

<a id="gates"></a>

## Gates

<p align="center">
  <img src="docs/assets/gate-layers.svg" alt="FAIL / WARN / Pending" width="100%"/>
</p>

<p align="center">
  <img src="docs/assets/cli-preview.svg" alt="CLI gate preview" width="100%"/>
</p>

| Layer | Meaning | Effect on RESULT |
|-------|---------|------------------|
| **FAIL** (in the PM report: “must fix”) | Hard block (vague then/AC, placeholder ui/defaults, broken refs, missing source file, human/prototype drift…) | Any 1 → **FAIL** |
| **WARN** (in the PM report: “needs your call”) | The spec filled in a guess the source did not state, or a clickable draft is still unverified | Alone does not fail; once someone accepts it, it stops nagging |
| **Pending** (in the PM report: “not decided yet”) | Open items need five fields: `id` / `missing` / `impact` / `owner` / `status` | Still open on `ready` → **FAIL** |

Details: [`docs/gate-modes.md`](docs/gate-modes.md)

---

<a id="examples"></a>

## Examples

| Case | Input | Gate | Open |
|------|-------|------|------|
| Order cancel · raw | Ops constraint list | PASS | [Open](examples/case-order-cancel-raw/) |
| Order cancel · bad | Fake-detail PRD → fixed draft | FAIL → PASS | [Open](examples/case-order-cancel-bad/) |
| Order cancel · FAQ | Support FAQ reverse-engineered | PASS | [Open](examples/case-order-cancel-ops-faq/) |
| List search | Product list search (non-order domain) | PASS | [Open](examples/case-list-search/) |

What kills a bad draft (examples): illegal Schema status, missing `ui` / `states` / `actors`, broken refs, then-clauses with “smart search / ASAP / great UX”, AC hitting the known empty-talk list, `ready` still holding `open_questions`.

More: [`examples/README.md`](examples/README.md)

---

<a id="structure"></a>

## Structure

<p align="center">
  <img src="docs/assets/architecture.svg" alt="CLI / Scaffold / Skill layout" width="100%"/>
</p>

| Path | Role |
|------|------|
| [`src/specnotary/`](src/specnotary/) | Python package: gate rules, renderer, schemas (what `pip install` ships) |
| [`cli/`](cli/) | No-install wrappers: `run-check.sh` · `run-generate-human.sh` · `run-report.sh` · `run-sync.sh` |
| [`templates/`](templates/) | Machine / human / prototype-manifest conventions (the template itself passes the gate) |
| [`examples/`](examples/) | Construction-grade samples (aligned + deliberately drifted prototypes) |
| [`skills/`](skills/) | Auxiliary: drafting and degraded checks |
| [`docs/what-is-dev-ready.md`](docs/what-is-dev-ready.md) | What “dev-ready” means |
| [`docs/human-view.md`](docs/human-view.md) | Human prose in Chinese; machine IDs only for reconciliation |

**Artifact roles**

| Artifact | Role |
|----------|------|
| Machine YAML/JSON | **Single source of truth** (edit here) |
| Human Markdown | The spec / construction view of the same contract (generated by the CLI) |
| Upstream PRD / ticket / FAQ | **Raw material**, not SpecNotary's formal output name |

**Rule:** samples are fictional; do not put a real business master into the SpecNotary product tree.

---

<a id="docs"></a>

## Documentation

| Doc | Contents |
|-----|----------|
| [`docs/what-is-dev-ready.md`](docs/what-is-dev-ready.md) | What “dev-ready” means |
| [`docs/gate-modes.md`](docs/gate-modes.md) | hard / degraded; source coverage and stale |
| [`docs/positioning.md`](docs/positioning.md) | Relation to GitHub spec-kit / OpenSpec (their docs can be ingested; no one-click Markdown-to-YAML) |
| [`docs/empty-talk-corpus.md`](docs/empty-talk-corpus.md) | Empty-talk good/bad sentence set (known list, not general NLP) |
| [`docs/skill-boundary.md`](docs/skill-boundary.md) | CLI vs Skill boundary |
| [`docs/release-checklist.md`](docs/release-checklist.md) | Public-release technical checklist |
| [`CHANGELOG.md`](CHANGELOG.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md) · [`SECURITY.md`](SECURITY.md) | Versions · contributing · security |
| [`examples/README.md`](examples/README.md) | Case index |
| [`skills/SKILL.md`](skills/SKILL.md) | Skill rules |

---

## Status

OwenBell · SpecNotary public preview (v0.3.0) · [GitHub](https://github.com/OwenBell0930/specnotary) · Product path: playground + hand the folder to Cursor / Codex
