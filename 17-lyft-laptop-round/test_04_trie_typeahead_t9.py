"""Tests for 04-trie-typeahead-t9.py.

Run: python3 -m unittest test_04_trie_typeahead_t9.py
"""

import importlib.util
import os
import sys
import unittest

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_MODULE_PATH = os.path.join(_THIS_DIR, "04-trie-typeahead-t9.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("trie_typeahead_t9", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


sol = _load_module()


class TestTypeahead(unittest.TestCase):
    def setUp(self):
        self.trie = sol.Typeahead()

    def test_suggest_ranks_by_frequency_descending(self):
        self.trie.add_word("cat", 5)
        self.trie.add_word("car", 10)
        self.trie.add_word("cap", 1)
        self.assertEqual(self.trie.suggest("ca", 3), ["car", "cat", "cap"])

    def test_suggest_respects_k(self):
        self.trie.add_word("cat", 5)
        self.trie.add_word("car", 10)
        self.trie.add_word("cap", 1)
        self.assertEqual(self.trie.suggest("ca", 2), ["car", "cat"])

    def test_ties_broken_alphabetically(self):
        self.trie.add_word("bee", 3)
        self.trie.add_word("bat", 3)
        self.trie.add_word("bit", 3)
        self.assertEqual(self.trie.suggest("b", 3), ["bat", "bee", "bit"])

    def test_prefix_not_present_returns_empty(self):
        self.trie.add_word("dog", 1)
        self.assertEqual(self.trie.suggest("cat"), [])

    def test_exact_word_is_included_as_its_own_prefix(self):
        self.trie.add_word("cat", 1)
        self.trie.add_word("catalog", 1)
        self.assertEqual(self.trie.suggest("cat", 5), ["cat", "catalog"])

    def test_k_zero_returns_empty(self):
        self.trie.add_word("cat", 1)
        self.assertEqual(self.trie.suggest("cat", 0), [])

    def test_empty_prefix_returns_top_k_across_everything(self):
        self.trie.add_word("cat", 5)
        self.trie.add_word("dog", 10)
        self.assertEqual(self.trie.suggest("", 2), ["dog", "cat"])

    def test_repeated_add_word_accumulates_frequency(self):
        self.trie.add_word("cat", 2)
        self.trie.add_word("cat", 3)
        self.trie.add_word("dog", 4)
        self.assertEqual(self.trie.suggest("", 2), ["cat", "dog"])

    def test_empty_word_raises(self):
        with self.assertRaises(ValueError):
            self.trie.add_word("")


class TestWordToDigits(unittest.TestCase):
    def test_known_encoding(self):
        self.assertEqual(sol.word_to_digits("cab"), "222")
        self.assertEqual(sol.word_to_digits("abc"), "222")

    def test_case_insensitive(self):
        self.assertEqual(sol.word_to_digits("CAB"), sol.word_to_digits("cab"))

    def test_non_alphabetic_raises(self):
        with self.assertRaises(ValueError):
            sol.word_to_digits("ca-b")


class TestT9Typeahead(unittest.TestCase):
    def setUp(self):
        self.t9 = sol.T9Typeahead()
        self.t9.add_word("cab", 3)
        self.t9.add_word("abc", 5)
        self.t9.add_word("act", 2)
        self.t9.add_word("bat", 4)

    def test_colliding_words_both_returned_ranked_by_frequency(self):
        # "cab" and "abc" both encode to 222 -- that collision is real T9 behavior.
        self.assertEqual(self.t9.suggest("222"), ["abc", "cab"])

    def test_distinct_digit_sequence(self):
        self.assertEqual(self.t9.suggest("228"), ["bat", "act"])

    def test_unknown_digit_sequence_returns_empty(self):
        self.assertEqual(self.t9.suggest("999"), [])

    def test_invalid_digit_raises(self):
        with self.assertRaises(ValueError):
            self.t9.suggest("12")  # 1 has no letters on a standard keypad

    def test_k_limits_results(self):
        self.assertEqual(self.t9.suggest("222", k=1), ["abc"])

    def test_k_zero_returns_empty(self):
        self.assertEqual(self.t9.suggest("222", k=0), [])

    def test_suggest_including_longer_finds_deeper_words(self):
        t9 = sol.T9Typeahead()
        t9.add_word("hi", 1)     # 4-4
        t9.add_word("hint", 5)   # 4-4-6-8
        self.assertEqual(t9.suggest("44"), ["hi"])
        self.assertEqual(t9.suggest_including_longer("44"), ["hint", "hi"])

    def test_empty_digits_matches_root(self):
        # an empty digit string is a legitimate (if unusual) prefix of everything
        self.assertEqual(self.t9.suggest(""), [])  # no word has zero letters
        result = self.t9.suggest_including_longer("", k=10)
        self.assertEqual(sorted(result), sorted(["cab", "abc", "act", "bat"]))


if __name__ == "__main__":
    unittest.main()
