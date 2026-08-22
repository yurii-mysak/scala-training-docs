# Standard Library for Interviews

> **Priority:** Required
> **Est. time:** 60 min
> **Track:** Both
> **HelloInterview:** DSA Track → Heap

You will not need 90% of the Python standard library in a laptop round. You will need about
twelve names from it, cold, without looking them up. This file is those twelve, in the order
they come up, with the two or three sharp edges each one has. `heapq` gets more space than
anything else here on purpose — see §2.

Everything below is standard library only, Python 3.10-compatible, and has been run as shown.

---

## 1 · `collections`

| Name | What it replaces | Reach for it when |
|------|-------------------|--------------------|
| `defaultdict(factory)` | `if k not in d: d[k] = default` boilerplate | building a graph, grouping, counting with custom logic |
| `Counter` | manual frequency-counting loops | "top-k frequent", anagram/histogram problems |
| `deque` | a list used as a queue or a fixed window | BFS, sliding window, anything popping from the front |
| `namedtuple` | a bare tuple, or a class with no behavior | a lightweight, readable record you'll compare/print |

```python
from collections import defaultdict, Counter, deque, namedtuple

# defaultdict: adjacency list without existence checks
edges = [(1, 2), (1, 3), (2, 3)]
graph = defaultdict(list)
for a, b in edges:
    graph[a].append(b)
    graph[b].append(a)
# CAUTION: graph[x] for a missing x auto-creates the key (`4 in graph` becomes True
# after you merely read graph[4]). Use `graph.get(x, [])` if you need a read that
# doesn't have that side effect.

# Counter: frequencies, top-k, and set-like arithmetic
c = Counter("mississippi")
print(c.most_common(2))        # [('i', 4), ('s', 4)]
print(c["z"])                  # 0 -- missing key returns 0, no KeyError (unlike a plain dict)
print("z" in c)                # False -- unlike defaultdict, reading does NOT insert the key
c2 = Counter("miss")
print(c - c2)                  # Counter subtraction: keeps only positive counts

# deque: O(1) both ends; `maxlen` gives you a ready-made fixed-size window
window = deque(maxlen=3)
for x in [1, 2, 3, 4, 5]:
    window.append(x)           # oldest falls off the left automatically
print(list(window))            # [3, 4, 5]

# namedtuple: an immutable record with named fields, still a real tuple
Point = namedtuple("Point", "x y")
p = Point(1, 2)
print(p.x, p[0], p == (1, 2))  # 1 1 True
print(p._replace(y=9))         # Point(x=1, y=9) -- returns a new instance, doesn't mutate
```

For a class-based record with methods, use `typing.NamedTuple` or `@dataclass` instead — see
[oop-and-design-in-python.md](oop-and-design-in-python.md). For an LRU cache, `OrderedDict`'s
`move_to_end`/`popitem(last=False)` is the standard tool — full worked example in that same file.

---

## 2 · `heapq` — learn this one cold

Candidates lose rounds hand-rolling heap logic from scratch — reimplementing sift-up/sift-down
by hand in a language that makes you — when the language they're actually being graded in gives
you a working binary heap for free, in one import. Do not be the candidate who spends fifteen
minutes reinventing `heapq`.

**The one thing to memorize: `heapq` is a min-heap, and only a min-heap.** There is no
`max_heapify`, no `reverse=True` kwarg. Everything else in this section is a workaround for
that one fact.

```python
import heapq

# heapify: O(n), turns a list into a valid heap IN PLACE
nums = [5, 1, 8, 2, 9, 3]
heapq.heapify(nums)
print(heapq.heappop(nums))         # 1 -- smallest, always at index 0 after heapify

# push/pop: O(log n) each
heapq.heappush(nums, 0)
print(heapq.heappop(nums))         # 0
```

### 2.1 The min-heap-only workaround: negate on the way in and out

To get a **max-heap**, push negated values and negate again when you pop. Nothing fancier exists.

```python
import heapq

nums = [5, 1, 8, 2, 9, 3]
max_heap = [-n for n in nums]
heapq.heapify(max_heap)
top3 = [-heapq.heappop(max_heap) for _ in range(3)]
print(top3)                        # [9, 8, 5]
```

