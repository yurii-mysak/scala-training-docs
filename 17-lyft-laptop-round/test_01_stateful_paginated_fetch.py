"""Tests for 01-stateful-paginated-fetch.py.

Run: python3 -m unittest test_01_stateful_paginated_fetch.py
"""

import importlib.util
import os
import sys
import unittest

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_MODULE_PATH = os.path.join(_THIS_DIR, "01-stateful-paginated-fetch.py")


def _load_module():
    # Solution files use hyphenated, digit-leading filenames (matching the NN-name
    # convention), which are not valid `import` targets -- load by path instead.
    # The module must be registered in sys.modules *before* exec_module() runs:
    # dataclasses resolves `from __future__ import annotations` string annotations
    # via sys.modules[cls.__module__], which is otherwise still unset at that point.
    spec = importlib.util.spec_from_file_location("stateful_paginated_fetch", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


sol = _load_module()


def make_upstream(pages):
    """pages: list of lists, e.g. [[1,2],[3,4],[5]]. Builds a fetch_page callable
    with a matching next_page_number chain, terminating in None."""

    def fetch_page(page_number):
        data = pages[page_number]
        next_page = page_number + 1 if page_number + 1 < len(pages) else None
        return {"data": data, "next_page_number": next_page}

    return fetch_page


class TestPaginatedFetcherBasics(unittest.TestCase):
    def test_single_call_within_one_page(self):
        fetcher = sol.PaginatedFetcher(make_upstream([[1, 2, 3, 4]]))
        self.assertEqual(fetcher.fetchN(2), [1, 2])

    def test_fetch_spans_multiple_pages(self):
        fetcher = sol.PaginatedFetcher(make_upstream([[1, 2], [3, 4], [5, 6]]))
        self.assertEqual(fetcher.fetchN(5), [1, 2, 3, 4, 5])

    def test_internal_buffering_across_calls(self):
        # page 0 has 4 items; fetchN(3) should leave 1 buffered for next call.
        fetcher = sol.PaginatedFetcher(make_upstream([[1, 2, 3, 4], [5, 6]]))
        self.assertEqual(fetcher.fetchN(3), [1, 2, 3])
        self.assertEqual(fetcher.fetchN(3), [4, 5, 6])

    def test_no_loss_or_duplication_across_many_small_calls(self):
        fetcher = sol.PaginatedFetcher(make_upstream([[1, 2, 3], [4, 5], [6, 7, 8, 9]]))
        collected = []
        for _ in range(9):
            collected.extend(fetcher.fetchN(1))
        self.assertEqual(collected, [1, 2, 3, 4, 5, 6, 7, 8, 9])

    def test_exhaustion_returns_fewer_than_requested(self):
        fetcher = sol.PaginatedFetcher(make_upstream([[1, 2, 3]]))
        self.assertEqual(fetcher.fetchN(10), [1, 2, 3])
        # subsequent calls after exhaustion return [] and never error
        self.assertEqual(fetcher.fetchN(5), [])
        self.assertEqual(fetcher.fetchN(1), [])

    def test_empty_page_mid_stream_is_not_treated_as_exhaustion(self):
        fetcher = sol.PaginatedFetcher(make_upstream([[1, 2], [], [3, 4]]))
        self.assertEqual(fetcher.fetchN(4), [1, 2, 3, 4])

    def test_upstream_immediately_exhausted(self):
        fetcher = sol.PaginatedFetcher(make_upstream([[]]))
        self.assertEqual(fetcher.fetchN(3), [])

    def test_fetchN_zero_returns_empty_without_touching_upstream(self):
        calls = []

        def fetch_page(page_number):
            calls.append(page_number)
            return {"data": [1, 2], "next_page_number": None}

        fetcher = sol.PaginatedFetcher(fetch_page)
        self.assertEqual(fetcher.fetchN(0), [])
        self.assertEqual(calls, [])

    def test_negative_n_raises_value_error(self):
        fetcher = sol.PaginatedFetcher(make_upstream([[1, 2]]))
        with self.assertRaises(ValueError):
            fetcher.fetchN(-1)

    def test_non_int_n_raises_type_error(self):
        fetcher = sol.PaginatedFetcher(make_upstream([[1, 2]]))
        with self.assertRaises(TypeError):
            fetcher.fetchN(2.5)

    def test_bool_n_is_rejected_even_though_bool_is_an_int_subclass(self):
        fetcher = sol.PaginatedFetcher(make_upstream([[1, 2]]))
        with self.assertRaises(TypeError):
            fetcher.fetchN(True)

    def test_exact_boundary_fetch_matches_page_size(self):
        fetcher = sol.PaginatedFetcher(make_upstream([[1, 2, 3], [4, 5, 6]]))
        self.assertEqual(fetcher.fetchN(3), [1, 2, 3])
        self.assertEqual(fetcher.fetchN(3), [4, 5, 6])
        self.assertEqual(fetcher.fetchN(1), [])


class TestReliablePaginatedFetcher(unittest.TestCase):
    def _no_op_sleep(self, _seconds):
        pass

    def _zero_rand(self):
        return 0.0

    def test_retries_then_succeeds(self):
        pages = [{"data": [1, 2], "next_page_number": None}]
        call_count = {"n": 0}

        def flaky_fetch_page(page_number):
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise sol.UpstreamError("simulated transient failure")
            return pages[page_number]

        fetcher = sol.ReliablePaginatedFetcher(
            flaky_fetch_page, sleep=self._no_op_sleep, rand=self._zero_rand
        )
        self.assertEqual(fetcher.fetchN(2), [1, 2])
        self.assertEqual(fetcher.metrics.retries, 2)
        self.assertEqual(fetcher.metrics.pages_fetched, 1)

    def test_gives_up_after_max_attempts(self):
        def always_fails(page_number):
            raise sol.UpstreamError("down")

        fetcher = sol.ReliablePaginatedFetcher(
            always_fails, max_attempts=3, sleep=self._no_op_sleep, rand=self._zero_rand
        )
        with self.assertRaises(sol.UpstreamError):
            fetcher.fetchN(1)

    def test_dedup_drops_items_seen_in_a_retried_page(self):
        # Simulates: the first attempt at page 0 actually succeeded upstream and
        # its response is what we see on "attempt 2" below; a naive retry that
        # just re-appends would duplicate items 1 and 2.
        responses = [
            {"data": [1, 2], "next_page_number": 1},  # phantom successful attempt
            {"data": [1, 2], "next_page_number": 1},  # what the retry actually returns
            {"data": [3, 4], "next_page_number": None},
        ]
        call_count = {"n": 0}

        def fetch_page(page_number):
            idx = call_count["n"]
            call_count["n"] += 1
            return responses[idx]

        fetcher = sol.ReliablePaginatedFetcher(
            fetch_page, sleep=self._no_op_sleep, rand=self._zero_rand
        )
        # Manually pull page 0 twice to model the duplicate-delivery scenario,
        # then let the normal flow continue into page 1.
        fetcher._load_next_page()  # consumes responses[0], buffers [1, 2]
        fetcher._load_next_page()  # consumes responses[1] again -> should dedup to []
        self.assertEqual(fetcher.metrics.items_deduped, 2)
        self.assertEqual(fetcher.fetchN(2), [3, 4])

    def test_metrics_track_items_returned(self):
        fetcher = sol.ReliablePaginatedFetcher(
            make_upstream_reliable([[1, 2, 3], [4, 5]]),
            sleep=self._no_op_sleep,
            rand=self._zero_rand,
        )
        fetcher.fetchN(3)
        fetcher.fetchN(2)
        self.assertEqual(fetcher.metrics.items_returned, 5)


def make_upstream_reliable(pages):
    def fetch_page(page_number):
        data = pages[page_number]
        next_page = page_number + 1 if page_number + 1 < len(pages) else None
        return {"data": data, "next_page_number": next_page}

    return fetch_page


if __name__ == "__main__":
    unittest.main()
