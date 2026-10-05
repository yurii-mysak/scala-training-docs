"""mark.py: status transitions, review_due, state recount, log, idempotency."""
from __future__ import annotations

import unittest

from .support import RepoTestCase

import common
import mark
import new_lesson


class MarkTests(RepoTestCase):
    def setUp(self):
        super().setUp()
        self.run_main(new_lesson.main, ["core", "--date", "2026-10-06", "--n", "1", "--new-day"])
        self.run_main(new_lesson.main, ["fresh", "--date", "2026-10-06", "--n", "2", "--title", "Fresh one",
                                        "--domain", "ai-ml"])
        self.a, self.b = "2026-10-06-1", "2026-10-06-2"

    def test_passed_updates_front_matter_state_and_log(self):
        res = mark.mark(self.a, "passed", by="dashboard", at="2026-10-06T18:30:00Z")
        self.assertEqual((res["status"], res["changed"], res["previous"]), ("passed", True, "sent"))
        fm = self.lesson_fm(self.a)
        self.assertEqual((fm["status"], fm["marked_at"], fm["review_due"]), ("passed", "2026-10-06T18:30:00Z", None))
        st = self.state()
        self.assertEqual((st["lessons_passed"], st["open"], st["lessons_sent"]), (1, [self.b], 2))
        last = self.log_events()[-1]
        self.assertEqual((last["event"], last["lesson"], last["by"]), ("passed", self.a, "dashboard"))

    def test_review_sets_due_date_seven_days_out(self):
        mark.mark(self.b, "review", by="chat", at="2026-10-06T18:30:00Z")
        fm = self.lesson_fm(self.b)
        self.assertEqual((fm["status"], fm["review_due"]), ("review", "2026-10-13"))
        self.assertNotIn(self.b, self.state()["open"])

    def test_review_due_uses_the_kyiv_date(self):
        mark.mark(self.b, "review", at="2026-10-06T22:30:00Z")           # 01:30 on the 7th in Kyiv
        self.assertEqual(self.lesson_fm(self.b)["review_due"], "2026-10-14")

    def test_skipped_clears_open_and_review_due(self):
        mark.mark(self.a, "review", at="2026-10-06T10:00:00Z")
        mark.mark(self.a, "skipped", at="2026-10-06T11:00:00Z")
        fm = self.lesson_fm(self.a)
        self.assertEqual((fm["status"], fm["review_due"]), ("skipped", None))
        st = self.state()
        self.assertEqual((st["lessons_passed"], st["open"]), (0, [self.b]))

    def test_marking_defaults_to_now(self):
        mark.mark(self.a, "passed")
        self.assertEqual(self.lesson_fm(self.a)["marked_at"], "2026-10-06T06:00:00Z")   # DOJO_NOW

    def test_idempotent(self):
        mark.mark(self.a, "passed", at="2026-10-06T18:30:00Z")
        events = len(self.log_events())
        before = (self.root / "dojo/lessons" / common.find_lesson_path(self.a).name).read_text(encoding="utf-8")
        res = mark.mark(self.a, "passed", by="chat", at="2026-10-07T09:00:00Z")
        self.assertFalse(res["changed"])
        self.assertEqual(len(self.log_events()), events)
        self.assertEqual(common.find_lesson_path(self.a).read_text(encoding="utf-8"), before)

    def test_sent_reopens_a_lesson(self):
        mark.mark(self.a, "passed", at="2026-10-06T18:30:00Z")
        mark.mark(self.a, "sent", by="chat", at="2026-10-06T19:00:00Z")
        self.assertEqual(self.lesson_fm(self.a)["status"], "sent")
        st = self.state()
        self.assertEqual((st["lessons_passed"], sorted(st["open"])), (0, [self.a, self.b]))
        self.assertEqual(self.log_events()[-1]["event"], "sent")

    def test_cli_accepts_all_four_statuses_and_path_or_id(self):
        for status in ("passed", "review", "skipped", "sent"):
            rc, out, err = self.run_main(mark.main, [self.a, status, "--by", "job"])
            self.assertEqual(rc, 0, err)
        rc, out, _ = self.run_main(mark.main, [str(common.find_lesson_path(self.b)), "passed"])
        self.assertIn('"status": "passed"', out)

    def test_unknown_lesson_is_a_clean_error(self):
        with self.assertRaises(common.DojoError):
            mark.mark("2099-01-01-1", "passed")


if __name__ == "__main__":
    unittest.main()
