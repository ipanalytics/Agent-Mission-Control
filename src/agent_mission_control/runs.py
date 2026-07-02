from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from .contracts import ContractError, load_contract
from .events import append_event, utc_now


class RunError(ValueError):
    """Raised when a mission run cannot be created or resolved."""


def slugify(text: str) -> str:
    """Convert a goal into a short filesystem-safe run id suffix."""

    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return slug[:48] or "mission"


def baseline_ref(cwd: str | Path = ".") -> str:
    """Return the current git commit or `no-git` outside repositories."""

    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=Path(cwd),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return "no-git"


def create_run(contract_path: str | Path, root: str | Path = ".") -> Path:
    """Create a durable mission run directory from a task contract."""

    contract_file = Path(contract_path)
    try:
        contract = load_contract(contract_file)
    except ContractError:
        raise
    except Exception as exc:  # pragma: no cover - defensive boundary
        raise RunError(str(exc)) from exc

    root_path = Path(root)
    runs_root = root_path / ".mission-control" / "runs"
    runs_root.mkdir(parents=True, exist_ok=True)
    stamp = utc_now().replace(":", "").replace("-", "").replace("Z", "")
    run_id = f"{stamp}-{slugify(contract.goal)}"
    run_dir = runs_root / run_id
    counter = 2
    while run_dir.exists():
        run_dir = runs_root / f"{run_id}-{counter}"
        counter += 1
    for child in ["evidence", "traces", "phases"]:
        (run_dir / child).mkdir(parents=True, exist_ok=True)
    shutil.copyfile(contract_file, run_dir / "contract.yaml")
    state = {
        "run_id": run_dir.name,
        "status": "created",
        "current_phase": 1,
        "created_at": utc_now(),
        "baseline_ref": baseline_ref(root_path),
        "contract": contract.summary(),
    }
    (run_dir / "state.json").write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")
    append_event(run_dir, "mission.created", {"contract": str(contract_file), "status": "created"})
    return run_dir


def resolve_run_dir(path: str | Path) -> Path:
    """Resolve either a concrete run directory or the newest child of runs/."""

    candidate = Path(path)
    if candidate.is_dir() and (candidate / "state.json").exists():
        return candidate
    if candidate.is_dir():
        run_dirs = sorted(
            [item for item in candidate.iterdir() if item.is_dir() and (item / "state.json").exists()],
            key=lambda item: item.stat().st_mtime,
        )
        if run_dirs:
            return run_dirs[-1]
    raise RunError(f"could not resolve run directory from {candidate}")
