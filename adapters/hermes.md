# Hermes Adapter

Hermes should act as the executor. Agent Mission Control supplies the contract,
scope checks, command-risk checks, evidence files, reports, and replay path.

## Bootstrap

```bash
amc agent bootstrap --target hermes --root .
amc contract validate templates/contract.yaml
amc mission init --contract templates/contract.yaml --root /private/tmp/amc-smoke
```

For repositories shared by Codex, Claude Code, and Hermes:

```bash
amc agent bootstrap --target both --root .
```

`both` writes `AGENTS.md`, `CLAUDE.md`, and `HERMES.md`.

## Goal-Style Prompt

```text
Follow HERMES.md. Execute the task in templates/contract.yaml.
Stay inside allowed paths. Classify risky commands before execution.
Record command evidence, run scope check, generate final report, and replay the run.
```

## Review Path

1. Inspect `.mission-control/runs/<run-id>/state.json`.
2. Review `evidence/scope-ledger.json`.
3. Review `evidence/command-evidence.jsonl`.
4. Read `final-report.md` and `pr-summary.md`.
5. Run `amc mission replay .mission-control/runs`.

## Division Of Responsibility

| Layer | Responsibility |
|---|---|
| Hermes | Executes repository, terminal, desktop, and MCP tasks |
| Agent Mission Control | Defines scope, records evidence, checks commands, writes reports |
| Human review | Approves the final diff and operational impact |

