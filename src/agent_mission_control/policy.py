from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .simple_yaml import SimpleYAMLError, load_file


class PolicyError(ValueError):
    """Raised when a policy file is invalid."""


@dataclass(frozen=True)
class Policy:
    """Command-risk policy loaded from a small repository-local YAML file."""

    name: str = "default"
    block_risk_at: str = "critical"
    protected_paths: list[str] = field(default_factory=list)
    allowed_commands: list[str] = field(default_factory=list)
    network_policy: str = "deny-by-default"

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "Policy":
        """Build a policy from parsed YAML data."""

        name = data.get("name", "default")
        block_risk_at = data.get("block_risk_at", "critical")
        network_policy = data.get("network_policy", "deny-by-default")
        if not all(isinstance(item, str) and item for item in [name, block_risk_at, network_policy]):
            raise PolicyError("policy fields name, block_risk_at, and network_policy must be text")
        protected_paths = _string_list(data, "protected_paths")
        allowed_commands = _string_list(data, "allowed_commands")
        return cls(
            name=name,
            block_risk_at=block_risk_at,
            protected_paths=protected_paths,
            allowed_commands=allowed_commands,
            network_policy=network_policy,
        )


def _string_list(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise PolicyError(f"policy field '{key}' must be a list of text values")
    return value


def load_policy(path: str | Path) -> Policy:
    """Load and validate a policy file from disk."""

    try:
        data = load_file(path)
    except (OSError, SimpleYAMLError) as exc:
        raise PolicyError(f"could not load policy: {exc}") from exc
    return Policy.from_mapping(data)
