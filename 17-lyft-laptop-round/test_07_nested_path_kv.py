"""Tests for 07-nested-path-kv.py.

Run: python3 -m unittest test_07_nested_path_kv.py
"""

import importlib.util
import os
import sys
import unittest

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_MODULE_PATH = os.path.join(_THIS_DIR, "07-nested-path-kv.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("nested_path_kv", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


sol = _load_module()


class TestSetGetDelete(unittest.TestCase):
    def setUp(self):
        self.store = sol.NestedPathKV()

    def test_set_and_get_single_segment(self):
        self.store.set("a", 1)
        self.assertEqual(self.store.get("a"), 1)

    def test_intermediates_are_auto_created(self):
        self.store.set("a.b.c", 42)
        self.assertEqual(self.store.get("a.b.c"), 42)
        # 'a' and 'a.b' exist as branches but were never set as leaves
        self.assertIsNone(self.store.get("a"))
        self.assertIsNone(self.store.get("a.b"))

    def test_get_on_missing_path_returns_none(self):
        self.assertIsNone(self.store.get("does.not.exist"))

    def test_overwrite_existing_leaf_updates_value(self):
        self.store.set("a.b", 1)
        self.store.set("a.b", 2)
        self.assertEqual(self.store.get("a.b"), 2)

    def test_delete_removes_leaf(self):
        self.store.set("a.b", 1)
        self.store.delete("a.b")
        self.assertIsNone(self.store.get("a.b"))

    def test_delete_nonexistent_path_is_a_no_op(self):
        self.store.delete("nope.nope")  # must not raise
        self.assertIsNone(self.store.get("nope.nope"))

    def test_delete_prunes_now_empty_ancestor_branches(self):
        self.store.set("a.b.c", 1)
        self.store.delete("a.b.c")
        self.assertEqual(self.store.children(""), [])  # 'a' pruned away entirely

    def test_delete_does_not_prune_a_branch_that_still_has_other_children(self):
        self.store.set("a.b.c", 1)
        self.store.set("a.b.d", 2)
        self.store.delete("a.b.c")
        self.assertEqual(self.store.children("a.b"), ["d"])
        self.assertEqual(self.store.get("a.b.d"), 2)

    def test_empty_path_raises(self):
        with self.assertRaises(ValueError):
            self.store.set("", 1)
        with self.assertRaises(ValueError):
            self.store.get("")


class TestChildren(unittest.TestCase):
    def setUp(self):
        self.store = sol.NestedPathKV()
        self.store.set("b.x", 1)
        self.store.set("a.y", 2)
        self.store.set("a.z", 3)

    def test_children_at_root_sorted(self):
        self.assertEqual(self.store.children(""), ["a", "b"])

    def test_children_default_argument_is_root(self):
        self.assertEqual(self.store.children(), ["a", "b"])

    def test_children_under_a_nested_prefix(self):
        self.assertEqual(self.store.children("a"), ["y", "z"])

    def test_children_of_nonexistent_prefix_is_empty(self):
        self.assertEqual(self.store.children("nope"), [])

    def test_children_of_a_leaf_path_is_empty(self):
        self.assertEqual(self.store.children("a.y"), [])


class TestFlatten(unittest.TestCase):
    def test_flatten_multiple_nested_leaves(self):
        store = sol.NestedPathKV()
        store.set("a.b.c", 1)
        store.set("a.b.d", 2)
        store.set("x", 9)
        self.assertEqual(store.flatten(), {"a.b.c": 1, "a.b.d": 2, "x": 9})

    def test_flatten_empty_store(self):
        store = sol.NestedPathKV()
        self.assertEqual(store.flatten(), {})

    def test_flatten_reflects_deletes(self):
        store = sol.NestedPathKV()
        store.set("a.b", 1)
        store.set("a.c", 2)
        store.delete("a.b")
        self.assertEqual(store.flatten(), {"a.c": 2})


class TestStrictTypeChecking(unittest.TestCase):
    def setUp(self):
        self.store = sol.NestedPathKV()

    def test_cannot_set_a_leaf_where_a_branch_already_exists(self):
        self.store.set("a.b", 1)  # 'a' is now a branch
        with self.assertRaises(TypeError):
            self.store.set("a", 5)  # would overwrite the branch with a leaf

    def test_cannot_descend_into_an_existing_leaf(self):
        self.store.set("a", 5)  # 'a' is now a leaf
        with self.assertRaises(TypeError):
            self.store.set("a.b", 1)  # would need 'a' to be a branch

    def test_type_error_does_not_corrupt_existing_state(self):
        self.store.set("a.b", 1)
        with self.assertRaises(TypeError):
            self.store.set("a", 5)
        self.assertEqual(self.store.get("a.b"), 1)  # unchanged after the failed set

    def test_deleting_then_setting_the_other_type_is_allowed(self):
        self.store.set("a.b", 1)
        self.store.delete("a.b")  # prunes 'a' away entirely
        self.store.set("a", 5)  # now legal: nothing left to conflict with
        self.assertEqual(self.store.get("a"), 5)


if __name__ == "__main__":
    unittest.main()
