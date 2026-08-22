# Job Scheduler / Interval-to-Worker Assignment

> **Priority:** Recommended
> **Est. time:** 45 min
> **Track:** Both
> **HelloInterview:** DSA — Heap; Intervals

**4 independent first-hand reports, including a 2026 pass.**

---

## 1 · Problem

Given jobs with a `start` time and a `duration`, assign each job to a worker such
that no worker ever runs two overlapping jobs, using the **minimum number of
workers**. Support at least: which worker a given job landed on, and how many
workers are busy at a given time.

---

## 2 · Why Python Wins This One

A reported failure in this exact family: a candidate **hand-rolled a binary heap
from scratch in Go** and ran out of time before finishing the actual scheduling
logic. That is the wrong place to spend your 60 minutes. In Python, `heapq` is a
zero-setup stdlib import — `heapq.heappush` / `heapq.heappop` on a plain list, O(log
n) each, done. If you catch yourself writing sift-up/sift-down by hand in this round,
stop — you have the wrong tool selected, not a genuinely hard sub-problem.

---

## 3 · Approach

Classic interval-scheduling shape (LeetCode 253, Meeting Rooms II):

1. Sort jobs by start time.
2. Keep a **min-heap of `(free_at_time, worker_id)`** for every worker currently in
   use.
3. For each job, in start-time order: if the earliest-freeing worker (`heap[0]`) is
   free by this job's start time, pop it, reuse it, push back with the new end time.
   Otherwise, open a new worker.
4. The number of workers ever opened is the answer.

**Boundary convention, state it out loud:** intervals are treated as `[start, end)`
— end-exclusive. A worker freeing at `t=5` is available for a job starting at `t=5`.
This is the single most common off-by-one in this family, and the interviewer may
not specify it either way — say which convention you're using before you're asked.

See [`05-job-scheduler-workers.py`](05-job-scheduler-workers.py) for the full
reference implementation (`WorkerScheduler`, `min_workers_needed`, `Job`).

Related repo material: [Binary Heap Summary](../08-algorithms-and-data-structures/binary_heap_summary.md)
for the heap mechanics themselves if they're rusty.

---

## 4 · Complexity

- **Time:** O(n log n) — the sort dominates; each `assign` is O(log n) for the heap
  push/pop.
- **Space:** O(n) — one heap entry per currently-open worker, at most n of them.
- `workers_busy_at(t)`: O(jobs assigned so far) as implemented — a linear scan is
  fine at interview scale. If pushed on "what if this query runs a million times,"
  the honest follow-up is an offline sweep-line index built once, then O(log n) or
  O(1) per query — name it, don't necessarily build it live.

---

## 5 · Edge Cases

| Case | Expected behavior |
|---|---|
| Empty job list | 0 workers needed |
| All jobs disjoint in time | 1 worker |
| All jobs share the same start time | n workers (one each) |
| Back-to-back jobs (`end == next start`) | Share a worker — this is the end-exclusive convention in action |
| Zero-duration job | Frees immediately; under `[start, end)` semantics it never actually occupies any instant |
| Jobs submitted out of start-time order to the incremental `assign()` API | This file: raises — the incremental API's contract requires sorted input, `min_workers_needed` sorts internally so it accepts any order |

---

## 6 · Follow-ups

- **LeetCode 1094 (Car Pooling)** is the same family one level up: instead of a
  binary "does this worker overlap," each interval carries a passenger *count*
  against a fixed-capacity vehicle — solved with the same idea (sort events, sweep,
  track a running total), via either a heap or a diff array over time. Name this
  connection if asked "what else looks like this."
- How would you support **cancelling** an already-assigned job? (Need to track each
  worker's active interval set, not just its next-free time — a bigger structural
  change than it sounds.)
- How would this change for jobs with **priorities** (a high-priority job can
  preempt a lower-priority one already running)? This turns into a scheduling
  policy question, not just an interval-packing one — worth explicitly flagging the
  scope change rather than quietly building it.

---

## Interview questions

1. **[Reported at Lyft]** Given jobs with start times and durations, assign them to
   the minimum number of workers.
   *Model answer:* sort by start time, track the earliest-freeing worker in a
   min-heap keyed by finish time; reuse it if free by the next job's start,
   otherwise open a new worker — heap size at the end is the answer.

2. Why a heap instead of, say, a sorted list you scan linearly?
   *Model answer:* a heap gives O(log n) access to the single earliest-freeing
   worker without keeping the whole worker set sorted; a full sort-and-scan
   approach is more work per step for no benefit, since you only ever need the
   minimum.

3. **[Reported at Lyft]** Why not implement the heap yourself?
   *Model answer:* `heapq` is a stdlib module with zero setup cost in Python —
   hand-rolling a heap spends interview time on a solved problem instead of on the
   actual scheduling logic being graded, and it's exactly the kind of misallocation
   that's cost candidates the round before.

4. What's the boundary behavior when a job ends exactly when another starts?
   *Model answer:* treat intervals as end-exclusive (`[start, end)`) so a worker
   freeing at the same instant a new job starts can be reused — state this
   assumption explicitly since the prompt may not specify it.

5. How is this related to LeetCode 1094, Car Pooling?
   *Model answer:* both are "sweep across start/end events, track a running total,
   answer a threshold question" — Car Pooling asks whether a running passenger
   count ever exceeds capacity, this problem asks how large the running "concurrent
   jobs" count gets; same sweep-line family, different aggregate being tracked.

6. What is the time complexity of your solution, and what dominates it?
   *Model answer:* O(n log n) overall — the initial sort is O(n log n) and there are
   n heap operations at O(log n) each, so the sort and the heap work are the same
   order and neither dominates asymptotically.

7. How would you answer "how many workers are busy at time t" efficiently for many
   repeated queries?
   *Model answer:* precompute an offline sweep-line index once (sorted start/end
   events with a running count, or a Fenwick tree over compressed time), turning
   each query into O(log n) or O(1) instead of rescanning all jobs per query.

8. How would you extend this to support cancelling a job that's already running?
   *Model answer:* the free-at-time-per-worker model isn't enough on its own — track
   each worker's actual set of assigned intervals so a cancellation can recompute
   that worker's true next-free time, rather than trusting a value that assumed the
   cancelled job would still run.