If you just need the top-k or bottom-k values and don't need an ongoing heap, skip the
negation dance entirely — `heapq` has both directions built in:

```python
import heapq

nums = [5, 1, 8, 2, 9, 3]
print(heapq.nlargest(3, nums))     # [9, 8, 5]  -- O(n log k), no manual negation
print(heapq.nsmallest(3, nums))    # [1, 2, 3]
print(heapq.nlargest(2, nums, key=lambda x: -x))   # key= works too, for custom priority
```

### 2.2 The tuple-comparison trick: priority queues with a tie-breaker

`heapq` orders tuples element-by-element, exactly like Python's normal tuple comparison. Push
`(priority, payload)` and you have a priority queue for free. The trap: if two priorities tie,
Python moves on to compare the **second** element — and if that's a dict, another custom
object, or anything else without a defined `<`, you get a crash mid-round:

```python
import heapq

pq = []
heapq.heappush(pq, (2, {"task": "b"}))
heapq.heappush(pq, (1, {"task": "a"}))
heapq.heappush(pq, (1, {"task": "also-a"}))   # SAME priority as the entry above
heapq.heappop(pq)   # TypeError: '<' not supported between instances of 'dict' and 'dict'
```

Fix: push `(priority, tie_breaker, payload)`, where `tie_breaker` is a strictly-increasing
counter. Two entries never have the same `(priority, tie_breaker)` pair, so the payload is
never compared:

```python
import heapq, itertools

counter = itertools.count()        # 0, 1, 2, ... forever
pq = []
heapq.heappush(pq, (2, next(counter), {"task": "b"}))
heapq.heappush(pq, (1, next(counter), {"task": "a"}))
heapq.heappush(pq, (1, next(counter), {"task": "also-a"}))

while pq:
    priority, _, payload = heapq.heappop(pq)
    print(priority, payload["task"])
# 1 a
# 1 also-a   <- tie broken by insertion order, never touches the dicts
# 2 b
```

The same trick, with no `itertools` import, using `id(payload)` as the tie-breaker when you
don't care about insertion order, only that ties never crash:

```python
heapq.heappush(pq, (priority, id(payload), payload))
```

### 2.3 Other `heapq` you'll actually use

```python
import heapq

# k-way merge of already-sorted iterables -- the mechanism behind external/merge sort
merged = list(heapq.merge([1, 4, 7], [2, 3, 9], [0, 5]))
print(merged)                      # [0, 1, 2, 3, 4, 5, 7, 9]

# a heap of your own objects works directly if the class defines ordering
from dataclasses import dataclass, field

@dataclass(order=True)
class Task:
    priority: int
    name: str = field(compare=False)   # excluded from comparison -> no tie-break crash

pq = []
for t in [Task(3, "low"), Task(1, "high"), Task(2, "mid")]:
    heapq.heappush(pq, t)
print(heapq.heappop(pq).name)      # high
```

Complexity to say out loud if asked: `heapify` is `O(n)` (not `O(n log n)` — a common
overstatement), `heappush`/`heappop` are `O(log n)`, `nlargest(k, ...)`/`nsmallest(k, ...)` are
`O(n log k)`. Cross-reference:
[Binary Heap Summary](../08-algorithms-and-data-structures/binary_heap_summary.md).

---

## 3 · `bisect` — binary search on a sorted sequence

```python
import bisect

sorted_list = [1, 3, 3, 5, 7]
bisect.bisect_left(sorted_list, 3)     # 1  -- leftmost insertion point for 3
bisect.bisect_right(sorted_list, 3)    # 3  -- rightmost insertion point for 3
bisect.bisect_left(sorted_list, 4)     # 3  -- 4 isn't present; this is where it WOULD go

bisect.insort(sorted_list, 4)          # insert while keeping the list sorted, O(n) (shift cost)
print(sorted_list)                     # [1, 3, 3, 4, 5, 7]
```

