from __future__ import annotations

import fnmatch
import json
import re
from dataclasses import dataclass, field
from typing import Any

from .policy import Policy


RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


@dataclass(frozen=True)
class CommandRisk:
    """Risk decision for a command string that has not been executed."""

    command: str
    risk: str
    score: int
    allowed: bool
    reasons: list[str] = field(default_factory=list)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "risk": self.risk,
            "score": self.score,
            "allowed": self.allowed,
            "reasons": self.reasons,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_mapping(), indent=2, sort_keys=True)


def _raise(current: str, candidate: str) -> str:
    return candidate if RISK_ORDER[candidate] > RISK_ORDER[current] else current


def classify_command(command: str, policy: Policy | None = None) -> CommandRisk:
    """Classify a shell command using conservative string-pattern checks."""

    policy = policy or Policy()
    lowered = command.lower()
    risk = "low"
    reasons: list[str] = []

    if re.search(r"\b(curl|wget)\b.+\|\s*(bash|sh|zsh)\b", lowered):
        risk = _raise(risk, "critical")
        reasons.append("remote shell execution")
    if re.search(r"\b(bash|sh|zsh)\s+<\s*\(", lowered):
        risk = _raise(risk, "critical")
        reasons.append("process substitution shell execution")
    if re.search(r"\brm\s+-[^\n]*r[^\n]*f\s+(/|\$home|~|\.)", lowered):
        risk = _raise(risk, "critical")
        reasons.append("broad destructive filesystem operation")
    if re.search(r"\b(curl|wget|ssh|scp|rsync|git\s+clone)\b", lowered):
        risk = _raise(risk, "medium")
        reasons.append("network-capable command")
    if re.search(r"\b(npm|pnpm|yarn|pip|uv|cargo|go)\s+(install|add|get|update|upgrade|sync)\b", lowered):
        risk = _raise(risk, "medium")
        reasons.append("dependency or package operation")
    if any(name in lowered for name in ["package-lock.json", "pnpm-lock.yaml", "yarn.lock", "uv.lock", "poetry.lock"]):
        risk = _raise(risk, "medium")
        reasons.append("lockfile modification or inspection")
    # These markers catch common secret paths even when no policy file is loaded.
    protected_markers = [".env", "id_rsa", "id_ed25519", ".ssh", "credentials", "token", "secret"]
    protected_markers.extend(policy.protected_paths)
    if any(fnmatch.fnmatch(lowered, f"*{marker.lower()}*") for marker in protected_markers):
        risk = _raise(risk, "high")
        reasons.append("protected secret or credential path")

    if not reasons:
        reasons.append("no risky pattern matched")
    threshold = RISK_ORDER.get(policy.block_risk_at, RISK_ORDER["critical"])
    # Explicit allow rules are useful for strict policies that still need safe test commands.
    allowed_by_pattern = any(fnmatch.fnmatch(command, pattern) for pattern in policy.allowed_commands)
    allowed = allowed_by_pattern or RISK_ORDER[risk] < threshold
    score = {"low": 5, "medium": 35, "high": 70, "critical": 100}[risk]
    return CommandRisk(command=command, risk=risk, score=score, allowed=allowed, reasons=reasons)
