"""Tests for 02-versioned-kv-store.py.

Run: python3 -m unittest test_02_versioned_kv_store.py
"""

import importlib.util
import os
import sys
import unittest

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_MODULE_PATH = os.path.join(_THIS_DIR, "02-versioned-kv-store.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("versioned_kv_store", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


sol = _load_module()


class TestVersionedKVStore(unittest.TestCase):
    def setUp(self):
        self.store = sol.VersionedKVStore()

    def test_set_returns_incrementing_version_per_key(self):
        self.assertEqual(self.store.set("a", "x"), 1)
        self.assertEqual(self.store.set("a", "y"), 2)
        self.assertEqual(self.store.set("b", "z"), 1)  # independent per key

    def test_get_exact_version(self):
        self.store.set("a", "v1")
        self.store.set("a", "v2")
        self.store.set("a", "v3")
        self.assertEqual(self.store.get("a", 2), "v2")

    def test_get_falls_back_to_latest_smaller_version(self):
        self.store.set("a", "v1")
        self.store.set("a", "v2")
        # version 5 was never set -- should fall back to the latest version <= 5
        self.assertEqual(self.store.get("a", 5), "v2")

    def test_get_before_first_version_returns_none(self):
        self.store.set("a", "v1")
        self.assertIsNone(self.store.get("a", 0))

    def test_get_unknown_key_returns_none(self):
        self.assertIsNone(self.store.get("missing", 1))

    def test_get_negative_version_returns_none(self):
        self.store.set("a", "v1")
        self.assertIsNone(self.store.get("a", -1))

    def test_multiple_keys_are_independent(self):
        self.store.set("a", "a1")
        self.store.set("b", "b1")
        self.store.set("a", "a2")
        self.assertEqual(self.store.get("a", 1), "a1")
        self.assertEqual(self.store.get("a", 2), "a2")
        self.assertEqual(self.store.get("b", 1), "b1")

    def test_single_set_then_get(self):
        self.store.set("only", "value")
        self.assertEqual(self.store.get("only", 1), "value")

    def test_latest_version_helper(self):
        self.store.set("a", "v1")
        self.store.set("a", "v2")
        self.assertEqual(self.store.latest_version("a"), 2)
        self.assertIsNone(self.store.latest_version("missing"))

    def test_values_that_are_not_orderable_do_not_break_the_bisect(self):
        # Regression guard: values are arbitrary objects (dicts here); the
        # predecessor search must never compare *values*, only version numbers.
        self.store.set("a", {"nested": 1})
        self.store.set("a", {"nested": 2})
        self.assertEqual(self.store.get("a", 10), {"nested": 2})


class TestVersionedKVStoreDictBacked(unittest.TestCase):
    """Same contract, alternate implementation -- see the read/write trade-off
    discussion in the accompanying .md."""

    def setUp(self):
        self.store = sol.VersionedKVStoreDictBacked()

    def test_exact_hit_uses_the_fast_path(self):
        self.store.set("a", "v1")
        self.store.set("a", "v2")
        self.assertEqual(self.store.get("a", 1), "v1")
        self.assertEqual(self.store.get("a", 2), "v2")

    def test_predecessor_fallback_matches_the_primary_implementation(self):
        self.store.set("a", "v1")
        self.store.set("a", "v2")
        self.assertEqual(self.store.get("a", 99), "v2")
        self.assertIsNone(self.store.get("a", 0))

    def test_unknown_key(self):
        self.assertIsNone(self.store.get("missing", 1))


class TestMainCommandFormat(unittest.TestCase):
    """End-to-end check of the stdin command format documented in main()."""

    def test_end_to_end_via_module_functions(self):
        store = sol.VersionedKVStore()
        store.set("a", "1")
        store.set("a", "2")
        store.set("a", "3")
        self.assertEqual(store.get("a", 2), "2")
        self.assertEqual(store.get("a", 99), "3")
        self.assertIsNone(store.get("b", 1))


if __name__ == "__main__":
    unittest.main()
