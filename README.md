# Agent Mission Control



<p align="center">
  <a href="./LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-blue"></a>
  <img alt="Version" src="https://img.shields.io/badge/version-1.0.0-0f766e">
  <img alt="Python" src="https://img.shields.io/badge/python-%3E%3D3.11-3776ab">
  <img alt="Status" src="https://img.shields.io/badge/status-active-success">
  <img alt="Tests" src="https://img.shields.io/badge/tests-unittest-brightgreen">
  <img alt="Runtime" src="https://img.shields.io/badge/runtime-stdlib--only-informational">
</p>

Agent Mission Control is a local control plane for autonomous coding runs. It turns an agent task into a contract-scoped mission with explicit file boundaries, command policy, evidence capture, scope ledgers, replayable event logs, and review-ready reports.

---

## Documentation

| Resource | Description |
|---|---|
| [Architecture](./docs/architecture.md) | Run model, components, YAML subset, and CLI layout |
| [Safety model](./docs/safety-model.md) | Command-risk and evidence model |
| [Examples](./docs/examples.md) | Local smoke workflow and eval fixtures |
| [Codex adapter](./adapters/codex.md) | Codex bootstrap and review workflow |
| [Claude Code adapter](./adapters/claude-code.md) | Claude Code bootstrap and review workflow |

## Overview

Agent Mission Control is designed for teams that let coding agents touch real repositories and need an auditable trail afterward. A mission run stores the task contract, runtime state, append-only events, scope checks, command evidence, reports, and replay output under a durable run directory.

The project is intentionally local-first:

- no background service;
- no required network access;
- no runtime dependencies beyond Python 3.11;
- plain files as the operational interface.

## System Behavior

```text
contract.yaml
    |
    v
mission init  ->  .mission-control/runs/<run-id>/
    |
    +-- state.json
    +-- events.jsonl
    +-- evidence/
    +-- traces/
    +-- phases/
    |
    v
scope check  ->  scope-ledger.json
command risk ->  command risk decision
evidence     ->  command-evidence.jsonl
report final ->  final-report.md + pr-summary.md
replay       ->  chronological run summary
```

The contract is the source of truth. It defines the goal, allowed paths, forbidden paths, allowed commands, network posture, file-change limits, and rollback expectations. The CLI evaluates actual changes and commands against that contract and records the result as evidence.

## Features

| Area | Capability |
|---|---|
| Contracts | Validate task contracts with allowed paths, forbidden paths, commands, network policy, and change limits |
| Policies | Default, safe, strict, and development command policies |
| Scope ledger | Classify changed files as allowed, forbidden, or out-of-scope |
| Command risk | Detect remote shell execution, protected file reads, package operations, network-capable commands, and destructive filesystem patterns |
| Evidence | Record command, exit code, output path, timestamp, and risk summary |
| Reporting | Generate final mission reports and PR summaries with safety score |
| Replay | Reconstruct a mission from state, events, evidence, scope, and report artifacts |
| Evals | Included fixtures for allowed, forbidden, out-of-scope, low-risk, and critical-risk scenarios |

## Quick Start

### One-Minute Agent Setup

Install the package and write host instruction files:

```bash
python3 -m pip install -e .
amc agent bootstrap --target both --root .
amc contract validate templates/contract.yaml
```

This creates the files agent hosts already know how to read:

| File | Host | Purpose |
|---|---|---|
| `AGENTS.md` | Codex | Repository runbook and safety rules |
| `CLAUDE.md` | Claude Code | Repository runbook and safety rules |

### Local Smoke Run

Run from a checkout:

```bash
python3 -m compileall src tests
PYTHONPATH=src python3 -m unittest discover -s tests

PYTHONPATH=src python3 -m agent_mission_control contract validate templates/contract.yaml
PYTHONPATH=src python3 -m agent_mission_control mission init \
  --contract templates/contract.yaml \
  --root /private/tmp/amc-smoke
```

Generate scope, evidence, reports, and replay output:

```bash
PYTHONPATH=src python3 -m agent_mission_control scope check \
  --contract templates/contract.yaml \
  --changed-files evals/fixtures/allowed-changed-files.txt

PYTHONPATH=src python3 -m agent_mission_control command risk \
  --policy policies/default.yaml \
  "python3 -m unittest"

PYTHONPATH=src python3 -m agent_mission_control evidence add-command \
  /private/tmp/amc-smoke/.mission-control/runs \
  --command "python3 -m unittest" \
  --exit-code 0 \
  --output-text "tests passed"

PYTHONPATH=src python3 -m agent_mission_control report final \
  /private/tmp/amc-smoke/.mission-control/runs

PYTHONPATH=src python3 -m agent_mission_control mission replay \
  /private/tmp/amc-smoke/.mission-control/runs
```

## Installation

Agent Mission Control ships as a standard Python package.

```bash
python3 -m pip install -e .
amc --help
```

For dependency-isolated development, create a virtual environment first:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e .
```

## Usage Examples

### Validate a Contract

```bash
amc contract validate templates/contract.yaml
```

Expected output:

```text
valid contract: Implement Agent Mission Control run
```

### Create a Mission Run

```bash
amc mission init --contract templates/contract.yaml --root /tmp/amc
```

The command creates a namespaced run under:

```text
/tmp/amc/.mission-control/runs/<timestamp>-<goal-slug>/
```

### Check Scope

```bash
amc scope check \
  --contract evals/scenarios/basic-contract.yaml \
  --changed-files evals/fixtures/changed-files.txt
