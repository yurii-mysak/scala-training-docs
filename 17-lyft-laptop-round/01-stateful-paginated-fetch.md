# Stateful Paginated Fetch (fetchN over a page-at-a-time upstream)

> **Priority:** Required
> **Est. time:** 45 min
> **Track:** Both
> **HelloInterview:** none

The single most-reported laptop-round shape: **7 independent first-hand reports**, more
than any other family. If you drill only one problem before the round, drill this one.

---

## 1 · Problem

You are given (or asked to build a fake stand-in for) an upstream that returns data one
page at a time:

```text
fetch_page(page_number) -> {"data": [...], "next_page_number": int | None}
```

Implement a wrapper with one method:

```text
fetchN(n) -> list   # the next n items, in source order
```

`fetchN` is called **repeatedly** by the caller (think: a consumer pulling a stream in
small batches). State must survive between calls — the wrapper is an object/closure,
not a stateless function.

---

## 2 · Approach

Hold three pieces of state on the wrapper: the **next page token**, an **internal
buffer** of items pulled from the most recently fetched page, and a **cursor** into
that buffer. `fetchN(n)`:

1. While fewer than `n` items collected and the upstream is not exhausted:
   - If the buffer still has unconsumed items, take as many as needed (up to what's
     left in the buffer) and advance the cursor.
   - Otherwise, fetch the next page, replace the buffer, reset the cursor to 0, and
     store the new `next_page_number`.
2. Return whatever was collected — **fewer than `n` means exhausted, not an error.**

"Exhausted" is `next_page_number is None AND the buffer is empty` — both conditions,
not either alone. An empty page with a non-`None` next token is not the end of the
stream; it is a signal to keep going. Treating an empty page as end-of-stream is the
single most common bug reported in this family.

See [`01-stateful-paginated-fetch.py`](01-stateful-paginated-fetch.py) for the full
reference implementation (`PaginatedFetcher`).

---

## 3 · Complexity

- **Time:** O(1) amortized per item across the lifetime of the fetcher — every item is
  copied out of a page buffer exactly once, and every page is fetched exactly once.
  A single `fetchN(n)` call costs O(n + pages touched).
- **Space:** O(page size) — only the current page is buffered, never the whole stream.

---

## 4 · Edge Cases

| Case | Expected behavior |
|---|---|
| `n == 0` | Return `[]` without calling the upstream at all |
| `n < 0` or non-int `n` | Raise (`ValueError` / `TypeError`) — decide and state your convention out loud |
| Upstream exhausted mid-`fetchN` | Return whatever was collected, shorter than `n` |
| Empty page, `next_page_number` still set | Keep fetching — **not** end-of-stream |
| Upstream exhausted before first call | `fetchN` returns `[]` for any `n` |
| Calls after exhaustion | Always return `[]`, never re-raise or loop forever |
| `fetchN` boundary equal to page size exactly | No off-by-one — buffer cursor must land exactly at page length, not skip or repeat the last item |
| Many small `fetchN(1)` calls back to back | Must reconstruct the exact same sequence as one large `fetchN(total)` call — this is the "no loss or duplication" requirement, and it's the one worth writing a test for explicitly |

---

## 5 · Part 2 — The Upstream Is Unreliable

Expect this. The follow-up turns the happy-path wrapper into a resilience exercise:

- **Retry with backoff** — `fetch_page` can raise transiently; retry a bounded number
  of times with exponential backoff (+ jitter, so many failing clients don't retry in
  lockstep). Make `sleep`/`rand` injectable parameters — that's what lets your tests
  run in milliseconds instead of real wall-clock delays, and it's a clean-code signal
  worth calling out to the interviewer unprompted.
- **Dedup** — a retry can mean the *request* failed to get a response even though the
  upstream *processed* it, so a retried page can hand back items you already buffered.
  Dedup by item identity (a set of seen ids), not by page number alone.
- **Metrics** — expose counts an on-call engineer would actually want: pages fetched,
  retries, items returned, items deduped. A `.metrics` object/dict is enough; you do
  not need to wire up a real metrics backend.

See `ReliablePaginatedFetcher` in the same file — it composes with `PaginatedFetcher`
by wrapping the upstream callable (`with_retry`) rather than duplicating the buffering
logic, which is the cleaner design if you're asked "why not just copy-paste and modify."

---

## 6 · Follow-ups

- How would `fetchN` behave if it had to support **concurrent callers** on the same
  fetcher instance? (Needs a lock around the buffer + page-token mutation, or a
  redesign around an internal queue fed by a single background fetch loop.)
- How would you cap memory if pages could be arbitrarily large? (Bound the buffer,
  or expose a streaming/generator interface instead of a list-returning `fetchN`.)
- What if `fetch_page` itself needed pagination *parameters* beyond a page number —
  e.g., a cursor token instead of an integer? (Same shape, swap `int` for `str` token
  type and stop comparing to `None` by identity if the sentinel changes.)

---

## Interview questions

1. **[Reported at Lyft]** Implement `fetchN(n)` over a paginated upstream that returns
   items across repeated calls, in source order, with no loss or duplication.
   *Model answer:* buffer the current page and a cursor as instance state; on each
   call, drain the buffer first, then fetch fresh pages only as needed until `n` items
   are collected or the upstream reports no more pages. Never re-fetch a page you've
   already buffered from.

2. Why is "empty page" not the same signal as "end of stream"?
   *Model answer:* a paginated API can return a page with zero items but a valid next
   token (e.g., a filtered page that happened to match nothing). Exhaustion is defined
   by the next-page token being absent, not by the item count of any single page.

3. How do you guarantee no duplication across two back-to-back `fetchN` calls?
   *Model answer:* the buffer cursor is instance state, not a local variable — it is
   never reset except when a new page is loaded, so every item is handed out exactly
   once regardless of how the `n` values are chunked across calls.

4. What's the time complexity of calling `fetchN(1)` `k` times versus `fetchN(k)` once?
   *Model answer:* both are O(k) amortized in total work; the small-call version does
   more per-call bookkeeping overhead but touches the same number of upstream pages
   and the same number of items, so asymptotically they're equivalent.

5. The upstream call can fail transiently. How do you make this reliable without
   hammering it?
   *Model answer:* wrap the call in retry-with-exponential-backoff-and-jitter, capped
   at a small number of attempts, and only retry the narrow exception type you expect
   from a transient failure — not every exception.

6. A retry succeeded upstream but the response was lost, so you retried again and got
   the same page back. How do you avoid double-counting those items?
   *Model answer:* dedup at the item level using a stable identity (id field, or a
   content hash if there's no id), not at the page level — the page number alone
   doesn't tell you whether its contents were already consumed.

7. How would you test this without real sleeps slowing the suite down?
   *Model answer:* inject the sleep function (and the jitter/random source) as
   constructor parameters with real implementations as defaults, and pass no-op /
   deterministic fakes in tests.

8. What would you change if `fetchN` needed to support out-of-order or random access
   (e.g., "give me items 100–110") instead of strictly sequential pulls?
   *Model answer:* sequential buffering no longer works; you'd need either a full
   index (defeats "don't load it all into memory") or an upstream that supports
   direct offset/range queries, and you'd cache pages by number instead of keeping a
   single rolling buffer.
