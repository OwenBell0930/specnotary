<p align="center">
  <img src="docs/assets/hero-banner.svg" alt="SpecNotary — forge dev-ready specs" width="100%"/>
</p>

<h1 align="center">SpecNotary</h1>

<p align="center">
  <strong>Forge vague requirements into dev-ready specs — writing + a hard gate in one suite.</strong><br/>
  You do three things: hand over raw material, confirm the result, take the pack to review.<br/>
  Try it in the browser first, then give this repo to Cursor or Codex and ask it to install.
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
| "smart search, great UX, as fast as possible" shipped as a spec | Hard `FAIL`: vague given/when/then, known empty-talk / placeholder AC phrasing, placeholder ui/defaults |
| Human doc and machine truth drift apart | Human view is **generated** from machine YAML; hand-editing it fails the gate (`body_hash`) |
| Nobody can show what the source material became | SourceClaim ledger over a **pinned source snapshot** (`content_hash`): touch the source file and every claim goes stale; every required entity needs a claim |
| Prototype quietly diverges from the spec | Manifest + `data-spec-id` DOM markers; re-attesting after machine edits is an **explicit action** (`sync --attest-prototype`), never a side effect |
| "Ready" specs full of open questions | Pending items and undecided decisions **block** `status: ready` |

The gate is **deterministic**: schema + rules + hash chains. No LLM, no API key, no network, no telemetry. LLMs are welcome to *draft* specs (that is the Skill layer); they never get to *judge* them.

> What PASS does and does not prove is spelled out in [`docs/proof-boundary.md`](docs/proof-boundary.md) — PASS means the structure and evidence chain are closed over declared scope, not that the business content is correct.

## Quick start

1. Open [`playground/index.html`](playground/index.html) and click the two sample buttons (one is rejected, one passes). No commands.
2. Copy this folder to Cursor, Codex, or another assistant that can edit files and run commands, and ask it to install and follow [`skills/SKILL.md`](skills/SKILL.md). You do not need GitHub collaboration with engineering.
3. Send it your draft. You only fill in what's missing, confirm the write-up, and take the review pack to the meeting.

Paste this to the assistant (you do not run it):

```text
Install SpecNotary from this repo (`pip install .`) and follow skills/SKILL.md strictly.
Ask me only: what raw material is still missing, whether the result is right, and where the review pack is.
Do not ask me to operate internal tools or edit internal files.
```

Commands the assistant runs are in [`skills/SKILL.md`](skills/SKILL.md).

## What you get

- **`specnotary new`** / **`ingest`** — start a case from a raw file, or register another source (GitHub spec-kit markdown included). Pins `content_hash`; does not invent claims or YAML body.
- **`specnotary check`** — the hard gate; `--json` for CI, `--explain` for the ready gap.
- **`specnotary human`** — a construction-grade human view (TOC, overview, architecture diagram, responsibilities, data contracts, state matrix, numbered main path, error codes, decision log) rendered from the machine source; diagrams are auto-generated or stored in the spec, so they cannot drift.
- **`specnotary report`** — product-manager self-check report: Chinese handling labels, source-item ids explained, PASS/FAIL glossed.
- **`specnotary confirm`** — record who accepted remaining WARNs (`--by`, `--reason`, `--accept-all-warn` or `--accept <id>`).
- **`specnotary sync`** — one command to keep the hash chain intact after edits.
- **`specnotary markers`** — retrofit helper: diff `data-spec-id` markers in an existing HTML/React/Vue tree against spec entities.
- **`specnotary mcp`** — optional maintainer adapter so an agent can call the gate as a tool. Not the product-manager path; not team online collaboration.
- **GitHub Action** (`action.yml`) — optional if someone later puts specs on GitHub. Current use is: give the folder to an assistant that runs the CLI locally.

## How it relates to GitHub spec-kit / OpenSpec

They orchestrate *how humans and agents work through* specs; SpecNotary is the writing + gate suite that verifies *whether the spec itself is buildable and review-ready*. Register their `spec.md` with `specnotary ingest … --kind speckit` (hash pin only — no Markdown-to-YAML import). Details: [`docs/positioning.md`](docs/positioning.md).

## Honest capability tiers

Everything advertised above is implemented and regression-tested; the gate has been adversarially hardened — negative cases from an external red-team audit are now regression tests. Node runtime is explicitly **Deferred** (stubs refuse to fake a hard PASS). The in-browser try page is the first-class demo (client-side, not a hosted web service). Proof boundary: [`docs/proof-boundary.md`](docs/proof-boundary.md).

## License

MIT © OwenBell
