"""Command-line behaviour: --help everywhere, repo root located from the script's own path."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import unittest

from .support import RepoTestCase, ENGINE_DIR

import common

SCRIPTS = ["pick", "new_lesson", "mermaid", "render_email", "mark", "file_passed", "sync_db", "state"]


class CliTests(RepoTestCase):
    def run_script(self, script, *args, cwd=None, env=None):
        return subprocess.run([sys.executable, str(ENGINE_DIR / f"{script}.py"), *args], cwd=cwd or self.root,
                              capture_output=True, text=True, env=env)

    def test_every_script_has_help(self):
        for script in SCRIPTS:
            with self.subTest(script=script):
                r = self.run_script(script, "--help")
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn("usage:", r.stdout)

    def test_new_lesson_subcommands_have_help(self):
        for sub in ("core", "fresh"):
            r = self.run_script("new_lesson", sub, "--help")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("--date", r.stdout)

    def test_scripts_find_the_repo_from_their_own_path(self):
        """Copy the engine into the fixture repo and run it with no $DOJO_REPO, from the repo root."""
        shutil.copytree(ENGINE_DIR, self.root / "dojo/engine",
                        ignore=shutil.ignore_patterns("tests", "__pycache__"))
        env = {k: v for k, v in os.environ.items() if k != "DOJO_REPO"}
        script = "dojo/engine/{}.py"
        run = lambda name, *a: subprocess.run([sys.executable, script.format(name), *a], cwd=self.root,
                                              capture_output=True, text=True, env=env)
        r = run("pick", "core")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["rung"]["id"], "ai-ml-01")
        r = run("new_lesson", "core", "--date", "2026-10-06", "--n", "1", "--new-day")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.root / r.stdout.strip()).exists())
        r = run("mark", "2026-10-06-1", "passed", "--by", "job")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = run("file_passed", "2026-10-06-1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.root / "24-ai-ml-foundations/README.md").exists())
        r = run("pick", "--dry-run", "4")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("ai-ml", r.stdout)

    def test_errors_are_one_line_with_exit_code_2(self):
        r = self.run_script("mark", "2099-01-01-1", "passed")
        self.assertEqual(r.returncode, 2)
        self.assertTrue(r.stderr.startswith("error: no lesson with id"))
        self.assertNotIn("Traceback", r.stderr)
        r = self.run_script("file_passed", "2099-01-01-1")
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
