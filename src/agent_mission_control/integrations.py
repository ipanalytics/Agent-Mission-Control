from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class IntegrationError(ValueError):
    """Raised when agent-host integration files cannot be written."""


@dataclass(frozen=True)
class IntegrationFile:
    """A file that an agent host reads from the repository root."""

    path: Path
    content: str


COMMON_RULES = """\
# Agent Mission Control Runbook

This repository uses Agent Mission Control for contract-scoped agent work.

## Standard Checks

- `python3 -m compileall src tests`
- `PYTHONPATH=src python3 -m unittest discover -s tests`
- `PYTHONPATH=src python3 -m agent_mission_control contract validate templates/contract.yaml`
- `PYTHONPATH=src python3 -m agent_mission_control command risk --policy policies/default.yaml "python3 -m unittest"`

## Operating Rules

- Treat `templates/contract.yaml` as the default task contract.
- Keep generated mission artifacts under `.mission-control/runs/` or `/private/tmp`.
- Record command evidence for meaningful build, test, scope, and report commands.
- Run `scope check` before reporting completion.
- Run `report final` and `mission replay` when a task changes repository files.
- Classify risky commands with `command risk`; do not execute remote installer pipelines.
- Do not read `.env`, SSH keys, credential files, or production secret material.

## Useful Commands

```bash
PYTHONPATH=src python3 -m agent_mission_control mission init --contract templates/contract.yaml --root /private/tmp/amc-smoke
PYTHONPATH=src python3 -m agent_mission_control scope check --contract templates/contract.yaml --changed-files evals/fixtures/allowed-changed-files.txt
PYTHONPATH=src python3 -m agent_mission_control report final /private/tmp/amc-smoke/.mission-control/runs
PYTHONPATH=src python3 -m agent_mission_control mission replay /private/tmp/amc-smoke/.mission-control/runs
```
"""


CODEX_NOTES = """\
## Codex Notes

Codex reads `AGENTS.md` from the repository. Keep this file short and operational:
commands to run, files to protect, and the expected evidence path.
"""


CLAUDE_NOTES = """\
## Claude Code Notes

Claude Code reads `CLAUDE.md` from the repository. Keep task-specific details in
the mission contract and use this file for stable project rules.
"""


HERMES_NOTES = """\
## Hermes Notes

Hermes reads `HERMES.md` as the local runbook for machine-side execution. Use it
to keep repeated Hermes tasks on the same contract, evidence, and review path.
"""


def integration_files(target: str, root: str | Path = ".") -> list[IntegrationFile]:
    """Return the host instruction files needed for the selected target."""

    root_path = Path(root)
    if target not in {"codex", "claude", "hermes", "both"}:
        raise IntegrationError("target must be one of: codex, claude, hermes, both")
    files: list[IntegrationFile] = []
    if target in {"codex", "both"}:
        files.append(IntegrationFile(root_path / "AGENTS.md", COMMON_RULES + "\n" + CODEX_NOTES))
    if target in {"claude", "both"}:
        files.append(IntegrationFile(root_path / "CLAUDE.md", COMMON_RULES + "\n" + CLAUDE_NOTES))
    if target in {"hermes", "both"}:
        files.append(IntegrationFile(root_path / "HERMES.md", COMMON_RULES + "\n" + HERMES_NOTES))
    return files


def bootstrap_agent_files(target: str = "both", root: str | Path = ".", force: bool = False) -> list[Path]:
    """Write Codex, Claude Code, and/or Hermes instruction files into a repository."""

    Path(root).mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for item in integration_files(target, root):
        if item.path.exists() and not force:
            raise IntegrationError(f"{item.path} already exists; pass --force to overwrite it")
        item.path.write_text(item.content, encoding="utf-8")
        written.append(item.path)
    return written
