# Testing with `unittest`

> **Priority:** Required
> **Est. time:** 40 min
> **Track:** Both
> **HelloInterview:** none

**The target machine has no `pytest`.** Every test in this program, and every test you write in the
laptop round, runs as `python3 -m unittest`. This file is the mechanics of writing tests fast in that
module — not whether to write them or how many, which
[17-lyft-laptop-round/00-protocol.md §4–§5](../17-lyft-laptop-round/00-protocol.md) already answers and
this file does not repeat.

---

## 1 · `TestCase` structure

```python
import unittest


class TestThing(unittest.TestCase):
    def test_does_the_thing(self):
        self.assertEqual(1 + 1, 2)


if __name__ == "__main__":
    unittest.main()
```

Three rules that matter more than they look like they should:

- **Method names must start with `test`** — discovery is name-based, not decorator-based like pytest.
  A typo (`tset_foo`) silently produces zero failures, not an error, which is the single most common
  "why did my test not run" bug under time pressure.
- **One class per unit under test is the default organisation.** For a laptop-round-sized project, one
  `TestX` class per class or module you wrote is enough structure; do not invent a deeper hierarchy.
- **`if __name__ == "__main__": unittest.main()`** makes the file runnable directly with
  `python3 file.py`, in addition to `python3 -m unittest`, satisfying this program's own rule that every
  `.py` file runs both ways.

---

## 2 · Assertion methods

| Method | Use it for | Why not just `assertTrue(a == b)` |
|--------|--------------|---------------------------------------|
| `assertEqual(a, b)` | The default — value equality | On failure, prints an actual **diff** of `a` and `b`; `assertTrue(a == b)` on failure prints only `False is not true`, which tells you nothing about *why* |
| `assertNotEqual(a, b)` | Inequality | Same diff benefit |
| `assertIs(a, b)` / `assertIsNot` | Identity, not equality — `is`, not `==` | Use for `None` checks and singleton/sentinel checks specifically |
| `assertIsNone(x)` / `assertIsNotNone` | The common `None` case | Reads better than `assertIs(x, None)` |
| `assertIn(a, b)` / `assertNotIn` | Membership | Diff shows the container, not just `False` |
| `assertTrue(x)` / `assertFalse` | Genuine booleans only — a condition, not a comparison | Reach for a more specific assertion whenever one exists; this is the fallback, not the default |
| `assertRaises(ExcType)` | Expecting an exception | Use as a context manager (below), not the older callable form — it is more readable and lets you assert on the exception object |
| `assertAlmostEqual(a, b, places=7)` | Floating-point comparison | Never use `assertEqual` on floats — accumulated error makes exact equality flaky |
| `assertListEqual` / `assertDictEqual` / `assertSetEqual` | Container equality with a container-shaped diff | `assertEqual` actually dispatches to these automatically when both arguments are the same container type — calling the specific one explicitly is rarely necessary, but knowing they exist explains why a list-vs-list failure message looks the way it does |

```python
with self.assertRaises(ValueError) as ctx:
    parse_config("not valid")
self.assertIn("line 1", str(ctx.exception))    # assert on the exception's content too, not just its type
```

**The general rule: pick the most specific assertion available.** It is not pedantry — the failure
message is the entire value of a test that fails during a live round with the interviewer watching. A
diff you can read in one second beats a boolean you have to debug.

---

## 3 · `setUp`, `tearDown`, and the class-level versions

```python
class TestWithFixture(unittest.TestCase):
    def setUp(self):
        self.store = {}                 # fresh state before EVERY test method

    def tearDown(self):
        pass                            # close files, delete temp dirs, etc. -- runs even if the test failed

    @classmethod
    def setUpClass(cls):
        cls.expensive_thing = build_once()   # shared across all tests in the class, built once
```

`setUp` runs before every single test method — use it for anything cheap that a test should not share
with another test (mutable state, especially). `setUpClass` runs once for the whole class — reach for it
only when the setup is genuinely expensive and safe to share, because shared state between tests is
exactly the kind of coupling that makes one test's failure mysteriously break another.

---

## 4 · `subTest` for table-driven cases

The single highest-leverage technique in this file for laptop-round speed: cover many cases in the time
it takes to write one loop.

```python
class TestIsPalindrome(unittest.TestCase):
    def test_cases(self):
        cases = [
            ("racecar", True),
            ("hello", False),
            ("", True),
            ("a", True),
            ("Aa", False),          # case-sensitive by design -- worth a case of its own
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(is_palindrome(text), expected)
```