`bisect_left` vs `bisect_right` only differ when the target is already present: `_left` gives
you the first valid insertion point (before duplicates), `_right` gives you the last (after
duplicates). For "does this exist / find its first index" use `bisect_left` and check
`i < len(a) and a[i] == target`.

Since 3.10, `bisect` takes a `key=` argument so you can binary-search parallel data without
building a separate list of keys:

```python
import bisect

people = sorted([("amy", 30), ("bob", 25), ("cory", 40)], key=lambda p: p[1])
i = bisect.bisect_left(people, 30, key=lambda p: p[1])
print(people[i])                       # ('amy', 30)
```

`bisect` requires the sequence already be sorted — it does not check, it just silently gives
you a wrong-looking answer if it isn't.

---

## 4 · `itertools` — the six you actually reach for

```python
import itertools

# chain: concatenate iterables lazily, including a list of lists
list(itertools.chain([1, 2], [3], [4, 5]))          # [1, 2, 3, 4, 5]
list(itertools.chain.from_iterable([[1, 2], [3]]))  # [1, 2, 3]

# product: cartesian product -- nested loops without nesting the loops
list(itertools.product("ab", "12"))        # [('a','1'), ('a','2'), ('b','1'), ('b','2')]
list(itertools.product(range(2), repeat=3))  # all 8 length-3 binary tuples

# combinations: choose k, order doesn't matter, no repeats (permutations: order matters)
list(itertools.combinations([1, 2, 3], 2))  # [(1,2), (1,3), (2,3)]
list(itertools.permutations([1, 2], 2))     # [(1,2), (2,1)]

# groupby: groups only CONSECUTIVE equal keys -- sort first, or this silently does the wrong thing
data = [("a", 1), ("b", 2), ("a", 3)]
[k for k, _ in itertools.groupby(data, key=lambda kv: kv[0])]   # ['a', 'b', 'a'] -- THREE groups!
data.sort(key=lambda kv: kv[0])
{k: [v for _, v in g] for k, g in itertools.groupby(data, key=lambda kv: kv[0])}
# {'a': [1, 3], 'b': [2]}   -- correct, only after sorting

# accumulate: running totals, i.e. prefix sums, for free
list(itertools.accumulate([1, 2, 3, 4]))               # [1, 3, 6, 10]
list(itertools.accumulate([3, 1, 4], initial=0))       # [0, 3, 4, 8]
list(itertools.accumulate([1, 5, 2, 4], func=max))     # running max: [1, 5, 5, 5]

# islice: slice an iterator (e.g. stdin, or an infinite generator) without materializing it
def naturals():
    n = 0
    while True:
        yield n
        n += 1
list(itertools.islice(naturals(), 5))      # [0, 1, 2, 3, 4]
list(itertools.islice(naturals(), 2, 5))   # [2, 3, 4]
```

3.10 bonus, worth knowing exists: `itertools.pairwise([1, 2, 3, 4])` → `[(1,2), (2,3), (3,4)]`,
consecutive pairs without a manual `zip(xs, xs[1:])`.

---

## 5 · `functools`

```python
import functools

# lru_cache: memoization in one line -- turns exponential recursion into linear
@functools.lru_cache(maxsize=None)
def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)
fib(35)     # fast; without the decorator this recomputes ~2^35 times

# cmp_to_key: sort by a custom comparator instead of a key function --
# needed when the ordering isn't a simple "extract a value and sort by it"
# (classic case: LeetCode 179, arrange numbers to form the largest concatenation)
def compare(a, b):
    ab, ba = a + b, b + a
    return -1 if ab > ba else (1 if ab < ba else 0)

nums = ["3", "30", "34", "5", "9"]
nums.sort(key=functools.cmp_to_key(compare))
print("".join(nums))       # '9534330'

# reduce: fold a sequence down to one value
functools.reduce(lambda acc, x: acc * x, [1, 2, 3, 4], 1)   # 24 (factorial-style fold)

# partial: bind some arguments now, call with the rest later
def power(base, exp):
    return base ** exp
square = functools.partial(power, exp=2)
square(5)   # 25
```

