from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .simple_yaml import SimpleYAMLError, load_file


class ContractError(ValueError):
    """Raised when a task contract is invalid."""


@dataclass(frozen=True)
class Contract:
    """Validated task boundary used by scope, evidence, and reporting code."""

    goal: str
    allowed_paths: list[str] = field(default_factory=list)
    forbidden_paths: list[str] = field(default_factory=list)
    allowed_commands: list[str] = field(default_factory=list)
    network_policy: str = "deny-by-default"
    max_files_changed: int = 25
    rollback_on_failure: bool = True

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "Contract":
        """Create a contract from parsed YAML data and reject unsafe shapes early."""

        goal = data.get("goal")
        if not isinstance(goal, str) or not goal.strip():
            raise ContractError("contract field 'goal' is required and must be text")
        allowed_paths = _string_list(data, "allowed_paths")
        forbidden_paths = _string_list(data, "forbidden_paths")
        allowed_commands = _string_list(data, "allowed_commands")
        network_policy = data.get("network_policy", "deny-by-default")
        if not isinstance(network_policy, str) or not network_policy:
            raise ContractError("contract field 'network_policy' must be text")
        max_files_changed = data.get("max_files_changed", 25)
        if not isinstance(max_files_changed, int) or max_files_changed < 0:
            raise ContractError("contract field 'max_files_changed' must be a non-negative integer")
        rollback_on_failure = data.get("rollback_on_failure", True)
        if not isinstance(rollback_on_failure, bool):
            raise ContractError("contract field 'rollback_on_failure' must be true or false")
        return cls(
            goal=goal.strip(),
            allowed_paths=allowed_paths,
            forbidden_paths=forbidden_paths,
            allowed_commands=allowed_commands,
            network_policy=network_policy,
            max_files_changed=max_files_changed,
            rollback_on_failure=rollback_on_failure,
        )

    def summary(self) -> dict[str, Any]:
        """Return JSON-safe contract data for state files and reports."""

        return {
            "goal": self.goal,
            "allowed_paths": self.allowed_paths,
            "forbidden_paths": self.forbidden_paths,
            "allowed_commands": self.allowed_commands,
            "network_policy": self.network_policy,
            "max_files_changed": self.max_files_changed,
            "rollback_on_failure": self.rollback_on_failure,
        }


def _string_list(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ContractError(f"contract field '{key}' must be a list of text values")
    return value


def load_contract(path: str | Path) -> Contract:
    """Load and validate a contract file from disk."""

    try:
        data = load_file(path)
    except (OSError, SimpleYAMLError) as exc:
        raise ContractError(f"could not load contract: {exc}") from exc
    return Contract.from_mapping(data)
