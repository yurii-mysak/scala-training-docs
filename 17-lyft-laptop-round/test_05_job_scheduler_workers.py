"""Tests for 05-job-scheduler-workers.py.

Run: python3 -m unittest test_05_job_scheduler_workers.py
"""

import importlib.util
import os
import sys
import unittest

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_MODULE_PATH = os.path.join(_THIS_DIR, "05-job-scheduler-workers.py")


def _load_module():
    spec = importlib.util.spec_from_file_location("job_scheduler_workers", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


sol = _load_module()


class TestMinWorkersNeeded(unittest.TestCase):
    def test_classic_meeting_rooms_ii_example(self):
        jobs = [sol.Job(0, 30), sol.Job(5, 10), sol.Job(15, 20)]
        self.assertEqual(sol.min_workers_needed(jobs), 2)

    def test_all_disjoint_needs_one_worker(self):
        jobs = [sol.Job(0, 5), sol.Job(5, 5), sol.Job(10, 5)]
        self.assertEqual(sol.min_workers_needed(jobs), 1)

    def test_all_identical_start_needs_n_workers(self):
        jobs = [sol.Job(0, 10) for _ in range(4)]
        self.assertEqual(sol.min_workers_needed(jobs), 4)

    def test_empty_job_list(self):
        self.assertEqual(sol.min_workers_needed([]), 0)

    def test_accepts_jobs_out_of_start_order(self):
        jobs = [sol.Job(15, 20), sol.Job(0, 30), sol.Job(5, 10)]
        self.assertEqual(sol.min_workers_needed(jobs), 2)

    def test_back_to_back_jobs_share_a_worker(self):
        # end == next start: [start, end) is end-exclusive, so these should reuse.
        jobs = [sol.Job(0, 5), sol.Job(5, 5)]
        self.assertEqual(sol.min_workers_needed(jobs), 1)

    def test_zero_duration_job_frees_immediately(self):
        # [start, end) is end-exclusive, so a zero-duration job's interval [0, 0)
        # never actually occupies any instant -- its worker is free again
        # immediately, even for a second job starting at that same t=0.
        jobs = [sol.Job(0, 0), sol.Job(0, 5)]
        self.assertEqual(sol.min_workers_needed(jobs), 1)


class TestWorkerScheduler(unittest.TestCase):
    def test_assign_returns_worker_ids_and_reuses_free_workers(self):
        scheduler = sol.WorkerScheduler()
        w0 = scheduler.assign(sol.Job(0, 30))
        w1 = scheduler.assign(sol.Job(5, 10))
        w2 = scheduler.assign(sol.Job(15, 20))
        self.assertEqual((w0, w1), (0, 1))
        self.assertEqual(w2, w1)  # worker 1 freed at t=15, job 3 starts at t=15
        self.assertEqual(scheduler.worker_count, 2)

    def test_out_of_order_start_raises(self):
        scheduler = sol.WorkerScheduler()
        scheduler.assign(sol.Job(10, 5))
        with self.assertRaises(ValueError):
            scheduler.assign(sol.Job(5, 5))

    def test_worker_of_matches_assignment_order(self):
        scheduler = sol.WorkerScheduler()
        scheduler.assign(sol.Job(0, 5))
        scheduler.assign(sol.Job(1, 5))
        self.assertEqual(scheduler.worker_of(0), 0)
        self.assertEqual(scheduler.worker_of(1), 1)

    def test_workers_busy_at_counts_overlapping_workers(self):
        scheduler = sol.WorkerScheduler()
        scheduler.assign(sol.Job(0, 30))   # worker 0, busy [0, 30)
        scheduler.assign(sol.Job(5, 10))   # worker 1, busy [5, 15)
        scheduler.assign(sol.Job(15, 20))  # worker 1 again, busy [15, 35)
        self.assertEqual(scheduler.workers_busy_at(7), 2)   # workers 0 and 1
        self.assertEqual(scheduler.workers_busy_at(20), 2)  # workers 0 and 1
        self.assertEqual(scheduler.workers_busy_at(40), 0)  # nothing running

    def test_job_boundary_is_end_exclusive_for_busy_query(self):
        scheduler = sol.WorkerScheduler()
        scheduler.assign(sol.Job(0, 5))  # busy [0, 5)
        self.assertEqual(scheduler.workers_busy_at(5), 0)  # already free at t=5
        self.assertEqual(scheduler.workers_busy_at(4), 1)


class TestJob(unittest.TestCase):
    def test_end_property(self):
        job = sol.Job(start=10, duration=5)
        self.assertEqual(job.end, 15)


if __name__ == "__main__":
    unittest.main()
