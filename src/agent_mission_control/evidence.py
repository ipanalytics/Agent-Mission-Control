from __future__ import annotations

import json
from pathlib import Path

from .command_risk import classify_command
from .events import append_event, utc_now
from .policy import Policy
from .runs import resolve_run_dir


def add_command_evidence(
    run_dir: str | Path,
    command: str,
    exit_code: int,
    output_text: str = "",
    policy: Policy | None = None,
) -> Path:
    """Persist command output metadata and append a matching run event."""

    resolved = resolve_run_dir(run_dir)
    evidence_dir = resolved / "evidence" / "commands"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    index = len(list(evidence_dir.glob("command-*.txt"))) + 1
    output_path = evidence_dir / f"command-{index}.txt"
    output_path.write_text(output_text, encoding="utf-8")
    risk = classify_command(command, policy)
    record = {
        "timestamp": utc_now(),
        "command": command,
        "exit_code": exit_code,
        "output_path": str(output_path.relative_to(resolved)),
        "risk": risk.to_mapping(),
    }
    log_path = resolved / "evidence" / "command-evidence.jsonl"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    append_event(resolved, "evidence.command", {"command": command, "exit_code": exit_code, "risk": risk.risk})
    return log_path


def read_command_evidence(run_dir: str | Path) -> list[dict]:
    """Read command evidence records from a mission run."""

    resolved = resolve_run_dir(run_dir)
    path = resolved / "evidence" / "command-evidence.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
