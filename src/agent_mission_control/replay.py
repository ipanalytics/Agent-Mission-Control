from __future__ import annotations

import json
from pathlib import Path

from .events import read_events
from .evidence import read_command_evidence
from .runs import resolve_run_dir


def replay_text(run_dir: str | Path) -> str:
    resolved = resolve_run_dir(run_dir)
    state = json.loads((resolved / "state.json").read_text(encoding="utf-8"))
    events = read_events(resolved)
    command_evidence = read_command_evidence(resolved)
    scope_path = resolved / "evidence" / "scope-ledger.json"
    report_path = resolved / "final-report.md"
    lines = [
        f"Mission replay: {resolved.name}",
        f"Status: {state.get('status', 'unknown')}",
        "Events:",
    ]
    if events:
        for event in events:
            lines.append(f"- {event['timestamp']} {event['type']}")
    else:
        lines.append("- warning: no events recorded")
    lines.append("Commands:")
    if command_evidence:
        for record in command_evidence:
            risk = record.get("risk", {}).get("risk", "low")
            lines.append(f"- exit {record.get('exit_code')} risk {risk}: {record.get('command')}")
    else:
        lines.append("- warning: no command evidence")
    if scope_path.exists():
        scope = json.loads(scope_path.read_text(encoding="utf-8"))
        lines.append(f"Scope: {len(scope.get('violations', []))} violation(s)")
    else:
        lines.append("Scope: warning: no scope ledger")
    if report_path.exists():
        lines.append(f"Final report: {report_path}")
    else:
        lines.append("Final report: warning: missing")
    return "\n".join(lines) + "\n"

