"""
LC 716 - Max Stack
https://leetcode.com/problems/max-stack/

A stack supporting push/pop/top plus:
  peekMax() -- return the current maximum without removing it.
  popMax()  -- remove and return the current maximum. If the maximum value
               occurs more than once, remove only the TOP-MOST occurrence
               (closest to the top of the stack), and every element that
               was above it must end up back on the stack, in its original
               relative order.

Two implementations, shown together on purpose: the O(n)-popMax version is
what a candidate should be able to produce correctly and quickly; the
O(log n)-amortized version is the follow-up almost every interviewer pushes
for once the first one works, and it is where this problem stops being
"easy."

Companion doc: lc716-max-stack.md
"""
from __future__ import annotations

import heapq
from itertools import count
from typing import Dict, List, Optional, Tuple


class MaxStackSimple:
    """O(1) push/pop/top/peekMax; O(n) popMax.

    A normal stack plus a parallel stack that always mirrors the running
    maximum below it. popMax has no way to jump straight to the target
    element, so it buffers everything above it, discards the max, then
    replays the buffer back through `push` (which is what keeps
    `_max_stack` correct without any special-casing).
    """

    def __init__(self) -> None:
        self._stack: List[int] = []
        self._max_stack: List[int] = []

    def push(self, x: int) -> None:
        self._stack.append(x)
        current_max = self._max_stack[-1] if self._max_stack else x
        self._max_stack.append(max(x, current_max))

    def pop(self) -> int:
        self._max_stack.pop()
        return self._stack.pop()

    def top(self) -> int:
        return self._stack[-1]

    def peekMax(self) -> int:
        return self._max_stack[-1]

    def popMax(self) -> int:
        max_val = self._max_stack[-1]
        buffer: List[int] = []
        while self._stack[-1] != max_val:
            buffer.append(self.pop())
        self.pop()  # discard the top-most occurrence of the max itself
        while buffer:
            self.push(buffer.pop())
        return max_val


class _Node:
    __slots__ = ("val", "id", "prev", "next")

    def __init__(self, val: int, id_: int) -> None:
        self.val = val
        self.id = id_
        self.prev: Optional["_Node"] = None
        self.next: Optional["_Node"] = None


class MaxStack:
    """O(1) pop/top; O(log n) amortized push/peekMax/popMax.

    Two structures over the same logical stack:
      - a doubly linked list (sentinel head/tail) for O(1) push/pop/top at
        the tail, and O(1) removal of any node once you already hold a
        reference to it;
      - a max-heap of (-value, -id), using LAZY DELETION: `pop()` removes a
        node from the linked list directly and does *not* touch the heap;
        stale heap entries are simply skipped (and permanently discarded)
        the next time they would surface at the top in peekMax/popMax.

    The `-id` (not `id`) as the heap tie-break is the crux of the problem:
    ties must resolve to the most-recently-pushed element, i.e. the largest
    id, and heapq is a MIN-heap, so the tie-break key has to be negated too.
    Getting this backwards is the single most common bug on this problem --
    it silently returns a *correct value* (the right max) while removing
    the *wrong occurrence*, which most ad hoc test cases never catch.

    Each id is pushed to the heap at most once and popped from it at most
    once over the object's lifetime (either explicitly in popMax, or lazily
    while cleaning stale entries), so the total heap work across N pushes
    is O(N log N) -- push/peekMax/popMax are each O(log n) amortized, even
    though a single peekMax call can, worst case, clean many stale entries
    at once.
    """

    def __init__(self) -> None:
        self._head = _Node(0, -1)
        self._tail = _Node(0, -1)
        self._head.next = self._tail
        self._tail.prev = self._head
        self._heap: List[Tuple[int, int]] = []  # (-value, -id)
        self._id_to_node: Dict[int, _Node] = {}
        self._next_id = count()

    def _unlink(self, node: "_Node") -> None:
        node.prev.next = node.next
        node.next.prev = node.prev

    def push(self, x: int) -> None:
        node = _Node(x, next(self._next_id))
        node.prev = self._tail.prev
        node.next = self._tail
        self._tail.prev.next = node
        self._tail.prev = node
        self._id_to_node[node.id] = node
        heapq.heappush(self._heap, (-x, -node.id))

    def pop(self) -> int:
        node = self._tail.prev
        self._unlink(node)
        del self._id_to_node[node.id]
        return node.val

    def top(self) -> int:
        return self._tail.prev.val

    def peekMax(self) -> int:
        neg_val, _ = self._clean_and_peek()
        return -neg_val

    def popMax(self) -> int:
        neg_val, neg_id = self._clean_and_peek()
        heapq.heappop(self._heap)
        node = self._id_to_node.pop(-neg_id)
        self._unlink(node)
        return node.val

    def _clean_and_peek(self) -> Tuple[int, int]:
        """Discard stale heap entries (already-removed ids) and return the
        top tuple *without* popping it -- the caller decides whether this
        is a peek or an actual removal.
        """
        while self._heap and -self._heap[0][1] not in self._id_to_node:
            heapq.heappop(self._heap)
        return self._heap[0]


if __name__ == "__main__":
    for cls in (MaxStackSimple, MaxStack):
        print(f"--- {cls.__name__} ---")
        stk = cls()
        stk.push(5)
        stk.push(1)
        stk.push(5)
        print("top:", stk.top())        # 5
        print("popMax:", stk.popMax())  # 5 (the top-most occurrence, id 2)
        print("top:", stk.top())        # 1
        print("peekMax:", stk.peekMax())  # 5 (the remaining, earlier 5)
        print("pop:", stk.pop())        # 1
        print("top:", stk.top())        # 5
