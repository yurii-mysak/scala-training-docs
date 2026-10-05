"""file_passed.py: section creation, README rows, root README blocks, filed copy, idempotency."""
from __future__ import annotations

import re
import unittest

from . import support
from .support import RepoTestCase

import common
import file_passed as fp
import mark


def table_rows(text: str, heading: str) -> list[str]:
    """Rows of the first table under `## heading` in a section README."""
    m = re.search(rf"^## {heading}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return [l for l in m.group(1).splitlines() if re.match(r"^\| \d+ \|", l)]


class NewSectionTests(RepoTestCase):
    def setUp(self):
        super().setUp()
        self.add_lesson("2026-10-06-1", "ai-ml-01", status="passed", marked_at="2026-10-07T07:00:00Z",
                        title="What machine learning actually optimises")

    def test_creates_section_readme_in_the_networking_shape(self):
        res = fp.file_lesson("2026-10-06-1")
        self.assertEqual((res["filed"], res["section_created"], res["filed_to"]),
                         (True, True, "24-ai-ml-foundations/what-machine-learning-actually-optimises.md"))
        readme = self.read("24-ai-ml-foundations/README.md")
        lines = readme.splitlines()
        self.assertEqual(lines[0], "# AI / ML Foundations")
        self.assertTrue(lines[2].startswith("Machine-learning foundations"))
        self.assertEqual(re.findall(r"^## (.+)$", readme, re.M),
                         ["Beginner", "Intermediate", "Advanced", "Key Interview Questions by Level"])
        self.assertEqual(readme.count("| # | Topic | File | Interview Focus |\n|---|-------|------|-----------------|"), 3)
        for level in ("Beginner", "Intermediate", "Advanced"):
            self.assertRegex(readme, rf"\*\*{level}\*\*: ")
        self.assertTrue(readme.endswith("\n") and not readme.endswith("\n\n"))

    def test_first_row_lands_in_the_beginner_table(self):
        fp.file_lesson("2026-10-06-1")
        readme = self.read("24-ai-ml-foundations/README.md")
        f = "what-machine-learning-actually-optimises.md"
        self.assertEqual(table_rows(readme, "Beginner"),
                         [f"| 1 | What machine learning actually optimises | [{f}]({f}) | "
                          "ai-ml point 1.1, ai-ml point 1.2, ai-ml point 1.3 |"])
        self.assertEqual(table_rows(readme, "Intermediate") + table_rows(readme, "Advanced"), [])

    def test_filed_copy_has_header_block_and_no_front_matter_or_next_section(self):
        fp.file_lesson("2026-10-06-1")
        text = self.read("24-ai-ml-foundations/what-machine-learning-actually-optimises.md")
        lines = text.splitlines()
        self.assertEqual(lines[0], "# What machine learning actually optimises")
        self.assertEqual(lines[2], "> Source: IT Iaido lesson 2026-10-06-1 · AI / ML foundations · Beginner · "
                                   "passed on 2026-10-07")
        self.assertFalse(text.startswith("---"))
        self.assertNotIn("status: passed", text)
        self.assertNotIn("Next on this track", text)
        self.assertNotIn("Gradient descent by hand", text)
        for kept in ("## Why this matters", "## Self-check", "## Sources", "```mermaid", "<details>"):
            self.assertIn(kept, text)

    def test_root_readme_gets_a_new_block_in_its_own_group_before_domain_specific(self):
        fp.file_lesson("2026-10-06-1")
        root = self.read("README.md")
        block = ("## AI & Machine Learning\n\n"
                 "### [24 — AI / ML Foundations](24-ai-ml-foundations/)\n| Level | Topics |\n|-------|--------|\n"
                 "| B | [What machine learning actually optimises]"
                 "(24-ai-ml-foundations/what-machine-learning-actually-optimises.md) |\n")
        self.assertIn(block, root)
        # the new group sits between the existing groups and Domain-Specific; nothing else moved
        self.assertLess(root.index("## AI & Machine Learning"), root.index("## Domain-Specific"))
        self.assertGreater(root.index("## AI & Machine Learning"), root.index("### [10 — Networking]"))
        self.assertTrue(root.startswith(support.ROOT_README.split("## Domain-Specific")[0].rstrip("-\n")),
                        "earlier content untouched")
        self.assertIn("## Domain-Specific\n\n### [16 — AdTech]", root)
        self.assertIn("| A | [High-Scale Bidding Engine](16-adtech/bidding.md) |", root)

    def test_front_matter_filed_to_and_log(self):
        fp.file_lesson("2026-10-06-1", by="chat")
        fm = self.lesson_fm("2026-10-06-1")
        self.assertEqual((fm["filed_to"], fm["status"]),
                         ("24-ai-ml-foundations/what-machine-learning-actually-optimises.md", "passed"))
        last = self.log_events()[-1]
        self.assertEqual((last["event"], last["lesson"], last["by"]), ("filed", "2026-10-06-1", "chat"))

    def test_idempotent(self):
        fp.file_lesson("2026-10-06-1")
        snapshot = {p: self.read(p) for p in ("README.md", "24-ai-ml-foundations/README.md")}
        events = len(self.log_events())
        res = fp.file_lesson("2026-10-06-1")
        self.assertFalse(res["filed"])
        self.assertEqual(res["reason"], "already filed")
        self.assertEqual({p: self.read(p) for p in snapshot}, snapshot)
        self.assertEqual(len(self.log_events()), events)

    def test_refiling_after_the_kb_file_was_deleted_does_not_duplicate_rows(self):
        fp.file_lesson("2026-10-06-1")
        (self.root / "24-ai-ml-foundations/what-machine-learning-actually-optimises.md").unlink()
        fp.file_lesson("2026-10-06-1")
        readme = self.read("24-ai-ml-foundations/README.md")
        self.assertEqual(readme.count("what-machine-learning-actually-optimises.md]("), 1)
        self.assertEqual(self.read("README.md").count("what-machine-learning-actually-optimises.md)"), 1)

    def test_only_passed_lessons_are_filed(self):
        for i, status in enumerate(("sent", "review", "skipped"), start=1):
            self.add_lesson(f"2026-10-0{i}-1", "ai-ml-02", status=status, title=f"T {status}", level="I")
            with self.assertRaises(common.DojoError) as cm:
                fp.file_lesson(f"2026-10-0{i}-1")
            self.assertIn(f"status '{status}': only passed lessons are filed", str(cm.exception))
        self.assertEqual(sorted(p.name for p in (self.root / "24-ai-ml-foundations").glob("*")) if self.exists("24-ai-ml-foundations") else [], [])
        self.assertNotIn("24-ai-ml-foundations", self.read("README.md"))


class SectionGrowthTests(RepoTestCase):
    def test_number_continues_across_level_tables_and_root_row_is_extended(self):
        self.add_lesson("2026-10-06-1", "ai-ml-01", status="passed", title="First B")
        self.add_lesson("2026-10-07-1", "ai-ml-02", status="passed", level="I", title="Second I")
        self.add_lesson("2026-10-08-1", "ai-ml-03", status="passed", level="A", title="Third A")
        self.add_lesson("2026-10-09-1", "ai-ml-01", status="passed", title="Fourth B")
        for lid in ("2026-10-06-1", "2026-10-07-1", "2026-10-08-1", "2026-10-09-1"):
            fp.file_lesson(lid)
        readme = self.read("24-ai-ml-foundations/README.md")
        self.assertEqual([r.split("|")[1].strip() for r in table_rows(readme, "Beginner")], ["1", "4"])
        self.assertEqual([r.split("|")[1].strip() for r in table_rows(readme, "Intermediate")], ["2"])
        self.assertEqual([r.split("|")[1].strip() for r in table_rows(readme, "Advanced")], ["3"])
        root = self.read("README.md")
        self.assertIn("| B | [First B](24-ai-ml-foundations/first-b.md), [Fourth B](24-ai-ml-foundations/fourth-b.md) |", root)
        self.assertIn("\n| I | [Second I](24-ai-ml-foundations/second-i.md) |\n| A | [Third A](24-ai-ml-foundations/third-a.md) |", root)
        self.assertEqual(root.count("### [24 — AI / ML Foundations]"), 1)

    def test_existing_section_gets_row_numbered_after_the_highest_and_missing_root_row_is_inserted(self):
        self.add_lesson("2026-10-06-1", "networking-03", track="networking", status="passed", level="A",
                        title="TLS 1.3 handshake", files_to="10-networking")
        fp.file_lesson("2026-10-06-1")
        readme = self.read("10-networking/README.md")
        self.assertEqual(table_rows(readme, "Advanced")[-1].split("|")[1].strip(), "5")
        self.assertIn("| 5 | TLS 1.3 handshake | [tls-1-3-handshake.md](tls-1-3-handshake.md) | ", readme)
        self.assertEqual(readme.count("## Advanced"), 1)
        self.assertTrue(readme.index("tls-1-3-handshake.md") < readme.index("## Key Interview Questions"))
        root = self.read("README.md")
        # networking block had B and I rows only: the A row is added right below the I row
        self.assertIn("| I | [DNS & DHCP](10-networking/Networking-DNS-DHCP.md) |\n"
                      "| A | [TLS 1.3 handshake](10-networking/tls-1-3-handshake.md) |\n", root)
        self.assertNotIn("### [24", root)

    def test_missing_b_row_is_inserted_before_the_i_row(self):
        self.write("16-adtech/README.md", support.NETWORKING_README.replace("# Networking", "# AdTech"))
        self.add_lesson("2026-10-06-1", "ai-ml-01", status="passed", title="Ad basics", files_to="16-adtech")
        fp.file_lesson("2026-10-06-1")
        root = self.read("README.md")
        self.assertIn("### [16 — AdTech](16-adtech/)\n| Level | Topics |\n|-------|--------|\n"
                      "| B | [Ad basics](16-adtech/ad-basics.md) |\n| I | [OpenRTB Protocol]", root)

    def test_new_sections_25_and_26_get_their_titles_and_stay_in_numeric_order(self):
        self.add_lesson("2026-10-06-1", "ai-ml-01", status="passed", title="Rust ownership", files_to="26-rust")
        self.add_lesson("2026-10-07-1", "ai-ml-02", status="passed", title="Layers and boundaries",
                        files_to="25-software-architecture", level="I")
        self.add_lesson("2026-10-08-1", "ai-ml-03", status="passed", title="Loss functions", level="A")
        for lid in ("2026-10-06-1", "2026-10-07-1", "2026-10-08-1"):     # 26 first, then 25, then 24
            fp.file_lesson(lid)
        self.assertEqual(self.read("25-software-architecture/README.md").splitlines()[0],
                         "# Software Architecture & Design")
        self.assertEqual(self.read("26-rust/README.md").splitlines()[0], "# Rust")
        root = self.read("README.md")
        order = [m.group(1) for m in re.finditer(r"^### \[(\d+) — ", root, re.M)]
        # 25 joins the existing "Infrastructure & Operations" group (after 10); 26 and 24 each create
        # their own group ("Core Language & Programming", "AI & Machine Learning") before Domain-Specific,
        # in the order they were filed; 16 stays last.
        self.assertEqual(order, ["10", "25", "26", "24", "16"])
        self.assertIn("### [25 — Software Architecture & Design](25-software-architecture/)", root)
        self.assertIn("### [26 — Rust](26-rust/)", root)
        infra = root[root.index("## Infrastructure & Operations"):root.index("## Core Language & Programming")]
        self.assertIn("### [25 —", infra)
        self.assertLess(root.index("## Core Language & Programming"), root.index("## AI & Machine Learning"))
        self.assertLess(root.index("## AI & Machine Learning"), root.index("## Domain-Specific"))

    def test_filename_collision_with_another_lesson_gets_the_id_suffix(self):
        self.add_lesson("2026-10-06-1", "ai-ml-01", status="passed", title="Same title")
        self.add_lesson("2026-10-07-1", "ai-ml-02", status="passed", title="Same title", level="I")
        fp.file_lesson("2026-10-06-1")
        res = fp.file_lesson("2026-10-07-1")
        self.assertEqual(res["filed_to"], "24-ai-ml-foundations/same-title-2026-10-07-1.md")
        self.assertTrue(self.exists("24-ai-ml-foundations/same-title.md"))

    def test_all_passed_unfiled(self):
        self.add_lesson("2026-10-06-1", "ai-ml-01", status="passed", title="One")
        self.add_lesson("2026-10-06-2", None, slot="fresh", status="passed", title="Two", domain="ai-ml", level="I")
        self.add_lesson("2026-10-07-1", "ai-ml-02", status="sent", title="Three", level="I")
        fp.file_lesson("2026-10-06-1")
        self.assertEqual(fp.unfiled_passed(), ["2026-10-06-2"])
        rc, out, err = self.run_main(fp.main, ["--all-passed-unfiled"])
        self.assertEqual(rc, 0, err)
        self.assertTrue(self.exists("24-ai-ml-foundations/two.md"))
        self.assertFalse(self.exists("24-ai-ml-foundations/three.md"))
        self.assertEqual(fp.unfiled_passed(), [])
        self.assertEqual(self.run_main(fp.main, ["--all-passed-unfiled"])[1].strip(), "[]")

    def test_works_end_to_end_with_mark(self):
        self.add_lesson("2026-10-06-1", "ai-ml-01", status="sent", title="Via mark")
        mark.mark("2026-10-06-1", "passed", at="2026-10-06T20:00:00Z")
        self.assertEqual(fp.unfiled_passed(), ["2026-10-06-1"])
        fp.file_lesson("2026-10-06-1")
        self.assertIn("passed on 2026-10-06", self.read("24-ai-ml-foundations/via-mark.md"))


class HelperTests(RepoTestCase):
    def test_interview_focus_from_key_points_is_trimmed(self):
        tracks = common.require_curriculum()
        focus = fp.interview_focus({"rung": "ai-ml-01"}, "", tracks)
        self.assertEqual(focus, "ai-ml point 1.1, ai-ml point 1.2, ai-ml point 1.3")
        data = common.load_yaml(self.root / "dojo/curriculum/ai-ml.yaml")
        data["rungs"][0]["key_points"] = ["A loss function turns 'wrong' into a single number we can minimise.",
                                          "Gradient descent follows the slope downhill.", "Third point"]
        common.save_yaml(self.root / "dojo/curriculum/ai-ml.yaml", data)
        focus = fp.interview_focus({"rung": "ai-ml-01"}, "", common.require_curriculum())
        self.assertEqual(focus, "A loss function turns 'wrong' into a single number we can minimise")
        self.assertLessEqual(len(focus), 90)

    def test_interview_focus_falls_back_to_first_sentence_of_why_this_matters(self):
        body = ("# T\n\n## Why this matters\n<!-- hint -->\nKV caches make **decoding** cheap enough to serve at "
                "scale because attention reuses earlier keys. More text here.\n\n## The idea\nx\n")
        focus = fp.interview_focus({"rung": None}, body, common.require_curriculum())
        self.assertTrue(focus.startswith("KV caches make decoding cheap"))
        self.assertLessEqual(len(focus), 82)
        self.assertTrue(focus.endswith("…"))

    def test_pipes_in_topic_are_escaped(self):
        text, n = fp.add_readme_row(fp.new_readme_text("X", "d"), "B", "A | B", "a-b.md", "x | y")
        self.assertIn("| 1 | A \\| B | [a-b.md](a-b.md) | x \\| y |", text)

    def test_readme_with_subtables_and_missing_level(self):
        readme = ("# DB\n\nd\n\n## Beginner\n\n| # | Topic | File | Interview Focus |\n|---|---|---|---|\n| 1 | a | [a.md](a.md) | x |\n\n"
                  "## Intermediate\n\n### One\n| # | Topic | File | Interview Focus |\n|---|---|---|---|\n| 2 | b | [b.md](b.md) | y |\n"
                  "### Two\n| # | Topic | File | Interview Focus |\n|---|---|---|---|\n| 3 | c | [c.md](c.md) | z |\n\n"
                  "## Key Interview Questions by Level\n\n**Beginner**: q\n")
        text, n = fp.add_readme_row(readme, "I", "New", "new.md", "f")
        self.assertEqual(n, 4)
        self.assertLess(text.index("| 3 | c |"), text.index("| 4 | New |"))
        self.assertLess(text.index("| 4 | New |"), text.index("## Key Interview"))
        text, n = fp.add_readme_row(text, "A", "Adv", "adv.md", "f")           # no Advanced heading yet
        self.assertEqual(n, 5)
        self.assertRegex(text, r"## Advanced\n\n\| # \| Topic \| File \| Interview Focus \|\n\|---\|-------\|------\|-----------------\|\n\| 5 \| Adv \|")
        self.assertLess(text.index("## Advanced"), text.index("## Key Interview"))
        self.assertGreater(text.index("## Advanced"), text.index("| 4 | New |"))

    def test_unknown_section_gets_a_title_from_its_folder_or_track(self):
        tracks = common.require_curriculum()
        self.assertEqual(fp.section_info("10-networking", tracks)[0], "Networking")
        title, desc = fp.section_info("30-data-viz", tracks)
        self.assertEqual((title, desc), ("Data Viz", fp.DEFAULT_DESCRIPTION))


if __name__ == "__main__":
    unittest.main()