**Why `subTest` and not a bare `for` loop with asserts:** without it, the first failing case stops the
test immediately and every later case in the loop goes unchecked in that run — you fix one bug, rerun,
and discover the *next* failure one at a time. `subTest` reports every failing case from a single run,
labelled by the `text=` value you passed it, which is a large speed advantage when time is the scarce
resource. This is the direct, table-driven answer to "clean code" grading buying more edge-case coverage
per line typed than five separate `test_` methods would.

---

## 5 · Mocking with `unittest.mock`

### 5.1 `Mock` and `MagicMock`

```python
from unittest.mock import Mock

fetch = Mock(return_value="ok")            # always returns "ok"
fetch()                                     # -> "ok"
fetch.assert_called_once()

flaky = Mock(side_effect=[ConnectionError(), "ok"])   # fails once, then succeeds
retrying = Mock(side_effect=ConnectionError("down"))  # fails on every call
```

`side_effect` as a **list** yields the next item per call (an exception *instance* in the list is
**raised**, not returned); `side_effect` as a **single exception** is raised on **every** call. That
distinction is the part worth having memorised rather than re-deriving live — see §6's worked example.

### 5.2 `patch` — replacing something the code under test imports

```python
from unittest.mock import patch

with patch("mymodule.requests.get") as mock_get:
    mock_get.return_value.status_code = 200
    ...
```

Patch the name **where it is looked up**, not where it is defined — `mymodule.requests.get`, because
`mymodule` did `import requests` and looks it up on its own module object at call time. This single
detail is responsible for most "my patch did not work" confusion.

### 5.3 The better fix, most of the time: do not mock at all

**The cleanest way to avoid needing a mock for time, randomness, or an external clock is dependency
injection** — pass `now: float`, `sleep`, or `rng` in as a parameter instead of reading `time.time()` or
calling `time.sleep()` directly inside the function. Every stateful class in
[15-system-design](../15-system-design/README.md)'s worked designs is written this way specifically so
its tests need no mocking at all — a `ConnectionRegistry` or `TokenBucket` takes `now` as an argument and
a test just passes whatever value it wants. **Reach for `unittest.mock` when the dependency is a real
external system you cannot restructure away** (an HTTP client, a database call, a file on disk) — which
in a from-scratch laptop-round project is less often than it first appears, because you own the whole
call graph and can inject instead of intercept.

---

## 6 · A worked example putting it together

```python
import unittest
from unittest.mock import Mock


def fetch_with_retry(fetch, max_attempts, sleep):
    """Retries fetch() up to max_attempts times, sleeping between attempts.
    `fetch` and `sleep` are injected so tests need no real I/O or real time."""
    last_exc = None
    for attempt in range(max_attempts):
        try:
            return fetch()
        except ConnectionError as exc:
            last_exc = exc
            if attempt < max_attempts - 1:
                sleep(attempt)
    raise last_exc


class TestFetchWithRetry(unittest.TestCase):
    def setUp(self):
        self.sleep = Mock()

    def test_succeeds_on_first_try_without_sleeping(self):
        fetch = Mock(return_value="ok")
        self.assertEqual(fetch_with_retry(fetch, max_attempts=3, sleep=self.sleep), "ok")
        self.sleep.assert_not_called()

    def test_retries_then_succeeds(self):
        fetch = Mock(side_effect=[ConnectionError(), ConnectionError(), "ok"])
        result = fetch_with_retry(fetch, max_attempts=3, sleep=self.sleep)
        self.assertEqual(result, "ok")
        self.assertEqual(self.sleep.call_count, 2)

    def test_exhausts_attempts_and_raises(self):
        fetch = Mock(side_effect=ConnectionError("down"))
        with self.assertRaises(ConnectionError):
            fetch_with_retry(fetch, max_attempts=3, sleep=self.sleep)
        self.assertEqual(fetch.call_count, 3)

    def test_table_driven_attempt_counts(self):
        for max_attempts, expected_calls in [(1, 1), (2, 2), (5, 5)]:
            with self.subTest(max_attempts=max_attempts):
                fetch = Mock(side_effect=ConnectionError("down"))
                sleep = Mock()
                with self.assertRaises(ConnectionError):
                    fetch_with_retry(fetch, max_attempts=max_attempts, sleep=sleep)
                self.assertEqual(fetch.call_count, expected_calls)


if __name__ == "__main__":
    unittest.main()
```

