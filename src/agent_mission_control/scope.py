from __future__ import annotations

import fnmatch
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import Contract


@dataclass(frozen=True)
class ScopeResult:
    """Scope ledger plus convenience helpers for CLI exit-code decisions."""

    ledger: dict[str, Any]

    @property
    def ok(self) -> bool:
        return not self.ledger["violations"]

    def to_json(self) -> str:
        return json.dumps(self.ledger, indent=2, sort_keys=True)


def _matches(path: str, patterns: list[str]) -> bool:
    normalized = _normalize_path(path)
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in patterns)


def _normalize_path(path: str) -> str:
    normalized = path.strip()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def classify_files(contract: Contract, files: list[str], baseline: str = "no-git") -> ScopeResult:
    """Classify changed files against allowed and forbidden contract paths."""

    allowed: list[str] = []
    forbidden: list[str] = []
    out_of_scope: list[str] = []
    for file_path in [_normalize_path(item) for item in files if item.strip()]:
        if _matches(file_path, contract.forbidden_paths):
            forbidden.append(file_path)
        elif contract.allowed_paths and _matches(file_path, contract.allowed_paths):
            allowed.append(file_path)
        elif not contract.allowed_paths:
            allowed.append(file_path)
        else:
            out_of_scope.append(file_path)
    violations: list[dict[str, Any]] = []
    if forbidden:
        violations.append({"type": "forbidden_path", "files": forbidden})
    if out_of_scope:
        violations.append({"type": "out_of_scope", "files": out_of_scope})
    total = len(allowed) + len(forbidden) + len(out_of_scope)
    if contract.max_files_changed and total > contract.max_files_changed:
        violations.append(
            {
                "type": "max_files_changed",
                "limit": contract.max_files_changed,
                "actual": total,
            }
        )
    return ScopeResult(
        {
            "baseline": baseline,
            "allowed_touched_files": allowed,
            "actually_touched_files": allowed + forbidden + out_of_scope,
            "forbidden_files": forbidden,
            "out_of_scope_files": out_of_scope,
            "justifications": {},
            "violations": violations,
        }
    )


def read_changed_files_manifest(path: str | Path) -> list[str]:
    """Read one changed file path per line from a manifest file."""

    return [line.strip() for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def git_changed_files(cwd: str | Path = ".") -> tuple[str, list[str]]:
    """Return the current git baseline and changed paths for a repository."""

    baseline = "no-git"
    rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=Path(cwd), text=True, capture_output=True, check=False)
    if rev.returncode == 0:
        baseline = rev.stdout.strip()
    status = subprocess.run(["git", "status", "--porcelain"], cwd=Path(cwd), text=True, capture_output=True, check=False)
    if status.returncode != 0:
        return baseline, []
    files: list[str] = []
    for line in status.stdout.splitlines():
        if len(line) > 3:
            files.append(line[3:].strip())
    return baseline, files
