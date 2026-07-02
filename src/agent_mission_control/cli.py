from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .command_risk import classify_command
from .contracts import ContractError, load_contract
from .evidence import add_command_evidence
from .integrations import IntegrationError, bootstrap_agent_files
from .policy import PolicyError, load_policy
from .reports import final_report, pr_summary
from .replay import replay_text
from .runs import RunError, create_run
from .scope import classify_files, git_changed_files, read_changed_files_manifest


def _write(text: str) -> None:
    sys.stdout.write(text)
    if text and not text.endswith("\n"):
        sys.stdout.write("\n")


def _error(text: str) -> int:
    sys.stderr.write(f"error: {text}\n")
    return 2


def build_parser() -> argparse.ArgumentParser:
    """Build the command tree without performing any filesystem work."""

    parser = argparse.ArgumentParser(prog="Agent Mission Control")
    parser.add_argument("--version", action="version", version=f"Agent Mission Control {__version__}")
    subparsers = parser.add_subparsers(dest="root_command")

    subparsers.add_parser("version", help="Show the Agent Mission Control version")

    contract = subparsers.add_parser("contract", help="Work with task contracts")
    contract_sub = contract.add_subparsers(dest="contract_command")
    validate = contract_sub.add_parser("validate", help="Validate a contract file")
    validate.add_argument("path")

    mission = subparsers.add_parser("mission", help="Create or replay mission runs")
    mission_sub = mission.add_subparsers(dest="mission_command")
    init = mission_sub.add_parser("init", help="Create a mission run directory")
    init.add_argument("--contract", required=True)
    init.add_argument("--root", default=".")
    replay = mission_sub.add_parser("replay", help="Replay a mission run")
    replay.add_argument("run_dir")

    scope = subparsers.add_parser("scope", help="Check changed files against a contract")
    scope_sub = scope.add_subparsers(dest="scope_command")
    check = scope_sub.add_parser("check", help="Generate a scope ledger")
    check.add_argument("--contract", required=True)
    check.add_argument("--changed-files")
    check.add_argument("--root", default=".")
    check.add_argument("--output")

    command = subparsers.add_parser("command", help="Classify command risk")
    command_sub = command.add_subparsers(dest="command_command")
    risk = command_sub.add_parser("risk", help="Classify a command string")
    risk.add_argument("--policy", default="policies/default.yaml")
    risk.add_argument("--json", action="store_true")
    risk.add_argument("shell_command")

    evidence = subparsers.add_parser("evidence", help="Record mission evidence")
    evidence_sub = evidence.add_subparsers(dest="evidence_command")
    add_command = evidence_sub.add_parser("add-command", help="Record command evidence")
    add_command.add_argument("run_dir")
    add_command.add_argument("--command", dest="evidence_command_text", required=True)
    add_command.add_argument("--exit-code", type=int, required=True)
    add_command.add_argument("--output-text", default="")
    add_command.add_argument("--policy", default="policies/default.yaml")

    report = subparsers.add_parser("report", help="Generate reports")
    report_sub = report.add_subparsers(dest="report_command")
    final = report_sub.add_parser("final", help="Generate final report")
    final.add_argument("run_dir")
    pr = report_sub.add_parser("pr-summary", help="Generate PR summary")
    pr.add_argument("run_dir")

    agent = subparsers.add_parser("agent", help="Install agent-host instruction files")
    agent_sub = agent.add_subparsers(dest="agent_command")
    bootstrap = agent_sub.add_parser("bootstrap", help="Write AGENTS.md and/or CLAUDE.md")
    bootstrap.add_argument("--target", choices=["codex", "claude", "both"], default="both")
    bootstrap.add_argument("--root", default=".")
    bootstrap.add_argument("--force", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return a process-style exit code."""

    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 0)
    if args.root_command is None:
        parser.print_help()
        return 0
    try:
        if args.root_command == "version":
            _write(f"Agent Mission Control {__version__}")
            return 0
        if args.root_command == "contract" and args.contract_command == "validate":
            contract = load_contract(args.path)
            _write(f"valid contract: {contract.goal}")
            return 0
        if args.root_command == "mission" and args.mission_command == "init":
            run_dir = create_run(args.contract, args.root)
            _write(str(run_dir))
            return 0
        if args.root_command == "mission" and args.mission_command == "replay":
            _write(replay_text(args.run_dir))
            return 0
        if args.root_command == "scope" and args.scope_command == "check":
            contract = load_contract(args.contract)
            if args.changed_files:
                files = read_changed_files_manifest(args.changed_files)
                baseline = "no-git"
            else:
                baseline, files = git_changed_files(args.root)
            result = classify_files(contract, files, baseline)
            text = result.to_json()
            if args.output:
                Path(args.output).parent.mkdir(parents=True, exist_ok=True)
                Path(args.output).write_text(text + "\n", encoding="utf-8")
            _write(text)
            return 0 if result.ok else 1
        if args.root_command == "command" and args.command_command == "risk":
            policy = load_policy(args.policy)
            result = classify_command(args.shell_command, policy)
            if args.json:
                _write(result.to_json())
            else:
                _write(
                    f"command: {result.command}\n"
                    f"risk: {result.risk}\n"
                    f"score: {result.score}\n"
                    f"allowed: {'yes' if result.allowed else 'no'}\n"
                    f"reasons: {', '.join(result.reasons)}"
                )
            return 0 if result.allowed else 1
        if args.root_command == "evidence" and args.evidence_command == "add-command":
            policy = load_policy(args.policy)
            path = add_command_evidence(args.run_dir, args.evidence_command_text, args.exit_code, args.output_text, policy)
            _write(str(path))
            return 0
        if args.root_command == "report" and args.report_command == "final":
            _write(str(final_report(args.run_dir)))
            return 0
        if args.root_command == "report" and args.report_command == "pr-summary":
            _write(str(pr_summary(args.run_dir)))
            return 0
        if args.root_command == "agent" and args.agent_command == "bootstrap":
            paths = bootstrap_agent_files(args.target, args.root, args.force)
            _write("\n".join(str(path) for path in paths))
            return 0
    except (ContractError, PolicyError, RunError, IntegrationError, OSError, ValueError) as exc:
        return _error(str(exc))
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
