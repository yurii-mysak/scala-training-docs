# OOP & Design in Python

> **Priority:** Required
> **Est. time:** 60 min
> **Track:** Both
> **HelloInterview:** Low-Level Design in a Hurry

The laptop round has drifted toward object-oriented design: "implement methods in a class," a
small stateful system (KV store with transactions, LRU cache, job scheduler, rate limiter), graded
on correctness, clean code, and performance. You already know OOD — you've built real systems in
Scala's trait/class model and C#'s interface model for over a decade. What you need here is the
Python-specific vocabulary: how the same design decisions get *expressed* — `self`, dunder
methods, dataclasses, composition idioms — so the code you write under a clock reads as fluent
Python, not translated Scala.

---

## 1 · Classes, `__init__`, and what's different from what you know

```python
class Vehicle:
    wheels = 4                          # class attribute -- shared unless shadowed per-instance

    def __init__(self, make: str, model: str):
        self.make = make                # instance attribute
        self.model = model
        self._odometer = 0              # leading underscore: "internal", a convention only

    def drive(self, miles: float) -> None:
        self._odometer += miles

class Car(Vehicle):
    def __init__(self, make: str, model: str, doors: int):
        super().__init__(make, model)   # NOT automatic -- you must call it explicitly
        self.doors = doors
```

What's genuinely different from C#/Scala/TypeScript, not just cosmetically:

- **`self` is an explicit parameter you write**, always first, on every instance method. Python
  passes the instance for you at call time, but the signature has to declare it — there's no
  hidden injection the way `this`/`self` sugar works elsewhere.
- **No access modifiers.** `private`/`protected`/`public` don't exist as language features.
  Convention: `_name` means "internal, don't touch it from outside," `__name` triggers **name
  mangling** (becomes `_ClassName__name`, mainly to avoid subclass attribute clashes, not real
  privacy). Nothing is actually enforced — this is a readability signal, not a compiler check.
- **No method overloading.** You can't define `def area(self, r)` and `def area(self, w, h)` in
  the same class — the second definition replaces the first. Use default arguments, `*args`, or
  `@functools.singledispatchmethod` if you truly need dispatch on argument type.
- **`super().__init__(...)` is not automatic.** A subclass that defines its own `__init__` and
  forgets to call `super().__init__(...)` silently skips the parent's setup — no compiler warns
  you.

---

## 2 · Properties

Python's idiom is to start with a plain public attribute and only add a `@property` later if you
need computed values or validation — you don't pre-emptively write getters/setters the way you
might in C#/Java, because plain-attribute access and property access look **identical** to the
caller, so switching later never breaks anyone.

```python
class Temperature:
    def __init__(self, celsius: float):
        self._celsius = celsius

    @property
    def celsius(self) -> float:
        return self._celsius

    @celsius.setter
    def celsius(self, value: float) -> None:
        if value < -273.15:
            raise ValueError("below absolute zero")
        self._celsius = value

    @property
    def fahrenheit(self) -> float:          # read-only derived value, no setter defined
        return self._celsius * 9 / 5 + 32

t = Temperature(0)
t.celsius = 100          # looks like plain attribute assignment, actually runs the setter
print(t.fahrenheit)      # 212.0
```

---

## 3 · Dunder methods — this is your operator-overloading and protocol toolkit

| Method | Powers | Default behavior if you skip it |
|--------|--------|-----------------------------------|
| `__repr__` | `repr(obj)`, what you see in a REPL/debugger/list of objects | `<Foo object at 0x7f...>` — useless for debugging under time pressure |
| `__eq__` | `==` | identity comparison (`is`) — two equal-looking objects compare unequal |
| `__hash__` | usability in a `set`/as a dict key | **defining `__eq__` sets `__hash__` to `None`** unless you also define `__hash__` (or use `frozen=True` on a dataclass) |
| `__lt__` (+ `functools.total_ordering`) | `sorted()`, `<`, `min`/`max` | `TypeError` on comparison |
| `__len__` | `len(obj)` | `TypeError: object of type 'Foo' has no len()` |
| `__contains__` | `x in obj` | falls back to iterating via `__iter__` if present, else `TypeError` |
| `__iter__` / `__next__` | `for x in obj`, `list(obj)` | `TypeError: 'Foo' object is not iterable` |
| `__getitem__` / `__setitem__` | `obj[key]`, `obj[key] = v` | `TypeError: 'Foo' object is not subscriptable` |

