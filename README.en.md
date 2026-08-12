<p align="center">
  <img src="docs/assets/hero-banner.svg" alt="SpecAnvil — forge dev-ready specs" width="100%"/>
</p>

<h1 align="center">SpecAnvil</h1>

<p align="center">
  <strong>ESLint for your specs — a deterministic hard gate that rejects vague requirements before anyone (or any agent) writes code.</strong><br/>
  Machine-readable YAML as the single source of truth · generated human construction-grade view · FAIL / WARN / Pending verdicts · zero LLM in the gate
</p>

<p align="center">
  <a href="README.md">简体中文</a> · English
</p>

<p align="center">
  <img alt="gate" src="https://img.shields.io/badge/gate-FAIL%20%7C%20WARN%20%7C%20Pending-DC2626"/>
  <img alt="runtime" src="https://img.shields.io/badge/hard%20gate-Python%20only-159947"/>
  <img alt="llm" src="https://img.shields.io/badge/LLM%20in%20gate-zero-0B6BCB"/>
  <img alt="license" src="https://img.shields.io/badge/license-MIT-0B6BCB"/>
</p>

---

## Why

Specs fail teams in ways linters never let code fail them:

| Pain | What SpecAnvil does |
|------|---------------------|
| "smart search, great UX, as fast as possible" shipped as a spec | Hard `FAIL`: vague given/when/then, unobservable acceptance criteria, placeholder ui/defaults |
| Human doc and machine truth drift apart | Human view is **generated** from machine YAML; hand-editing it fails the gate (`body_hash`) |
| Nobody can prove the source material was covered | SourceClaim ledger: every statement gets a disposition (covered / omitted / assumption / conflict), every required entity needs a claim |
| Prototype quietly diverges from the spec | Prototype manifest + `data-spec-id` DOM markers verified against the spec hash |
| "Ready" specs full of open questions | Pending items and undecided decisions **block** `status: ready` |

The gate is **deterministic**: schema + rules + hash chains. No LLM, no API key, no network, no telemetry. LLMs are welcome to *draft* specs (that is the Skill layer); they never get to *judge* them.

## Quick start

```bash
pip install .            # or: uvx specanvil ... (after PyPI release)

# Watch a fake-detailed PRD get rejected
specanvil check examples/case-order-cancel-bad/machine/spec.yaml

# And its fixed version pass
specanvil check examples/case-order-cancel-bad/machine/spec.fixed.yaml

# Start your own spec
cp templates/machine/spec.template.yaml my-feature/machine/spec.yaml
specanvil check my-feature/machine/spec.yaml --explain   # READY-GAP tells you what ready still needs

# After editing the machine source: regenerate human view + refresh prototype hash
specanvil sync my-feature/machine/spec.yaml

# English human view
specanvil human my-feature/machine/spec.yaml out.md --lang en
```

## What you get

- **`specanvil check`** — the hard gate; `--json` for CI, `--explain` for the ready gap.
- **`specanvil human`** — a construction-grade human view (TOC, overview, architecture diagram, responsibilities, data contracts, state matrix, numbered main path, error codes, decision log) rendered from the machine source; diagrams are auto-generated or stored in the spec, so they cannot drift.
- **`specanvil report`** — review-readiness evidence: source coverage buckets + prototype drift buckets.
- **`specanvil sync`** — one command to keep the hash chain intact after edits.
- **`specanvil markers`** — retrofit helper: diff `data-spec-id` markers in an existing HTML/React/Vue tree against spec entities.
- **`specanvil mcp`** — stdio MCP server so agents can call the gate as a tool (experimental).
- **GitHub Action** (`action.yml`) — PR annotations from gate verdicts; **pre-commit hook** included.

## How it relates to GitHub spec-kit / OpenSpec

They orchestrate *how humans and agents work through* specs; SpecAnvil verifies *whether the spec itself is buildable and review-ready*. Use them together: their output is SpecAnvil's raw material. Details: [`docs/positioning.md`](docs/positioning.md).

## Honest capability tiers

Everything advertised above is implemented and tested (57+ regression tests, each gate rule has a failing-input test). Node runtime and web UI are explicitly **Deferred** — the stubs refuse to fake a hard PASS rather than shipping a second rule set.

## License

MIT © OwenBell
