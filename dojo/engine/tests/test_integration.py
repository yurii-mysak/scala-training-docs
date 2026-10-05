"""End to end: the exact CLI sequence the scheduled job runs, over two simulated days."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from unittest import mock

from . import support
from .support import RepoTestCase, ENGINE_DIR

import common


class TwoDayRunTests(RepoTestCase):
    tracks_factory = staticmethod(support.six_tracks)
    with_readmes = False

    def cli(self, script: str, *args: str) -> str:
        env = {**os.environ, "DOJO_REPO": str(self.root)}
        r = subprocess.run([sys.executable, str(ENGINE_DIR / f"{script}.py"), *args], cwd=self.root,
                           capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0, f"{script} {args}: {r.stderr}")
        return r.stdout

    def run_day(self, date: str) -> tuple[str, str]:
        self.enterContext(mock.patch.dict(os.environ, {"DOJO_NOW": f"{date}T06:00:00Z"}))
        core = self.cli("new_lesson", "core", "--date", date, "--n", "1", "--new-day").strip()
        fresh = json.loads(self.cli("pick", "fresh"))
        self.cli("new_lesson", "fresh", "--date", date, "--n", "2", "--title", f"Fresh for {date}",
                 "--domain", fresh["domain"], "--level", fresh["reader_level"], "--est-min", "20")
        for lid in (f"{date}-1", f"{date}-2"):
            self.cli("mermaid", lid)
        self.cli("render_email", f"{date}-1", f"{date}-2")
        self.cli("sync_db", "all")
        self.cli("state", "touch")
        return core, fresh["domain"]

    def test_two_days(self):
        core1, dom1 = self.run_day("2026-10-06")
        self.assertTrue(core1.startswith("dojo/lessons/2026-10-06-1-ai-ml-lesson-1"))
        email = json.loads((self.root / "dojo/out/email.json").read_text(encoding="utf-8"))
        self.assertTrue(email["subject"].startswith("IT Iaido · Day 1 · ai-ml lesson 1 · Fresh for 2026-10-06"))

        # reader marks on the dashboard; the next job run mirrors the marks into the repo
        self.cli("mark", "2026-10-06-1", "passed", "--by", "dashboard", "--at", "2026-10-06T18:00:00Z")
        self.cli("mark", "2026-10-06-2", "review", "--by", "dashboard", "--at", "2026-10-06T18:01:00Z")
        filed = json.loads(self.cli("file_passed", "--all-passed-unfiled"))
        self.assertEqual([f["id"] for f in filed], ["2026-10-06-1"])
        self.assertTrue((self.root / filed[0]["filed_to"]).exists())

        core2, dom2 = self.run_day("2026-10-07")
        email = json.loads((self.root / "dojo/out/email.json").read_text(encoding="utf-8"))
        self.assertTrue(email["subject"].startswith("IT Iaido · Day 2 ·"))

        st = self.state()
        self.assertEqual((st["day"], st["lessons_sent"], st["lessons_passed"]), (2, 4, 1))
        self.assertEqual(st["open"], ["2026-10-07-1", "2026-10-07-2"])      # the review lesson is not "open"
        self.assertEqual(st["last_run_at"], "2026-10-07T06:00:00Z")
        self.assertEqual(len(st["last_fresh_domains"]), 2)
        events = [(e["event"], e["lesson"], e["by"]) for e in self.log_events()]
        self.assertEqual(events[:6], [("sent", "2026-10-06-1", "job"), ("sent", "2026-10-06-2", "job"),
                                      ("passed", "2026-10-06-1", "dashboard"), ("review", "2026-10-06-2", "dashboard"),
                                      ("filed", "2026-10-06-1", "job"), ("sent", "2026-10-07-1", "job")])
        meta = json.loads((self.root / "dojo/out/db/meta/state.json").read_text(encoding="utf-8"))
        self.assertEqual((meta["day"], meta["lessons_passed"], meta["streak"]), (2, 1, 1))
        self.assertEqual(len(list((self.root / "dojo/out/db/lessons").glob("*.json"))), 4)
        self.assertEqual(len(list((self.root / "dojo/out/db/tracks").glob("*.json"))), 6)
        # the weight-5 track leads the cadence, the second core pick is a different track
        picks = [common.load_lesson(common.find_lesson_path(f"2026-10-0{d}-1"))[0]["track"] for d in (6, 7)]
        self.assertEqual(picks[0], "ai-ml")
        self.assertEqual(len(set(picks)), 2)


if __name__ == "__main__":
    unittest.main()
