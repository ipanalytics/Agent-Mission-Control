# Agent Mission Control Runbook

This repository uses Agent Mission Control for contract-scoped agent work.

## Standard Checks

- `python3 -m compileall src tests`
- `PYTHONPATH=src python3 -m unittest discover -s tests`
- `PYTHONPATH=src python3 -m agent_mission_control contract validate templates/contract.yaml`
- `PYTHONPATH=src python3 -m agent_mission_control plan create .mission-control/runs`
- `PYTHONPATH=src python3 -m agent_mission_control command risk --policy policies/default.yaml "python3 -m unittest"`

## Operating Rules

- Treat `templates/contract.yaml` as the default task contract.
- Keep generated mission artifacts under `.mission-control/runs/` or `/private/tmp`.
- Record command evidence for meaningful build, test, scope, and report commands.
- Use `plan create` before long-running autonomous work.
- Run `scope check` before reporting completion.
- Run `report final` and `mission replay` when a task changes repository files.
- Classify risky commands with `command risk`; do not execute remote installer pipelines.
- Do not read `.env`, SSH keys, credential files, or production secret material.

## Useful Commands

```bash
PYTHONPATH=src python3 -m agent_mission_control mission init --contract templates/contract.yaml --root /private/tmp/amc-smoke
PYTHONPATH=src python3 -m agent_mission_control plan create /private/tmp/amc-smoke/.mission-control/runs
PYTHONPATH=src python3 -m agent_mission_control plan goal /private/tmp/amc-smoke/.mission-control/runs
PYTHONPATH=src python3 -m agent_mission_control scope check --contract templates/contract.yaml --changed-files evals/fixtures/allowed-changed-files.txt
PYTHONPATH=src python3 -m agent_mission_control report final /private/tmp/amc-smoke/.mission-control/runs
PYTHONPATH=src python3 -m agent_mission_control mission replay /private/tmp/amc-smoke/.mission-control/runs
```

## Claude Code Notes

Claude Code reads `CLAUDE.md` from the repository. Keep task-specific details in
the mission contract and use this file for stable project rules.

Hermes uses the same contract and evidence model through `HERMES.md`.
