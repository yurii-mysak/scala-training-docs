"""mermaid.py: renders diagrams with the real mmdc when present (skipped otherwise)."""
from __future__ import annotations

import unittest
from unittest import mock

from .support import RepoTestCase

import common
import mermaid

GOOD = "flowchart LR\n  A[Data] --> B[Model] --> C[Loss]"


def lesson_with(*diagrams: str) -> str:
    body = "# T\n\n## The idea\n"
    for d in diagrams:
        body += f"\n```mermaid\n{d}\n```\n"
    return body + "\n```python\nprint('not a diagram')\n```\n"


class MermaidWithoutBinaryTests(RepoTestCase):
    def test_missing_mmdc_is_tolerated(self):
        path = self.add_lesson("2026-10-06-1", "ai-ml-01", body=lesson_with(GOOD))
        with mock.patch.object(mermaid, "find_mmdc", return_value=None):
            res = mermaid.render_lesson(path)
        self.assertEqual(len(res), 1)
        self.assertIsNone(res[0]["png"])
        self.assertIn("mmdc not found", res[0]["error"])
        self.assertEqual((res[0]["k"], res[0]["mermaid_source"]), (1, GOOD))

    def test_lesson_without_diagrams_returns_empty_list(self):
        path = self.add_lesson("2026-10-06-1", "ai-ml-01", body="# T\n\nno diagram\n")
        self.assertEqual(mermaid.render_lesson(path), [])


@unittest.skipUnless(mermaid.find_mmdc(), "mmdc (Mermaid CLI) is not installed")
class MermaidRenderTests(RepoTestCase):
    def test_renders_png_idempotently_and_reports_json(self):
        path = self.add_lesson("2026-10-06-1", "ai-ml-01", body=lesson_with(GOOD, "graph TD\n  X --> Y"))
        res = mermaid.render_lesson(path)
        self.assertEqual([r["k"] for r in res], [1, 2])
        for r in res:
            self.assertIsNone(r.get("error"), r)
            png = self.root / r["png"]
            self.assertEqual(r["png"], f"dojo/lessons/assets/2026-10-06-1-{r['k']}.png")
            self.assertEqual(png.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
            self.assertGreater(png.stat().st_size, 1000)
        self.assertEqual(res[0]["mermaid_source"], GOOD)
        mtimes = [(self.root / r["png"]).stat().st_mtime_ns for r in res]
        again = mermaid.render_lesson(path)
        self.assertEqual([(self.root / r["png"]).stat().st_mtime_ns for r in again], mtimes, "not re-rendered")
        with mock.patch.object(mermaid.subprocess, "run", side_effect=AssertionError("mmdc must not run")):
            mermaid.render_lesson(path)

    def test_changed_source_is_re_rendered(self):
        path = self.add_lesson("2026-10-06-1", "ai-ml-01", body=lesson_with(GOOD))
        first = mermaid.render_lesson(path)[0]
        before = (self.root / first["png"]).read_bytes()
        common.save_lesson(path, *(lambda fm, b: (fm, b.replace("Loss", "Cost and a much longer label here")))(
            *common.load_lesson(path)))
        second = mermaid.render_lesson(path)[0]
        self.assertNotEqual((self.root / second["png"]).read_bytes(), before)

    def test_bad_diagram_yields_error_not_crash(self):
        path = self.add_lesson("2026-10-06-1", "ai-ml-01", body=lesson_with(GOOD, "this is definitely not mermaid ((("))
        res = mermaid.render_lesson(path)
        self.assertIsNotNone(res[0]["png"])
        self.assertIsNone(res[1]["png"])
        self.assertTrue(res[1]["error"])

    def test_rendered_diagram_is_embedded_in_the_email(self):
        import render_email
        path = self.add_lesson("2026-10-06-1", "ai-ml-01", body=lesson_with(GOOD))
        mermaid.render_lesson(path)
        render_email.IMG_MODE["mode"] = "cid"
        try:
            email = render_email.build_email(["2026-10-06-1"])
        finally:
            render_email.IMG_MODE["mode"] = "raw"
        self.assertIn('<img src="cid:2026-10-06-1-1.png" alt="diagram"', email["html"])
        att = email["attachments"][0]
        self.assertEqual((att["cid"], att["mimeType"], att["inline"]), ("2026-10-06-1-1.png", "image/png", True))
        with open(att["path"], "rb") as fh:
            self.assertEqual(fh.read(8), b"\x89PNG\r\n\x1a\n")
        self.assertNotIn("flowchart LR", email["html"])

    def test_cli_prints_json_list(self):
        import json
        self.add_lesson("2026-10-06-1", "ai-ml-01", body=lesson_with(GOOD))
        rc, out, err = self.run_main(mermaid.main, ["2026-10-06-1"])
        data = json.loads(out)
        self.assertEqual((rc, len(data), data[0]["k"]), (0, 1, 1))
        self.assertTrue(data[0]["png"].endswith("2026-10-06-1-1.png"))


if __name__ == "__main__":
    unittest.main()
