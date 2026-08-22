# Versioned (Temporal) Key-Value Store

> **Priority:** Required
> **Est. time:** 40 min
> **Track:** Both
> **HelloInterview:** DSA — Binary Search

**6 independent first-hand reports** — the second most common laptop-round shape after
[stateful paginated fetch](01-stateful-paginated-fetch.md).

---

## 1 · Problem

```text
set(key, value) -> int        # stores value, returns the new version for key
get(key, version) -> value    # value at that version, or the latest version < it
```

Each `set` on a given key **increments that key's own version counter**, starting at
1. `get(key, version)` returns the value recorded at exactly that version if it
exists; if it does not (the version was skipped, or is beyond what's been set, or
predates the first `set`), it returns the value at the **latest recorded version
smaller than the one requested** — or nothing if no such version exists.

---

## 2 · Approach

Per key, keep a list of `(version, value)` pairs. Because `set` always assigns
`latest + 1`, appends land in strictly increasing version order for free — **no
re-sorting on write**, ever. `get` is then a single binary search: find the rightmost
entry whose version is `<= version`. Python's `bisect.bisect_right(..., key=...)`
(3.10+) does this in one call without ever comparing the stored *values* against each
other — only the version numbers, which is important because values can be any type.

See [`02-versioned-kv-store.py`](02-versioned-kv-store.py) for the full reference
implementation (`VersionedKVStore`), plus a second implementation
(`VersionedKVStoreDictBacked`) built purely to make the next section concrete.

Related repo material: [Event Sourcing Guide](../06-databases-and-distributed-data/Event-Sourcing-Guide.md)
covers the same "immutable append-only history, derive current state by folding or
by picking a point in time" idea at a systems-design scale — worth skimming if this
family comes up in a design round too, not just the laptop round.

---

## 3 · Complexity

- **Write (`set`):** O(1) amortized — append to the end of that key's list.
- **Read (`get`):** O(log v) where v = number of versions recorded for that key.
- **Space:** O(total number of `set` calls) — this store never overwrites history,
  by design; if that's not desired, that's a scope question worth asking (see
  Follow-ups).

---

## 4 · Read vs Write Optimisation — you will likely be asked this directly

Candidates report being probed specifically on this trade-off, so have the answer
ready before you're asked, not while you're being asked.

| Design | Write cost | Read cost (exact version) | Read cost (predecessor) | Extra memory |
|---|---|---|---|---|
| **Sorted list + binary search** (default above) | O(1) append | O(log v) | O(log v) | none beyond the list itself |
| **Dict of exact versions, plus a sorted list of version numbers** | O(1) append to both | O(1) | O(log v) — you still need the sorted list, the dict alone can't answer "nearest below" | a full second index, same size as the first |

The dict-of-versions design only pays for itself if **most reads are exact-version
hits** — e.g., a cache-style access pattern where callers usually ask for a version
they already know exists. If reads are a mix of exact and historical/predecessor
lookups (the general case this problem describes), the dict buys you nothing: you
still need the sorted list for the predecessor case, so you're paying for two
structures to serve the query one already serves in O(log v). The one case worth
special-casing on its own is **"give me the latest value"** — track it as a single
`Dict[key, value]` alongside the history, O(1), independent of which of the two
designs above you pick for everything else.

**Practical answer to give out loud:** start with the sorted-list-and-append design —
it's simpler, it's optimal for writes, and reads are already O(log v) which is fine
unless told otherwise. Only add the dict fast-path if the interviewer tells you reads
are dominated by exact-version hits, and say so explicitly rather than guessing.

---

## 5 · Edge Cases

| Case | Expected behavior |
|---|---|
| `get` for a version before the key's first `set` | No value (`None` / not found) |
| `get` for a version beyond the latest | Returns the **latest** value — "latest smaller" still applies |
| `get` for a key never `set` | No value |
| `get` for version `0` or negative | No value (versions start at 1) |
| Multiple `set` calls, `get` an intermediate version | Exact historical value, not the latest |
| Values that aren't mutually orderable (e.g., dicts) | Must never be compared against each other — only version numbers are compared |

---

## 6 · Follow-ups

No specific Part 2 was reported for this family, but expect one — see
[00-protocol.md](00-protocol.md) on always asking. Plausible extensions worth
pre-thinking, not reported facts, just informed guesses:

- `delete(key)` — as a tombstone version (so history and "value at version" stays
  correct for reads before the delete) versus a hard delete (simpler, but destroys
  history).
- TTL / expiry per version.
- A range query: all `(version, value)` pairs between two versions — trivial with the
  sorted-list design (a slice), painful with the dict-only design.
- Multi-key atomic `set` (several keys advance together or none do) — this starts to
  look like [in-memory KV with transactions](03-inmemory-kv-transactions.md).

---

## Interview questions

1. **[Reported at Lyft]** Implement `set`/`get` for a per-key versioned store where
   `get` on a missing version falls back to the latest smaller one.
   *Model answer:* append-only sorted history per key (free, since versions are
   assigned in increasing order), binary search on read for the rightmost entry
   `<= version`.

2. **[Reported at Lyft]** Would you use a sorted list with binary search, or a dict
   keyed by version, and why?
   *Model answer:* sorted list by default — O(1) writes, O(log v) reads for both
   exact and predecessor queries. A dict only helps if reads are dominated by exact-
   version hits, and even then you still need the sorted list for predecessor
   queries, so it's additive complexity, not a replacement.

3. Why don't you need to re-sort the list on every write?
   *Model answer:* versions are assigned by the store itself as `latest + 1`, so
   every write is already the largest version seen for that key — appending
   preserves sort order for free.

4. What's the time complexity of `get`?
   *Model answer:* O(log v), v = number of versions recorded for that key — a binary
   search over that key's history.

5. How is this related to LeetCode 981 (Time Based Key-Value Store)?
   *Model answer:* structurally identical — LC 981 uses an externally supplied
   timestamp instead of an auto-incrementing version, but the query ("largest
   recorded key <= the one asked for") and the binary-search solution are the same.

6. How would you support a `delete`?
   *Model answer:* prefer a tombstone value recorded as a new version, so that
   historical reads before the delete remain correct; a hard delete from the history
   would corrupt any `get` for an earlier version that should still resolve.

7. How would this change if versions could be set out of order, or supplied by the
   caller instead of auto-incremented?
   *Model answer:* the list is no longer guaranteed sorted on insert; you'd need to
   `bisect.insort` on write (O(v) due to the shift) or switch to a structure that
   tolerates out-of-order insertion better, e.g. a balanced tree — direct evidence
   that the "append is free" property depends entirely on versions being caller-
   controlled monotonic, and you should say so if the interviewer changes this
   constraint on you.

8. How would you extend this to multiple keys updated atomically in one call?
   *Model answer:* wrap the per-key updates in a transaction boundary so either all
   keys' new versions become visible together or none do — this is effectively the
   [in-memory KV transactions](03-inmemory-kv-transactions.md) problem layered on top.
