# LC 981 — Time Based Key-Value Store

> **Priority:** Required
> **Est. time:** 40 min
> **Track:** Both
> **HelloInterview:** DSA / Binary Search

---

## 1 · Problem Statement

Design a class supporting:

- `set(key, value, timestamp)` — store `value` under `key`, tagged with
  `timestamp`. Timestamps for a given key arrive in strictly increasing
  order.
- `get(key, timestamp)` — return the value stored for `key` whose timestamp
  is the **largest one that is `<= timestamp`** ("floor" lookup). Return
  `""` if `key` has never been set, or if every recorded timestamp for it is
  after the query timestamp.

This is not "get the value at this exact timestamp" — the floor semantics
are the entire point, and are the part candidates most often get wrong on
the first pass.

## 2 · Evidence

SPEC's laptop-round research found the **versioned / temporal KV store**
family is the **second most-reported laptop-round problem, with 6
independent reports** — just behind the stateful paginated-fetch family
covered in [`lc158-read-n-chars-given-read4-ii.md`](lc158-read-n-chars-given-read4-ii.md).
LC 981 is the cleanest CS-fundamentals-round proxy for that skill: "store a
value tagged with a point in time, retrieve the value as-of a different
point in time" is the core idea underneath every reported laptop-round
variant (begin/commit/rollback stores, nested dot-path KV, etc.).

**Cross-reference:** [Versioned KV Store](../../17-lyft-laptop-round/02-versioned-kv-store.md)
— the laptop-round version, with transactional semantics layered on top of
the same floor-lookup idea.

## 3 · Key Insight

Because `set` timestamps for a given key are guaranteed strictly increasing,
each key's history is *already sorted by construction* if you simply
append. "Find the value as of time T" is then exactly binary search for the
rightmost timestamp `<= T` — `bisect_right(timestamps, T) - 1`. The whole
problem is a hash map from key to a growable sorted list, plus one binary
search call. There is no need for a balanced tree, a skip list, or anything
fancier — recognizing that the "sorted list + binary search" combination is
already optimal is the signal the interviewer is looking for.

## 4 · Approach & Complexity

1. `_store: dict[str, list[tuple[int, str]]]` — one list per key, kept
   sorted by timestamp (ascending, from the strictly-increasing guarantee).
2. `set(key, value, timestamp)`: append `(timestamp, value)` to
   `_store[key]`. O(1) amortized.
3. `get(key, timestamp)`: if the key was never set, return `""`. Otherwise
   binary search for the rightmost entry with timestamp `<= timestamp`
   (`bisect_right` with a `key=` extractor on the timestamp field); if the
   resulting index is before the start of the list, return `""`, else
   return that entry's value.

- **Time:** O(1) amortized for `set`; O(log m) for `get`, where m is the
  number of times *that specific key* was set (not the total store size).
- **Space:** O(total number of `set` calls across all keys).

Reference implementation: [`lc981_time_based_key_value_store.py`](lc981_time_based_key_value_store.py).
Tests: [`test_lc981_time_based_key_value_store.py`](test_lc981_time_based_key_value_store.py).

## 5 · Edge Cases

