# Architecture

Agent Mission Control is organized around a mission run. A run is a durable directory containing the contract, phase plan, protocol, state, events, evidence, verifier output, and final report.

## Components

- Planner: turns a user request into a contract-aware plan.
- Protocol writer: creates host-neutral instructions for long-running Codex, Claude Code, and Hermes execution.
- Builder: performs scoped implementation work.
- Scope checker: compares actual file changes against the contract.
- Command risk engine: classifies commands before and after execution.
- Evidence collector: records diffs, command output, screenshots, responses, and check results.
- Verifier: audits the completed work without trusting builder self-report.
- Reporter: writes the final mission report and safety score.
- Replay: reads state, event logs, evidence, scope ledgers, and report locations back in chronological order.

## Contract First

The contract is the source of truth for what the agent may touch and how the work should be verified. It should be explicit enough that the verifier can decide whether a completed run stayed inside scope.

Example fields:

```yaml
goal: "Implement a provider health dashboard"
allowed_paths:
  - src/dashboard/**
  - src/lib/providers/**
forbidden_paths:
  - .env
  - infra/production/**
allowed_commands:
  - npm test
  - npm run lint
network_policy: deny-by-default
max_files_changed: 25
rollback_on_failure: true
```

## Evidence First

Every claim in the final report should point back to evidence:

- Tests passed: command output is stored.
- Scope was respected: changed files are listed and checked.
- UI was verified: screenshots are stored.
- External calls were made: requests and responses are summarized.
- Risk was low: command classifications are logged.

## Phase Planning

`amc plan create` writes the execution plan into the run directory:

```text
PROTOCOL.md
goal.txt
phases/
  phase-01.md
  phase-02.md
  phase-03.md
  phase-04.md
  phase-05.md
```

The protocol is host-neutral. Codex, Claude Code, and Hermes all receive the same short goal string from `amc plan goal`; the detailed work lives in files so the agent can run for longer without depending on an oversized prompt.

## YAML Subset

Agent Mission Control 1.0 uses a dependency-free YAML subset for contracts and policies:

- top-level `key: value` mappings;
- top-level lists using indented `- item` entries;
- string, integer, boolean, and null scalar values;
- comments beginning with `#` outside quoted strings.

Nested mappings and anchors are not supported in 1.0. Use the included templates as the compatibility target.

## CLI Layout

Core commands:

- `agent bootstrap --target <codex|claude|hermes|both> --root <path>`
- `contract validate <path>`
- `mission init --contract <path> --root <path>`
- `plan create <run-dir>`
- `plan goal <run-dir>`
- `plan status <run-dir>`
- `scope check --contract <path> --changed-files <manifest>`
- `command risk --policy <path> <command>`
- `evidence add-command <run-dir>`
- `report final <run-dir>`
- `mission replay <run-dir>`
