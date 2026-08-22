"""17-lyft-laptop-round / 01-stateful-paginated-fetch

Part 1: fetchN(n) over a paginated upstream that hands back one page at a time.
Part 2: same contract, but the upstream is unreliable -- add retry with backoff,
         dedup, and metrics.

Relation to a known problem: this is the "read N given a page-at-a-time upstream"
family, structurally the same bug surface as LeetCode 158 (Read N Characters Given
Read4 II - Call multiple times). There, read4() hands back up to 4 characters per
call and you must buffer the leftover across repeated read(n) calls without losing
or repeating characters. Here, fetch_page() hands back a page of items plus a
"next page" token instead of a fixed 4-character chunk, but the state-machine shape
-- an internal buffer, a cursor into it, and a "have we reached the end" flag that
all persist across calls -- is identical.

Run directly to see a demo against an in-memory fake upstream:
    python3 01-stateful-paginated-fetch.py
"""

from __future__ import annotations

import random
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set

Page = Dict[str, Any]  # {"data": [...], "next_page_number": Optional[int]}
FetchPageFn = Callable[[int], Page]


# --------------------------------------------------------------------------- #
# Part 1 -- fetchN over a well-behaved upstream
# --------------------------------------------------------------------------- #


class PaginatedFetcher:
    """Wraps a paginated upstream and exposes fetchN(n): return the next n items
    in source order, across as many separate fetchN() calls as the caller likes.

    Upstream contract:
        fetch_page(page_number) -> {"data": [...], "next_page_number": int | None}

    next_page_number is None once there is nothing left to fetch. A page CAN be
    empty (data == []) while next_page_number is still not None -- that means
    "keep going", not "stop". Treating an empty page as end-of-stream is the most
    common bug in this family.
    """

    def __init__(self, fetch_page: FetchPageFn, start_page: int = 0) -> None:
        self._fetch_page = fetch_page
        self._next_page_number: Optional[int] = start_page
        self._buffer: List[Any] = []
        self._buffer_pos = 0

    def fetchN(self, n: int) -> List[Any]:
        """Returns up to n items, in source order. Returns fewer than n only when
        the upstream is exhausted -- that is how a caller detects end-of-stream;
        this never raises for "not enough items left".
        """
        if not isinstance(n, int) or isinstance(n, bool):
            raise TypeError(f"n must be an int, got {type(n).__name__}")
        if n < 0:
            raise ValueError("n must be >= 0")

        result: List[Any] = []
        while len(result) < n and not self._is_exhausted():
            if not self._has_buffered_items():
                self._load_next_page()
                continue
            take = min(n - len(result), len(self._buffer) - self._buffer_pos)
            result.extend(self._buffer[self._buffer_pos:self._buffer_pos + take])
            self._buffer_pos += take
        return result

    def _has_buffered_items(self) -> bool:
        return self._buffer_pos < len(self._buffer)

    def _is_exhausted(self) -> bool:
        return self._next_page_number is None and not self._has_buffered_items()

    def _load_next_page(self) -> None:
        page = self._fetch_page(self._next_page_number)
        self._buffer = list(page.get("data", []))
        self._buffer_pos = 0
        self._next_page_number = page.get("next_page_number")


# --------------------------------------------------------------------------- #
# Part 2 -- the upstream is unreliable: retry + backoff, dedup, metrics
# --------------------------------------------------------------------------- #


class UpstreamError(Exception):
    """Raised by a flaky fetch_page to simulate a transient upstream failure."""


