"""sync_db.py: lesson / track / meta documents for the dashboard database."""
from __future__ import annotations

import json
import unittest

from .support import RepoTestCase

import common
import mark
import new_lesson
import state as state_mod
import sync_db


class SyncDbTests(RepoTestCase):
    def setUp(self):
        super().setUp()
        self.run_main(new_lesson.main, ["core", "--date", "2026-10-06", "--n", "1", "--new-day"])
        self.run_main(new_lesson.main, ["fresh", "--date", "2026-10-06", "--n", "2", "--title", "Fresh thing",
                                        "--domain", "ai-ml", "--level", "I"])

    def doc(self, collection, name):
        return json.loads((self.root / f"dojo/out/db/{collection}/{name}.json").read_text(encoding="utf-8"))

    def test_lesson_export_has_every_spec_field(self):
        written = sync_db.export_lessons(["2026-10-06-1"])
        self.assertEqual(written, [{"collection": "lessons", "id": "2026-10-06-1",
                                    "path": "dojo/out/db/lessons/2026-10-06-1.json"}])
        d = self.doc("lessons", "2026-10-06-1")
        self.assertEqual(set(d), {"id", "date", "slot", "track", "track_name", "domain", "rung", "level", "title",
                                  "est_min", "status", "sent_at", "marked_at", "summary", "md", "filed_to",
                                  "review_due", "sources", "day"})
        self.assertEqual((d["track"], d["track_name"], d["slot"], d["rung"], d["level"], d["status"], d["day"]),
                         ("ai-ml", "AI / ML foundations", "core", "ai-ml-01", "B", "sent", 1))
        self.assertEqual(d["summary"], "Summary of ai-ml rung 1. It teaches one idea.")
        self.assertEqual(d["sources"], [{"title": "Source for ai-ml 1", "url": "https://example.com/ai-ml/1"}])
        self.assertTrue(d["md"].startswith("# What machine learning actually optimises"))
        self.assertNotIn("---\nid:", d["md"])                         # front matter stripped
        self.assertNotIn("<!--", d["md"])                             # scaffold hints stripped

    def test_fresh_lesson_document(self):
        sync_db.export_lessons(["2026-10-06-2"])
        d = self.doc("lessons", "2026-10-06-2")
        self.assertEqual((d["track"], d["track_name"], d["domain"], d["rung"], d["slot"]),
                         ("fresh", "Fresh", "ai-ml", None, "fresh"))

    def test_export_all_and_status_changes_are_reflected(self):
        mark.mark("2026-10-06-1", "review", at="2026-10-06T18:00:00Z")
        written = sync_db.export_lessons(None)
        self.assertEqual([w["id"] for w in written], ["2026-10-06-1", "2026-10-06-2"])
        d = self.doc("lessons", "2026-10-06-1")
        self.assertEqual((d["status"], d["marked_at"], d["review_due"]), ("review", "2026-10-06T18:00:00Z", "2026-10-13"))

    def test_tracks(self):
        mark.mark("2026-10-06-1", "passed")
        written = sync_db.export_tracks()
        self.assertEqual({w["id"] for w in written}, {"ai-ml", "networking"})
        self.assertEqual(self.doc("tracks", "ai-ml"),
                         {"key": "ai-ml", "name": "AI / ML foundations", "weight": 2, "total": 3, "done": 1,
                          "next_title": "Gradient descent by hand", "next_level": "I",
                          "files_to": "24-ai-ml-foundations"})
        n = self.doc("tracks", "networking")
        self.assertEqual((n["done"], n["total"], n["next_title"], n["next_level"]), (0, 3, "Network models", "B"))

    def test_finished_track_has_null_next(self):
        st = state_mod.load_state()
        st["next_rung"]["networking"] = 3
        state_mod.save_state(st)
        sync_db.export_tracks()
        n = self.doc("tracks", "networking")
        self.assertEqual((n["next_title"], n["next_level"]), (None, None))

    def test_meta(self):
        st = state_mod.load_state()
        st.update({"trigger_id": "trig_1", "reminder_trigger_id": "trig_2", "last_run_at": "2026-10-06T06:01:00Z"})
        state_mod.save_state(st)
        mark.mark("2026-10-06-1", "passed", at="2026-10-06T10:00:00Z")
        sync_db.export_meta()
        m = self.doc("meta", "state")
        self.assertEqual(set(m), {"day", "lessons_sent", "lessons_passed", "open", "last_run_at", "last_run_summary",
                                  "trigger_id", "reminder_trigger_id", "repo_url", "streak"})
        self.assertEqual((m["day"], m["lessons_sent"], m["lessons_passed"], m["open"]), (1, 2, 1, ["2026-10-06-2"]))
        self.assertEqual((m["trigger_id"], m["reminder_trigger_id"], m["last_run_at"]),
                         ("trig_1", "trig_2", "2026-10-06T06:01:00Z"))
        self.assertEqual(m["repo_url"], "https://github.com/yurii-mysak/scala-training-docs")
        self.assertIn("2 lessons sent", m["last_run_summary"])
        self.assertEqual(m["streak"], 1)

    def test_streak_counts_consecutive_days_with_a_pass(self):
        L = lambda d: [{"fm": {"status": "passed", "marked_at": d}}]
        import datetime as dt
        today = dt.date(2026, 10, 6)
        days = L("2026-10-06T10:00:00Z") + L("2026-10-05T10:00:00Z") + L("2026-10-04T10:00:00Z") + L("2026-10-02T10:00:00Z")
        self.assertEqual(sync_db.compute_streak(days, today), 3)
        self.assertEqual(sync_db.compute_streak(days[1:], today), 2, "today still open: count from yesterday")
        self.assertEqual(sync_db.compute_streak(days[3:], today), 0)
        self.assertEqual(sync_db.compute_streak([], today), 0)

    def test_cli_all_lists_everything_written(self):
        rc, out, err = self.run_main(sync_db.main, ["all"])
        self.assertEqual(rc, 0, err)
        written = json.loads(out)
        self.assertEqual(sorted(w["collection"] for w in written),
                         ["lessons", "lessons", "meta", "tracks", "tracks"])
        self.assertTrue(all((self.root / w["path"]).exists() for w in written))


if __name__ == "__main__":
    unittest.main()
