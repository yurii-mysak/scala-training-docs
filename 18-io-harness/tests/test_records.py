"""
Unit tests for harness.records.

Run: python3 -m unittest tests.test_records   (from the 18-io-harness/ directory)
 or: python3 -m unittest discover tests
"""
import sys
import unittest
from pathlib import Path

# Make `harness` importable regardless of how/where this file is invoked from.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harness import records


class CoerceTests(unittest.TestCase):
    def test_int(self) -> None:
        self.assertEqual(records.coerce("42"), 42)
        self.assertIsInstance(records.coerce("42"), int)

    def test_negative_and_signed_int(self) -> None:
        self.assertEqual(records.coerce("-7"), -7)
        self.assertEqual(records.coerce("+7"), 7)

    def test_float(self) -> None:
        self.assertEqual(records.coerce("3.14"), 3.14)
        self.assertIsInstance(records.coerce("3.14"), float)

    def test_float_variants(self) -> None:
        self.assertEqual(records.coerce(".5"), 0.5)
        self.assertEqual(records.coerce("5."), 5.0)
        self.assertEqual(records.coerce("1e3"), 1000.0)

    def test_bool_true_variants(self) -> None:
        for text in ["true", "True", "TRUE", "yes", "y", "1"]:
            self.assertIs(records.coerce(text), True, text)

    def test_bool_false_variants(self) -> None:
        for text in ["false", "False", "no", "n", "0"]:
            self.assertIs(records.coerce(text), False, text)

    def test_empty_or_blank_string_is_none(self) -> None:
        self.assertIsNone(records.coerce(""))
        self.assertIsNone(records.coerce("   "))

    def test_plain_string_passthrough(self) -> None:
        self.assertEqual(records.coerce("hello"), "hello")

    def test_whitespace_padded_string_preserved_on_fallback(self) -> None:
        self.assertEqual(records.coerce("  hello  "), "  hello  ")

    def test_numeric_looking_but_not_quite(self) -> None:
        # Guards against Python's own permissive float()/int(): these must NOT
        # silently become numbers or special floats.
        self.assertEqual(records.coerce("inf"), "inf")
        self.assertEqual(records.coerce("nan"), "nan")
        self.assertEqual(records.coerce("Infinity"), "Infinity")
        self.assertEqual(records.coerce("1_000"), "1_000")
        self.assertEqual(records.coerce("12abc"), "12abc")
        self.assertEqual(records.coerce("3.14.15"), "3.14.15")

    def test_unicode_passthrough(self) -> None:
        self.assertEqual(records.coerce("café"), "café")

    def test_row(self) -> None:
        self.assertEqual(records.coerce_row(["1", "a", "", "2.5", "true"]), [1, "a", None, 2.5, True])

    def test_row_empty(self) -> None:
        self.assertEqual(records.coerce_row([]), [])


