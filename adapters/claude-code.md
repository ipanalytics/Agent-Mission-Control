# Claude Code Adapter

Claude Code integration uses `CLAUDE.md` for stable project rules and a mission contract for task-specific scope. Agent Mission Control keeps the workflow file-based so it works in local repositories and CI workspaces.

## Bootstrap

```bash
amc agent bootstrap --target claude --root .
amc contract validate templates/contract.yaml
amc mission init --contract templates/contract.yaml --root /private/tmp/amc-smoke
amc plan create /private/tmp/amc-smoke/.mission-control/runs
amc plan goal /private/tmp/amc-smoke/.mission-control/runs
```

## Claude Code Prompt Shape

```text
Follow CLAUDE.md. Treat templates/contract.yaml as the scope boundary.
Follow the generated PROTOCOL.md and phases. Record command evidence, run scope check, generate final report, and replay the run before completion.
```

## Review Path

1. Inspect `.mission-control/runs/<run-id>/state.json`.
2. Review `evidence/scope-ledger.json`.
3. Review `evidence/command-evidence.jsonl`.
4. Read `final-report.md` and `pr-summary.md`.
5. Run `amc mission replay .mission-control/runs`.
