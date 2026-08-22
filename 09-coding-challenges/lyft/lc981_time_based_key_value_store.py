"""
LC 981 - Time Based Key-Value Store
https://leetcode.com/problems/time-based-key-value-store/

Design a key-value store that supports:
  set(key, value, timestamp) -- store `value` for `key` at `timestamp`.
  get(key, timestamp)        -- return the value stored for `key` whose
                                 timestamp is the largest one <= the query
                                 timestamp; "" if no such entry exists.

LeetCode guarantees timestamps passed to `set` for a given key are strictly
increasing, so each key's history is already append-sorted -- the whole
problem reduces to "binary search for a floor value in a sorted list."

This is the same shape as a versioned / temporal store more generally: see
../../17-lyft-laptop-round/02-versioned-kv-store.md for the laptop-round
version (begin/commit/rollback semantics on top of the same "query as of a
point in time" idea).

Companion doc: lc981-time-based-key-value-store.md
"""
from __future__ import annotations

from bisect import bisect_right, insort
from collections import defaultdict
from typing import Dict, List, Tuple


class TimeMap:
    def __init__(self) -> None:
        # key -> list of (timestamp, value), sorted by timestamp.
        self._store: Dict[str, List[Tuple[int, str]]] = defaultdict(list)

    def set(self, key: str, value: str, timestamp: int) -> None:
        entries = self._store[key]
        if entries and entries[-1][0] >= timestamp:
            # Defensive: the problem guarantees strictly increasing
            # timestamps per key, but insort keeps correctness even if a
            # caller violates that (see the .md's edge-case discussion).
            insort(entries, (timestamp, value))
        else:
            entries.append((timestamp, value))

    def get(self, key: str, timestamp: int) -> str:
        entries = self._store.get(key)
        if not entries:
            return ""
        # Rightmost index whose timestamp is <= the query timestamp.
        idx = bisect_right(entries, timestamp, key=lambda pair: pair[0]) - 1
        return entries[idx][1] if idx >= 0 else ""


if __name__ == "__main__":
    tm = TimeMap()
    tm.set("foo", "bar", 1)
    print(tm.get("foo", 1))   # "bar"
    print(tm.get("foo", 3))   # "bar"  (floor of 3 is the entry at 1)
    tm.set("foo", "bar2", 4)
    print(tm.get("foo", 4))   # "bar2"
    print(tm.get("foo", 5))   # "bar2"
    print(tm.get("foo", 0))   # ""     (before any entry)
    print(tm.get("missing", 1))  # ""  (unknown key)
