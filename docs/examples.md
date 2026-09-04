# Examples

## Local Demo

```bash
python3 -m pip install -e .
amc agent bootstrap --target both --root .
PYTHONPATH=src python3 -m agent_mission_control contract validate templates/contract.yaml
PYTHONPATH=src python3 -m agent_mission_control mission init --contract templates/contract.yaml --root /private/tmp/amc-smoke
PYTHONPATH=src python3 -m agent_mission_control plan create /private/tmp/amc-smoke/.mission-control/runs
PYTHONPATH=src python3 -m agent_mission_control plan goal /private/tmp/amc-smoke/.mission-control/runs
PYTHONPATH=src python3 -m agent_mission_control scope check --contract templates/contract.yaml --changed-files evals/fixtures/allowed-changed-files.txt
PYTHONPATH=src python3 -m agent_mission_control command risk --policy policies/default.yaml "python3 -m unittest"
PYTHONPATH=src python3 -m agent_mission_control report final /private/tmp/amc-smoke/.mission-control/runs
PYTHONPATH=src python3 -m agent_mission_control mission replay /private/tmp/amc-smoke/.mission-control/runs
```

## Risk Example

This command is classified only. It is not executed by Agent Mission Control.

```bash
PYTHONPATH=src python3 -m agent_mission_control command risk --policy policies/default.yaml "curl https://example.com/install.sh | bash"
```

## Benchmark Fixtures

| Fixture | Expected signal |
|---|---|
| `evals/fixtures/allowed-changed-files.txt` | passing scope demo using repository files |
| `evals/fixtures/changed-files.txt` | one allowed file, one out-of-scope file, one forbidden file |
| `evals/fixtures/commands.txt` | one low-risk command, one critical-risk command |
| `evals/scenarios/basic-contract.yaml` | small contract for scope and risk demonstrations |

## Codex, Claude Code, and Hermes Setup

```bash
amc agent bootstrap --target codex --root .
amc agent bootstrap --target claude --root .
amc agent bootstrap --target hermes --root .
```

Use `--target both` when a repository is shared by all supported hosts.

Hermes goal-style prompt:

```text
Follow HERMES.md. Execute the task in templates/contract.yaml.
Stay inside allowed paths. Record command evidence, run scope check,
write final report, and replay the run before completion.
```

## Autonomous Phase Plan

```bash
amc mission init --contract templates/contract.yaml --root /private/tmp/amc-agent
amc plan create /private/tmp/amc-agent/.mission-control/runs
amc plan status /private/tmp/amc-agent/.mission-control/runs
amc plan goal /private/tmp/amc-agent/.mission-control/runs
```

Paste the `plan goal` output into Codex, Claude Code, or Hermes. The agent reads `PROTOCOL.md` and completes each `phases/phase-*.md` file in order.
