import json
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agent_mission_control.cli import main
from agent_mission_control.contracts import load_contract
from agent_mission_control.scope import classify_files


class ScopeTests(unittest.TestCase):
    def test_classifies_scope(self):
        contract = load_contract("templates/contract.yaml")
        result = classify_files(contract, ["src/x.py", "billing/x.py", ".env"], "no-git")
        ledger = result.ledger
        self.assertIn("src/x.py", ledger["allowed_touched_files"])
        self.assertIn("billing/x.py", ledger["out_of_scope_files"])
        self.assertIn(".env", ledger["forbidden_files"])
        self.assertFalse(result.ok)

    def test_max_files_changed_violation(self):
        contract = load_contract("evals/scenarios/basic-contract.yaml")
        result = classify_files(contract, [f"src/{index}.py" for index in range(8)], "no-git")
        self.assertIn("max_files_changed", [item["type"] for item in result.ledger["violations"]])

    def test_cli_manifest_modes(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "changed.txt"
            manifest.write_text("src/ok.py\n", encoding="utf-8")
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(
                    main(["scope", "check", "--contract", "templates/contract.yaml", "--changed-files", str(manifest)]),
                    0,
                )
            bad = Path(tmp) / "bad.txt"
            bad.write_text(".env\n", encoding="utf-8")
            output = Path(tmp) / "scope.json"
            bad_out = io.StringIO()
            with redirect_stdout(bad_out):
                self.assertNotEqual(
                    main(
                        [
                            "scope",
                            "check",
                            "--contract",
                            "templates/contract.yaml",
                            "--changed-files",
                            str(bad),
                            "--output",
                            str(output),
                        ]
                    ),
                    0,
                )
            ledger = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(ledger["baseline"], "no-git")
            self.assertTrue(ledger["violations"])


if __name__ == "__main__":
    unittest.main()