```python
from functools import total_ordering

@total_ordering
class Money:
    def __init__(self, cents: int):
        self.cents = cents
    def __eq__(self, other):
        return self.cents == other.cents
    def __lt__(self, other):
        return self.cents < other.cents
    def __repr__(self):
        return f"Money({self.cents})"

print(sorted([Money(300), Money(100), Money(200)]))   # [Money(100), Money(200), Money(300)]
print(Money(100) <= Money(200))    # True -- total_ordering derives <=, >, >= from __eq__ + __lt__
```

A custom container gets to use `obj[x]`/`len(obj)`/`x in obj` the same way a `list`/`dict` does,
just by implementing the relevant dunders:

```python
class Grid:
    def __init__(self, rows: int, cols: int):
        self._data = [0] * (rows * cols)
        self.rows, self.cols = rows, cols
    def __getitem__(self, rc):
        r, c = rc
        return self._data[r * self.cols + c]
    def __setitem__(self, rc, value):
        r, c = rc
        self._data[r * self.cols + c] = value
    def __len__(self):
        return len(self._data)
    def __contains__(self, value):
        return value in self._data

g = Grid(2, 2)
g[0, 1] = 5
print(g[0, 1], len(g), 5 in g)     # 5 4 True
```

A custom **iterator** implements both `__iter__` (returns an object with `__next__`, usually
`self`) and `__next__` (returns the next value, raises `StopIteration` when done). Unlike a bare
generator function, an object like this can be iterated more than once if `__iter__` resets its
state each time:

```python
class CountUp:
    def __init__(self, n):
        self.n = n
    def __iter__(self):
        self._i = 0
        return self
    def __next__(self):
        if self._i >= self.n:
            raise StopIteration
        self._i += 1
        return self._i

counter = CountUp(3)
print(list(counter))   # [1, 2, 3]
print(list(counter))   # [1, 2, 3] again -- __iter__ reset _i, unlike an exhausted generator
```

---

## 4 · `dataclass` vs plain class vs `NamedTuple`

| | `@dataclass` | plain `class` | `typing.NamedTuple` |
|---|---|---|---|
| Boilerplate for `__init__`/`__repr__`/`__eq__` | generated | you write it | generated |
| Mutable | yes, unless `frozen=True` | yes | **no** — always immutable |
| Hashable | only if `frozen=True` (or `eq=False`) | only if you define `__hash__` | yes, always |
| Ordering (`<`, `sorted()`) | opt in with `order=True` | you write `__lt__` etc. | inherited from tuple: compares element-by-element |
| Positional pattern matching (`match`) | yes, `__match_args__` auto-generated | no, unless you add it | yes |
| When to reach for it | a record with a few fields, maybe some behavior | genuine invariants, complex state, many methods | an immutable record, no mutation ever needed |

```python
from dataclasses import dataclass, field

@dataclass(order=True, frozen=True)
class Point:
    x: int
    y: int

@dataclass
class Bucket:
    # NEVER `items: list = []` here -- see the mutable-default-argument trap in
    # errors-and-edge-cases.md. default_factory calls list() fresh per instance.
    items: list = field(default_factory=list)

b1, b2 = Bucket(), Bucket()
b1.items.append(1)
print(b2.items)     # [] -- independent, unlike the plain-function version of this bug
```

Reach for a **plain class** once the type has real behavior beyond holding data — invariants
that must hold across multiple fields, methods that do meaningful work, or mutable internal
state a `@dataclass`'s auto-generated `__init__` doesn't model well (the worked example in §9 is
exactly this case).

---

## 5 · Composition over inheritance

Nothing about Python forces this — the language supports deep inheritance trees just as readily
as Scala or C# do. The difference is idiomatic culture: Python code (and most laptop-round
rubrics) rewards a shallow, composed design over an inheritance hierarchy built to anticipate
variation that the problem hasn't asked for yet.

