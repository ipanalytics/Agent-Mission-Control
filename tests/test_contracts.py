import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_mission_control.cli import main
from agent_mission_control.contracts import ContractError, load_contract
from agent_mission_control.policy import load_policy


class ContractTests(unittest.TestCase):
    def test_load_template_contract(self):
        contract = load_contract("templates/contract.yaml")
        self.assertEqual(contract.goal, "Implement Agent Mission Control run")
        self.assertIn("src/**", contract.allowed_paths)
        self.assertIn(".env", contract.forbidden_paths)
        self.assertIn("python3 -m compileall src tests", contract.allowed_commands)
        self.assertEqual(contract.network_policy, "deny-by-default")
        self.assertEqual(contract.max_files_changed, 80)

    def test_rejects_invalid_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.yaml"
            path.write_text("allowed_paths:\n  - src/**\nmax_files_changed: -1\n", encoding="utf-8")
            with self.assertRaises(ContractError):
                load_contract(path)

    def test_policy_presets_include_protected_paths(self):
        for name in ["default", "safe", "strict", "development"]:
            policy = load_policy(f"policies/{name}.yaml")
            joined = "\n".join(policy.protected_paths)
            self.assertIn(".env", joined)
            self.assertIn("id_rsa", joined)
            self.assertIn("credentials", joined)
            self.assertIn("token", joined)

    def test_cli_validate_valid_and_invalid(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(["contract", "validate", "templates/contract.yaml"]), 0)
        self.assertIn("valid contract", out.getvalue())
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.yaml"
            path.write_text("goal: ''\nmax_files_changed: -1\n", encoding="utf-8")
            err = io.StringIO()
            with redirect_stderr(err):
                self.assertNotEqual(main(["contract", "validate", str(path)]), 0)
            self.assertIn("goal", err.getvalue())


if __name__ == "__main__":
    unittest.main()

