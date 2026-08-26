<p align="center">
  <img src="docs/assets/hero-banner.svg" alt="SpecNotary — review-ready product requirements" width="100%"/>
</p>

<h1 align="center">SpecNotary</h1>

<p align="center">
  <strong>Turn scattered requirements into a product proposal ready for serious review.</strong><br/>
  <strong>Built for product managers and product operations teams.</strong> High-quality Draft, Product Review, and deterministic Structure Gate in one workflow.<br/>
  Keep reviews focused on <strong>goals, boundaries, product and information architecture, business flows, and UX</strong>.<br/>
  <strong>Agent-first:</strong> send <a href="https://github.com/OwenBell0930/specnotary">github.com/OwenBell0930/specnotary</a> to Cursor or Codex and use it directly in your current workspace.
</p>

<p align="center">
  <a href="#quick-start"><strong>Get started</strong></a> ·
  <a href="https://owenbell0930.github.io/specnotary/playground/">Live playground</a> ·
  <a href="examples/product-review-fixture/reports/product-review.md">Product review sample</a>
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
  <img alt="audience" src="https://img.shields.io/badge/for-Product%20Managers-7C3AED"/>
  <img alt="workflow" src="https://img.shields.io/badge/workflow-Draft%20%7C%20Review%20%7C%20Gate-0B6BCB"/>
  <img alt="agents" src="https://img.shields.io/badge/agents-Cursor%20%7C%20Codex-159947"/>
  <img alt="traceable" src="https://img.shields.io/badge/output-review--ready-0F766E"/>
  <img alt="license" src="https://img.shields.io/badge/license-MIT-0B6BCB"/>
  <img alt="author" src="https://img.shields.io/badge/by-OwenBell-0F172A"/>
</p>

---

<a id="value"></a>

## Value · at a glance

**Who it is for:** product managers turning ambiguous business needs into clear product proposals, and product operations teams standardizing requirement quality.

**Where it fits:** from incoming PRDs, tickets, meeting notes, FAQs, or rough ideas to the moment a requirements review begins.

**Core value:** move from “the document is written” to “the proposal can be reviewed effectively” — grounded goals and boundaries, clear product and information architecture, discussable flows and UX, and traceable assumptions, conflicts, and open decisions.

| Capability | What it helps you do | Standalone entry |
|------------|----------------------|------------------|
| **Draft · high-quality drafting** | Organize scattered inputs into a candidate product spec with goals, scope, roles, architecture, flows, interactions, exceptions, and decisions | `/draft-spec` |
| **Review · product-quality review** | Assess core correctness, boundary quality, architectural extensibility, flow logic, and UX against one quality model, with evidence-backed findings | `/review-spec` |
| **Gate · deterministic structure gate** | Check structure, source traceability, machine/human consistency, and optional prototype mapping with reproducible results | `/gate-spec` |

Use `/write-spec` for the full workflow. Teams with an existing proposal can run Review + Gate only. All three share one [product quality model](docs/product-quality-model.md), while keeping their verdicts separate.

### What you get

- **Standard product spec** for reading, discussion, and review
- **Machine-readable requirement source** for Cursor, Codex, and other agents
- **Product-quality review report** with strengths, risks, evidence, and decisions needed
- **Structure-gate result** covering structure, traceability, and document drift
- **Optional prototype traceability** mapping screens back to spec items when a prototype is selected

| Before | With SpecNotary |
|--------|-----------------|
| Inputs are scattered across documents, tickets, and conversations | One review pack with source links and decision records |
| Goals, boundaries, or flow gaps surface during the meeting | Draft and Review help expose the critical gaps before review |
| A document looks complete but product quality remains unclear | Product quality and structural completeness receive separate verdicts |
| Human docs, machine specs, and prototypes evolve independently | A source of truth, hashes, and mappings keep them traceable |

<p align="center">
  <img src="docs/assets/ipo-flow.svg" alt="Input → Process → Output" width="100%"/>
</p>

### Three steps to prepare for review

**You do three things:**