Four tests, each earning its place: the happy path, the recovery path, the total-failure path, and one
`subTest`-driven sweep over attempt counts that would otherwise be three more near-duplicate methods.
`fetch` and `sleep` are both mocked because they are genuinely external; `max_attempts` and the retry
logic itself are not mocked, because that is the thing under test.

---

## 7 · Running it

```
python3 -m unittest path/to/test_module.py          # one file
python3 -m unittest path.to.test_module              # one file, module syntax
python3 -m unittest path.to.test_module.TestClass.test_method   # one test
python3 -m unittest discover -s . -p "test_*.py"     # everything matching the pattern
python3 -m unittest -v ...                            # verbose: one line per test, not just a dot
```

Run with `-v` by default while developing — a dot per test tells you nothing when something hangs; a
verbose run shows you exactly which test was running when it did.

---

## 8 · How much to write when the clock is running

The full answer is [00-protocol.md §4–§5](../17-lyft-laptop-round/00-protocol.md): get it correct, then
clean, **then** test — three or four cases covering the edge cases you already stated out loud beats a
large suite you did not have time to finish, given the grading is correctness 45% / clean code 35% /
performance 20%, and tests are evidence for the second number, not a fourth category of their own.

**The unittest-specific lever this file adds:** `subTest` (§4) is how you make that time budget stretch
further — the same handful of minutes that would write two or three separate `test_` methods can instead
write one `subTest` loop covering five or six cases, which is strictly more edge-case evidence for the
same typing time. When time is short, prefer one well-chosen table of cases over several hand-written
methods that each test one thing.

---

## Interview questions

**1. Why `unittest` instead of `pytest` for this round?**
The target machine has no `pytest` installed, and the round is graded on what you can demonstrate running
in that environment — `python3 -m unittest` is guaranteed to work with zero setup, which matters more than
`pytest`'s nicer assertion introspection when the clock is running.

**2. What is the difference between `assertEqual(a, b)` and `assertTrue(a == b)`?**
Behaviourally nothing — both fail when `a != b`. The difference is entirely in the failure message:
`assertEqual` prints a diff of the two values, `assertTrue` prints only that the boolean was false. Given
that the failure message is often the only debugging information available live, the specific assertion
is the better default.

**3. What does `subTest` buy you over a plain loop with asserts inside it?**
Without it, the first failing iteration stops the whole test method, so a run only ever reports one
failure at a time even if several cases are broken. `subTest` lets every case in the loop run and report
independently, labelled by whatever keyword you pass it, which surfaces every failure from a single run
instead of one bug-fix cycle per case.

**4. When should you use `setUp` versus `setUpClass`?**
`setUp` runs before every test method and should hold anything mutable, because sharing it across tests
would let one test's mutation leak into another's result. `setUpClass` runs once for the whole class and
is for something expensive and genuinely safe to share — reach for it only when `setUp`'s per-test cost
is actually a problem, not by default.

**5. How does `Mock(side_effect=...)` behave differently as a list versus a single exception?**
A list is consumed one item per call, and an exception instance inside that list is raised on the call
that reaches it rather than returned. A single exception instance or class as `side_effect` is raised on
*every* call to that mock. Mixing the two up is the most common live bug when writing a retry test.

**6. When would you avoid `unittest.mock` entirely?**
Whenever the dependency can be restructured into a parameter instead — pass `now`, `sleep`, or a random
generator into the function rather than reading a global clock inside it. That turns a mocking problem
into a plain function argument, which is simpler to write, simpler to read, and needs no patch target at
all. Mocking earns its place for dependencies that are genuinely external and cannot be passed in, like a
real network call.

**7. How much testing should you write in a 90-minute round?**
Three or four cases covering the edge cases already discussed with the interviewer, written after the
solution is correct and cleaned up, not before — tests are part of the 35% clean-code signal, not a
separate grading category, so a small, well-chosen set beats an unfinished large one. `subTest` is the
tactical way to fit more edge-case coverage into that same time budget.

**8. What does `patch("mymodule.requests.get")` actually patch, and what is the common mistake?**
It replaces the `get` attribute on `mymodule`'s own reference to the `requests` module, not on the
`requests` module globally. The common mistake is patching `requests.get` directly, which does nothing if
`mymodule` already imported `requests` and looks up `get` on its own copy of that reference at call time —
patch where the name is *looked up*, not where it was *defined*.
