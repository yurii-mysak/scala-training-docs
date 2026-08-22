"""
LC 480 - Sliding Window Median
https://leetcode.com/problems/sliding-window-median/

Given `nums` and window size `k`, return the median of every contiguous
window of length k as it slides across `nums`.

The classic running-median trick (two heaps, split at the median) extends
here, but naive heaps don't support removing an arbitrary element in
O(log n) -- and a sliding window constantly needs to remove the element
that just fell off the back. The fix is LAZY DELETION: mark a value as
"owed a removal" and only actually pop it once it would otherwise surface
at a heap's top.

Companion doc: lc480-sliding-window-median.md
"""
from __future__ import annotations

import heapq
from collections import defaultdict
from typing import DefaultDict, List


class _TwoHeapMedian:
    """A running median over a multiset supporting add/remove in O(log n)
    amortized, via two heaps split at the median plus lazy deletion.

    Invariant (of *live* elements -- i.e. ignoring anything counted in
    `_delayed` but not yet physically popped): `_small` (max-heap, values
    stored negated) holds the lower half, `_large` (min-heap) holds the
    upper half, and `len(small) - len(large)` (logical sizes) is always 0
    or 1. Both heap tops are always "clean" (not pending deletion)
    immediately after every add/remove call returns -- that is what lets
    `median()` read `_small[0]`/`_large[0]` directly with no pruning.
    """

    def __init__(self) -> None:
        self._small: List[int] = []   # max-heap, negated
        self._large: List[int] = []   # min-heap
        self._delayed: DefaultDict[int, int] = defaultdict(int)
        self._small_size = 0
        self._large_size = 0

    def _prune(self, heap: List[int], negate: bool) -> None:
        """Pop stale (pending-deletion) entries off the top of `heap`
        until a live one surfaces or the heap empties.
        """
        while heap:
            top = -heap[0] if negate else heap[0]
            if self._delayed[top] > 0:
                self._delayed[top] -= 1
                if self._delayed[top] == 0:
                    del self._delayed[top]
                heapq.heappop(heap)
            else:
                return

    def _rebalance(self) -> None:
        if self._small_size > self._large_size + 1:
            heapq.heappush(self._large, -heapq.heappop(self._small))
            self._small_size -= 1
            self._large_size += 1
            self._prune(self._small, negate=True)
        elif self._small_size < self._large_size:
            heapq.heappush(self._small, -heapq.heappop(self._large))
            self._large_size -= 1
            self._small_size += 1
            self._prune(self._large, negate=False)

    def add(self, num: int) -> None:
        if not self._small or num <= -self._small[0]:
            heapq.heappush(self._small, -num)
            self._small_size += 1
        else:
            heapq.heappush(self._large, num)
            self._large_size += 1
        self._rebalance()

    def remove(self, num: int) -> None:
        """Mark `num` as logically gone. It is only physically popped once
        it would otherwise surface at the top of whichever heap it is in.
        """
        self._delayed[num] += 1
        if self._small and num <= -self._small[0]:
            self._small_size -= 1
            if num == -self._small[0]:
                self._prune(self._small, negate=True)
        else:
            self._large_size -= 1
            if self._large and num == self._large[0]:
                self._prune(self._large, negate=False)
        self._rebalance()

    def median(self, k: int) -> float:
        if k % 2:
            return float(-self._small[0])
        return (-self._small[0] + self._large[0]) / 2.0


def median_sliding_window(nums: List[int], k: int) -> List[float]:
    window = _TwoHeapMedian()
    result: List[float] = []
    for i, num in enumerate(nums):
        window.add(num)
        if i >= k:
            window.remove(nums[i - k])
        if i >= k - 1:
            result.append(window.median(k))
    return result


if __name__ == "__main__":
    print(median_sliding_window([1, 3, -1, -3, 5, 3, 6, 7], 3))
    # [1.0, -1.0, -1.0, 3.0, 5.0, 6.0]
    print(median_sliding_window([1, 2], 2))
    # [1.5]
    print(median_sliding_window([2, 3, 4], 2))
    # [2.5, 3.5]