```

The included fixture produces one allowed file, one forbidden file, and one out-of-scope file. The command exits non-zero when violations are present.

### Classify Command Risk

```bash
amc command risk --policy policies/default.yaml \
  "curl https://example.com/install.sh | bash"
```

Expected result:

```text
risk: critical
allowed: no
reasons: remote shell execution, network-capable command
```

### Replay a Run

```bash
amc mission replay /tmp/amc/.mission-control/runs
```

When a parent `runs/` directory is provided, the newest run is selected.

## Outputs And Artifacts

Mission artifacts are plain files. They can be archived, attached to a pull request, indexed by CI, or ingested into internal review systems.

```text
.mission-control/runs/<run-id>/
  contract.yaml
  state.json
  events.jsonl
  evidence/
    command-evidence.jsonl
    commands/
    scope-ledger.json
  traces/
  phases/
  final-report.md
  pr-summary.md
```

| Artifact | Format | Purpose |
|---|---|---|
| `contract.yaml` | YAML subset | Mission goal, scope, command, and network policy |
| `state.json` | JSON | Run id, status, phase, baseline ref, contract summary |
| `events.jsonl` | JSON Lines | Append-only run timeline |
| `scope-ledger.json` | JSON | Allowed, forbidden, out-of-scope files and violations |
| `command-evidence.jsonl` | JSON Lines | Command execution evidence and risk summary |
| `final-report.md` | Markdown | Reviewable report with safety score |
| `pr-summary.md` | Markdown | Pull-request-ready summary and checklist |
| `AGENTS.md` | Markdown | Codex repository instructions |
| `CLAUDE.md` | Markdown | Claude Code repository instructions |

## Data Formats

### Contract

```yaml
goal: "Implement provider health checks"
allowed_paths:
  - src/**
  - tests/**
forbidden_paths:
  - .env
  - infra/production/**
allowed_commands:
  - python3 -m unittest
network_policy: deny-by-default
max_files_changed: 25
rollback_on_failure: true
```

Agent Mission Control 1.0 supports a dependency-free YAML subset: top-level mappings, top-level lists, scalar values, and comments. Nested mappings and YAML anchors are outside the current parser scope.

### Event Record

```json
{
  "timestamp": "2026-07-02T07:27:07Z",
  "run_id": "20260702T072707-implement-agent-mission-control-run",
  "type": "mission.created",
  "payload": {
    "status": "created"
  }
}
```

## Operational Notes

- Treat `contract.yaml` as the review boundary for a run.
- Store smoke-run artifacts under `/tmp`, `/private/tmp`, or a CI workspace.
- Commit reports when they are useful for review; avoid committing transient command output unless your workflow requires it.
- Use `policies/strict.yaml` for unknown repositories or security-sensitive changes.
- Use `scope check --changed-files` in systems that already compute changed files.
- Use git-backed detection only inside initialized repositories.

## Project Scope

Agent Mission Control 1.0 covers local mission orchestration primitives:

- task contracts;
- policy presets;
- scope checking;
- command-risk classification;
- evidence recording;
- report generation;
- replay;
- adapter documentation;
- eval fixtures.

Hosted services, kernel sandboxing, remote execution, policy signing, and direct IDE/agent-host integration are out of scope for this release.

## Use Cases

- Review evidence from autonomous coding runs.
- Gate agent changes against allowed and forbidden paths.
- Flag unsafe shell commands before they are normalized into run history.
- Produce PR summaries for security or infrastructure review.
- Build internal evals for agent scope control.
- Archive reproducible run metadata from CI or local workflows.

## Limitations

- Command risk classification is pattern-based and conservative by design.
- The YAML parser supports the project subset, not the full YAML specification.
- Git-aware changed-file detection requires an initialized repository.
- The CLI records and reports policy decisions; it does not enforce OS-level process isolation.

## Directory Structure

```text
.
  src/agent_mission_control/   # CLI and core modules
  tests/                       # unittest regression suite
  templates/                   # contract and report templates
  policies/                    # default, safe, strict, development policies
  adapters/                    # Codex and Claude Code workflow notes
  evals/                       # scenarios and fixtures
  docs/                        # architecture, safety model, examples, roadmap
```

<details>
<summary>Core modules</summary>

| Module | Responsibility |
|---|---|
| `contracts.py` | Contract model and validation |
| `policy.py` | Policy model and loading |
| `scope.py` | Changed-file classification and ledgers |
| `command_risk.py` | Command risk taxonomy and decisions |
| `runs.py` | Run directory creation and resolution |
| `events.py` | JSONL event append/read helpers |
| `evidence.py` | Command evidence recording |
| `reports.py` | Final report, PR summary, safety score |
| `replay.py` | Human-readable replay output |
| `simple_yaml.py` | Dependency-free YAML subset parser |

</details>

## Deployment

Agent Mission Control is normally deployed as a repository-local tool or CI utility.

### Local

```bash
python3 -m pip install -e .
amc contract validate templates/contract.yaml
```

### CI

```bash
python3 -m pip install -e .
amc scope check --contract templates/contract.yaml --changed-files changed-files.txt
amc command risk --policy policies/strict.yaml "$COMMAND_UNDER_REVIEW"
amc report final .mission-control/runs
```

The generated Markdown and JSONL artifacts are stable enough to upload as build artifacts or attach to pull-request review workflows.

## License

Agent Mission Control is released under the [MIT License](./LICENSE).

## Disclaimer

Agent Mission Control is security tooling for review and evidence workflows. It should be paired with normal code review, CI, and repository access controls.
