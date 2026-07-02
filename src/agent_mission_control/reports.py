from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .events import read_events
from .evidence import read_command_evidence
from .runs import resolve_run_dir


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def safety_score(scope_ledger: dict[str, Any], command_evidence: list[dict[str, Any]], warnings: list[str]) -> int:
    score = 100
    violations = scope_ledger.get("violations", []) if scope_ledger else []
    for violation in violations:
        if violation.get("type") == "forbidden_path":
            score -= 30
        elif violation.get("type") == "out_of_scope":
            score -= 15
        else:
            score -= 10
    for record in command_evidence:
        risk = record.get("risk", {}).get("risk", "low")
        if risk == "critical":
            score -= 30
        elif risk == "high":
            score -= 20
        elif risk == "medium":
            score -= 8
        if record.get("exit_code", 0) != 0:
            score -= 5
    score -= min(len(warnings) * 3, 15)
    return max(0, score)


def final_report(run_dir: str | Path) -> Path:
    resolved = resolve_run_dir(run_dir)
    state = _load_json(resolved / "state.json", {})
    scope_ledger = _load_json(resolved / "evidence" / "scope-ledger.json", {})
    command_evidence = read_command_evidence(resolved)
    events = read_events(resolved)
    warnings: list[str] = []
    if not scope_ledger:
        warnings.append("scope ledger missing")
    if not command_evidence:
        warnings.append("command evidence missing")
    score = safety_score(scope_ledger, command_evidence, warnings)
    changed_count = len(scope_ledger.get("actually_touched_files", [])) if scope_ledger else 0
    violations = scope_ledger.get("violations", []) if scope_ledger else []
    highest_risk = "low"
    order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    for record in command_evidence:
        risk = record.get("risk", {}).get("risk", "low")
        if order.get(risk, 0) > order.get(highest_risk, 0):
            highest_risk = risk

    lines = [
        "# Agent Mission Control Final Report",
        "",
        f"Run: {resolved.name}",
        f"Status: {state.get('status', 'unknown')}",
        f"Goal: {state.get('contract', {}).get('goal', 'unknown')}",
        f"Safety score: {score}/100",
        "",
        "## Summary",
        "",
        f"- Changed files: {changed_count}",
        f"- Scope violations: {len(violations)}",
        f"- Highest command risk: {highest_risk}",
        f"- Events recorded: {len(events)}",
    ]
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)
    lines.extend(["", "## Verification", "", "- Review the evidence directory for command output and scope ledgers."])
    report_path = resolved / "final-report.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    pr_summary(resolved, score, changed_count, violations, highest_risk)
    return report_path


def pr_summary(
    run_dir: str | Path,
    score: int | None = None,
    changed_count: int | None = None,
    violations: list[dict[str, Any]] | None = None,
    highest_risk: str | None = None,
) -> Path:
    resolved = resolve_run_dir(run_dir)
    if score is None:
        scope_ledger = _load_json(resolved / "evidence" / "scope-ledger.json", {})
        command_evidence = read_command_evidence(resolved)
        score = safety_score(scope_ledger, command_evidence, [])
        changed_count = len(scope_ledger.get("actually_touched_files", []))
        violations = scope_ledger.get("violations", [])
        highest_risk = "low"
    lines = [
        "# PR Summary",
        "",
        "## Changed Files",
        "",
        f"- Files changed: {changed_count or 0}",
        "",
        "## Verification Checklist",
        "",
        "- [ ] Tests passed",
        "- [ ] Scope ledger reviewed",
        "- [ ] Command risk reviewed",
        "",
        "## Reviewer Notes",
        "",
        f"- Safety score: {score}/100",
        f"- Scope violations: {len(violations or [])}",
        f"- Highest command risk: {highest_risk or 'low'}",
    ]
    path = resolved / "pr-summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path

