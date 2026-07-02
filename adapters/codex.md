# Codex Adapter

Codex integration uses two repository-local files: `AGENTS.md` for stable operating rules and `contract.yaml` for task boundaries. Agent Mission Control provides both the run layout and CLI checks used by the agent during a `/goal` workflow.

## Bootstrap

```bash
amc agent bootstrap --target codex --root .
amc contract validate templates/contract.yaml
amc mission init --contract templates/contract.yaml --root /private/tmp/amc-smoke
```

## Codex Prompt Shape

```text
Use AGENTS.md as the repository runbook. Work inside templates/contract.yaml.
Record command evidence, run scope check, generate final report, and replay the run before completion.
```

## Review Path

1. Inspect `.mission-control/runs/<run-id>/state.json`.
2. Review `evidence/scope-ledger.json`.
3. Review `evidence/command-evidence.jsonl`.
4. Read `final-report.md` and `pr-summary.md`.
5. Run `amc mission replay .mission-control/runs`.