```python
from abc import ABC, abstractmethod

# inheritance-first instinct (common if you're used to a trait/interface hierarchy):
class AbstractRateLimiter(ABC):
    @abstractmethod
    def allow(self, key: str) -> bool: ...

class AlwaysAllowRateLimiter(AbstractRateLimiter):
    def allow(self, key: str) -> bool:
        return True
    # a second algorithm means a second subclass, and every caller is coupled to the hierarchy

# composition-first instinct (usually faster to build correctly, and to change):
class RateLimiter:
    def __init__(self, strategy):
        self._strategy = strategy        # strategy is any object with an .allow(key) method
    def allow(self, key: str) -> bool:
        return self._strategy.allow(key)

class AlwaysAllowStrategy:               # no shared base class needed -- duck typing
    def allow(self, key: str) -> bool:
        return True

limiter = RateLimiter(AlwaysAllowStrategy())
print(limiter.allow("user-42"))          # True -- swapping strategies never touches RateLimiter
```

The composed version needs no shared base class at all — Python's duck typing means
`self._strategy` just needs an `.allow` method, full stop. This matters concretely for the
recurring problem families: a job scheduler is a composition of a queue and a clock, not an
inheritance tree of scheduler types; a rate limiter is a composition of a counter/window
strategy, not a subclass per algorithm.

One inheritance trap specific to Python, not an opinion: **subclassing a built-in container
(`dict`, `list`) is fragile**, because the built-in's own C-implemented methods do not route
through your overrides:

```python
class LoudDict(dict):
    def __setitem__(self, key, value):
        print(f"setting {key}")
        super().__setitem__(key, value)

d = LoudDict()
d["a"] = 1          # prints "setting a" -- goes through your override
d.update({"b": 2})  # does NOT print anything -- dict.update() bypasses __setitem__ entirely
```

If you need dict-like behavior that's guaranteed to route through your own methods, subclass
`collections.UserDict` (or `UserList`/`UserString`) instead — or, usually simpler and what §9
does, don't subclass a builtin at all: hold one as a private attribute (composition) and expose
only the methods you actually want.

---

## 6 · ABCs and Protocols

Two ways to say "this type must support X," matching two things you already know:

- **`abc.ABC` + `@abstractmethod`** is nominal, like a Scala trait or a C# interface — a class
  must explicitly `class Square(Shape):` to count as a `Shape`, and Python refuses to
  instantiate it until every abstract method is implemented.
- **`typing.Protocol`** is structural — like duck typing, formalized with a type hint. A class
  satisfies a `Protocol` just by having the right methods, with **no inheritance relationship at
  all**. This is closer to how Python code is idiomatically written day to day.

```python
from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...

class Square(Shape):
    def __init__(self, side): self.side = side
    def area(self): return self.side ** 2

try:
    Shape()
except TypeError as e:
    print(e)   # Can't instantiate abstract class Shape with abstract method area

@runtime_checkable
class HasArea(Protocol):
    def area(self) -> float: ...

class Circle:                      # note: no inheritance from HasArea at all
    def __init__(self, r): self.r = r
    def area(self): return 3.14159 * self.r ** 2

print(isinstance(Circle(1), HasArea))   # True -- structural match, zero coupling to the protocol
```

For a laptop round, default to plain duck typing (no `ABC`, no `Protocol`) unless the
interviewer specifically asks how you'd enforce an interface across multiple implementations —
then reach for `ABC` first, since it's more familiar to read and faster to write correctly under
a clock than `Protocol`.

---

## 7 · Context managers

```python
class Timer:
    def __enter__(self):
        import time
        self.start = time.perf_counter()
        return self
    def __exit__(self, exc_type, exc, tb):
        import time
        self.elapsed = time.perf_counter() - self.start
        return False           # False/None -- don't swallow exceptions; True would suppress them

with Timer() as t:
    sum(range(1_000_000))     # stand-in for "the work being timed"
print(t.elapsed)
```

The generator-based shortcut via `contextlib` is almost always less code for the same result,
and is what to reach for first in an interview:

```python
from contextlib import contextmanager
import time

@contextmanager
def timer():
    start = time.perf_counter()
    try:
        yield lambda: time.perf_counter() - start
    finally:
        pass    # cleanup goes here, runs even if the `with` body raises

with timer() as elapsed:
    sum(range(1_000_000))     # stand-in for "the work being timed"
print(elapsed())
```

Use a context manager whenever a laptop-round problem has a resource with a clear
open/close or start/stop shape — a file, a lock, a "transaction" — even if you build it in five
minutes with `@contextmanager`; the interviewer reads it as fluency with the language, not just
a working solution.

