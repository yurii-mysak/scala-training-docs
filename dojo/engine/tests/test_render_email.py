"""render_email.py: subject, HTML structure, inline diagrams, plain text, attachments."""
from __future__ import annotations

import html as html_lib
import json
import re
import unittest

from .support import RepoTestCase, tiny_png

import common
import new_lesson
import render_email as re_mod
import state as state_mod

FOOTER = "Mark them on the Dojo, or tell Claude in the IT Iaido project: 'passed both' / 'review 1' / 'skip 2'"


class RenderEmailTests(RepoTestCase):
    def setUp(self):
        super().setUp()
        self.add_lesson("2026-10-06-1", "ai-ml-01", title="What machine learning actually optimises", day=12)
        self.add_lesson("2026-10-06-2", None, slot="fresh", title="KV cache explained", level="I", domain="ai-ml",
                        day=12, est_min=25, body="# KV cache explained\n\n> Fresh · AI / ML foundations · Intermediate · ~25 min\n\n"
                                     "## Why this matters\nBecause *speed*.\n\n## The idea\n"
                                     "```mermaid\nflowchart TD\n  A --> B\n```\n\n"
                                     "> \"Keys and values are cached.\" — Org, *Post*, 2025-01-01, https://example.com\n\n"
                                     "## Self-check\n1. Q <details><summary>Answer</summary>A</details>\n")
        (self.root / "dojo/lessons/assets").mkdir(parents=True, exist_ok=True)
        (self.root / "dojo/lessons/assets/2026-10-06-1-1.png").write_bytes(tiny_png(800, 300))
        st = state_mod.load_state()
        st["dashboard_url"] = "https://claude.ai/artifact/dojo123"
        state_mod.save_state(st)
        self.email = re_mod.build_email(["2026-10-06-1", "2026-10-06-2"])

    def test_subject(self):
        self.assertEqual(self.email["subject"],
                         "IT Iaido · Day 12 · What machine learning actually optimises · KV cache explained")

    def test_html_header_cards_footer(self):
        page = self.email["html"]
        plain = html_lib.unescape(page)
        self.assertTrue(page.startswith("<!doctype html>"))
        self.assertIn("IT Iaido · Day 12 · Tue 6 Oct 2026", plain)
        self.assertIn("2 lessons · 45 min total", plain)                     # 20 + 25 est_min
        self.assertEqual(page.count("lesson 1 of 2") + page.count("lesson 2 of 2"), 2)
        self.assertIn("Core · lesson 1 of 2 · 20 min", plain)
        self.assertIn("Fresh · lesson 2 of 2 · 25 min", plain)
        self.assertIn("AI / ML foundations · Beginner · ~20 min · rung 1 of 3", plain)   # meta line in the card header
        self.assertIn('href="https://claude.ai/artifact/dojo123"', page)
        self.assertIn(FOOTER, plain)
        self.assertIn("max-width:680px", page)

    def test_email_safe_markup(self):
        page = self.email["html"]
        self.assertNotIn("<style", page)
        self.assertNotIn("<script", page)
        self.assertNotIn("<!--", page)
        self.assertNotIn("{{", page)
        self.assertNotIn("```", page)
        self.assertRegex(page, r'<pre style="[^"]*background:#f6f8fa')       # readable code blocks
        self.assertRegex(page, r'<blockquote style="[^"]*border-left:4px solid')   # evidence quotes
        self.assertIn("<details", page)                                      # self-check answers kept
        self.assertIn("<summary", page)
        self.assertRegex(page, r"<table [^>]*border-collapse:collapse")

    def test_mermaid_with_png_becomes_raw_github_image_by_default(self):
        page = self.email["html"]
        self.assertIn('<img src="https://raw.githubusercontent.com/yurii-mysak/scala-training-docs/main/'
                      'dojo/lessons/assets/2026-10-06-1-1.png" alt="diagram"', page)
        self.assertRegex(page, r'<img src="https://raw\.githubusercontent\.com[^"]*2026-10-06-1-1\.png" alt="diagram"[^>]*style="[^"]*max-width:100%')
        self.assertEqual(self.email["attachments"], [])                      # nothing attached in raw mode
        self.assertIn('width="400"', page)                                   # 2x render shown at half width

    def test_mermaid_with_png_becomes_cid_image_and_attachment_in_cid_mode(self):
        re_mod.IMG_MODE["mode"] = "cid"
        try:
            email = re_mod.build_email(["2026-10-06-1", "2026-10-06-2"])
        finally:
            re_mod.IMG_MODE["mode"] = "raw"
        page = email["html"]
        self.assertIn('<img src="cid:2026-10-06-1-1.png" alt="diagram"', page)
        self.assertEqual(len(email["attachments"]), 1)
        att = email["attachments"][0]
        self.assertEqual((att["filename"], att["cid"], att["mimeType"], att["inline"]),
                         ("2026-10-06-1-1.png", "2026-10-06-1-1.png", "image/png", True))
        self.assertTrue(att["path"].endswith("dojo/lessons/assets/2026-10-06-1-1.png"))

    def test_mermaid_without_png_falls_back_to_pre(self):
        page = self.email["html"]
        self.assertNotIn("2026-10-06-2-1.png", page)
        self.assertRegex(page, r"<pre[^>]*><code[^>]*>flowchart TD")

    def test_plain_text_version(self):
        text = self.email["text"]
        self.assertTrue(text.startswith("IT Iaido · Day 12 · Tue 6 Oct 2026 · 2 lessons · 45 min"))
        self.assertNotRegex(text, r"</?(p|div|table|details|summary|pre)\b")
        self.assertIn("What machine learning actually optimises", text)
        self.assertIn("[diagram: see the HTML version or the Dojo]", text)
        self.assertIn("Dojo dashboard: https://claude.ai/artifact/dojo123", text)
        self.assertIn(FOOTER, text)
        self.assertIn("Answer: A", text)

    def test_cli_writes_email_json(self):
        rc, out, err = self.run_main(re_mod.main, ["2026-10-06-1", "2026-10-06-2", "--img-mode", "cid"])
        self.assertEqual(rc, 0, err)
        data = json.loads((self.root / "dojo/out/email.json").read_text(encoding="utf-8"))
        self.assertEqual(set(data) >= {"subject", "html", "text", "attachments"}, True)
        self.assertEqual(data["attachments"][0]["cid"], "2026-10-06-1-1.png")
        self.assertEqual(json.loads(out)["attachments"], 1)
        re_mod.IMG_MODE["mode"] = "raw"  # main() set the module flag; restore for other tests

    def test_single_lesson_subject_and_missing_dashboard(self):
        st = state_mod.load_state()
        st["dashboard_url"] = None
        state_mod.save_state(st)
        email = re_mod.build_email(["2026-10-06-2"])
        self.assertEqual(email["subject"], "IT Iaido · Day 12 · KV cache explained")
        self.assertNotIn("Open the Dojo dashboard", email["html"])
        self.assertIn("1 lesson ·", html_lib.unescape(email["html"]))

    def test_scaffold_hints_never_leak_into_the_email(self):
        self.run_main(new_lesson.main, ["core", "--date", "2026-10-07", "--n", "1", "--new-day"])
        email = re_mod.build_email(["2026-10-07-1"])
        self.assertNotIn("WRITER", email["html"])
        self.assertNotIn("EVIDENCE RULE", email["text"])

    def test_user_text_is_escaped_in_the_header(self):
        self.add_lesson("2026-10-08-1", "ai-ml-02", title="Ampersands & <tags>", level="I", day=13)
        email = re_mod.build_email(["2026-10-08-1"])
        self.assertIn("Ampersands &amp; &lt;tags&gt;", email["html"])
        self.assertEqual(email["subject"], "IT Iaido · Day 13 · Ampersands & <tags>")


if __name__ == "__main__":
    unittest.main()
