"""Tests for 06-file-log-csv-parsing.py.

Run: python3 -m unittest test_06_file_log_csv_parsing.py
"""

import importlib.util
import os
import sys
import tempfile
import unittest

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_MODULE_PATH = os.path.join(_THIS_DIR, "06-file-log-csv-parsing.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("file_log_csv_parsing", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


sol = _load_module()


class _TempFileMixin:
    def _write_temp(self, content: str) -> str:
        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        self.addCleanup(os.remove, path)
        return path


class TestKthNonEmptyLine(unittest.TestCase, _TempFileMixin):
    def test_basic_kth_line(self):
        path = self._write_temp("a\nb\nc\n")
        self.assertEqual(sol.kth_non_empty_line(path, 2), "b")

    def test_skips_blank_lines(self):
        path = self._write_temp("a\n\nb\n\n\nc\n")
        self.assertEqual(sol.kth_non_empty_line(path, 2), "b")
        self.assertEqual(sol.kth_non_empty_line(path, 3), "c")

    def test_skips_whitespace_only_lines(self):
        path = self._write_temp("a\n   \nb\n")
        self.assertEqual(sol.kth_non_empty_line(path, 2), "b")

    def test_fewer_than_k_lines_returns_none(self):
        path = self._write_temp("a\nb\n")
        self.assertIsNone(sol.kth_non_empty_line(path, 5))

    def test_no_trailing_newline_on_last_line(self):
        path = self._write_temp("a\nb\nc")  # no trailing \n
        self.assertEqual(sol.kth_non_empty_line(path, 3), "c")

    def test_file_of_only_blank_lines(self):
        path = self._write_temp("\n\n\n")
        self.assertIsNone(sol.kth_non_empty_line(path, 1))

    def test_k_zero_or_negative_raises(self):
        path = self._write_temp("a\n")
        with self.assertRaises(ValueError):
            sol.kth_non_empty_line(path, 0)
        with self.assertRaises(ValueError):
            sol.kth_non_empty_line(path, -1)

    def test_utf8_content(self):
        path = self._write_temp("héllo\nworld\nÜnïcode\n")
        self.assertEqual(sol.kth_non_empty_line(path, 3), "Ünïcode")


class TestSplitCsvLine(unittest.TestCase):
    def test_simple_line(self):
        self.assertEqual(sol.split_csv_line("a,b,c"), ["a", "b", "c"])

    def test_quoted_field_with_embedded_delimiter(self):
        self.assertEqual(sol.split_csv_line('a,"b,c",d'), ["a", "b,c", "d"])

    def test_escaped_quote_inside_quoted_field(self):
        self.assertEqual(sol.split_csv_line('"he said ""hi"""'), ['he said "hi"'])

    def test_custom_delimiter_pipe(self):
        self.assertEqual(sol.split_csv_line("a|b|c", delimiter="|"), ["a", "b", "c"])

    def test_custom_delimiter_tab(self):
        self.assertEqual(sol.split_csv_line("a\tb\tc", delimiter="\t"), ["a", "b", "c"])

    def test_empty_line_yields_one_empty_field(self):
        self.assertEqual(sol.split_csv_line(""), [""])

    def test_trailing_delimiter_yields_trailing_empty_field(self):
        self.assertEqual(sol.split_csv_line("a,b,"), ["a", "b", ""])

    def test_quoted_field_at_start_and_plain_after(self):
        self.assertEqual(sol.split_csv_line('"quoted",plain'), ["quoted", "plain"])

    def test_all_fields_quoted(self):
        self.assertEqual(sol.split_csv_line('"a","b","c"'), ["a", "b", "c"])


class TestPercentile(unittest.TestCase):
    def test_p50_and_p95_on_one_to_hundred(self):
        values = list(range(1, 101))  # 1..100, already sorted
        self.assertEqual(sol.percentile(values, 50), 50)
        self.assertEqual(sol.percentile(values, 95), 95)

    def test_single_element(self):
        self.assertEqual(sol.percentile([42], 50), 42)
        self.assertEqual(sol.percentile([42], 95), 42)

    def test_empty_sequence_raises(self):
        with self.assertRaises(ValueError):
            sol.percentile([], 50)

    def test_out_of_range_p_raises(self):
        with self.assertRaises(ValueError):
            sol.percentile([1, 2, 3], 150)
        with self.assertRaises(ValueError):
            sol.percentile([1, 2, 3], -1)


class TestAggregateLatencies(unittest.TestCase, _TempFileMixin):
    def test_basic_aggregation(self):
        path = self._write_temp("\n".join(str(x) for x in range(1, 101)) + "\n")
        result = sol.aggregate_latencies(path)
        self.assertEqual(result["count"], 100)
        self.assertEqual(result["p50"], 50)
        self.assertEqual(result["p95"], 95)

    def test_timestamp_prefixed_rows_use_last_field(self):
        path = self._write_temp("t1,100\nt2,200\nt3,300\n")
        result = sol.aggregate_latencies(path)
        self.assertEqual(result["count"], 3)

    def test_blank_and_malformed_lines_are_skipped_not_fatal(self):
        path = self._write_temp("100\n\nbad-data\n200\n")
        result = sol.aggregate_latencies(path)
        self.assertEqual(result["count"], 2)

    def test_all_malformed_returns_none_percentiles_not_a_crash(self):
        path = self._write_temp("nope\nnot-a-number\n")
        result = sol.aggregate_latencies(path)
        self.assertEqual(result, {"count": 0, "p50": None, "p95": None})

    def test_empty_file(self):
        path = self._write_temp("")
        result = sol.aggregate_latencies(path)
        self.assertEqual(result, {"count": 0, "p50": None, "p95": None})


if __name__ == "__main__":
    unittest.main()