---

## 8 · Iterators and generators

A **generator function** (any function with `yield`) is the fast way to get iterator-protocol
behavior without writing `__iter__`/`__next__` by hand — but it is single-pass:

```python
def fibonacci(limit):
    a, b = 0, 1
    while a < limit:
        yield a
        a, b = b, a + b

gen = fibonacci(20)
print(list(gen))    # [0, 1, 1, 2, 3, 5, 8, 13]
print(list(gen))    # [] -- exhausted, not memoized, not restartable
```

This matters for the design worked example below and for the performance grade: a generator
never materializes the full sequence in memory, so it's the right tool whenever a laptop-round
problem says "stream" or hands you a file too large to hold comfortably in a `list`. Full
memory-vs-list treatment: [performance-notes.md](performance-notes.md).

---

## 9 · Worked example — designing a small stateful class the way the laptop round expects

**The prompt:** design and implement an LRU cache: `get(key)` returns the value or `None`;
`put(key, value)` inserts or updates; when the cache exceeds capacity, evict the
least-recently-used entry. This exact family (`LRU variants`) has been reported at Lyft's laptop
round, and the underlying shape — a fixed-capacity container with an eviction policy — recurs
across half the reported problem families (KV store, rate limiter, pagination cache).

**Before writing code, say out loud what you're deciding and why — this is most of the "clean
code" grade:**

- **Complexity target:** `get` and `put` both `O(1)`. That rules out a plain `list` scan for
  recency (`O(n)`) and points at a hash map for `O(1)` lookup plus *some* structure that tracks
  recency in `O(1)`.
- **Composition, not inheritance.** The cache *has a* mapping; it is not *a kind of* `dict`. See
  the subclassing trap in §5 — a `dict` subclass would let a caller call `.update()` and silently
  desync the LRU ordering, because `dict.update()` doesn't route through any override.
- **What tracks recency in `O(1)`?** `collections.OrderedDict` gives you `move_to_end(key)` and
  `popitem(last=False)`, both `O(1)` — that's the whole mechanism. State the fallback too: if the
  interviewer says "no `OrderedDict`," the answer is a hash map plus a hand-rolled doubly linked
  list, shown second below.

```python
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self._capacity = capacity
        self._data: "OrderedDict[str, object]" = OrderedDict()

    def get(self, key):
        if key not in self._data:
            return None
        self._data.move_to_end(key)          # mark as most-recently-used
        return self._data[key]

    def put(self, key, value) -> None:
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = value
        if len(self._data) > self._capacity:
            self._data.popitem(last=False)    # evict least-recently-used

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        return key in self._data

    def __repr__(self):
        return f"LRUCache({list(self._data.items())!r})"
```

```python
cache = LRUCache(2)
cache.put("a", 1)
cache.put("b", 2)
cache.get("a")          # touches "a" -> now most-recently-used
cache.put("c", 3)       # over capacity -> evicts "b" (least-recently-used)
print(cache.get("b"))   # None
print(len(cache), "a" in cache, "c" in cache)   # 2 True True
```

**The "no `OrderedDict`" fallback** — a dict for `O(1)` lookup, plus a hand-rolled doubly linked
list with sentinel head/tail nodes for `O(1)` reordering:

```python
class _Node:
    __slots__ = ("key", "value", "prev", "next")
    def __init__(self, key=None, value=None):
        self.key, self.value = key, value
        self.prev = self.next = None

class LRUCacheManual:
    def __init__(self, capacity: int):
        self._capacity = capacity
        self._map: dict = {}
        self._head, self._tail = _Node(), _Node()   # sentinels: head.next = most-recently-used
        self._head.next = self._tail
        self._tail.prev = self._head

    def _remove(self, node):
        node.prev.next, node.next.prev = node.next, node.prev

    def _insert_front(self, node):
        node.next, node.prev = self._head.next, self._head
        self._head.next.prev = node
        self._head.next = node

    def get(self, key):
        if key not in self._map:
            return None
        node = self._map[key]
        self._remove(node)
        self._insert_front(node)
        return node.value

    def put(self, key, value) -> None:
        if key in self._map:
            self._remove(self._map[key])
        node = _Node(key, value)
        self._map[key] = node
        self._insert_front(node)
        if len(self._map) > self._capacity:
            lru = self._tail.prev
            self._remove(lru)
            del self._map[lru.key]
```

