import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lc716_max_stack import MaxStack, MaxStackSimple


class _MaxStackContractMixin:
    """Both implementations must satisfy the same contract, so the test
    bodies live once here and each concrete TestCase below only supplies
    which class to instantiate.
    """

    cls = None  # set by subclasses

    def test_leetcode_example(self) -> None:
        stk = self.cls()
        stk.push(5)
        stk.push(1)
        stk.push(5)
        self.assertEqual(stk.top(), 5)
        self.assertEqual(stk.popMax(), 5)
        self.assertEqual(stk.top(), 1)
        self.assertEqual(stk.peekMax(), 5)
        self.assertEqual(stk.pop(), 1)
        self.assertEqual(stk.top(), 5)

    def test_popmax_removes_topmost_occurrence_not_first(self) -> None:
        # Three 5's at different depths. popMax must remove the one closest
        # to the top (pushed last), leaving the other two, in their
        # original relative order, still on the stack.
        stk = self.cls()
        stk.push(5)   # bottom
        stk.push(2)
        stk.push(5)   # middle
        stk.push(3)
        stk.push(5)   # top-most -- this is the one popMax must remove
        self.assertEqual(stk.popMax(), 5)
        self.assertEqual(stk.pop(), 3)   # confirms the 3 survived, in place
        self.assertEqual(stk.pop(), 5)   # the middle 5 is now on top
        self.assertEqual(stk.pop(), 2)
        self.assertEqual(stk.pop(), 5)   # bottom 5 last

    def test_popmax_then_push_then_popmax_again(self) -> None:
        stk = self.cls()
        stk.push(1)
        stk.push(5)
        self.assertEqual(stk.popMax(), 5)
        stk.push(5)
        self.assertEqual(stk.popMax(), 5)
        self.assertEqual(stk.popMax(), 1)

    def test_single_element(self) -> None:
        stk = self.cls()
        stk.push(42)
        self.assertEqual(stk.peekMax(), 42)
        self.assertEqual(stk.top(), 42)
        self.assertEqual(stk.popMax(), 42)

    def test_ascending_pushes_max_is_always_the_last_pushed(self) -> None:
        stk = self.cls()
        for x in range(1, 6):
            stk.push(x)
        self.assertEqual(stk.peekMax(), 5)
        self.assertEqual(stk.pop(), 5)
        self.assertEqual(stk.peekMax(), 4)

    def test_negative_values(self) -> None:
        stk = self.cls()
        stk.push(-5)
        stk.push(-1)
        stk.push(-10)
        self.assertEqual(stk.peekMax(), -1)
        self.assertEqual(stk.popMax(), -1)
        self.assertEqual(stk.top(), -10)

    def test_interleaved_push_pop_popmax(self) -> None:
        stk = self.cls()
        stk.push(3)
        stk.push(7)
        stk.pop()             # removes 7
        stk.push(7)
        stk.push(1)
        self.assertEqual(stk.popMax(), 7)   # stack is now [3, 1]
        self.assertEqual(stk.top(), 1)


class TestMaxStackSimple(_MaxStackContractMixin, unittest.TestCase):
    cls = MaxStackSimple


class TestMaxStack(_MaxStackContractMixin, unittest.TestCase):
    cls = MaxStack


class TestDifferential(unittest.TestCase):
    """The two implementations should be indistinguishable from the
    outside. A randomized differential test catches disagreements neither
    hand-written case happened to hit -- particularly useful here since the
    O(log n) version's bug (wrong heap tie-break) produces a plausible-
    looking but wrong result, not a crash.
    """

    def test_random_operation_sequences_agree(self) -> None:
        rng = random.Random(1234567)
        for _trial in range(200):
            simple = MaxStackSimple()
            fast = MaxStack()
            size = 0
            for _step in range(30):
                ops = ["push"]
                if size > 0:
                    ops += ["pop", "top", "peekMax", "popMax"]
                op = rng.choice(ops)
                if op == "push":
                    x = rng.randint(-5, 5)  # small range forces tie-breaks
                    simple.push(x)
                    fast.push(x)
                    size += 1
                elif op == "pop":
                    self.assertEqual(simple.pop(), fast.pop())
                    size -= 1
                elif op == "top":
                    self.assertEqual(simple.top(), fast.top())
                elif op == "peekMax":
                    self.assertEqual(simple.peekMax(), fast.peekMax())
                elif op == "popMax":
                    self.assertEqual(simple.popMax(), fast.popMax())
                    size -= 1


if __name__ == "__main__":
    unittest.main()
