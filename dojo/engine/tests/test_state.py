"""state.py: creation, track top-up, preservation of unknown keys, recount."""
from __future__ import annotations

import json
import unittest

from .support import RepoTestCase

import common
import state as state_mod


class StateTests(RepoTestCase):
    def test_new_state_has_every_track(self):
        st = state_mod.load_state()
        self.assertEqual(st["schema"], 1)
        self.assertEqual(st["credits"], {"ai-ml": 0, "networking": 0})
        self.assertEqual(st["next_rung"], {"ai-ml": 0, "networking": 0})
        self.assertEqual((st["day"], st["lessons_sent"], st["open"]), (0, 0, []))
        self.assertFalse((self.root / "dojo/progress/state.json").exists(), "load must not write")

    def test_unknown_keys_survive_and_new_tracks_are_added(self):
        state_mod.save_state({"schema": 1, "day": 4, "credits": {"ai-ml": 3}, "next_rung": {"ai-ml": 2},
                              "dashboard_url": "https://claude.ai/artifact/x", "my_custom_key": {"a": 1}})
        common.save_yaml(self.root / "dojo/curriculum/rust.yaml",
                         {"track": "rust", "name": "Rust", "weight": 1, "files_to": "26-rust", "rungs": []})
        st = state_mod.load_state()
        self.assertEqual(st["my_custom_key"], {"a": 1})
        self.assertEqual(st["credits"]["ai-ml"], 3)                       # existing value untouched
        self.assertEqual(st["credits"]["rust"], 0)                        # new track initialised
        self.assertEqual(st["next_rung"]["rust"], 0)
        state_mod.save_state(st)
        self.assertEqual(self.state()["my_custom_key"], {"a": 1})

    def test_recount_from_lesson_files(self):
        self.add_lesson("2026-10-05-1", "ai-ml-01", status="passed")
        self.add_lesson("2026-10-05-2", None, slot="fresh", status="review", domain="ai-ml")
        self.add_lesson("2026-10-06-1", "networking-01", status="sent")
        st = state_mod.recount(state_mod.load_state())
        self.assertEqual((st["lessons_sent"], st["lessons_passed"]), (3, 1))
        self.assertEqual(st["open"], ["2026-10-06-1"])

    def test_cli_init_set_touch_log(self):
        rc, out, _ = self.run_main(state_mod.main, ["init"])
        self.assertEqual(rc, 0)
        self.assertTrue((self.root / "dojo/progress/state.json").exists())
        self.run_main(state_mod.main, ["set", "dashboard_url", "https://claude.ai/artifact/abc"])
        self.run_main(state_mod.main, ["set", "day", "7"])
        self.run_main(state_mod.main, ["touch"])
        st = self.state()
        self.assertEqual((st["dashboard_url"], st["day"], st["last_run_at"]),
                         ("https://claude.ai/artifact/abc", 7, "2026-10-06T06:00:00Z"))
        self.run_main(state_mod.main, ["log", "reminded", "--lesson", "2026-10-06-1", "--note", "open"])
        self.assertEqual(self.log_events()[-1]["event"], "reminded")


if __name__ == "__main__":
    unittest.main()