1. **Hand over the inputs** — give the assistant requirement notes, tickets, meeting notes, or an existing proposal
2. **Confirm key decisions** — verify goals, boundaries, architecture, flows, and explicitly listed assumptions
3. **Take the pack to review** — enter the meeting with the standard spec, product review report, and gate result

The fastest path: send Cursor or Codex the [GitHub URL](https://github.com/OwenBell0930/specnotary) and ask it to install and follow [`skills/specnotary/SKILL.md`](skills/specnotary/SKILL.md). Specs stay in your business workspace; product managers do not need to operate the CLI.

**Individual PMs** can run the complete flow to improve a proposal. **Product operations teams** can invoke Review + Gate only to standardize existing documents.

**Product boundary:** focused on the PM journey from incoming requirement material to a standard proposal for requirements review; engineering implementation and QA delivery continue in the team's existing systems.

<details>
<summary><strong>Maintainer capability matrix (click to expand)</strong></summary>

> This table lets assistants and maintainers verify implementation status. Product managers can stay with the three steps above.

| Capability | Status | Notes |
|------------|--------|-------|
| YAML/JSON machine validation (schema + rules) | **Available** | `specnotary check` / `./cli/run-check.sh` |
| Start a case / register another source | **Available** | `specnotary new --from` · `specnotary ingest --spec` (pins hash; does not invent claims) |
| WARN acceptance ledger | **Available** | `specnotary confirm --by --reason --accept-all-warn` (who / when / why; stale ids FAIL on ready) |
| Ready-gap report | **Available** | `specnotary check --explain` prints `READY-GAP` |
| Human review view | **Available** | `specnotary human` (refuses to write on FAIL) |
| One-command derivative sync | **Available** | `specnotary sync`: regenerate human view + re-run the gate; prototype attestation needs explicit `--attest-prototype` |
| FAIL / DRAFT / PASS and finding layers | **Available** | See `docs/gate-modes.md`; a structurally valid draft never impersonates a final PASS |
| Generic `action_matrix` (non-order example) | **Available** | See `examples/case-list-search/` |
| Skill drafting / independent review / degraded check | **Available** | `/write-spec` full flow; `/draft-spec` `/review-spec` `/gate-spec` separable; degraded must be labelled `degraded` |
| Product quality model (shared by Draft/Review) | **Available** | [`docs/product-quality-model.md`](docs/product-quality-model.md); review contract + anti-corpus; **not** in the Python hard gate |
| Source coverage (SourceClaim) | **Available** | On ready every source needs a real path + content_hash; deleting path cannot bypass; required entities must be cited; `specnotary report` writes the PM self-check report |
| Global human view (TOC / overview / features / product & information architecture / duties / data contracts / error codes / decisions) | **Available** | renderer v13; machine IDs expanded to Chinese; mermaid diagrams generated deterministically |
| Decision-log gate | **Available** | Undecided `decisions` FAIL on `ready` |
| Human hash / stale detection | **Available** | `spec_hash` + byte-identical body + `renderer_version`; editing only the body still FAILs |
| Prototype decision + manifest consistency | **Available** | `D-PROTOTYPE` must decide none/static HTML/local service/other; a selected prototype requires a manifest, while an explicit no-prototype choice creates no missing-manifest warning |
| Marker retrofit on existing trees | **Available** | `specnotary markers`: listed / illegal / still-to-fill `data-spec-id` |
| Dangling-id check | **Available** | Prose mentions of `P-*`/`AC-*`/`SRC-*` must exist |
| Mutation coverage metric | **Available** | `tests/test_mutations.py`: operator × object family, prints `KILL_RATE`, runs in CI |
| Docs-do-not-drift self-check | **Available** | `tests/test_doc_consistency.py`: capability wording / version / subcommands / flags vs code |
| pip install | **Available** | `pip install "git+https://github.com/OwenBell0930/specnotary.git"` (SpecNotary need not be the workspace; not on PyPI yet) |
| Machine verdict output | **Available** | `specnotary check --json` includes `fail_by_layer` (machine/source/human/prototype) |
| English human view | **Available** | `specnotary human --lang en`; Chinese output is byte-stable |
| pre-commit hook | **Maintainer optional** | The assistant can run the CLI locally. Not the product-manager path, and not team online collaboration |
| GitHub Action | **Not the product path** | Code exists. Current use: send the URL to an assistant that runs the check locally |
| MCP server | **Not the product path** | Code exists. The assistant follows the Skill and runs commands; no extra protocol required |
| Try it in the browser | **Available** | [`playground/`](playground/index.html): zero install; click to see a bad spec get rejected |
| Hand to an agent to write your own spec | **Available** | PM supplies raw material and confirms; the agent drafts and gates per the Skill |
| Node-equivalent hard gate | **Deferred** | stubs refuse; they never fake a hard PASS |
| Hosted web service | **Deferred** | — |

</details>

---

<a id="overview"></a>

## Overview · what the suite looks like

Product managers can skip this section. It describes the internals the assistant actually uses.

**Carriers (Agent is the PM-facing front door):**

| Layer | What it is | Duty |
|-------|------------|------|
| **Agent Skills / Commands** | `/write-spec` `/draft-spec` `/review-spec` `/gate-spec` + `skills/` | **PM-facing entry**: full flow or single capability |
| **CLI** (Python) | `specnotary check / human / report / sync / …` | **Structure Gate engine** (plus case setup/sync); not the PM's daily UI |
| **Scaffold / Schema / Docs** | `templates/` · `examples/` · `docs/` | Supporting assets: templates, samples, quality model, proof boundary |

<p align="center">
  <img src="docs/assets/flow.svg" alt="SpecNotary main flow" width="100%"/>
</p>

**Available capabilities (short)**

| Capability | In plain words |
|------------|----------------|
| Agent entry | Cursor/Codex follows Skills/Commands; PM only supplies material, confirms, takes the pack |
| Machine-first | Edit YAML/JSON; human view is generated by the CLI; default is no generate on FAIL |
| Product Review | Semantic review bound to `content_hash`; re-review after edits; separate from Gate |
| Hard CLI gate | Python Structure Gate: `FAIL_COUNT` must be 0; schema + ID/ref checks |
| Degraded Skill | Usable without Python; the result must be labelled `degraded` |

---

<a id="demo"></a>

## Demo · speak with a real spec

<p align="center">
  <img src="docs/assets/before-after.svg" alt="Fake detail vs review-spec density" width="100%"/>
</p>

A slice of the “unshipped order cancel” human view — wireframe, control visibility, failure copy as written.
A review succeeds when **each proposal can be judged from this table**, not because of slogans.

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
2. If it looks useful, send Cursor, Codex, or another assistant that can edit files and run commands the [GitHub URL](https://github.com/OwenBell0930/specnotary). Ask it to install and follow Skills/Commands. Specs live in whatever folder you already use; SpecNotary does not need to be the current workspace.
3. Pick the entry for your situation (the assistant runs it; you do not operate the CLI):

| Situation | Entry | Notes |
|-----------|-------|-------|
| Raw material → full review pack | `/write-spec` | Draft → Review (re-review after edits) → Gate; verdicts separate |
| Candidate draft only | `/draft-spec` | Draft only; no automatic Review/Gate |
| Existing doc: product-quality review only | `/review-spec` | Default: do not edit the subject; bind `content_hash` |
| Existing doc: Review + Gate | `/review-spec` then `/gate-spec` | Skip Draft; **plain Markdown cannot hard-PASS** — need a legal machine spec (or extract-only normalize/projection, then re-review, then Gate) |
| Structure gate only | `/gate-spec` | Legal machine spec only; Gate PASS ≠ sound product design |

Paste this to the assistant (you do not run it):

```text
Install SpecNotary from https://github.com/OwenBell0930/specnotary (it does not need to be the current workspace):
pip install "git+https://github.com/OwenBell0930/specnotary.git"
Follow that repo's skills/specnotary/SKILL.md strictly. Write the spec in the folder I already have open.
Ask me only: what raw material is still missing, whether the result is right, and where the review pack is.
Do not ask me to operate internal tools or edit internal files.
```

Steps the assistant runs are in [`skills/specnotary/SKILL.md`](skills/specnotary/SKILL.md). Shipped samples live in `examples/`.

**Regression:**

```bash
python3 tests/test_cli.py
```

> [!NOTE]
> **Scale:** turning vague notes into a review pack takes work — a 12-line ops note becomes a long spec. Use it for multi-state, multi-exception work; skip it for tiny tweaks.
> If the assistant has no Python, it can only run a degraded check and must write `gate_mode: degraded`.
> Node runtime = **Deferred**; it must not fake a formal verdict.

### Cursor Customize

The official catalog in Cursor's **Customize** sidebar is the [Marketplace](https://cursor.com/marketplace). SpecNotary already ships `.cursor-plugin/plugin.json` (skills + `/write-spec` `/draft-spec` `/review-spec` `/gate-spec`; no MCP). Listing requires submitting the public Git URL at [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish). Cursor reviews every plugin by hand; it appears in Customize only after that. Until then, send the GitHub URL to the assistant.

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
  <img src="docs/assets/architecture.svg" alt="Agent entry / CLI Gate engine / supporting assets" width="100%"/>
</p>

| Path | Role |
|------|------|
| [`src/specnotary/`](src/specnotary/) | Python package: Structure Gate, renderer, schemas |
| [`cli/`](cli/) | No-install wrappers: `run-check.sh` · `run-generate-human.sh` · `run-report.sh` · `run-sync.sh` |
| [`templates/`](templates/) | Machine / human / prototype-manifest conventions (the template itself passes the gate) |
| [`examples/`](examples/) | Review-grade samples (aligned + deliberately drifted prototypes) |
| [`skills/`](skills/) · [`commands/`](commands/) | **User entry**: full-flow + Draft / Review / Gate |
| [`docs/what-is-dev-ready.md`](docs/what-is-dev-ready.md) | What “review-ready” means (legacy filename retained) |
| [`docs/human-view.md`](docs/human-view.md) | Human prose in Chinese; machine IDs only for reconciliation |

**Artifact roles**

| Artifact | Role |
|----------|------|
| Machine YAML/JSON | **Single source of truth** (edit here) |
| Human Markdown | The spec / review view of the same contract (generated by the CLI) |
| Upstream PRD / ticket / FAQ | **Raw material**, not SpecNotary's formal output name |

**Rule:** samples are fictional; do not put a real business master into the SpecNotary product tree.

---

<a id="docs"></a>

## Documentation

| Doc | Contents |
|-----|----------|
| [`docs/what-is-dev-ready.md`](docs/what-is-dev-ready.md) | What “review-ready” means |
| [`docs/product-quality-model.md`](docs/product-quality-model.md) | Shared Draft/Review product quality model |
| [`docs/product-review-contract.md`](docs/product-review-contract.md) | Product-review report fields and verdicts |
| [`docs/product-review-corpus.md`](docs/product-review-corpus.md) | Structurally valid but product-bad anti-examples |
| [`docs/gate-modes.md`](docs/gate-modes.md) | hard / degraded; source coverage and stale |
| [`docs/proof-boundary.md`](docs/proof-boundary.md) | What the gate can and cannot prove |
| [`docs/positioning.md`](docs/positioning.md) | Relation to GitHub spec-kit / OpenSpec (their docs can be ingested; no one-click Markdown-to-YAML) |
| [`docs/empty-talk-corpus.md`](docs/empty-talk-corpus.md) | Empty-talk good/bad sentence set (known list, not general NLP) |
| [`docs/skill-boundary.md`](docs/skill-boundary.md) | CLI vs Draft/Review/Gate Skill boundary |
| [`docs/release-checklist.md`](docs/release-checklist.md) | Public-release technical checklist |
| [`CHANGELOG.md`](CHANGELOG.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md) · [`SECURITY.md`](SECURITY.md) | Versions · contributing · security |
| [`examples/README.md`](examples/README.md) | Case index |
| [`skills/specnotary/SKILL.md`](skills/specnotary/SKILL.md) | Default full-flow orchestrator |

---

## Status

OwenBell · SpecNotary public preview (v0.3.0) · [GitHub](https://github.com/OwenBell0930/specnotary) · Product path: playground + send the URL to Cursor / Codex; SpecNotary need not be the workspace
