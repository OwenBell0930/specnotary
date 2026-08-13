<p align="center">
  <img src="docs/assets/hero-banner.svg" alt="SpecNotary — forge dev-ready specs" width="100%"/>
</p>

<h1 align="center">SpecNotary</h1>

<p align="center">
  <strong>ESLint for your specs — a deterministic hard gate that rejects vague requirements before anyone (or any agent) writes code.</strong><br/>
  Machine-readable YAML as the single source of truth · generated human construction-grade view · FAIL / WARN / Pending verdicts · zero LLM in the gate
</p>

<p align="center">
  <a href="README.md">简体中文</a> · English
</p>

> Formerly Spec Kit, then SpecAnvil — both renamed over collisions (github/spec-kit, specanvil.com). Not affiliated with the CNCF Notary Project (OCI artifact signing).

<p align="center">
  <img alt="gate" src="https://img.shields.io/badge/gate-FAIL%20%7C%20WARN%20%7C%20Pending-DC2626"/>
  <img alt="runtime" src="https://img.shields.io/badge/hard%20gate-Python%20only-159947"/>
  <img alt="llm" src="https://img.shields.io/badge/LLM%20in%20gate-zero-0B6BCB"/>
  <img alt="license" src="https://img.shields.io/badge/license-MIT-0B6BCB"/>
</p>

---

## Why

Specs fail teams in ways linters never let code fail them:

| Pain | What SpecNotary does |
|------|---------------------|
| "smart search, great UX, as fast as possible" shipped as a spec | Hard `FAIL`: vague given/when/then, unobservable acceptance criteria, placeholder ui/defaults |
| Human doc and machine truth drift apart | Human view is **generated** from machine YAML; hand-editing it fails the gate (`body_hash`) |
| Nobody can show what the source material became | SourceClaim ledger over a **pinned source snapshot** (`content_hash`): touch the source file and every claim goes stale; every required entity needs a claim |
| Prototype quietly diverges from the spec | Manifest + `data-spec-id` DOM markers; re-attesting after machine edits is an **explicit action** (`sync --attest-prototype`), never a side effect |
| "Ready" specs full of open questions | Pending items and undecided decisions **block** `status: ready` |

The gate is **deterministic**: schema + rules + hash chains. No LLM, no API key, no network, no telemetry. LLMs are welcome to *draft* specs (that is the Skill layer); they never get to *judge* them.

> What PASS does and does not prove is spelled out in [`docs/proof-boundary.md`](docs/proof-boundary.md) — PASS means the structure and evidence chain are closed over declared scope, not that the business content is correct.

## Quick start

```bash
pip install .            # or: uvx specnotary ... (after PyPI release)

# Watch a fake-detailed PRD get rejected
specnotary check examples/case-order-cancel-bad/machine/spec.yaml

# And its fixed version pass
specnotary check examples/case-order-cancel-bad/machine/spec.fixed.yaml

# Start your own spec
cp templates/machine/spec.template.yaml my-feature/machine/spec.yaml
specnotary check my-feature/machine/spec.yaml --explain   # READY-GAP tells you what ready still needs

# After editing the machine source: regenerate the human view (a real derivation)
specnotary sync my-feature/machine/spec.yaml
# The prototype is not regenerated here — re-verify it, then endorse explicitly:
specnotary sync my-feature/machine/spec.yaml --attest-prototype

# English human view
specnotary human my-feature/machine/spec.yaml out.md --lang en
```

## What you get

- **`specnotary check`** — the hard gate; `--json` for CI, `--explain` for the ready gap.
- **`specnotary human`** — a construction-grade human view (TOC, overview, architecture diagram, responsibilities, data contracts, state matrix, numbered main path, error codes, decision log) rendered from the machine source; diagrams are auto-generated or stored in the spec, so they cannot drift.
- **`specnotary report`** — review-readiness evidence: source coverage buckets + prototype drift buckets.
- **`specnotary sync`** — one command to keep the hash chain intact after edits.
- **`specnotary markers`** — retrofit helper: diff `data-spec-id` markers in an existing HTML/React/Vue tree against spec entities.
- **`specnotary mcp`** — stdio MCP server so agents can call the gate as a tool (experimental).
- **GitHub Action** (`action.yml`) — PR annotations from gate verdicts; **pre-commit hook** included.

## How it relates to GitHub spec-kit / OpenSpec

They orchestrate *how humans and agents work through* specs; SpecNotary verifies *whether the spec itself is buildable and review-ready*. Use them together: their output is SpecNotary's raw material. Details: [`docs/positioning.md`](docs/positioning.md).

## Honest capability tiers

Everything advertised above is implemented and regression-tested; the gate has been adversarially hardened — negative cases from an external red-team audit are now regression tests. Node runtime and web UI are explicitly **Deferred** — the stubs refuse to fake a hard PASS rather than shipping a second rule set. Proof boundary: [`docs/proof-boundary.md`](docs/proof-boundary.md).

## License

MIT © OwenBell
