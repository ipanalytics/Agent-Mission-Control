from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .events import append_event, utc_now
from .runs import resolve_run_dir


class PlanningError(ValueError):
    """Raised when a mission plan cannot be created or read."""


@dataclass(frozen=True)
class PhaseSpec:
    """A verifiable unit of agent work."""

    number: int
    title: str
    objective: str
    checks: list[str]
    evidence: list[str]

    @property
    def filename(self) -> str:
        return f"phase-{self.number:02d}.md"


def default_phases(contract: dict[str, Any]) -> list[PhaseSpec]:
    """Build a conservative phase plan from the mission contract."""

    goal = contract.get("goal", "Complete the mission")
    allowed = contract.get("allowed_paths", [])
    commands = contract.get("allowed_commands", [])
    scope_text = ", ".join(allowed) if allowed else "the contract allowed paths"
    command_text = ", ".join(commands) if commands else "the repository standard checks"
    return [
        PhaseSpec(
            1,
            "Recon And Scope Lock",
            f"Read the repository rules, validate the contract, identify the impacted files, and confirm the work stays inside {scope_text}.",
            ["contract validate passes", "impacted paths are listed", "risks and dependencies are recorded"],
            ["contract validation output", "short risk/dependency notes"],
        ),
        PhaseSpec(
            2,
            "Execution Plan",
            f"Turn the goal into implementation steps for: {goal}. Keep each step small enough to verify independently.",
            ["phase dependencies are explicit", "rollback expectations are clear", "test strategy is selected"],
            ["updated plan notes", "selected verification commands"],
        ),
        PhaseSpec(
            3,
            "Scoped Implementation",
            "Apply the code and documentation changes inside the approved boundary. Record meaningful command evidence as work progresses.",
            ["changed files stay in scope", "risky commands are classified first", "no protected files are read"],
            ["command evidence", "implementation notes"],
        ),
        PhaseSpec(
            4,
            "Verification And Evidence",
            f"Run the agreed checks, including {command_text}, then write scope and command evidence for review.",
            ["tests or equivalent checks pass", "scope ledger has no violations", "command evidence is complete"],
            ["scope-ledger.json", "command-evidence.jsonl", "test output summary"],
        ),
        PhaseSpec(
            5,
            "Final Audit And Replay",
            "Audit the finished mission against the original contract, repair any gaps, then generate reports and replay output.",
            ["final report exists", "PR summary exists", "mission replay is readable", "open warnings are explained"],
            ["final-report.md", "pr-summary.md", "mission replay output"],
        ),
    ]


def phase_markdown(phase: PhaseSpec, contract: dict[str, Any]) -> str:
    """Render one phase as a host-neutral instruction file."""

    lines = [
        f"# Phase {phase.number}: {phase.title}",
        "",
        "## Objective",
        "",
        phase.objective,
        "",
        "## Mission Boundary",
        "",
        f"- Goal: {contract.get('goal', 'unknown')}",
        f"- Allowed paths: {', '.join(contract.get('allowed_paths', [])) or 'none declared'}",
        f"- Forbidden paths: {', '.join(contract.get('forbidden_paths', [])) or 'none declared'}",
        f"- Network policy: {contract.get('network_policy', 'unknown')}",
        "",
        "## Required Checks",
        "",
    ]
    lines.extend(f"- {check}" for check in phase.checks)
    lines.extend(["", "## Evidence To Record", ""])
    lines.extend(f"- {item}" for item in phase.evidence)
    lines.extend(
        [
            "",
            "## Completion Rule",
            "",
            "Do not mark this phase complete until the checks above are true or the remaining gap is explicitly recorded in the final report.",
        ]
    )
    return "\n".join(lines) + "\n"


def protocol_markdown(run_dir: Path, phases: list[PhaseSpec]) -> str:
    """Render the long-running agent protocol for Codex, Claude Code, or Hermes."""

    lines = [
        "# Agent Mission Control Protocol",
        "",
        "Execute this mission phase by phase. The contract is the boundary; the phase files are the execution plan.",
        "",
        "## Control Loop",
        "",
        "1. Read `contract.yaml`, `state.json`, and the next file under `phases/`.",
        "2. Classify risky commands before execution with `amc command risk`.",
        "3. Record meaningful command evidence with `amc evidence add-command`.",
        "4. Run `amc scope check` before reporting completion.",
        "5. Generate `amc report final` and `amc mission replay` after repository changes.",
        "6. If a phase fails, write the gap down, repair it, and rerun the relevant checks before advancing.",
        "",
        "## Phases",
        "",
    ]
    lines.extend(f"- Phase {phase.number}: `{phase.filename}` - {phase.title}" for phase in phases)
    lines.extend(
        [
            "",
            "## Done Condition",
            "",
            "All phase completion rules are satisfied, the final report exists, replay output is readable, and no unreviewed scope violation remains.",
            "",
            f"Run directory: `{run_dir}`",
        ]
    )
    return "\n".join(lines) + "\n"


def goal_prompt(run_dir: str | Path) -> str:
    """Return the short goal string intended for Codex, Claude Code, or Hermes."""

    resolved = resolve_run_dir(run_dir)
    return (
        f"Follow {resolved / 'PROTOCOL.md'} and complete every phase in {resolved / 'phases'}. "
        "Do not stop until final-report.md, pr-summary.md, scope evidence, command evidence, and mission replay are complete."
    )


def create_phase_plan(run_dir: str | Path, force: bool = False) -> list[Path]:
    """Create phase files, protocol instructions, and a goal prompt for a run."""

    resolved = resolve_run_dir(run_dir)
    state_path = resolved / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    contract = state.get("contract", {})
    phases = default_phases(contract)
    phase_root = resolved / "phases"
    phase_root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for phase in phases:
        path = phase_root / phase.filename
        if path.exists() and not force:
            raise PlanningError(f"{path} already exists; pass --force to overwrite it")
        path.write_text(phase_markdown(phase, contract), encoding="utf-8")
        written.append(path)
    protocol_path = resolved / "PROTOCOL.md"
    goal_path = resolved / "goal.txt"
    if not force:
        for path in [protocol_path, goal_path]:
            if path.exists():
                raise PlanningError(f"{path} already exists; pass --force to overwrite it")
    protocol_path.write_text(protocol_markdown(resolved, phases), encoding="utf-8")
    goal_path.write_text(goal_prompt(resolved) + "\n", encoding="utf-8")
    written.extend([protocol_path, goal_path])
    state["status"] = "planned"
    state["current_phase"] = 1
    state["phase_count"] = len(phases)
    state["planned_at"] = utc_now()
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    append_event(resolved, "mission.planned", {"phase_count": len(phases)})
    return written


def plan_status(run_dir: str | Path) -> str:
    """Return a compact human-readable phase status."""

    resolved = resolve_run_dir(run_dir)
    state = json.loads((resolved / "state.json").read_text(encoding="utf-8"))
    phases = sorted((resolved / "phases").glob("phase-*.md"))
    lines = [
        f"Run: {resolved.name}",
        f"Status: {state.get('status', 'unknown')}",
        f"Current phase: {state.get('current_phase', 'unknown')}",
        f"Phases: {len(phases)}",
    ]
    lines.extend(f"- {path.name}" for path in phases)
    return "\n".join(lines) + "\n"