class CoerceAsTests(unittest.TestCase):
    def test_success(self) -> None:
        self.assertEqual(records.coerce_as("42", int), 42)
        self.assertEqual(records.coerce_as("3.5", float), 3.5)
        self.assertEqual(records.coerce_as("x", str), "x")

    def test_failure_raises_value_error_with_offending_value(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            records.coerce_as("abc", int)
        self.assertIn("abc", str(ctx.exception))

    def test_custom_converter(self) -> None:
        self.assertEqual(records.coerce_as("true", lambda v: v == "true"), True)


class SplitCsvLineTests(unittest.TestCase):
    def test_simple(self) -> None:
        self.assertEqual(records.split_csv_line("a,b,c"), ["a", "b", "c"])

    def test_quoted_field_with_embedded_delimiter(self) -> None:
        self.assertEqual(records.split_csv_line('a,"b,c",d'), ["a", "b,c", "d"])

    def test_escaped_quote_inside_quoted_field(self) -> None:
        self.assertEqual(records.split_csv_line('a,"say ""hi""",c'), ["a", 'say "hi"', "c"])

    def test_trailing_newline_stripped(self) -> None:
        self.assertEqual(records.split_csv_line("a,b,c\n"), ["a", "b", "c"])

    def test_trailing_crlf_stripped(self) -> None:
        self.assertEqual(records.split_csv_line("a,b,c\r\n"), ["a", "b", "c"])

    def test_empty_field(self) -> None:
        self.assertEqual(records.split_csv_line("a,,c"), ["a", "", "c"])

    def test_empty_line(self) -> None:
        self.assertEqual(records.split_csv_line(""), [])

    def test_single_field_no_delimiter(self) -> None:
        self.assertEqual(records.split_csv_line("onlyfield"), ["onlyfield"])

    def test_custom_delimiter(self) -> None:
        self.assertEqual(records.split_csv_line("a|b|c", delimiter="|"), ["a", "b", "c"])

    def test_unicode_field(self) -> None:
        self.assertEqual(records.split_csv_line("café,日本語"), ["café", "日本語"])

    def test_malformed_unbalanced_quote_does_not_raise(self) -> None:
        result = records.split_csv_line('a,"b,c')
        self.assertIsInstance(result, list)

    def test_malformed_stray_quote_mid_field_does_not_raise(self) -> None:
        result = records.split_csv_line('a,b"c,d')
        self.assertIsInstance(result, list)


class RecordFactoryTests(unittest.TestCase):
    def test_builds_typed_record(self) -> None:
        make_point = records.record_factory("Point", {"x": int, "y": int})
        p = make_point(["3", "4"])
        self.assertEqual((p.x, p.y), (3, 4))

    def test_field_order_matches_definition_order(self) -> None:
        make_row = records.record_factory("Row", {"name": str, "age": int})
        r = make_row(["alice", "30"])
        self.assertEqual(repr(r), "Row(name='alice', age=30)")

    def test_field_count_mismatch_raises(self) -> None:
        make_point = records.record_factory("Point", {"x": int, "y": int})
        with self.assertRaises(ValueError):
            make_point(["3"])
        with self.assertRaises(ValueError):
            make_point(["3", "4", "5"])

    def test_bad_field_value_raises_value_error(self) -> None:
        make_point = records.record_factory("Point", {"x": int, "y": int})
        with self.assertRaises(ValueError):
            make_point(["3", "not-a-number"])

    def test_mutable_by_default(self) -> None:
        make_point = records.record_factory("Point", {"x": int, "y": int})
        p = make_point(["3", "4"])
        p.x = 99
        self.assertEqual(p.x, 99)

    def test_frozen_option_prevents_mutation(self) -> None:
        make_point = records.record_factory("Point", {"x": int, "y": int}, frozen=True)
        p = make_point(["3", "4"])
        with self.assertRaises(AttributeError):
            p.x = 99  # type: ignore[misc]

    def test_mixed_converter_types(self) -> None:
        make_row = records.record_factory(
            "Row", {"name": str, "age": int, "active": lambda v: v == "true"}
        )
        r = make_row(["alice", "30", "true"])
        self.assertEqual((r.name, r.age, r.active), ("alice", 30, True))

    def test_using_coerce_as_a_converter(self) -> None:
        make_row = records.record_factory("Row", {"a": records.coerce, "b": records.coerce})
        r = make_row(["1", "hello"])
        self.assertEqual((r.a, r.b), (1, "hello"))


class EndToEndCsvToRecordTests(unittest.TestCase):
    """Exercises the three pieces of records.py together, the way solve() would."""

    def test_csv_line_to_typed_record(self) -> None:
        make_row = records.record_factory("Row", {"name": str, "age": int})
        fields = records.split_csv_line('"Doe, John",42')
        row = make_row(fields)
        self.assertEqual((row.name, row.age), ("Doe, John", 42))


if __name__ == "__main__":
    unittest.main()
