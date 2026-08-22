# Python for Interviews

> **Priority:** Required
> **Est. time:** 10 min
> **Track:** Both
> **HelloInterview:** none

**His primary language for the last year has been Lua; his Python is rusty.** Every laptop-round problem
family in this program is solved in Python, standard library only — this section exists to make the
language stop being the bottleneck, so the round is graded on the problem, not on syntax recall.

---

## Read in this order

| # | File | Priority | Est. time | Description |
|---|------|----------|-----------|-------------|
| 1 | [from-lua-and-scala-to-python.md](from-lua-and-scala-to-python.md) | Required | 45 min | Not a tutorial — transfer errors specifically from Lua and from Scala, and the top 20 first-day mistakes each background produces |
| 2 | [data-structures-and-idioms.md](data-structures-and-idioms.md) | Required | 45 min | `list`/`tuple`/`set`/`dict` real complexities, comprehensions, slicing, unpacking, `zip`/`enumerate`, sorting, why `+=` in a string loop is a trap, f-strings |
| 3 | [stdlib-for-interviews.md](stdlib-for-interviews.md) | Required | 60 min | The ~10% of the standard library you actually need: `collections`, `heapq` (learn it cold), `bisect`, `itertools`, `functools`, `dataclasses`/`enum`, `typing`, `re`, `json`/`csv`, `pathlib`, `sys.stdin` |
| 4 | [oop-and-design-in-python.md](oop-and-design-in-python.md) | Required | 60 min | Classes and `__init__`, properties, dunder methods as the operator-overloading/protocol toolkit, `dataclass` vs. plain class, composition over inheritance, ABCs/Protocols, context managers, iterators and generators, a full worked stateful-class example |
| 5 | [io-and-parsing.md](io-and-parsing.md) | Required | 40 min | The dominant failure mode in the laptop round is I/O handling, not algorithms: `sys.stdin` patterns, file reading, `argparse`, encoding/newlines, `csv` quirks, parsing command-string protocols |
| 6 | [testing-with-unittest.md](testing-with-unittest.md) | Required | 40 min | `unittest` as the interview default (the target machine has no `pytest`): `TestCase` structure, assertion methods, `setUp`/`tearDown`, `subTest` for table-driven cases, `unittest.mock`, running via `python3 -m unittest`, and how much to write when the clock is running |
| 7 | [speed-drills.md](speed-drills.md) | Required | 10 min to read; ~5-6 h to run | A 3-week timed drill programme — not a reference — covering `dict`/`defaultdict`/`Counter`, `heapq`, `bisect`, string parsing, dunder-method class design, generators/iterators, and sorting with keys, each drill mapped to the laptop-round problem family it feeds |

---

## If you only have an hour

Read [from-lua-and-scala-to-python.md](from-lua-and-scala-to-python.md) in full, then skim
[stdlib-for-interviews.md](stdlib-for-interviews.md)'s `heapq` and `bisect` sections. Those two are the
fastest path to not losing time to syntax during a live round — the rest of this section is depth to add
once the drills in [speed-drills.md](speed-drills.md) are underway.

## How this section fits the rest of the program

This is reference and practice; [17-lyft-laptop-round](../17-lyft-laptop-round/README.md) is where the
constructs get exercised against full, timed problem simulations, and
[15-system-design](../15-system-design/README.md)'s worked designs are written in the same
standard-library-only, `unittest`-tested style this section teaches — every code sample in that section
is fair game as extra reading practice once this section's mechanics are comfortable.

## Interview questions

**1. Where should someone fluent in Lua and Scala but rusty in Python start in this section?**
[from-lua-and-scala-to-python.md](from-lua-and-scala-to-python.md) first — it is not a Python tutorial,
it is a list of the specific transfer errors each background produces, which is a faster fix than
generic review for someone who already has 13 years of engineering judgement and just needs the syntax
and stdlib reflexes caught up.

**2. What does `defaultdict(list)` save you over a plain `dict`?**
It removes the "check if the key exists, initialise if not" branch that otherwise precedes every
grouping or accumulation operation — `d[key].append(x)` just works on a first-seen key, because the
factory function supplies the missing value automatically instead of raising `KeyError`.

**3. Why is `s += chunk` in a loop a trap for building a large string?**
Strings are immutable, so each `+=` allocates an entirely new string and copies everything seen so far
into it, making the whole loop quadratic in the final length. `"".join(parts)` (accumulating into a list
first) or an `io.StringIO` buffer are both linear, and this is exactly the kind of small idiom mistake
that costs both the performance and the clean-code portion of the grade at once.

**4. Implement a running median using two heaps.**
A max-heap (values negated, since `heapq` is min-heap-only) for the lower half of numbers seen so far, a
min-heap for the upper half, rebalanced after every insertion so the sizes never differ by more than one.
The median is then the top of the larger heap, or the average of both tops when they are equal in size —
worked and tested in [speed-drills.md §5.2](speed-drills.md).

**5. Why `unittest` instead of `pytest` for this program?**
The target machine has no `pytest` installed, and every test in this program is written to run as
`python3 -m unittest` with zero setup for exactly that reason — see
[testing-with-unittest.md](testing-with-unittest.md).

**6. Where does a Lua or Scala background actively mislead in Python, rather than just being unfamiliar?**
Two examples worth having ready: Lua's 1-based indexing and table semantics can produce silent off-by-one
errors that do not crash, they just quietly compute the wrong answer; Scala's expression-oriented,
immutable-by-default style can lead to over-engineering an interview solution with unnecessary
abstraction when a plain mutable loop would be both faster to write and more readable — and readability
is 35% of the grade. [from-lua-and-scala-to-python.md §2-3](from-lua-and-scala-to-python.md) has the full
list for both.

**7. How do you know when you have drilled enough and should stop?**
When a repeat pass over the drills that were previously slow no longer needs a stdlib lookup and finishes
inside its time box — see [speed-drills.md §6](speed-drills.md). At that point the remaining gap is
problem-level judgement, which [17-lyft-laptop-round](../17-lyft-laptop-round/README.md)'s full timed
simulations exercise, not this section.
