# 17 — Lyft Laptop Round

The 90-minute own-IDE coding round: own laptop, own editor, interviewer on the call
with camera and mic off and no screen share, internet allowed, a zipped project
submitted by email at the end. Graded **correctness 45% / clean code 35% /
performance 20%**, and finishing the whole problem is explicitly not required —
but every family in this section has a reported or clearly implied second part,
and treating the stated problem as the whole problem is the most common way this
round is lost. The dominant failure mode across every report behind this section is
**input/output handling, not algorithms** — confirming the I/O channel and output
format in the first five minutes matters more than any single algorithm choice.

This is flagged as the single most important new section in this program: of the
technical rounds in the loop, this is the one candidates most often fail, and it
fails on process as often as on content. Read [00-protocol.md](00-protocol.md)
first — it is the drill everything else in this section runs inside of. Then work
through the problem families roughly in priority order, using
[09-timed-drill-log.md](09-timed-drill-log.md) to track real timed attempts rather
than just reading approaches.

Each problem family below has three files: a `.md` (explanation, approach,
complexity, edge cases, follow-ups, interview questions), a `.py` reference
solution (stdlib only, runnable via `python3 <file>.py`, reading stdin by default
with a documented file-input variant), and a `test_*.py` (`unittest`, runnable via
`python3 -m unittest test_*.py`).

---

## Section Index

| File | Priority | Est. time | Description |
|---|---|---|---|
| [00-protocol.md](00-protocol.md) | Required | 30 min (+90/drill) | The round as a repeatable drill: 15/60/15 split, first-five-minutes checklist, working-then-refactor-then-tests sequencing, when to stop optimising, the demo/zip/email step, and the explicit "part 2 is not optional" warning |
| [01-stateful-paginated-fetch](01-stateful-paginated-fetch.md) (+ `.py`, `test_01_*.py`) | Required | 45 min | `fetchN(n)` over a paginated upstream: internal buffering, page-token progression, exhaustion, no loss/duplication across calls. Part 2: unreliable upstream — retry with backoff, dedup, metrics. **7 reports, the most common family.** Relates to LC 158 |
| [02-versioned-kv-store](02-versioned-kv-store.md) (+ `.py`, `test_02_*.py`) | Required | 40 min | Per-key versioned `set`/`get` with predecessor fallback; the sorted-list-vs-dict-of-versions read/write trade-off, explicitly — candidates report being probed on it directly. **6 reports.** Relates to LC 981 |
| [03-inmemory-kv-transactions](03-inmemory-kv-transactions.md) (+ `.py`, `test_03_*.py`) | Required | 60 min | SET/GET/DELETE, then nested BEGIN/COMMIT/ROLLBACK as an explicit part 2. **4 reports, incl. 2026** — the family with the clearest documented "we expect that part to be covered" failure |
| [04-trie-typeahead-t9](04-trie-typeahead-t9.md) (+ `.py`, `test_04_*.py`) | Required | 50 min | Frequency-ranked trie autocomplete, then the T9 numeric-keypad variant — a near-exact match for the reported "word analyzer (T9)" problem. **5 reports.** Relates to LC 642, LC 208 |
| [05-job-scheduler-workers](05-job-scheduler-workers.md) (+ `.py`, `test_05_*.py`) | Recommended | 45 min | Minimum-workers interval scheduling via a min-heap of worker free-times; queries against the resulting assignment. **4 reports, incl. a 2026 pass.** Relates to LC 253, LC 1094. Python's `heapq` is free — a reported failure here was a hand-rolled heap in Go |
| [06-file-log-csv-parsing](06-file-log-csv-parsing.md) (+ `.py`, `test_06_*.py`) | Recommended | 45 min | Three bundled I/O-heavy sub-problems: K-th non-empty line of a large file (streamed), hand-rolled CSV splitting with quoted fields, and p50/p95 log aggregation. **4 reports** |
| [07-nested-path-kv](07-nested-path-kv.md) (+ `.py`, `test_07_*.py`) | Optional | 40 min | Dot-path KV with auto-created intermediates, `children(prefix)`, `flatten()`, and strict branch/leaf type checking. **2 reports** — lowest frequency, but a good synthesis drill |
| [08-oneoffs.md](08-oneoffs.md) | Recommended | 30 min | Approach notes (no full solutions) for eight lower-frequency reported patterns: Max Stack, ArrayList-backed LRU, union-find, DAG/topological sort, the iterator pattern, grid/BFS spread, an `attack`-method OOD class, and shopping-list-vs-promotions matching |
| [09-timed-drill-log.md](09-timed-drill-log.md) | Optional | 10 min | A template for logging real timed attempts (date, problem, part-1 time, part-2 reached, I/O channel, what broke, fix), plus per-family target times |

---

## Priority, In One Line

**Required** (00, 01-04): the highest-frequency families plus the protocol itself —
skipping any of these is the most direct path to a downlevel or a rejection on this
round specifically. **Recommended** (05, 06, 08): materially raises your odds,
lower individual frequency or narrower scope than the Required set. **Optional**
(07, 09): worth doing if time allows — 07 for the practice value, 09 because it only
pays off once you're actually running timed drills against the material above it.