**What an interviewer is listening for** while you build this, beyond "does it work": did you
state the complexity target before coding (not after); did you notice the subclassing trap
instead of writing `class LRUCache(OrderedDict):` and hoping; can you produce the manual fallback
on request, which tests whether you understood the mechanism or just memorized the one-liner. A
table-driven test for exactly this class is in
[testing-with-unittest.md](testing-with-unittest.md#7--copy-pasteable-table-driven-test-template).

The other recurring stateful-class family — an in-memory KV store with `BEGIN`/`COMMIT`/
`ROLLBACK` — is worked in full, including the command-dispatch parsing it's normally packaged
with, in [io-and-parsing.md](io-and-parsing.md#6--parsing-command-string-protocols).

---

## Interview questions

1. **Design an LRU cache with O(1) get and put. What two data structures do you combine, and
   why does neither alone suffice?**
   A hash map for O(1) key lookup, plus a structure that supports O(1) "move this to the front"
   and "remove the back" for recency tracking — a doubly linked list (or `OrderedDict`, which
   *is* one internally). A hash map alone has no order; a linked list alone has no O(1) lookup.

2. **Why is `class LRUCache(dict):` a worse starting point than composing a dict as an
   attribute?** Because `dict`'s own C-implemented methods (`update`, `setdefault`, `__init__`
   with an initial mapping) don't route through your overrides — a caller using an inherited
   method can silently desync your eviction bookkeeping. Composition guarantees every access
   goes through the methods you actually wrote.

3. **[Reported at Lyft]** A coding-screen prompt asked candidates to "implement methods in a
   class." What's the first thing you say before writing any code?** State the class's
   invariants and the complexity target for each method — what must stay true after every
   operation, and how fast each operation needs to be — before choosing internal data
   structures. Choosing structures before stating the target is how you end up rewriting
   halfway through the round.

4. **What's the practical difference between `abc.ABC` and `typing.Protocol` for enforcing an
   interface, and which would you reach for first in a 60-minute round?** `ABC` is nominal
   (explicit inheritance, refuses to instantiate until all abstract methods exist); `Protocol`
   is structural (any matching class satisfies it, no inheritance needed). Default to `ABC` in
   a timed round — it's more familiar to write and to read quickly; reach for `Protocol` only if
   you specifically want to type-check against third-party classes you can't modify.

5. **A `@dataclass` and a hand-written class both "work" for a record type. When do you choose
   the plain class?** When the type has real behavior beyond holding data: invariants spanning
   multiple fields, methods that do meaningful work, or internal mutable state that the
   dataclass's generated `__init__` doesn't model (the LRU cache in §9 is this case — it isn't
   "a few fields," it's a capacity, a map, and an eviction rule).

6. **You defined `__eq__` on a class so instances compare by value. Sorting works, but adding an
   instance to a `set` raises `TypeError: unhashable type`. Why, and what's the fix?**
   Defining `__eq__` makes Python set `__hash__` to `None` automatically, because a mutable
   object with custom equality is, by default, assumed unsafe to hash. Fix: either define
   `__hash__` explicitly (consistent with your `__eq__`), or use `@dataclass(frozen=True)`,
   which does this for you.

7. **When would you choose composition over inheritance for a small system design like a rate
   limiter or job scheduler?** By default — Python's duck typing means a composed strategy
   object needs no shared base class at all, the design stays flexible to swap algorithms
   without touching the caller, and it avoids the specific `dict`/`list` subclassing trap. Reach
   for inheritance only when there's a genuine "is-a" relationship and shared, non-overridden
   behavior to inherit.

8. **How would you make a custom class iterable, and what's the difference between doing that
   with `__iter__`/`__next__` versus a generator method?** Implement `__iter__` (returning an
   object with `__next__`) and `__next__` (returning values, raising `StopIteration` when done)
   for a reusable iterator whose state you control explicitly; or give the class a method that
   itself is a generator function (uses `yield`) for less code when you don't need to iterate
   the same instance concurrently from two places. A generator is simpler but single-pass per
   call; a hand-written `__iter__`/`__next__` can reset and be iterated again, as shown in §3.
