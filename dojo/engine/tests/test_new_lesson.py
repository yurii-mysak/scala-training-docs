"""new_lesson.py: scaffold content, front matter, state commit, idempotency, fresh lessons."""
from __future__ import annotations

import re
import unittest

from .support import RepoTestCase

import common
import new_lesson

SECTIONS = ["Why this matters", "The idea", "Worked example", "Self-check", "Sources", "Next on this track"]


def headings(body: str) -> list[str]:
    return [m.group(1) for m in re.finditer(r"^## (.+)$", body, re.M)]


class CoreLessonTests(RepoTestCase):
    def make(self, *extra, n="1"):
        rc, out, err = self.run_main(new_lesson.main, ["core", "--date", "2026-10-06", "--n", n, *extra])
        self.assertEqual(rc, 0, err)
        return out.strip()

    def test_creates_file_with_filled_front_matter(self):
        path = self.make("--new-day")
        self.assertEqual(path, "dojo/lessons/2026-10-06-1-what-machine-learning-actually-optimises.md")
        fm, body = common.load_lesson(self.root / path)
        self.assertEqual({k: fm[k] for k in ("id", "date", "slot", "track", "domain", "rung", "level", "title",
                                              "est_min", "files_to", "status", "sent_at", "marked_at", "filed_to",
                                              "review_due", "day")},
                         {"id": "2026-10-06-1", "date": "2026-10-06", "slot": "core", "track": "ai-ml",
                          "domain": "ai-ml", "rung": "ai-ml-01", "level": "B",
                          "title": "What machine learning actually optimises", "est_min": 20,
                          "files_to": "24-ai-ml-foundations", "status": "sent", "sent_at": "2026-10-06T06:00:00Z",
                          "marked_at": None, "filed_to": None, "review_due": None, "day": 1})
        self.assertEqual(fm["sources"], [{"title": "Source for ai-ml 1", "url": "https://example.com/ai-ml/1"}])
        self.assertTrue(body.startswith("# What machine learning actually optimises\n"))

    def test_scaffold_has_every_section_in_order_with_writer_hints(self):
        _, body = common.load_lesson(self.root / self.make())
        self.assertEqual(headings(body), SECTIONS)
        self.assertIn("> AI / ML foundations · Beginner · ~20 min · rung 1 of 3 · needs: —", body)
        for needle in ("EVIDENCE RULE", "VERBATIM quote", "mermaid", "accessed 2026-10-06",
                       "ai-ml point 1.1", "A diagram of ai-ml 1.", "A tiny example for ai-ml 1."):
            self.assertIn(needle, body)
        self.assertIn("<details><summary>Answer</summary>", body)
        self.assertIn("Next on AI / ML foundations: **Gradient descent by hand** (rung 2 of 3, Intermediate).", body)
        self.assertNotIn("{{", body)
        self.assertNotIn("## Primer", body)

    def test_presentation_hint_follows_the_rung(self):
        path = self.root / "dojo/curriculum/ai-ml.yaml"
        data = common.load_yaml(path)
        data["rungs"][0]["presentation"] = "deep"
        common.save_yaml(path, data)
        _, body = common.load_lesson(self.root / self.make())
        self.assertIn("Presentation DEEP", body)
        self.assertNotIn("Presentation MINIMAL", body)

    def test_commits_picker_state(self):
        self.make("--new-day")
        st = self.state()
        self.assertEqual((st["day"], st["lessons_sent"], st["lessons_passed"], st["open"]),
                         (1, 1, 0, ["2026-10-06-1"]))
        self.assertEqual(st["next_rung"], {"ai-ml": 1, "networking": 0})
        self.assertEqual(st["credits"], {"ai-ml": -1, "networking": 1})
        events = self.log_events()
        self.assertEqual((events[-1]["event"], events[-1]["lesson"]), ("sent", "2026-10-06-1"))

    def test_idempotent_for_the_same_id(self):
        first = self.make("--new-day")
        before = self.state()
        again = self.make("--new-day")
        self.assertEqual(first, again)
        self.assertEqual(self.state(), before)
        self.assertEqual(len(list((self.root / "dojo/lessons").glob("*.md"))), 1)

    def test_day_counter_increments_once_per_date(self):
        self.make("--new-day", n="1")
        self.make("--new-day", n="2")                                    # same date: no second increment
        self.assertEqual(self.state()["day"], 1)
        rc, out, _ = self.run_main(new_lesson.main, ["core", "--date", "2026-10-07", "--n", "1", "--new-day"])
        self.assertEqual(self.state()["day"], 2)
        self.assertEqual(common.load_lesson(self.root / out.strip())[0]["day"], 2)

    def test_without_new_day_the_counter_stays(self):
        self.make()
        self.assertEqual(self.state()["day"], 0)

    def test_two_core_lessons_follow_the_cadence(self):
        a = self.make(n="1")
        b = self.make(n="3")                                             # on-demand slot 3
        rungs = [common.load_lesson(self.root / p)[0]["rung"] for p in (a, b)]
        self.assertEqual(rungs, ["ai-ml-01", "networking-01"])

    def test_primer_flag_when_prerequisite_missing(self):
        common.save_json(self.root / "dojo/progress/state.json",
                         {"credits": {}, "next_rung": {"ai-ml": 1, "networking": 3}})
        path = self.make()
        fm, body = common.load_lesson(self.root / path)
        self.assertEqual((fm["rung"], fm.get("primer_needed")), ("ai-ml-02", True))
        self.assertIn("## Primer", body)
        self.assertIn("needs: Network models (networking-01) [not done yet: primer included]", body)


