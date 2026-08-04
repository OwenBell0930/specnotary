# 门禁模式 / Gate modes

| Mode | When | Authority |
|------|------|-----------|
| `hard` | Python or Node CLI ran successfully against machine source | Pass/fail is authoritative for local release steps |
| `degraded` | No runtime; Skill + LLM performed check/transform | Advisory only; must show `gate_mode: degraded`; cannot satisfy “CLI tests green” alone for GitHub upload checklist |

Upload to GitHub still requires the nine-step agreement: prefer restoring `hard` mode before claiming automated tests passed.
