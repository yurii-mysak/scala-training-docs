"""17-lyft-laptop-round / 05-job-scheduler-workers

Jobs with a start time and a duration; assign each job to the minimum number of
workers such that no worker runs two overlapping jobs, and support a couple of
obvious follow-up queries against the resulting assignment.

Relation to known problems: this is LeetCode 253 (Meeting Rooms II) with "rooms"
renamed to "workers" -- sort by start time, track the earliest-freeing busy worker
in a min-heap keyed by finish time, reuse it if it's free by the time the next job
starts, otherwise open a new one. LeetCode 1094 (Car Pooling) is the same family of
technique one level up (a running-total sweep over interval start/end events,
whether via a heap or a diff array) -- worth naming if asked "what else have you
seen like this."

Python's heapq is the whole point of doing this in Python: it is a stdlib import
with no setup cost. A reported failure in this exact family was a candidate who
hand-rolled a binary heap from scratch in Go and ran out of time before finishing
the actual scheduling logic. Do not build a heap by hand in this round -- `heapq` is
free, use it.

Run directly to see a demo:
    python3 05-job-scheduler-workers.py
"""

from __future__ import annotations

import heapq
import sys
from dataclasses import dataclass
from typing import List, Sequence, Tuple


@dataclass(frozen=True)
class Job:
    start: int
    duration: int

    @property
    def end(self) -> int:
        return self.start + self.duration


class WorkerScheduler:
    """Assigns jobs, given in non-decreasing start-time order, to the minimum
    number of workers, using a min-heap of (free_at_time, worker_id) so the
    earliest-freeing worker is always O(log n) to find and reuse.

    Boundary convention: a worker that frees up exactly when the next job starts
    IS considered free for it (a job ending at t=5 and one starting at t=5 can
    share a worker) -- intervals are treated as [start, end), end-exclusive. State
    this convention explicitly; it is the single most common off-by-one in this
    family and the interviewer may not have specified it either way.
    """

    def __init__(self) -> None:
        self._heap: List[Tuple[int, int]] = []  # (free_at, worker_id), min-heap
        self._next_worker_id = 0
        self._jobs: List[Job] = []
        self._job_worker: List[int] = []
        self._last_start = float("-inf")

    def assign(self, job: Job) -> int:
        """Assigns job to a worker, returning that worker's id. Jobs must be
        submitted in non-decreasing start-time order -- if the whole batch is
        known up front, sort it first (see min_workers_needed below)."""
        if job.start < self._last_start:
            raise ValueError("jobs must be assigned in non-decreasing start-time order")
        self._last_start = job.start

        if self._heap and self._heap[0][0] <= job.start:
            _, worker_id = heapq.heappop(self._heap)
            heapq.heappush(self._heap, (job.end, worker_id))
        else:
            worker_id = self._next_worker_id
            self._next_worker_id += 1
            heapq.heappush(self._heap, (job.end, worker_id))

        self._jobs.append(job)
        self._job_worker.append(worker_id)
        return worker_id

    @property
    def worker_count(self) -> int:
        return self._next_worker_id

    def worker_of(self, job_index: int) -> int:
        """Which worker the job_index-th assigned job (0-indexed, in assignment
        order) ended up on."""
        return self._job_worker[job_index]

    def workers_busy_at(self, t: int) -> int:
        """Distinct workers with a job covering time t (job.start <= t < job.end).
        O(jobs assigned so far) -- fine at interview scale. If this needed to
        answer many repeated queries at production scale, the follow-up answer is
        an offline sweep-line index built once in O(n log n), then O(log n) or
        O(1) per query, not a fresh scan every time."""
        return len({
            self._job_worker[i]
            for i, job in enumerate(self._jobs)
            if job.start <= t < job.end
        })


def min_workers_needed(jobs: Sequence[Job]) -> int:
    """The classic Meeting-Rooms-II answer: the minimum number of workers that
    can run every job in `jobs` without any worker double-booked. Sorts internally,
    so unlike WorkerScheduler.assign this accepts jobs in any order."""
    scheduler = WorkerScheduler()
    for job in sorted(jobs, key=lambda j: j.start):
        scheduler.assign(job)
    return scheduler.worker_count


def main() -> None:
    """Reads one job per line as "start duration" (whitespace-separated) from
    stdin by default, or from a file path given as argv[1]. Prints the minimum
    worker count, then one line per job showing which worker it landed on.
    Example input:
        0 30
        5 10
        15 20
    """
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    else:
        lines = sys.stdin.read().splitlines()

    jobs = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        start_str, duration_str = line.split()
        jobs.append(Job(int(start_str), int(duration_str)))

    ordered = sorted(jobs, key=lambda j: j.start)
    scheduler = WorkerScheduler()
    for job in ordered:
        scheduler.assign(job)

    print(f"workers={scheduler.worker_count}")
    for i, job in enumerate(ordered):
        print(f"job(start={job.start}, duration={job.duration}) -> worker {scheduler.worker_of(i)}")


if __name__ == "__main__":
    main()