class FreshLessonTests(RepoTestCase):
    def make(self, *extra, n="2"):
        rc, out, err = self.run_main(new_lesson.main, [
            "fresh", "--date", "2026-10-06", "--n", n, "--title", "KV cache explained",
            "--domain", "ai-ml", "--level", "I", "--est-min", "25", *extra])
        self.assertEqual(rc, 0, err)
        return out.strip()

    def test_fresh_front_matter(self):
        path = self.make()
        self.assertEqual(path, "dojo/lessons/2026-10-06-2-kv-cache-explained.md")
        fm, body = common.load_lesson(self.root / path)
        self.assertEqual((fm["slot"], fm["track"], fm["domain"], fm["rung"], fm["level"], fm["est_min"]),
                         ("fresh", "fresh", "ai-ml", None, "I", 25))
        self.assertEqual((fm["files_to"], fm["status"], fm["title"]), ("24-ai-ml-foundations", "sent", "KV cache explained"))
        self.assertEqual(headings(body), SECTIONS)
        self.assertIn("at least TWO verbatim quoted passages", body)

    def test_state_changes_for_fresh(self):
        self.make()
        st = self.state()
        self.assertEqual(st["last_fresh_domains"], ["ai-ml"])
        self.assertEqual(st["next_rung"], {"ai-ml": 0, "networking": 0}, "fresh lessons never consume a rung")
        self.assertEqual((st["lessons_sent"], st["open"]), (1, ["2026-10-06-2"]))

    def test_files_to_override_and_unknown_domain(self):
        path = self.make("--files-to", "25-software-architecture")
        self.assertEqual(common.load_lesson(self.root / path)[0]["files_to"], "25-software-architecture")
        with self.assertRaises(common.DojoError):
            self.run_main(new_lesson.main, ["fresh", "--date", "2026-10-06", "--n", "3", "--title", "x",
                                            "--domain", "no-such-track"])

    def test_primer_section_goes_right_after_why_this_matters(self):
        _, body = common.load_lesson(self.root / self.make("--primer"))
        self.assertEqual(headings(body), ["Why this matters", "Primer", "The idea", "Worked example", "Self-check",
                                          "Sources", "Next on this track"])

    def test_recent_domains_keep_the_last_eight(self):
        st = {"last_fresh_domains": ["networking"] * 8}
        common.save_json(self.root / "dojo/progress/state.json", st)
        self.make()
        self.assertEqual(self.state()["last_fresh_domains"], ["networking"] * 7 + ["ai-ml"])


if __name__ == "__main__":
    unittest.main()
