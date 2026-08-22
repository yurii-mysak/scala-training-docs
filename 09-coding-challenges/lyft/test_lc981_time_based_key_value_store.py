import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lc981_time_based_key_value_store import TimeMap


class TestTimeMap(unittest.TestCase):
    def test_leetcode_example(self) -> None:
        tm = TimeMap()
        tm.set("foo", "bar", 1)
        self.assertEqual(tm.get("foo", 1), "bar")
        self.assertEqual(tm.get("foo", 3), "bar")
        tm.set("foo", "bar2", 4)
        self.assertEqual(tm.get("foo", 4), "bar2")
        self.assertEqual(tm.get("foo", 5), "bar2")

    def test_query_before_any_set_returns_empty(self) -> None:
        tm = TimeMap()
        tm.set("foo", "bar", 5)
        self.assertEqual(tm.get("foo", 4), "")
        self.assertEqual(tm.get("foo", 0), "")

    def test_unknown_key_returns_empty(self) -> None:
        tm = TimeMap()
        tm.set("foo", "bar", 1)
        self.assertEqual(tm.get("baz", 1), "")

    def test_exact_timestamp_match(self) -> None:
        tm = TimeMap()
        tm.set("k", "v1", 1)
        tm.set("k", "v2", 2)
        tm.set("k", "v3", 3)
        self.assertEqual(tm.get("k", 2), "v2")

    def test_floor_lookup_between_writes(self) -> None:
        tm = TimeMap()
        tm.set("k", "v1", 1)
        tm.set("k", "v2", 10)
        tm.set("k", "v3", 100)
        self.assertEqual(tm.get("k", 5), "v1")
        self.assertEqual(tm.get("k", 50), "v2")
        self.assertEqual(tm.get("k", 1000), "v3")

    def test_multiple_keys_are_independent(self) -> None:
        tm = TimeMap()
        tm.set("a", "a1", 1)
        tm.set("b", "b1", 1)
        tm.set("a", "a2", 2)
        self.assertEqual(tm.get("a", 2), "a2")
        self.assertEqual(tm.get("b", 2), "b1")

    def test_out_of_order_set_still_resolves_correctly(self) -> None:
        # Defensive case: the problem guarantees strictly increasing
        # timestamps per key, but the implementation should not silently
        # corrupt the floor search if that guarantee is ever violated.
        tm = TimeMap()
        tm.set("k", "late", 10)
        tm.set("k", "early", 2)
        self.assertEqual(tm.get("k", 5), "early")
        self.assertEqual(tm.get("k", 20), "late")


if __name__ == "__main__":
    unittest.main()
