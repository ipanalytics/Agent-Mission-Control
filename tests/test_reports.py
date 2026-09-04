import json
import tempfile
import unittest
from pathlib import Path

from agent_mission_control.evidence import add_command_evidence
from agent_mission_control.planning import create_phase_plan
from agent_mission_control.reports import final_report, safety_score
from agent_mission_control.runs import create_run


class ReportTests(unittest.TestCase):
    def test_report_and_score_deductions(self):
        scope = {
            "actually_touched_files": ["src/a.py", ".env"],
            "violations": [{"type": "forbidden_path", "files": [".env"]}],
        }
        command_evidence = [
            {"exit_code": 1, "risk": {"risk": "critical"}},
            {"exit_code": 0, "risk": {"risk": "high"}},
        ]
        self.assertLess(safety_score(scope, command_evidence, ["missing"]), 100)

    def test_final_report_writes_files_with_warnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = create_run("templates/contract.yaml", tmp)
            evidence_dir = run_dir / "evidence"
            ledger = {
                "actually_touched_files": ["src/a.py"],
                "violations": [],
            }
            (evidence_dir / "scope-ledger.json").write_text(json.dumps(ledger), encoding="utf-8")
            add_command_evidence(run_dir, "python3 -m unittest", 0, "ok")
            report = final_report(run_dir)
            self.assertTrue(report.exists())
            self.assertTrue((run_dir / "pr-summary.md").exists())
            text = report.read_text(encoding="utf-8")
            self.assertIn("Safety score:", text)
            self.assertIn("Changed files: 1", text)
            self.assertIn("phase plan missing", text)

    def test_final_report_includes_phase_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = create_run("templates/contract.yaml", tmp)
            create_phase_plan(run_dir)
            report = final_report(run_dir)
            text = report.read_text(encoding="utf-8")
            self.assertIn("Phase files: 5", text)
            self.assertIn("Protocol: present", text)


if __name__ == "__main__":
    unittest.main()
