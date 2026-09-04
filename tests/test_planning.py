import json
import tempfile
import unittest

from agent_mission_control.planning import create_phase_plan, goal_prompt, plan_status
from agent_mission_control.runs import create_run


class PlanningTests(unittest.TestCase):
    def test_create_phase_plan_writes_protocol_and_goal(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = create_run("templates/contract.yaml", tmp)
            paths = create_phase_plan(run_dir)
            names = {path.name for path in paths}
            self.assertIn("phase-01.md", names)
            self.assertIn("phase-05.md", names)
            self.assertIn("PROTOCOL.md", names)
            self.assertIn("goal.txt", names)
            protocol = (run_dir / "PROTOCOL.md").read_text(encoding="utf-8")
            self.assertIn("Control Loop", protocol)
            self.assertIn("Done Condition", protocol)
            goal = (run_dir / "goal.txt").read_text(encoding="utf-8")
            self.assertIn("complete every phase", goal)
            state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["status"], "planned")
            self.assertEqual(state["phase_count"], 5)

    def test_goal_prompt_and_status_are_compact(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = create_run("templates/contract.yaml", tmp)
            create_phase_plan(run_dir)
            self.assertIn("PROTOCOL.md", goal_prompt(run_dir))
            status = plan_status(run_dir)
            self.assertIn("Status: planned", status)
            self.assertIn("Phases: 5", status)


if __name__ == "__main__":
    unittest.main()
