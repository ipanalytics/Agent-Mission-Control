import tempfile
import unittest

from agent_mission_control.events import append_event
from agent_mission_control.evidence import add_command_evidence
from agent_mission_control.planning import create_phase_plan
from agent_mission_control.replay import replay_text
from agent_mission_control.runs import create_run


class ReplayTests(unittest.TestCase):
    def test_replay_ordering_and_warnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = create_run("templates/contract.yaml", tmp)
            append_event(run_dir, "mission.checked", {"ok": True})
            text = replay_text(run_dir)
            self.assertIn("mission.created", text)
            self.assertIn("mission.checked", text)
            self.assertIn("warning: no command evidence", text)
            self.assertIn("warning: no scope ledger", text)
            self.assertIn("Plan: warning: no phase files", text)

    def test_replay_with_command_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = create_run("templates/contract.yaml", tmp)
            add_command_evidence(run_dir, "python3 -m unittest", 0, "ok")
            text = replay_text(run_dir)
            self.assertIn("exit 0 risk low", text)

    def test_replay_lists_phase_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = create_run("templates/contract.yaml", tmp)
            create_phase_plan(run_dir)
            text = replay_text(run_dir)
            self.assertIn("Phases: 5", text)
            self.assertIn("phase-01.md", text)


if __name__ == "__main__":
    unittest.main()
