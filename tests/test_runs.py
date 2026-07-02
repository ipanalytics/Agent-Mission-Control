import json
import io
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

from agent_mission_control.cli import main
from agent_mission_control.runs import create_run


class RunTests(unittest.TestCase):
    def test_create_run_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = create_run("templates/contract.yaml", tmp)
            self.assertTrue((run_dir / "contract.yaml").exists())
            self.assertTrue((run_dir / "state.json").exists())
            self.assertTrue((run_dir / "events.jsonl").exists())
            self.assertTrue((run_dir / "evidence").is_dir())
            self.assertTrue((run_dir / "traces").is_dir())
            self.assertTrue((run_dir / "phases").is_dir())
            state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["status"], "created")
            self.assertEqual(state["current_phase"], 1)
            self.assertIn("baseline_ref", state)
            self.assertIn("contract", state)
            events = (run_dir / "events.jsonl").read_text(encoding="utf-8")
            self.assertIn("mission.created", events)
            self.assertRegex(run_dir.name, r"^\d{8}t?\d*")

    def test_cli_init_contract_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.yaml"
            bad.write_text("allowed_paths:\n  - src/**\n", encoding="utf-8")
            err = io.StringIO()
            with redirect_stderr(err):
                self.assertNotEqual(main(["mission", "init", "--contract", str(bad), "--root", tmp]), 0)
            self.assertIn("goal", err.getvalue())


if __name__ == "__main__":
    unittest.main()
