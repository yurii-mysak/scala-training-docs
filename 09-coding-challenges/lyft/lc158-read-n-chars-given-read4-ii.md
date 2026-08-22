# LC 158 — Read N Characters Given Read4 II (Call Multiple Times)

> **Priority:** Required
> **Est. time:** 40 min
> **Track:** Both
> **HelloInterview:** none

---

## 1 · Problem Statement

You are given a `read4(buf4)` primitive: it fills up to 4 characters of an
underlying file into `buf4` and returns how many characters it actually
wrote — fewer than 4 only at end-of-file. You do not control `read4` and
cannot rewind it. Implement `read(buf, n)` on top of it, which must copy
exactly `n` characters into `buf` (or fewer, only if the file runs out) and
return the count copied.

The "II" is the whole problem: **`read` may be called multiple times on the
same object**, in any sequence of `n` values, and calls must behave as if
they were reading one continuous stream — no characters lost, none
duplicated, none re-fetched from a `read4` block that was already partially
consumed by an earlier call.

## 2 · Evidence

SPEC's laptop-round research found **stateful paginated fetch / read-N is
the single most-reported laptop-round problem family — 7 independent
reports**, ahead of every other family including the versioned-KV-store
family below. LC 158 is included here as the CS-fundamentals-round proxy for
that exact skill: no report names LC 158 by number, but "implement pagination
on an API endpoint" appears directly in Lyft's reported coding-screen
questions, and it is the same shape — a primitive that hands you a bounded
chunk per call and forces you to carry leftover state forward yourself. If
the laptop round hands you a paginated-fetch or chunked-read problem, this is
the drill that builds the exact muscle memory for it.

**Cross-reference:** [Stateful Paginated Fetch](../../17-lyft-laptop-round/01-stateful-paginated-fetch.md)
— the laptop-round version of the same problem, in a real-API framing
instead of a LeetCode-judge framing. Do this file first; it is the smaller,
faster-to-debug version of the same statefulness bug surface.

## 3 · Key Insight

The entire problem is: **what state has to survive between calls, and
exactly when do you refill it?** You need three pieces of instance state,
not one:

1. A 4-character buffer (`buf4`).
2. How many of those 4 characters are currently *valid* (`read4` can return
   fewer than 4).
3. How far into that valid range you have already *consumed* on behalf of
   previous `read` calls.

A single-call test suite cannot catch a broken implementation here — the bug
only appears the moment two calls to `read` straddle one `read4` block
boundary. This is exactly why the reference tests below deliberately choose
call sizes that do not divide evenly into 4.

## 4 · Approach & Complexity

1. On construction, initialize `buf4 = [''] * 4`, `buf4_len = 0`,
   `buf4_ptr = 0` — an empty, fully-consumed buffer.
2. In `read(buf, n)`, loop while `total < n`:
   - If `buf4_ptr == buf4_len` (nothing left over from before), call
     `read4(buf4)` exactly once, reset `buf4_ptr = 0`, and set `buf4_len` to
     what it returned. If that is `0`, the source is exhausted — break.
   - Copy from `buf4[buf4_ptr:buf4_len]` into `buf` until either `buf` has
     `n` characters or `buf4` runs out again, advancing both pointers.
3. Return `total`.

- **Time:** O(n) per call — amortized O(1) per character copied, plus at
  most one `read4` call for every 4 characters actually consumed across the
  *lifetime* of the object, not per call.
- **Space:** O(1) beyond the fixed 4-character buffer.

Reference implementation: [`lc158_read_n_chars_given_read4_ii.py`](lc158_read_n_chars_given_read4_ii.py).
Tests: [`test_lc158_read_n_chars_given_read4_ii.py`](test_lc158_read_n_chars_given_read4_ii.py).

## 5 · Edge Cases

- **`n = 0`** — return 0 immediately, must not call `read4` at all (a common
  off-by-one is calling it once "just in case").
- **File length not a multiple of 4** — the last `read4` call returns 1–3
  characters; the loop must stop pulling from `buf4` at `buf4_len`, not at a
  hardcoded 4.
- **`read` called again after EOF** — must return 0 immediately without
  re-calling `read4` forever (a broken loop condition can spin here since
  `read4` correctly keeps returning 0, but a naive "call until we get some"
  loop would never terminate — the `if buf4_len == 0: break` is what saves
  it).
