# Speed Drills — Python Muscle Memory

> **Priority:** Required
> **Est. time:** 10 min to read; ~5-6 h spread over 2-3 weeks to run the drills
> **Track:** Both
> **HelloInterview:** none

The other files in this section are references — read once, consulted again under pressure. This one is
not a reference. It is a programme of small, timed exercises, because the actual gap is not knowledge of
Python, it is **typing speed and reach-for-it reflex** after a year where the muscle memory built up
around Lua instead. Reading [from-lua-and-scala-to-python.md](from-lua-and-scala-to-python.md) once tells
you what is different. Running these drills is what makes the difference stop costing you time in a
90-minute round.

---

## 1 · How to run a drill

1. Read the task. Do not read the idiom hint yet if you can help it — the point is training the reflex of
   reaching for the right tool, not transcribing a known answer.
2. Start a timer for the stated box. Write the function, no reference material open.
3. If you are stuck past the halfway point of the box, **look up the one construct you are missing**
   (this section's own reference files, or the stdlib docs), finish, and note it — a drill you had to look
   something up for is exactly the one to repeat in three days.
4. If you finish early, add one edge case unprompted (empty input, one element, duplicates) before moving
   on. Anticipating edge cases without being asked is graded behaviour in the real round.

Do a week's table in order once, then **redo the ones you were slow on** before moving to the next week —
repetition on the actual gaps is the entire mechanism, not novelty.

---

## 2 · Week 1 — dicts, `Counter`, sorting with keys, string parsing

| # | Task | Time box | Idiom trained |
|---|------|----------|-----------------|
| 1 | Given free text, return the 3 most common words, ties broken alphabetically | 8 min | `collections.Counter`; `sorted(key=lambda w: (-count, w))` |
| 2 | Given a list of `(name, department)` pairs, group into `dept -> [names]` | 6 min | `collections.defaultdict(list)` |
| 3 | Given `"user_id,event,ts"` log lines, build `user_id -> [events]` sorted by timestamp | 10 min | `defaultdict(list)` + `str.split` + `sorted(key=...)` |
| 4 | Parse `"k1=v1;k2=v2"` into a dict; decide and state what happens on a malformed pair | 8 min | `str.split`, dict comprehension, an explicit error-handling decision |
| 5 | Merge word counts from two documents into one combined count | 6 min | `Counter + Counter`, or `Counter.update` |
| 6 | Sort a list of dicts by score descending, then name ascending, as one `sorted` call | 8 min | Tuple sort key with a negated numeric field: `key=lambda d: (-d["score"], d["name"])` |
| 7 | Find the longest word that also has the highest frequency; state the tie-break rule you chose | 10 min | `max(..., key=...)` combined with `Counter` |
| 8 | Given a nested dict and a dotted path `"a.b.c"`, implement `get(path)` and `set(path, value)`, creating intermediate dicts on `set` | 12 min | `str.split(".")`, iterative walk — see the full problem family in [nested-path-kv.md](../17-lyft-laptop-round/07-nested-path-kv.md) |

---

## 3 · Week 2 — `heapq`, `bisect`, generators and iterators

| # | Task | Time box | Idiom trained |
|---|------|----------|-----------------|
| 1 | Find the k largest elements of a list two ways: the one-liner, and hand-rolled with a size-capped heap | 10 min | `heapq.nlargest`; a manual `heapq` of bounded size |
| 2 | Merge k already-sorted lists into one sorted iterator, without concatenating and re-sorting | 12 min | `heapq.merge`, then hand-rolled with `(value, list_idx, elem_idx)` tuples |
| 3 | Maintain a running median over a stream of numbers | 15 min | Two heaps — a negated max-heap for the lower half, a min-heap for the upper half. Worked solution in §5 |
| 4 | Given a sorted list, find the insertion point, and separately the count of elements in `[lo, hi)` | 8 min | `bisect.bisect_left`, `bisect.bisect_right` |
| 5 | Given sorted `(timestamp, value)` pairs, answer "what was the value as of time T" | 10 min | `bisect` on an extracted key list — the exact mechanism behind the versioned-KV-store problem family |
| 6 | Write a lazy Fibonacci generator, then a generator that yields sliding windows of size k over any iterable | 10 min | `yield`; `itertools.islice` or a manually managed `collections.deque(maxlen=k)` |
| 7 | Write a generator-based paginator over a large in-memory list: yield pages of size N, resuming where the last call left off | 12 min | Generator state as the cursor — directly the *stateful paginated fetch* family, the single most-reported laptop problem |
| 8 | Chain three iterables into one lazily, without materialising any of them | 6 min | `itertools.chain` |

**A job-scheduler note:** drills 2 and 3 above are the same core mechanism — a heap ordered by a due time
or priority — as the *job scheduler / interval-to-worker* laptop family. If those two drills felt slow,
that family is worth extra time; see
[05-job-scheduler-workers.md](../17-lyft-laptop-round/05-job-scheduler-workers.md) for the full problem.

---

## 4 · Week 3 — class design with dunder methods, integration drills

| # | Task | Time box | Idiom trained |
|---|------|----------|-----------------|
| 1 | Implement an immutable `Money` class: `__add__`, `__eq__`, `__lt__`, `__repr__`; raise on adding mismatched currencies | 15 min | Dunder methods; consider `@dataclass(frozen=True)` as the faster route to the same thing |
| 2 | Give a class a correct `__hash__`/`__eq__` pair so instances work as dict keys; then explain in one sentence why a *mutable* field would break it | 10 min | `__hash__`, `__eq__`, the immutability discipline hashability requires |
| 3 | Make a custom class iterable two ways: `__iter__`/`__next__` on the class itself, and a generator-based `__iter__` | 12 min | The iterator protocol |
| 4 | Give a class `__lt__` plus `functools.total_ordering`; sort a list of instances both by natural order and by `key=attrgetter(...)` | 10 min | `functools.total_ordering`, `operator.attrgetter` |
| 5 | Build an LRU cache from scratch: `get`/`put` at capacity, evicting the least-recently-used entry | 15 min | `collections.OrderedDict`, `move_to_end`, `popitem(last=False)` |
| 6 | Write a context-manager class that times a code block and prints the elapsed time on exit | 8 min | `__enter__`/`__exit__` |
| 7 | **Integration:** an in-memory KV store class with `get`/`set`/`delete` plus `begin`/`commit`/`rollback` | 15 min | Combine class design with a stack of diffs — the *in-memory KV with transactions* family, see [03-inmemory-kv-transactions.md](../17-lyft-laptop-round/03-inmemory-kv-transactions.md) |
| 8 | **Integration:** a `Trie` class with `insert`, `search`, `starts_with` | 15 min | A `TrieNode` with a `children` dict — the *typeahead/autocomplete/T9* family. Worked solution in §5 |

---

## 5 · Three worked solutions, for self-checking after the timer runs out

Do not read these before attempting the drill. They exist to check your version against, not to copy.

### 5.1 Week 1, drill 1 — top-k words

```python
import re
from collections import Counter


def top_k_words(text: str, k: int) -> list[str]:
    words = re.findall(r"[a-z']+", text.lower())
    counts = Counter(words)
    return sorted(counts, key=lambda w: (-counts[w], w))[:k]
```

### 5.2 Week 2, drill 3 — running median

```python
import heapq


class RunningMedian:
    """Two heaps: a max-heap (values negated) for the lower half, a
    min-heap for the upper half, kept within one element of each other in
    size. The median is then an O(1) read and an O(log n) update."""

    def __init__(self) -> None:
        self._lo: list[int] = []      # max-heap, values negated
        self._hi: list[int] = []      # min-heap, values as-is

    def add(self, num: int) -> None:
        heapq.heappush(self._lo, -num)
        heapq.heappush(self._hi, -heapq.heappop(self._lo))
        if len(self._hi) > len(self._lo):
            heapq.heappush(self._lo, -heapq.heappop(self._hi))

    def median(self) -> float:
        if len(self._lo) > len(self._hi):
            return float(-self._lo[0])
        return (-self._lo[0] + self._hi[0]) / 2.0
```

### 5.3 Week 3, drill 8 — Trie

```python
class TrieNode:
    def __init__(self) -> None:
        self.children: dict[str, "TrieNode"] = {}
        self.is_word = False


class Trie:
    def __init__(self) -> None:
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        node = self.root
        for ch in word:
            node = node.children.setdefault(ch, TrieNode())
        node.is_word = True

    def search(self, word: str) -> bool:
        node = self._walk(word)
        return node is not None and node.is_word

    def starts_with(self, prefix: str) -> bool:
        return self._walk(prefix) is not None

    def _walk(self, s: str) -> "TrieNode | None":
        node = self.root
        for ch in s:
            if ch not in node.children:
                return None
            node = node.children[ch]
        return node
```

```python
import unittest


class TestWorkedSolutions(unittest.TestCase):
    def test_top_k_words(self):
        text = "the cat sat on the mat the cat ran"
        self.assertEqual(top_k_words(text, 2), ["the", "cat"])

    def test_running_median(self):
        rm = RunningMedian()
        for v, expected in [(5, 5.0), (15, 10.0), (1, 5.0), (3, 4.0)]:
            rm.add(v)
            self.assertAlmostEqual(rm.median(), expected)

    def test_trie(self):
        t = Trie()
        t.insert("cat")
        t.insert("car")
        self.assertTrue(t.search("cat"))
        self.assertFalse(t.search("ca"))
        self.assertTrue(t.starts_with("ca"))
        self.assertFalse(t.starts_with("do"))


if __name__ == "__main__":
    unittest.main()
```

---

## 6 · Cadence

Three weeks, run once each, then a fourth pass repeating only the drills that took longer than their box
or needed a lookup — that fourth pass should be markedly faster, and that gap closing is the actual signal
that this worked. After that, retire this file; the goal is that
[stdlib-for-interviews.md](stdlib-for-interviews.md) and
[oop-and-design-in-python.md](oop-and-design-in-python.md) stop being references you consult mid-problem
and become things your hands already do.

---

## Interview questions

**1. Why drill Python specifically, given 13 years of engineering experience?**
Engineering judgement transfers immediately; syntax and stdlib reach-for-it reflexes do not. The laptop
round is timed and graded partly on clean code, and stopping to recall whether it is `defaultdict(list)`
or a `.setdefault` chain costs minutes that a fluent candidate does not spend — the drills exist to move
that recall from conscious to automatic before the round, not during it.

**2. Why heapq and bisect specifically, out of the whole standard library?**
Because they map directly onto the most-reported laptop-round problem families: a heap underlies job
scheduling, running statistics, and k-largest problems; `bisect` underlies the versioned/temporal KV
store family, one of the most frequently reported. Drilling the two constructs that show up across
several problem families is a better use of limited prep time than broad, shallow stdlib coverage.

**3. What is the two-heap technique for a running median, in one sentence?**
Keep the lower half of the numbers seen so far in a max-heap and the upper half in a min-heap, rebalance
after every insertion so their sizes never differ by more than one, and the median is then either the top
of the larger heap or the average of both tops — O(log n) per insertion, O(1) per read.

**4. Why practice class design with dunder methods specifically?**
The laptop round has drifted toward object-oriented design — "implement methods in a class" is a reported
prompt shape — and dunder methods are exactly the vocabulary a Python interviewer expects for making a
custom type behave like a built-in one: comparable, hashable, iterable. Getting `__eq__`/`__hash__`/`__lt__`
right without hesitation is a fluency signal on its own, independent of the problem being solved.

**5. How do you know when to stop running these drills?**
When a fourth pass over the drills you were previously slow on no longer needs a lookup and finishes
inside the time box. At that point the marginal value shifts from this file to full problem simulations —
see [17-lyft-laptop-round](../17-lyft-laptop-round/README.md) — because the remaining gap is problem-level
judgement, not construct-level recall.

**6. What is the fastest way to build k-largest elements: sort everything, or use a heap?**
Sorting the whole collection is O(n log n); a size-capped heap is O(n log k), which matters once n is much
larger than k. `heapq.nlargest(k, iterable)` already implements the heap version and is the right default
in an interview — know the complexity reasoning, and reach for the stdlib call rather than hand-rolling it
unless asked specifically to implement it.
