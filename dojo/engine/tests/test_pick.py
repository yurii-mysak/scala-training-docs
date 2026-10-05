"""pick.py: weighted round-robin cadence, prerequisites, dry-run, fresh slot, empty curriculum."""
from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
import unittest
from collections import Counter

from . import support
from .support import RepoTestCase, ENGINE_DIR

import common
import pick as pick_mod
import state as state_mod

WEIGHTS = {"ai-ml": 5, "fp-scala": 3, "ddia": 3, "architecture": 2, "networking": 2, "rust": 1}


class CadenceTests(RepoTestCase):
    tracks_factory = staticmethod(support.six_tracks)
    with_readmes = False

    def test_sixteen_picks_match_the_weights(self):
        picks = pick_mod.simulate(common.require_curriculum(), state_mod.load_state(), {}, dt.date(2026, 10, 6), 16)
        self.assertEqual(len(picks), 16)
        self.assertEqual(dict(Counter(p["track"] for p in picks)), WEIGHTS)

    def test_cadence_is_smooth_and_deterministic(self):
        args = (common.require_curriculum(), state_mod.load_state(), {}, dt.date(2026, 10, 6), 16)
        a = [p["track"] for p in pick_mod.simulate(*args)]
        b = [p["track"] for p in pick_mod.simulate(*args)]
        self.assertEqual(a, b)
        self.assertEqual(a[0], "ai-ml")
        # smooth: the weight-5 track never runs more than two days in a row
        runs = max(len(list(g)) for k, g in __import__("itertools").groupby(a) if k == "ai-ml")
        self.assertLessEqual(runs, 2)

    def test_committed_picks_advance_state_and_credits_return_to_zero(self):
        for _ in range(16):
            pick_mod.pick_core(commit=True, today=dt.date(2026, 10, 6))
        st = self.state()
        self.assertEqual(st["next_rung"], WEIGHTS)                         # one rung per pick
        self.assertTrue(all(v == 0 for v in st["credits"].values()), st["credits"])

    def test_core_without_commit_does_not_touch_state(self):
        first = pick_mod.pick_core(commit=False)
        second = pick_mod.pick_core(commit=False)
        self.assertEqual(first["rung"]["id"], second["rung"]["id"])
        self.assertFalse((self.root / "dojo/progress/state.json").exists())

    def test_dry_run_prints_table_and_never_mutates(self):
        rc, out, _ = self.run_main(pick_mod.main, ["--dry-run", "16"])
        self.assertEqual(rc, 0)
        data_rows = [l for l in out.splitlines() if l.startswith(tuple("123456789"))]
        self.assertEqual(len(data_rows), 16)
        self.assertIn("ai-ml-01", out)
        self.assertIn("counts: ai-ml 5", out)
        self.assertFalse((self.root / "dojo/progress/state.json").exists())

    def test_pick_output_shape(self):
        p = pick_mod.pick_core()
        for key in ("track", "rung", "rung_index", "total_rungs", "primer_needed", "level"):
            self.assertIn(key, p)
        self.assertEqual((p["track"], p["rung_index"], p["total_rungs"], p["primer_needed"], p["level"]),
                         ("ai-ml", 0, 6, False, "B"))
        self.assertEqual(p["rung"]["id"], "ai-ml-01")

    def test_finished_tracks_drop_out(self):
        st = state_mod.load_state()
        st["next_rung"] = {k: 6 for k in WEIGHTS}
        st["next_rung"]["rust"] = 5                                         # only rust has a rung left
        state_mod.save_state(st)
        self.assertEqual(pick_mod.pick_core(commit=True)["track"], "rust")
        with self.assertRaises(common.DojoError):
            pick_mod.pick_core()


