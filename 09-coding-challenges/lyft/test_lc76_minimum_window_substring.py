import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lc76_minimum_window_substring import min_window


class TestMinWindow(unittest.TestCase):
    def test_example_1(self) -> None:
        self.assertEqual(min_window("ADOBECODEBANC", "ABC"), "BANC")

    def test_single_char_match(self) -> None:
        self.assertEqual(min_window("a", "a"), "a")

    def test_no_valid_window(self) -> None:
        self.assertEqual(min_window("a", "aa"), "")

    def test_t_longer_than_s(self) -> None:
        self.assertEqual(min_window("ab", "abc"), "")

    def test_duplicates_in_t(self) -> None:
        self.assertEqual(min_window("aa", "aa"), "aa")

    def test_whole_string_is_answer(self) -> None:
        self.assertEqual(min_window("abc", "cba"), "abc")

    def test_empty_t_returns_empty(self) -> None:
        self.assertEqual(min_window("abc", ""), "")

    def test_empty_s_returns_empty(self) -> None:
        self.assertEqual(min_window("", "a"), "")

    def test_window_must_cover_full_multiplicity(self) -> None:
        # Only the trailing run has three a's; an early pair is not enough.
        self.assertEqual(min_window("aaflslflsldkalskaaa", "aaa"), "aaa")

    def test_extra_characters_outside_window_are_ignored(self) -> None:
        self.assertEqual(min_window("xxxxabcxxxx", "abc"), "abc")


if __name__ == "__main__":
    unittest.main()
