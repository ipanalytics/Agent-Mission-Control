import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_mission_control.cli import main


class CLITests(unittest.TestCase):
    def test_help_exits_zero(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = main(["--help"])
        self.assertEqual(code, 0)
        self.assertIn("Agent Mission Control", buffer.getvalue())

    def test_version(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = main(["version"])
        self.assertEqual(code, 0)
        self.assertIn("Agent Mission Control 1.0.0", buffer.getvalue())

    def test_agent_bootstrap_writes_host_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = main(["agent", "bootstrap", "--target", "both", "--root", tmp])
            self.assertEqual(code, 0)
            self.assertTrue((Path(tmp) / "AGENTS.md").exists())
            self.assertTrue((Path(tmp) / "CLAUDE.md").exists())
            self.assertTrue((Path(tmp) / "HERMES.md").exists())
            self.assertIn("AGENTS.md", buffer.getvalue())
            self.assertIn("CLAUDE.md", buffer.getvalue())
            self.assertIn("HERMES.md", buffer.getvalue())

    def test_agent_bootstrap_writes_hermes_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                code = main(["agent", "bootstrap", "--target", "hermes", "--root", tmp])
            self.assertEqual(code, 0)
            self.assertFalse((Path(tmp) / "AGENTS.md").exists())
            self.assertFalse((Path(tmp) / "CLAUDE.md").exists())
            hermes = Path(tmp) / "HERMES.md"
            self.assertTrue(hermes.exists())
            self.assertIn("Hermes reads `HERMES.md`", hermes.read_text(encoding="utf-8"))

    def test_agent_bootstrap_refuses_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text("keep me\n", encoding="utf-8")
            err = io.StringIO()
            with redirect_stderr(err):
                self.assertNotEqual(main(["agent", "bootstrap", "--target", "codex", "--root", tmp]), 0)
            self.assertEqual((root / "AGENTS.md").read_text(encoding="utf-8"), "keep me\n")
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(main(["agent", "bootstrap", "--target", "codex", "--root", tmp, "--force"]), 0)
            self.assertIn("Agent Mission Control Runbook", (root / "AGENTS.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