def with_retry(
    fetch_page: FetchPageFn,
    max_attempts: int = 4,
    base_delay: float = 0.05,
    sleep: Callable[[float], None] = time.sleep,
    rand: Callable[[], float] = random.random,
    on_retry: Optional[Callable[[int, int, Exception], None]] = None,
) -> FetchPageFn:
    """Wraps a flaky fetch_page with exponential backoff + jitter.

    Retries UpstreamError up to max_attempts times before giving up and letting
    it propagate. sleep/rand are injectable so tests run instantly instead of
    waiting on real delays -- always design retry logic this way, it is the
    difference between a test suite that runs in milliseconds and one that
    takes minutes.
    """

    def wrapped(page_number: int) -> Page:
        last_error: Optional[Exception] = None
        for attempt in range(max_attempts):
            try:
                return fetch_page(page_number)
            except UpstreamError as exc:
                last_error = exc
                if attempt == max_attempts - 1:
                    break
                if on_retry is not None:
                    on_retry(page_number, attempt, exc)
                delay = base_delay * (2 ** attempt) * (1 + rand())
                sleep(delay)
        raise UpstreamError(
            f"page {page_number} failed after {max_attempts} attempts"
        ) from last_error

    return wrapped


@dataclass
class FetchMetrics:
    pages_fetched: int = 0
    retries: int = 0
    items_returned: int = 0
    items_deduped: int = 0


class ReliablePaginatedFetcher(PaginatedFetcher):
    """Part 2. Same fetchN(n) contract as PaginatedFetcher, but assumes:

    1. fetch_page can raise UpstreamError transiently (network blip, timeout) --
       handled by wrapping it in with_retry.
    2. A retried page can hand back items already seen, because the *response*
       to a successful attempt can be lost in flight even though the attempt
       itself succeeded upstream -- handled by item-level dedup via id_fn.
    3. Someone will ask "how do you know this is working in production" --
       handled by exposing .metrics.
    """

    def __init__(
        self,
        fetch_page: FetchPageFn,
        start_page: int = 0,
        max_attempts: int = 4,
        id_fn: Callable[[Any], Any] = lambda item: item,
        sleep: Callable[[float], None] = time.sleep,
        rand: Callable[[], float] = random.random,
    ) -> None:
        self.metrics = FetchMetrics()
        self._id_fn = id_fn
        self._seen: Set[Any] = set()
        reliable_fetch = with_retry(
            fetch_page,
            max_attempts=max_attempts,
            sleep=sleep,
            rand=rand,
            on_retry=lambda *_: self._bump_retry(),
        )
        super().__init__(reliable_fetch, start_page=start_page)

    def _bump_retry(self) -> None:
        self.metrics.retries += 1

    def _load_next_page(self) -> None:
        super()._load_next_page()
        self.metrics.pages_fetched += 1
        deduped: List[Any] = []
        for item in self._buffer:
            key = self._id_fn(item)
            if key in self._seen:
                self.metrics.items_deduped += 1
                continue
            self._seen.add(key)
            deduped.append(item)
        self._buffer = deduped
        self._buffer_pos = 0

    def fetchN(self, n: int) -> List[Any]:
        items = super().fetchN(n)
        self.metrics.items_returned += len(items)
        return items


# --------------------------------------------------------------------------- #
# main() -- stdin by default, or pass a file path as argv[1]
# --------------------------------------------------------------------------- #


def _demo_upstream(page_size: int = 4, total_items: int = 17) -> FetchPageFn:
    """An in-memory fake upstream, standing in for the real network call. Real
    interview upstreams are usually handed to you as a function just like this."""
    items = list(range(1, total_items + 1))

    def fetch_page(page_number: int) -> Page:
        start = page_number * page_size
        chunk = items[start:start + page_size]
        next_page = page_number + 1 if start + page_size < len(items) else None
        return {"data": chunk, "next_page_number": next_page}

    return fetch_page


def main() -> None:
    """Demonstrates fetchN driven by a line of integers as the "n" values to
    request, one fetchN(n) call per number.

    Input, from stdin by default, or from a file path given as argv[1] --
    confirm which one the interviewer actually wants before you build either;
    this file supports both so the choice costs you nothing either way:
        5 5 5 5

    Output: one line per fetchN(n) call, the items returned, space separated.
    """
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            raw = f.read()
    else:
        raw = sys.stdin.read()

    n_values = [int(tok) for tok in raw.split()]
    fetcher = PaginatedFetcher(_demo_upstream())
    for n in n_values:
        batch = fetcher.fetchN(n)
        print(" ".join(str(x) for x in batch))


if __name__ == "__main__":
    main()
