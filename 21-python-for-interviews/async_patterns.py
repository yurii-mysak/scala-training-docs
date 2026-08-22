"""Runnable demonstration of three asyncio patterns that show up together in
practice: fan-out with gather() and per-task error handling, a timeout on a
single call, and bounded concurrency with a semaphore so a fan-out never
opens more connections than a downstream service can take.

Companion to async-and-concurrency.md, section 12. Deliberately
3.10-compatible -- no TaskGroup, no asyncio.timeout() (both 3.11+, covered
in that file's section 9 instead) -- since 3.10 is this program's baseline.

Run:
    python3 async_patterns.py
"""
import asyncio


class FlakyService:
    """Stands in for a downstream call: succeeds after a delay, or raises
    for the request ids listed in `failing`. Deterministic (no real
    randomness) so the demo's output is stable across runs."""

    def __init__(self, failing=frozenset(), slow=frozenset(), base_delay=0.05):
        self._failing = failing
        self._slow = slow
        self._base_delay = base_delay

    async def fetch(self, request_id: int) -> str:
        delay = self._base_delay * (10 if request_id in self._slow else 1)
        await asyncio.sleep(delay)
        if request_id in self._failing:
            raise ValueError(f"upstream rejected request {request_id}")
        return f"result-{request_id}"


async def gather_with_error_handling(service: FlakyService, request_ids):
    """Fan out N requests concurrently. `return_exceptions=True` is the
    difference between "one bad request kills the whole batch" and "collect
    what succeeded, report what failed" -- almost always what you want, and
    it is a one-keyword decision worth naming out loud in a design round."""
    results = await asyncio.gather(
        *(service.fetch(rid) for rid in request_ids),
        return_exceptions=True,
    )
    ok, failed = [], []
    for rid, result in zip(request_ids, results):
        if isinstance(result, Exception):
            failed.append((rid, result))
        else:
            ok.append(result)
    return ok, failed


async def fetch_with_timeout(service: FlakyService, request_id: int, timeout: float):
    """asyncio.wait_for cancels the inner call and raises TimeoutError if it
    does not finish in time. 3.10-compatible. (3.11+ adds asyncio.timeout()
    as a context manager -- same idea, and it composes better across several
    awaits under one shared deadline; see async-and-concurrency.md, section
    9.)"""
    try:
        return await asyncio.wait_for(service.fetch(request_id), timeout=timeout)
    except asyncio.TimeoutError:
        return None


async def bounded_fetch_all(service: FlakyService, request_ids, max_concurrent: int):
    """Bounded concurrency: a Semaphore caps how many fetch() calls are ever
    in flight at once, no matter how many request_ids there are. Without
    this, gather() over 10,000 ids opens 10,000 connections simultaneously."""
    semaphore = asyncio.Semaphore(max_concurrent)
    in_flight = 0
    peak_in_flight = 0

    async def bounded_one(rid):
        nonlocal in_flight, peak_in_flight
        async with semaphore:
            in_flight += 1
            peak_in_flight = max(peak_in_flight, in_flight)
            try:
                return await service.fetch(rid)
            finally:
                in_flight -= 1

    results = await asyncio.gather(*(bounded_one(rid) for rid in request_ids))
    return results, peak_in_flight


async def main():
    print("=== gather() with per-task error handling ===")
    service = FlakyService(failing={2, 5})
    ok, failed = await gather_with_error_handling(service, range(6))
    print(f"succeeded: {ok}")
    print(f"failed:    {[(rid, str(exc)) for rid, exc in failed]}")

    print("\n=== timeout on a single call ===")
    slow_service = FlakyService(slow={1}, base_delay=0.05)
    fast_result = await fetch_with_timeout(slow_service, 0, timeout=0.2)
    slow_result = await fetch_with_timeout(slow_service, 1, timeout=0.1)
    print(f"request 0 (fast, under budget):    {fast_result}")
    print(f"request 1 (slow, exceeds 0.1s cap): {slow_result}")

    print("\n=== bounded concurrency with a semaphore ===")
    bounded_service = FlakyService(base_delay=0.02)
    request_ids = list(range(12))
    results, peak = await bounded_fetch_all(bounded_service, request_ids, max_concurrent=3)
    print(f"fetched {len(results)} results, peak concurrent in-flight: {peak}")
    assert peak <= 3, "semaphore should have capped concurrency at 3"
    print("semaphore held the cap")


if __name__ == "__main__":
    asyncio.run(main())
