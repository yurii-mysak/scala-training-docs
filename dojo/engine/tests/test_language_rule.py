"""SPEC §4 Language rule: check_lesson.py rejects non-Scala/Rust code; run_lab.py finds runnable programs."""
from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from dojo.engine.tests import support  # noqa: F401  (puts the engine on sys.path)
import check_lesson
import run_lab

HEAD = "---\nid: 2026-10-14-1\ndate: 2026-10-14\nslot: core\ntrack: ai-ml\nlevel: B\ntitle: t\nest_min: 20\n---\n# t\n\n## Lab\n"


def lang_errors(body: str) -> list[str]:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "2026-10-14-1-t.md"
        p.write_text(HEAD + textwrap.dedent(body))
        return [e for e in check_lesson.check(p)["errors"] if "Language rule" in e]


class CheckerTests(unittest.TestCase):
    def test_python_block_is_rejected(self):
        self.assertTrue(lang_errors("```python\nprint(1)\n```\n"))

    def test_untagged_python_is_rejected(self):
        self.assertTrue(lang_errors("```\nimport numpy as np\nprint(np.ones(2))\n```\n"))
        self.assertEqual(lang_errors("```\nline A:  MAE = 5.0\n```\n"), [])

    def test_shell_calling_python_is_rejected(self):
        self.assertTrue(lang_errors("```bash\npython3 lab.py\n```\n"))

    def test_tool_shell_and_sql_are_allowed(self):
        self.assertEqual(lang_errors("```bash\ndig +trace example.com\nscala Lab.scala\n```\n```sql\nSELECT 1;\n```\n"), [])

    def test_scala_main_needs_file_marker(self):
        self.assertTrue(lang_errors("```scala\n@main def lab(): Unit = println(1)\n```\n"))
        self.assertEqual(lang_errors("```scala\n// file: Lab.scala\n@main def lab(): Unit = println(1)\n```\n"), [])

    def test_rust_fragment_without_main_is_fine(self):
        self.assertEqual(lang_errors("```rust\nlet x = 1;\n```\n"), [])

    def test_run_local_needs_label(self):
        code = "```rust\n// file: main.rs\n// run: local\nfn main() {}\n```\n"
        self.assertTrue(lang_errors(code))
        self.assertEqual(lang_errors(code + "\nExpected output — run locally:\n"), [])


class RunnerParsingTests(unittest.TestCase):
    def test_programs_are_found_with_deps_and_local_flag(self):
        body = textwrap.dedent("""\
            ```scala
            // file: Lab.scala
            @main def lab(): Unit = println(1)
            ```
            ```rust
            // file: main.rs
            // deps: ndarray@0.16, candle-core@0.8+metal
            // run: local
            fn main() {}
            ```
            ```scala
            val fragment = 1
            ```
            """)
        progs = run_lab.programs(body)
        self.assertEqual([(p["lang"], p["file"], p["local"]) for p in progs],
                         [("scala", "Lab.scala", False), ("rust", "main.rs", True)])
        self.assertEqual(progs[1]["deps"], ["ndarray@0.16", "candle-core@0.8+metal"])


if __name__ == "__main__":
    unittest.main()


class VisualAndExampleRuleTests(unittest.TestCase):
    def errs(self, idea: str, extra_files: dict | None = None) -> list[str]:
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "assets").mkdir()
            for name, content in (extra_files or {}).items():
                (Path(d) / "assets" / name).write_text(content)
            p = Path(d) / "2026-10-14-1-t.md"
            p.write_text(HEAD.replace("## Lab\n", "") + "## The idea\n" + textwrap.dedent(idea))
            return [e for e in check_lesson.check(p)["errors"] if "Visual rule" in e or "Show-by-example" in e]

    def test_bare_lesson_fails_both_rules(self):
        e = self.errs("Words only.\n```mermaid\nflowchart LR\nA-->B\n```\n")
        self.assertTrue(any("Visual rule" in x for x in e))
        self.assertTrue(any("Show-by-example" in x for x in e))

    def test_complete_lesson_passes(self):
        pair = "```scala\nprintln(1)\n```\n```text\n1\n```\n"
        idea = ("```mermaid\nflowchart LR\nA-->B\n```\n*Figure 0: a diagram.*\n\n" + pair + pair +
                "![c](assets/2026-10-14-1-chart-1.png)\n\n*Figure 1: c. Generated from the lab output.*\n\n"
                "![f](assets/2026-10-14-1-fig-1.png)\n\n*Figure 2: f. Source: X (MIT).*\n")
        self.assertEqual(self.errs(idea, {"2026-10-14-1-chart-1.json": "{}"}), [])

    def test_uncaptioned_image_and_missing_spec_fail(self):
        e = self.errs("![c](assets/2026-10-14-1-chart-1.png)\nno caption\n")
        self.assertTrue(any("caption" in x for x in e))
        self.assertTrue(any("JSON spec" in x for x in e))