`functools.cache` (unparameterized, `maxsize=None` built in) exists from 3.9 — `lru_cache` works
everywhere back to 3.2 and is the safer one to type from memory.

---

## 6 · `dataclasses` and `enum` — quick reference

Full treatment, including the `__eq__`/`__hash__`/`order=True` interplay and a worked class
design, is in [oop-and-design-in-python.md](oop-and-design-in-python.md). Here's the shape:

```python
from dataclasses import dataclass, field
import enum

@dataclass(order=True, frozen=True)
class Point:
    x: int
    y: int

class Status(enum.Enum):
    PENDING = "pending"
    DONE = "done"

Status.PENDING.value       # 'pending'
Status.PENDING == "pending"   # False! -- an Enum member is not equal to its raw value
Status("pending") is Status.PENDING   # True -- look a member up BY its value

class Priority(enum.IntEnum):   # compares/sorts like a plain int
    LOW = 1
    HIGH = 2
Priority.HIGH > Priority.LOW    # True

class Color(enum.Enum):
    RED = enum.auto()           # 1, 2, 3, ... auto-assigned, in definition order
    GREEN = enum.auto()
```

---

## 7 · `typing` — advisory, not enforced

```python
from typing import Optional, Union

def find(d: dict, key: str) -> Optional[int]:   # same as Union[int, None]
    return d.get(key)

def add(a: int, b: int) -> int:
    return a + b

print(add("x", "y"))   # 'xy' -- runs to completion, no error, and returns a str where
                        # the hint promised an int. Type hints are documentation for
                        # humans and mypy -- CPython checks NOTHING here at call time,
                        # and there is no mypy on the grading machine.
```

Write hints on public function signatures anyway (rule of thumb, and the SPEC's own
requirement for this repo) — they're free documentation and make your intent legible to the
interviewer skimming your code, which is exactly what the 35%-clean-code grade rewards.

---

## 8 · `re` — the basics you need without a regex reference open

```python
import re

re.match(r"\d+", "123abc")          # matches at the START only; .group() -> '123'
re.search(r"\d+", "abc123def")      # matches ANYWHERE; .group() -> '123'
re.findall(r"\d+", "a1 b22 c333")   # ['1', '22', '333']
re.sub(r"\s+", " ", "a   b\tc")     # 'a b c'
re.split(r"[,;]\s*", "a, b;c")      # ['a', 'b', 'c']

pattern = re.compile(r"^\w+@\w+\.\w+$")   # compile once, reuse, if matching in a loop
bool(pattern.match("a@b.com"))            # True
```

Use a **raw string** (`r"..."`) for every pattern — otherwise `\d`, `\s`, `\w` collide with
Python's own string-escape rules. `match` anchors at the start of the string only; `search`
and `findall` scan the whole thing.

---

## 9 · `json`

```python
import json

obj = {"name": "amy", "scores": [1, 2, 3], "active": True, "meta": None}
s = json.dumps(obj, indent=2)      # -> str, pretty-printed
back = json.loads(s)               # -> dict, round-trips cleanly for JSON-native types

# gotchas: dict keys always become strings; tuples come back as lists
json.loads(json.dumps({1: "a"}))          # {'1': 'a'}  -- key 1 (int) became '1' (str)
json.loads(json.dumps((1, 2, 3)))         # [1, 2, 3]   -- list, not tuple

with open("out.json", "w") as f:
    json.dump(obj, f)               # dump/load (no -s) work directly with a file handle
```

---

## 10 · `csv`

```python
import csv

with open("out.csv", "w", newline="") as f:    # write a sample file to read back below
    writer = csv.writer(f)
    writer.writerow(["name", "age"])
    writer.writerow(["amy, the great", 30])    # embedded comma is quoted automatically

with open("out.csv", newline="") as f:     # newline="" -- let csv, not the text layer, own line endings
    reader = csv.reader(f)
    rows = list(reader)                    # list of lists of str; every value is a string
print(rows)                                # [['name', 'age'], ['amy, the great', '30']]

with open("out.csv", newline="") as f:
    for row in csv.DictReader(f):          # dict per row, keyed by the header line
        print(row["name"])                 # amy, the great
```