- **`get` on a key that was never `set`** → `""`.
- **`get` with a timestamp earlier than every recorded entry for that key**
  → `""`, even though the key exists (a common bug: returning the first
  entry instead of nothing, because the index computation reads `-1` as
  Python's "last element" instead of "before the start").
- **`get` with a timestamp exactly matching a stored timestamp** → return
  that entry's value, not the previous one (floor is inclusive).
- **Multiple `set` calls at the same key with the guarantee upheld** — later
  calls always compare greater, so plain `append` keeps the list sorted;
  the reference solution still defends against a violated guarantee (falls
  back to `bisect.insort`) since "the problem promises X" and "the judge/
  interviewer actually upholds X" are not always the same thing worth
  saying out loud in an interview.
- **Very large number of `set` calls for one hot key** — this is where the
  O(log m) binary search matters; a linear scan from the end would degrade
  a hot key to O(m) per `get`, which is the naive mistake this problem is
  designed to catch.

## 6 · Follow-Up Variations

- **"Support `delete(key, timestamp)`."** — the cleanest approach without
  disturbing the sorted-list invariant is a tombstone value written via the
  same `set` path (a sentinel meaning "deleted as of this timestamp"),
  rather than mutating history in place.
- **"What if timestamps for a key are *not* guaranteed increasing?"** —
  swap the plain `append` for `bisect.insort`, which keeps the list sorted
  at O(log m) find + O(m) insert (list shifting) instead of O(1) append;
  worth naming the trade-off explicitly rather than silently eating the
  cost.
- **"Support a range query: all values set between T1 and T2."** — two
  binary searches (`bisect_left`/`bisect_right`) bound a contiguous slice of
  the sorted list; still no new data structure needed.
- **"Now support transactions: `begin()`, `commit()`, `rollback()` on top of
  this store."** — this is exactly the laptop-round version; see
  [Versioned KV Store](../../17-lyft-laptop-round/02-versioned-kv-store.md).
  The floor-lookup core stays identical, transactions add a stack of
  pending writes that either flush into the sorted lists (`commit`) or are
  discarded (`rollback`).
- **"Memory grows unbounded as `set` is called forever — how would you
  cap it?"** — this is Lyft's live napkin-math/memory probe pattern from
  the design rounds, applied at code-review scale: options are TTL-based
  pruning of old versions, a max-versions-per-key cap, or offloading cold
  history to a slower store, each with an explicit space/correctness
  trade-off to state out loud.

## 7 · Reference Solution

See [`lc981_time_based_key_value_store.py`](lc981_time_based_key_value_store.py)
— `TimeMap.set`/`TimeMap.get`, stdlib-only (`bisect`, `collections.defaultdict`),
with a `__main__` demo matching the LeetCode example. Tests in
[`test_lc981_time_based_key_value_store.py`](test_lc981_time_based_key_value_store.py)
cover floor semantics, unknown keys, pre-history queries, and the defensive
out-of-order case.

---

## Interview questions

1. **Why is a hash map of sorted lists sufficient here — why not a balanced
   BST or a skip list per key?** The per-key timestamp stream is already
   sorted on arrival (by the problem's own guarantee), so a plain
   append-only list plus binary search already achieves O(log m) lookup
   with O(1) amortized insert — a self-balancing tree would add rebalancing
   overhead for no asymptotic benefit here.
2. **Walk through exactly what `bisect_right(..., T) - 1` computes and why
   it's `bisect_right` and not `bisect_left`.** `bisect_right` returns the
   insertion point *after* any existing entries equal to `T`, so subtracting
   1 lands on the last entry `<= T` — using `bisect_left` would instead land
   one position too early when there is an exact match at `T`.
3. **What changes if `get` needs the ceiling (smallest timestamp `>=` query)
   instead of the floor?** Use `bisect_left(..., T)` directly (no `-1`), and
   check that the resulting index is within bounds before returning it — the
   asymmetry between floor and ceiling is a common point of confusion worth
   being explicit about.
4. **[Reported at Lyft, laptop-round framing]** **How would you add
   begin/commit/rollback transactions on top of this store?** Keep the
   committed history as the sorted-list-per-key structure described here;
   layer a stack of pending `(key, value)` writes for the active
   transaction, applied to the real store only on `commit` and discarded on
   `rollback` — see the cross-referenced laptop-round doc for the full
   design.
5. **How would this be different in a distributed setting with multiple
   writers for the same key?** The strictly-increasing-timestamp guarantee
   becomes much harder to uphold without a coordinated clock; you'd likely
   need either a single writer per key (partition by key), a logical clock
   (Lamport/vector clocks) to break ties deterministically, or acceptance of
   last-writer-wins with a documented conflict policy.
6. **What is the space cost of never expiring old versions, and how would
   you bound it?** Unbounded — O(total sets) forever. Bound it with a
   TTL, a max-versions-per-key cap with eviction of the oldest, or tiering
   cold versions to slower storage; state the trade-off (history loss vs.
   memory) explicitly.
7. **Why does the reference implementation fall back to `bisect.insort` on
   out-of-order input instead of just trusting the problem's guarantee?**
   A production version of this class (as opposed to a LeetCode submission)
   should not silently corrupt its invariant if an upstream caller violates
   the contract — the defensive branch costs one comparison in the common
   case and avoids an unsorted list turning binary search incorrect.
