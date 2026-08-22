"""Tests for 03-inmemory-kv-transactions.py.

Run: python3 -m unittest test_03_inmemory_kv_transactions.py
"""

import importlib.util
import os
import sys
import unittest

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_MODULE_PATH = os.path.join(_THIS_DIR, "03-inmemory-kv-transactions.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("inmemory_kv_transactions", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


sol = _load_module()


class TestPart1PlainKV(unittest.TestCase):
    """The part candidates reportedly stopped at, believing they were done."""

    def setUp(self):
        self.store = sol.TransactionalKVStore()

    def test_set_then_get(self):
        self.store.set("a", "1")
        self.assertEqual(self.store.get("a"), "1")

    def test_get_missing_key_returns_none(self):
        self.assertIsNone(self.store.get("missing"))

    def test_set_overwrites(self):
        self.store.set("a", "1")
        self.store.set("a", "2")
        self.assertEqual(self.store.get("a"), "2")

    def test_delete_removes_key(self):
        self.store.set("a", "1")
        self.store.delete("a")
        self.assertIsNone(self.store.get("a"))

    def test_delete_missing_key_is_a_no_op(self):
        self.store.delete("never-set")  # must not raise
        self.assertIsNone(self.store.get("never-set"))

    def test_not_in_transaction_by_default(self):
        self.assertFalse(self.store.in_transaction)
        self.assertEqual(self.store.transaction_depth, 0)


class TestPart2Transactions(unittest.TestCase):
    """Part 2 -- explicitly in scope, not a stretch goal. See 00-protocol.md."""

    def setUp(self):
        self.store = sol.TransactionalKVStore()

    def test_rollback_discards_uncommitted_write(self):
        self.store.set("a", "10")
        self.store.begin()
        self.store.set("a", "20")
        self.store.rollback()
        self.assertEqual(self.store.get("a"), "10")

    def test_commit_persists_write(self):
        self.store.begin()
        self.store.set("a", "1")
        self.store.commit()
        self.assertEqual(self.store.get("a"), "1")
        self.assertFalse(self.store.in_transaction)

    def test_reads_inside_a_transaction_see_uncommitted_writes(self):
        self.store.set("a", "1")
        self.store.begin()
        self.store.set("a", "2")
        self.assertEqual(self.store.get("a"), "2")  # visible before commit

    def test_delete_inside_transaction_then_rollback_restores_value(self):
        self.store.set("a", "1")
        self.store.begin()
        self.store.delete("a")
        self.assertIsNone(self.store.get("a"))
        self.store.rollback()
        self.assertEqual(self.store.get("a"), "1")

    def test_delete_inside_transaction_then_commit_persists_deletion(self):
        self.store.set("a", "1")
        self.store.begin()
        self.store.delete("a")
        self.store.commit()
        self.assertIsNone(self.store.get("a"))

    def test_nested_commit_commit_persists_to_committed_store(self):
        self.store.begin()
        self.store.set("a", "1")
        self.store.begin()
        self.store.set("a", "2")
        self.store.commit()  # merges into the outer (still-open) frame
        self.assertEqual(self.store.get("a"), "2")  # visible, but not committed yet
        self.assertTrue(self.store.in_transaction)
        self.store.commit()  # outer commit reaches the committed store
        self.assertFalse(self.store.in_transaction)
        self.assertEqual(self.store.get("a"), "2")

    def test_nested_rollback_rollback_discards_everything(self):
        self.store.set("a", "1")
        self.store.begin()
        self.store.set("a", "2")
        self.store.begin()
        self.store.set("a", "3")
        self.store.rollback()
        self.store.rollback()
        self.assertEqual(self.store.get("a"), "1")

    def test_inner_commit_then_outer_rollback_undoes_the_inner_commit_too(self):
        # This is the classic nested-transaction trap: a COMMIT at a nested level
        # is only durable if every enclosing transaction also commits.
        self.store.set("a", "1")
        self.store.begin()
        self.store.begin()
        self.store.set("a", "99")
        self.store.commit()   # merges "99" into the still-open outer frame
        self.store.rollback()  # discards the outer frame entirely, "99" included
        self.assertEqual(self.store.get("a"), "1")

    def test_get_finds_a_shadowed_delete_in_an_outer_frame(self):
        # outer frame deletes 'a'; inner frame never mentions 'a' at all -- get()
        # must walk past the inner frame to find the outer frame's deletion,
        # not fall all the way through to the (still populated) committed store.
        self.store.set("a", "1")
        self.store.begin()
        self.store.delete("a")
        self.store.begin()
        self.assertIsNone(self.store.get("a"))

    def test_commit_with_no_open_transaction_raises(self):
        with self.assertRaises(RuntimeError):
            self.store.commit()

    def test_rollback_with_no_open_transaction_raises(self):
        with self.assertRaises(RuntimeError):
            self.store.rollback()

    def test_transaction_depth_tracks_nesting(self):
        self.store.begin()
        self.store.begin()
        self.store.begin()
        self.assertEqual(self.store.transaction_depth, 3)
        self.store.commit()
        self.assertEqual(self.store.transaction_depth, 2)


class TestRunCommands(unittest.TestCase):
    """End-to-end over the command-string format main() reads."""

    def test_transcript_matches_documented_conventions(self):
        script = [
            "SET a 10",
            "GET a",
            "BEGIN",
            "SET a 20",
            "GET a",
            "ROLLBACK",
            "GET a",
            "BEGIN",
            "SET b 5",
            "COMMIT",
            "GET b",
            "DELETE a",
            "GET a",
            "COMMIT",
            "ROLLBACK",
        ]
        output = sol.run_commands(script)
        self.assertEqual(
            output,
            [
                "10", "20", "10", "5", "NULL",
                "COMMIT with no active transaction",
                "ROLLBACK with no active transaction",
            ],
        )

    def test_blank_lines_are_ignored(self):
        output = sol.run_commands(["SET a 1", "", "   ", "GET a"])
        self.assertEqual(output, ["1"])

    def test_unrecognized_command_reported_without_crashing(self):
        output = sol.run_commands(["NOPE", "GET a"])
        self.assertEqual(output[0].startswith("ERROR"), True)
        self.assertEqual(output[1], "NULL")

    def test_value_with_spaces_is_preserved(self):
        output = sol.run_commands(["SET greeting hello world", "GET greeting"])
        self.assertEqual(output, ["hello world"])


if __name__ == "__main__":
    unittest.main()