- **`n` larger than the remaining file** — return only what exists, not `n`.
- **Multiple `Solution` instances against different files** — state must be
  per-instance (`self.buf4`, not a class attribute); this is the most common
  copy-paste bug when candidates crib a single-call solution and bolt
  statefulness on afterward.
- **A call to `read` that exactly drains `buf4` to zero leftover** — the next
  call must correctly detect `buf4_ptr == buf4_len` and fetch fresh, not
  read stale data.

## 6 · Follow-Up Variations

- **"What if `read4` itself can fail transiently and should be retried?"**
  — tests whether the candidate keeps the retry logic *outside* the
  state-management logic (wrap the `read4` call site, don't touch the
  pointer bookkeeping) — directly analogous to retrying a paginated API
  call without corrupting the pagination cursor.
- **"Make `read4` variable-width instead of fixed-4."** — generalizes cleanly:
  `buf4` becomes a dynamically-sized buffer and `buf4_len` is still "how
  much of it is valid," nothing else changes. Good candidates recognize the
  algorithm never actually depended on the width being exactly 4 — this is
  effectively the paginated-fetch shape directly, see the laptop-round
  cross-reference above.
- **"What if two threads call `read` concurrently on the same instance?"**
  — the honest answer is that the reference implementation is not
  thread-safe (unsynchronized read-modify-write on `buf4_ptr`/`buf4_len`);
  a correct answer either adds a lock around the whole method body or states
  the concurrency assumption explicitly rather than silently ignoring it.
- **"Read backward / seek to an offset."** — breaks the whole approach,
  since `read4` is explicitly one-directional and non-rewindable; the
  correct answer is that this requires a different underlying primitive
  entirely, not a patch to this algorithm — worth saying out loud rather
  than trying to force it.

## 7 · Reference Solution

See [`lc158_read_n_chars_given_read4_ii.py`](lc158_read_n_chars_given_read4_ii.py)
— `FileReader4` simulates the judge's hidden file via an in-memory string
(exposing only `read4`, exactly like the real judge), and `Solution.read`
holds the three pieces of state described above. Tests in
[`test_lc158_read_n_chars_given_read4_ii.py`](test_lc158_read_n_chars_given_read4_ii.py)
specifically use call sizes that do not divide evenly into 4, to force
leftover-buffer reuse across calls.

---

## Interview questions

1. **Why can't you just call `read4` in a loop inside `read` without saving
   any state between calls?** Because `read4` cannot be rewound — any
   characters it returns beyond what the current `read` call consumes would
   be permanently lost on the next call, silently corrupting every
   subsequent read.
2. **What's the minimum state you need to carry between calls, and why
   exactly three fields?** The buffer's contents, how many of its slots are
   valid (since the last `read4` may have returned < 4), and how far into
   the valid range you've already consumed — dropping any one of the three
   either loses characters or replays already-consumed ones.
3. **[Reported at Lyft]** (framed as pagination, not read4) **How would you
   implement a client that fetches all results from a paginated API where
   each page also returns a cursor?** Same shape: persist the cursor as
   instance state between calls, and don't fetch a new page until the
   current page's items are exhausted — see
   [Stateful Paginated Fetch](../../17-lyft-laptop-round/01-stateful-paginated-fetch.md).
4. **How do you unit test statefulness bugs like this, given that a single
   call can look correct?** Deliberately choose call sizes that straddle
   the underlying primitive's block boundary (here, sizes that don't divide
   4) — a suite of only 4-aligned reads would pass a broken implementation.
5. **What happens if `read4` is not idempotent and has side effects (e.g. it
   advances a real file descriptor)?** Then it must be called at most once
   per needed refill, never speculatively or more than once per empty
   buffer — which is exactly the guarantee the `if buf4_ptr == buf4_len`
   guard provides.
6. **Is this implementation thread-safe? If not, what's the minimal fix?**
   No — concurrent calls race on `buf4_ptr`/`buf4_len`. The minimal fix is a
   single lock (`threading.Lock`) held for the duration of `read`, at the
   cost of serializing all reads on one instance.
7. **How does this generalize to `read4` being replaced by `readN(buf, k)`
   for an arbitrary `k`?** The algorithm is unchanged; only the fixed
   constant 4 becomes a parameter — the state machine (buffer, valid-count,
   consumed-pointer) doesn't care what the block size is.