class PrerequisiteTests(RepoTestCase):
    """default_tracks(): weights ai-ml 2 / networking 1; ai-ml-02 needs networking-01; networking-03 needs -02."""

    TODAY = dt.date(2026, 10, 6)

    def picks(self, n=4, today=None):
        tracks = common.require_curriculum()
        index = pick_mod.build_sent_index(common.load_all_lessons())
        return pick_mod.simulate(tracks, state_mod.load_state(tracks), index, today or self.TODAY, n)

    def test_blocked_track_is_skipped_for_the_next_best(self):
        seq = [(p["rung"]["id"], p["primer_needed"]) for p in self.picks(4)]
        self.assertEqual(seq[0], ("ai-ml-01", False))
        self.assertEqual(seq[1], ("networking-01", False))
        # day 3: ai-ml-02 has the highest credit but networking-01 was only sent today -> networking-02 instead
        self.assertEqual(seq[2], ("networking-02", False))

    def test_all_blocked_takes_highest_credit_with_primer_needed(self):
        tracks = common.require_curriculum()
        # ai-ml-02 needs networking-01 and networking-03 needs networking-02; neither was ever sent.
        st = {"credits": {"ai-ml": 0, "networking": 0}, "next_rung": {"ai-ml": 1, "networking": 2}}
        pick, credits, nxt = pick_mod.pick_next(tracks, st, {}, self.TODAY)
        self.assertEqual((pick["rung"]["id"], pick["primer_needed"]), ("ai-ml-02", True))
        self.assertEqual((credits, nxt), ({"ai-ml": 2 - 3, "networking": 1}, {"ai-ml": 2, "networking": 2}))
        self.assertFalse(pick["prereqs"][0]["satisfied"])

    def test_simulation_counts_each_pick_as_sent_on_its_day(self):
        # by day 4 networking-01 (sent on day 2) is two days old, so ai-ml-02 is no longer blocked
        seq = [(p["rung"]["id"], p["primer_needed"]) for p in self.picks(4)]
        self.assertEqual(seq[3], ("ai-ml-02", False))

    def test_prerequisite_satisfied_by_passed_or_skipped_lesson(self):
        for status in ("passed", "skipped"):
            with self.subTest(status=status):
                path = self.add_lesson("2026-10-06-1", "networking-01", status=status)
                state_mod.save_state({**state_mod.load_state(), "next_rung": {"ai-ml": 1, "networking": 1},
                                      "credits": {"ai-ml": 0, "networking": 0}})
                p = self.picks(1)[0]
                self.assertEqual((p["rung"]["id"], p["primer_needed"]), ("ai-ml-02", False))
                path.unlink()

    def test_prerequisite_satisfied_when_sent_two_days_ago_but_not_yesterday(self):
        state_mod.save_state({**state_mod.load_state(), "next_rung": {"ai-ml": 1, "networking": 1}})
        self.add_lesson("2026-10-05-1", "networking-01", status="sent")             # yesterday: not yet
        self.assertEqual(self.picks(1)[0]["rung"]["id"], "networking-02")
        for f in (self.root / "dojo/lessons").glob("*.md"):
            f.unlink()
        self.add_lesson("2026-10-04-1", "networking-01", status="sent")             # 2 days ago: fine
        p = self.picks(1)[0]
        self.assertEqual((p["rung"]["id"], p["primer_needed"]), ("ai-ml-02", False))

    def test_pick_reports_prereq_status(self):
        tracks = common.require_curriculum()
        st = {"credits": {}, "next_rung": {"ai-ml": 1, "networking": 3}}        # only ai-ml-02 is left
        pick, _, _ = pick_mod.pick_next(tracks, st, {}, self.TODAY)
        self.assertEqual(pick["prereqs"], [{"id": "networking-01", "title": "Network models", "satisfied": False}])
        index = {"networking-01": [{"status": "passed", "sent_date": self.TODAY}]}
        pick, _, _ = pick_mod.pick_next(tracks, st, index, self.TODAY)
        self.assertEqual((pick["prereqs"][0]["satisfied"], pick["primer_needed"]), (True, False))


class FreshSlotTests(RepoTestCase):
    def test_equal_shares_without_feeds_file(self):
        self.assertFalse((self.root / "dojo/feeds.yaml").exists())
        shares = pick_mod.load_shares(common.require_curriculum())
        self.assertEqual(shares, {"ai-ml": 0.5, "networking": 0.5})

    def test_domain_furthest_below_its_share(self):
        self.write("dojo/feeds.yaml", "domain_shares:\n  ai-ml: 0.6\n  networking: 0.4\n")
        st = state_mod.load_state()
        st["last_fresh_domains"] = ["ai-ml", "ai-ml", "ai-ml"]
        state_mod.save_state(st)
        r = pick_mod.pick_fresh()
        self.assertEqual(r["domain"], "networking")
        self.assertEqual(r["recent"], ["ai-ml", "ai-ml", "ai-ml"])
        self.assertAlmostEqual(r["shares"]["ai-ml"], 0.6)
        self.assertEqual(r["reader_level"], "B")

    def test_first_fresh_pick_goes_to_the_biggest_share(self):
        self.write("dojo/feeds.yaml", "domain_shares:\n  ai-ml: 0.7\n  networking: 0.3\n")
        self.assertEqual(pick_mod.pick_fresh()["domain"], "ai-ml")

    def test_recent_window_is_last_eight(self):
        st = state_mod.load_state()
        st["last_fresh_domains"] = ["networking"] * 5 + ["ai-ml"] * 8
        state_mod.save_state(st)
        self.assertEqual(pick_mod.pick_fresh()["recent"], ["ai-ml"] * 8)

    def test_reader_level_follows_last_passed_rung_of_the_track(self):
        self.assertEqual(pick_mod.reader_level("ai-ml", common.require_curriculum(), common.load_all_lessons()), "B")
        self.add_lesson("2026-10-01-1", "ai-ml-01", status="passed")
        self.add_lesson("2026-10-02-1", "ai-ml-02", status="passed", level="I")
        self.add_lesson("2026-10-03-1", "ai-ml-03", status="sent", level="A")        # not passed: ignored
        self.assertEqual(pick_mod.reader_level("ai-ml", common.require_curriculum(), common.load_all_lessons()), "I")

    def test_fresh_cli_prints_json(self):
        rc, out, _ = self.run_main(pick_mod.main, ["fresh"])
        data = json.loads(out)
        self.assertEqual(rc, 0)
        self.assertEqual(set(["domain", "reader_level", "shares", "recent"]) - set(data), set())


class EmptyCurriculumTests(RepoTestCase):
    with_readmes = False

    def test_clear_error_on_empty_curriculum_folder(self):
        for f in (self.root / "dojo/curriculum").glob("*.yaml"):
            f.unlink()
        for mode in (["core"], ["--dry-run", "16"]):
            r = subprocess.run([sys.executable, str(ENGINE_DIR / "pick.py"), *mode], cwd=self.root,
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn("no curriculum found", r.stderr)
            self.assertNotIn("Traceback", r.stderr)


if __name__ == "__main__":
    unittest.main()
