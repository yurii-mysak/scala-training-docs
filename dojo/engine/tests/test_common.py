"""common.py: slugs, front matter, time helpers, log, templates."""
from __future__ import annotations

import datetime as dt
import json
import unittest

from . import support
from .support import RepoTestCase

import common


class CommonTests(RepoTestCase):
    def test_slugify(self):
        self.assertEqual(common.slugify("What machine learning actually optimises"),
                         "what-machine-learning-actually-optimises")
        self.assertEqual(common.slugify("DNS & DHCP: how (and why)?"), "dns-dhcp-how-and-why")
        self.assertEqual(common.slugify("Привіт"), "lesson")            # nothing ASCII left
        long = common.slugify("word " * 40, max_len=30)
        self.assertLessEqual(len(long), 30)
        self.assertFalse(long.endswith("-"))

    def test_front_matter_round_trip_keeps_dates_as_strings(self):
        fm = {"id": "2026-10-06-1", "date": "2026-10-06", "sent_at": "2026-10-06T06:00:00Z", "marked_at": None,
              "est_min": 20, "title": "Gradient: a story", "sources": [{"title": "T", "url": "https://x.y/z"}]}
        text = common.build_lesson_text(fm, "# Body\n")
        self.assertTrue(text.startswith("---\nid: 2026-10-06-1\n"))
        back, body = common.parse_front_matter(text)
        self.assertEqual(back, fm)
        self.assertEqual(body, "# Body\n")
        self.assertEqual(common.parse_front_matter("# no front matter\n"), ({}, "# no front matter\n"))

    def test_kyiv_time_follows_dst(self):
        summer = common.to_kyiv(common.parse_ts("2026-10-06T06:00:00Z"))
        winter = common.to_kyiv(common.parse_ts("2026-12-01T06:00:00Z"))
        self.assertEqual((summer.hour, winter.hour), (9, 8))            # 09:00 Kyiv delivery
        self.assertEqual(common.kyiv_date_of("2026-10-06T22:30:00Z"), dt.date(2026, 10, 7))
        self.assertEqual(common.kyiv_today(), dt.date(2026, 10, 6))     # DOJO_NOW pinned by the fixture

    def test_kyiv_fallback_matches_zoneinfo(self):
        fb = common._KyivFallback()
        for ts in ("2026-01-15T12:00:00Z", "2026-03-28T12:00:00Z", "2026-03-29T00:30:00Z", "2026-03-29T01:30:00Z",
                   "2026-07-01T00:00:00Z", "2026-10-24T23:00:00Z", "2026-10-25T00:30:00Z", "2026-10-25T01:30:00Z"):
            utc = common.parse_ts(ts)
            self.assertEqual(utc.astimezone(fb).replace(tzinfo=None), common.to_kyiv(utc).replace(tzinfo=None), ts)

    def test_log_event_appends_json_lines(self):
        common.log_event("sent", "2026-10-06-1", "job", "first")
        common.log_event("passed", "2026-10-06-1", "dashboard")
        events = self.log_events()
        self.assertEqual([e["event"] for e in events], ["sent", "passed"])
        self.assertEqual(events[0], {"ts": "2026-10-06T06:00:00Z", "event": "sent", "lesson": "2026-10-06-1",
                                     "by": "job", "note": "first"})

    def test_strip_html_comments_spares_code_fences(self):
        md = "a <!-- hint -->b\n```html\n<!-- keep -->\n```\n<!-- multi\nline -->\nend\n"
        out = common.strip_html_comments(md)
        self.assertIn("<!-- keep -->", out)
        self.assertNotIn("hint", out)
        self.assertNotIn("multi", out)

    def test_render_template_conditionals_and_safe_values(self):
        tpl = "A {{x}}\n{{#on}}\nshown {{y}}\n{{/on}}\n{{#off}}\nhidden\n{{/off}}\nend"
        out = common.render_template(tpl, {"x": "{{y}}", "y": "why", "on": True, "off": False})
        self.assertEqual(out, "A {{y}}\nshown why\nend")

    def test_mermaid_block_finder(self):
        md = "x\n```mermaid\nflowchart LR\n  A-->B\n```\ny\n```python\nz\n```\n```mermaid\ngraph TD\n```\n"
        blocks = common.find_mermaid_blocks(md)
        self.assertEqual([b["k"] for b in blocks], [1, 2])
        self.assertIn("A-->B", blocks[0]["source"])

    def test_curriculum_loading_orders_tracks_and_reports_empty(self):
        self.assertEqual(list(common.load_curriculum()), ["ai-ml", "networking"])
        for f in (self.root / "dojo" / "curriculum").glob("*.yaml"):
            f.unlink()
        with self.assertRaises(common.DojoError) as cm:
            common.require_curriculum()
        self.assertIn("no curriculum", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