Always pass `newline=""` to `open()` when reading or writing CSV — the csv module writes its
own `\r\n` line terminators and needs to control that itself; skip it and files can end up with
doubled line endings depending on platform. `DictReader`/`DictWriter` take a `fieldnames=`
argument when the source has no header row to infer from.

---

## 11 · `pathlib`

```python
from pathlib import Path

Path("data").mkdir(exist_ok=True)  # write_text does not create parent directories
p = Path("data") / "input.txt"     # `/` composes paths -- works on every OS
p.write_text("line1\nline2\n", encoding="utf-8")
text = p.read_text(encoding="utf-8")
lines = text.splitlines()

p.exists(), p.suffix, p.stem       # (True, '.txt', 'input')
list(Path("data").glob("*.txt"))   # every .txt file directly under data/
```

Prefer `pathlib.Path` over building strings with `os.path.join`; it's more readable under time
pressure and `read_text`/`write_text` collapse the usual `open(...) as f: f.read()` dance to one
call for the common case.

---

## 12 · `sys.stdin`

```python
import sys

data = sys.stdin.read().split()        # bulk-read everything, split on any whitespace
nums = list(map(int, data))

for line in sys.stdin:                  # lazy, one line at a time, keeps the trailing \n
    line = line.rstrip("\n")
```

`input()` is fine for one interactive prompt; it is the wrong tool for bulk stdin parsing under
a clock. Full treatment — including why, and the exact patterns for each recurring laptop-round
I/O shape — is in [io-and-parsing.md](io-and-parsing.md).

---

## Interview questions

1. **Why does `heapq.heappush(pq, (priority, payload))` sometimes crash on a tie, and how do you
   prevent it in one line?** `heapq` breaks ties on tuples by comparing the next element; if two
   entries share a `priority` and `payload` isn't orderable (a `dict`, a custom object without
   `__lt__`), comparison raises `TypeError`. Fix: push `(priority, next(counter), payload)` so
   the tie-breaker is always unique and the payload is never compared.

2. **How do you get a max-heap out of `heapq`?** You don't, directly — negate values on push and
   negate again on pop, or use `heapq.nlargest(k, iterable)` if you only need the top k and
   don't need an ongoing heap.

3. **What's the time complexity of `heapq.heapify`, and why is that surprising?**
   `O(n)`, not `O(n log n)` — pushing `n` items one at a time would be `O(n log n)`, but
   heapify's bottom-up sift-down approach amortizes to linear. Worth stating correctly if asked.

4. **`itertools.groupby` returned three groups from data with only two distinct keys. What
   happened?** The input wasn't sorted by that key first — `groupby` only merges *consecutive*
   equal keys. Sort by the same key function before grouping.

5. **What does `Counter()["missing_key"]` return, and how is that different from both a plain
   `dict` and a `defaultdict(int)`?** It returns `0` without raising — like `defaultdict(int)` —
   but unlike `defaultdict`, reading a missing key from a `Counter` does **not** insert it; the
   key still won't appear in `.keys()` afterward.

6. **Why doesn't a `-> Optional[int]` type hint stop a caller from getting a runtime error?**
   Hints are metadata; nothing in the interpreter enforces them, and mypy isn't installed on the
   grading machine. The caller still has to check for `None` explicitly.

7. **[Reported at Lyft]** Interviewers have asked candidates to "implement methods in a class"
   as part of a coding-screen problem. If that class needs ordered/priority behavior, what's
   the fastest correct path — hand-write a heap, or reach for `heapq`? Always `heapq` first;
   define `__lt__` (or `@dataclass(order=True)`) on the class if you need it to sort by a
   specific field, and let the stdlib do the sift-up/sift-down.

8. **When would you choose `bisect.insort` over just appending and re-sorting?** When you're
   inserting one element at a time into an already-sorted structure repeatedly — `insort` keeps
   it sorted in `O(n)` per insert (due to the shift), versus `O(n log n)` for a full re-sort
   each time. For many insertions, a heap is usually still the better structure than a sorted
   list.
