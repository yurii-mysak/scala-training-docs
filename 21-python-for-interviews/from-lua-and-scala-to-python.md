# From Lua & Scala to Python

> **Priority:** Required
> **Est. time:** 45 min
> **Track:** Both
> **HelloInterview:** none

This is not a Python tutorial. You have 13 years of engineering judgement; the problem is not
programming, it's that your last year of muscle memory is Lua, and the years before that were
Scala/Akka, C#/.NET, and Node/TypeScript. Under a 60-90 minute clock, muscle memory is what
fails first — you'll know *what* to build and reach for the wrong syntax to build it. This file
is a map of exactly where that happens: a transfer-errors table for each language, then the
top 20 mistakes an experienced non-Python engineer makes on day one. Every snippet below runs
as-is under `python3`.

---

## 1 · How to use this file

Read the two tables once, closely — most of these will land as "oh, right" rather than new
information. Then skim the top-20 list and actually run the two or three you're least sure of.
The goal isn't memorizing this document; it's having run into each bug once here, on purpose,
so it doesn't cost you five minutes finding it live in front of an interviewer.

---

## 2 · Transfer errors — Lua to Python

| # | Concept | In Lua | In Python | The specific bug this causes |
|---|---------|--------|-----------|-------------------------------|
| 1 | Indexing base | Sequences are **1-based**: `t[1]` is the first element. | Sequences are **0-based**: `lst[0]` is the first element. | Porting `for i=1,#t do` to `for i in range(1, len(t)):` skips index `0` and reads one past the end. |
| 2 | Absence of a value | `nil` means both "absent" and "never set"; `t[k] == nil` covers both. | `None` is a real, distinct value. Indexing a missing dict key **raises `KeyError`**, it does not return `None`. | `if d[key] == None:` crashes with `KeyError` the first time `key` was never set — need `d.get(key)` or `key in d`. |
| 3 | Falsiness | Only `nil` and `false` are falsy. `0` and `""` are truthy. | `None`, `False`, `0`, `0.0`, `""`, `[]`, `{}`, `set()` are **all** falsy. | `if not count:` meant as "count was never set" also fires when `count == 0`, silently skipping legitimate zero values. |
| 4 | Tables as array *and* map | One `table` type is simultaneously array, map, and (via metatables) object. `#t` counts only the contiguous array part. | `list`, `dict`, `set`, `tuple` are separate types, separate APIs, no overlap. | Calling `.append()` on a `dict`, or expecting `len()` to mean "array part only" on a dict that also has string keys. |
| 5 | No built-in classes | OOP is a convention: a table of functions, `self` passed explicitly, `:` is sugar for `(self, ...)`, inheritance wired by hand with `setmetatable(t, {__index = Parent})`. | `class` is a keyword; `self` is an explicit first parameter Python passes for you at call time; `class Child(Parent):` is real inheritance. | Hand-rolling a "class" out of a table of closures out of habit — wasted time Python doesn't ask for — **or** forgetting `self` must still be written as the literal first parameter of every method. |
| 6 | String concatenation | `..` operator; auto-coerces numbers to strings. | `+` operator on `str`; **no** auto-coercion. | `"score: " + score` raises `TypeError: can only concatenate str (not "int") to str` the instant `score` is numeric. |
| 7 | Length | `#t` / `#s` — a prefix **operator**. | `len(x)` — a **function call**, uniform across `str`/`list`/`dict`/`set`/`tuple`. | Writing `#lst` is a `SyntaxError` in Python (`#` starts a comment). |
| 8 | Closures over loop variables | The `for` control variable is a **fresh local every iteration** — a closure captures that iteration's value correctly. | The loop variable is **one variable, reassigned** each iteration — a closure captures the *name*, resolved when the closure finally runs. | `[lambda: i for i in range(3)]` — all three closures return `2`, not `0, 1, 2`. See §2.1. |
| 9 | Metatables vs. dunder methods | Operator overloading, `tostring`, inheritance all go through a separate `metatable` attached with `setmetatable(t, mt)` — the behavior lives outside the table. | Operator overloading and string conversion are ordinary methods defined **directly on the class**: `__add__`, `__repr__`, `__eq__`. No separate object to attach. | Hunting for a `setmetatable`-shaped API to add equality/printing and either skipping it (objects print as `<Foo object at 0x7f...>`, never compare equal) or reaching for metaclasses — the wrong tool for this job. |
| 10 | Multiple return values | Functions natively return several values: `return a, b`; `local x = f()` silently keeps just the first. | `return a, b` returns **one tuple** `(a, b)`. A single-name assignment binds the whole tuple. | `x = f()` where `f` returns two values makes `x` a `(a, b)` tuple — not "just `a`" — and the next line that treats `x` as a number blows up. |
| 11 | Scope by default | Variables are **global unless declared `local`**. | Assignment *anywhere* in a function body makes that name **local for the whole function**, even on lines before the assignment. | Reading an outer/global name early in a function that *later* assigns to the same name raises `UnboundLocalError` — Python decided the name was local from the assignment alone, at compile time. |
| 12 | Iterating | `pairs(t)` for key/value; `ipairs(t)` for the 1-based array part. | `for x in seq`, `for k, v in d.items()`, `for i, x in enumerate(seq)`. | Writing `for i, v in ipairs(lst):` (doesn't exist) instead of `enumerate(lst)`; or `for k, v in d:` expecting automatic pairs. |

### 2.1 Run these once

The loop-closure trap, verified — and the fix (default-argument trick pins the value at
*definition* time instead of *call* time):

```python
funcs = [lambda: i for i in range(3)]
print([f() for f in funcs])          # [2, 2, 2] -- all three see the final i

funcs_fixed = [lambda i=i: i for i in range(3)]
print([f() for f in funcs_fixed])    # [0, 1, 2]
```

Metatables vs. dunder methods — the Python side of the same idea, no separate object required:

```python
class Point:
    def __init__(self, x, y):
        self.x, self.y = x, y
    def __add__(self, other):        # was Point.__add__ in a Lua metatable
        return Point(self.x + other.x, self.y + other.y)
    def __repr__(self):              # was Point.__tostring
        return f"Point({self.x}, {self.y})"

print(Point(1, 2) + Point(3, 4))     # Point(4, 6)
```

---

## 3 · Transfer errors — Scala to Python

| # | Concept | In Scala | In Python | The specific bug this causes |
|---|---------|----------|-----------|-------------------------------|
| 1 | Mutability by default | `val` is the default; idiomatic collections (`List`, `Map`, `Vector`) are immutable — a function cannot mutate what you passed it unless the type says so. | No `val`/`var` distinction. `list`/`dict`/`set` are mutable and passed **by reference** — a function can mutate the caller's object. | Being surprised a helper mutated the caller's list — **or** the mirror-image bug: `def f(x, acc=[]):` — Python evaluates the default **once, at `def` time**, and that single object is shared and accumulates across every call that omits it. (Scala re-evaluates a default parameter expression fresh at every call site; Python does not.) |
| 2 | Optional values | `Option[T] = Some(x) \| None`; the compiler forces unwrapping (`map`, `getOrElse`, pattern match) — forgetting is a compile error. | `None` is a plain value of any type. `Optional[int]` is a **hint**, enforced by nothing at runtime. `None` has no `.map`/`.getOrElse`. | Trusting a `-> Optional[int]` return type as a real guarantee and skipping the `is None` check — the program still runs; it just raises `AttributeError` later, at the call site that assumed a value. |
| 3 | For-comprehensions | `for { x <- xs; y <- ys if p } yield e` desugars to `flatMap`/`map`/`withFilter`, and works over *any* type with those methods — `Option`, `Future`, `List`, all the same syntax. | `[e for x in xs for y in ys if p]` looks similar but only iterates real iterables. `yield` inside it means something else entirely (a generator). No monadic generalization to `Optional`/futures exists. | Typing `for x <- xs` (`SyntaxError`); or expecting a comprehension to "flatMap through" an `Optional[List[int]]` the way Scala flatMaps through `Option[List[Int]]` — you write the `is not None` check by hand instead. |
| 4 | Pattern matching | `match` is an **expression**, exhaustiveness-checked against sealed traits, usable anywhere a value is expected: `val y = x match { ... }`. | `match` (3.10+) is a **statement** — `y = match x: ...` is a `SyntaxError`. Destructuring is real; exhaustiveness checking is not — a missed `case` is silently a no-op, never a compiler warning. | Hunting for a way to assign a `match`'s result directly; or trusting an unmarked `match` to be exhaustive — Python won't flag a missing branch until that input shows up at runtime. |
| 5 | Implicits | `implicit` parameters/conversions let the compiler silently thread typeclass instances and coercions through scope. | Nothing like this exists. Every conversion is explicit (`int(x)`); "polymorphic" dispatch is an `if isinstance(...)` chain or a dunder method the object itself defines. | Building a hand-rolled typeclass-emulation (`dict` of `type -> handler`) when two `isinstance` branches would solve the actual problem in a tenth of the code and the clock is running. |
| 6 | Laziness | `lazy val`, by-name parameters (`=> T`) are language features; a `LazyList` is lazy **and memoizes** its computed elements. | Eager everywhere except generators, a few lazy stdlib iterators (`map`, `filter`, `itertools.*`), and `and`/`or` short-circuiting. **Nothing memoizes automatically.** | Assuming a generator behaves like a `lazy val` — it does not cache: exhaust it once with `list(gen)` and the *second* call returns `[]`. Also: `[x for x in range(10**8)]` eagerly builds the whole list; the lazy equivalent is `(x for x in range(10**8))`, chosen explicitly. |
| 7 | Type safety at runtime | Generics erase in bytecode, but the compiler still catches huge classes of bugs before the program runs. | `def f(x: int) -> str:` is metadata for humans and tools (mypy — **not installed on the grading machine**). Nothing checks it when you run `python3 file.py`. | Writing correct-looking type hints and treating them as proof of correctness — skipping the runtime check or test that would have caught a bad value, "because the types line up." |
| 8 | Case classes | `case class Point(x: Int, y: Int)` gives `equals`/`hashCode`/`toString`/`copy`/pattern support for free; instances are immutable and hashable by default. | `@dataclass` gives `__init__`/`__repr__`/`__eq__` for free — but a **plain** dataclass is **unhashable**: `__eq__` (the default) sets `__hash__ = None` unless you pass `frozen=True`. Positional pattern matching *does* work out of the box. | Putting plain-`@dataclass` instances into a `set()` or using them as dict keys — `TypeError: unhashable type` — because "case classes are values, values go in sets" doesn't carry the hashability over automatically. |
| 9 | Error-handling idiom | Idiomatic Scala favors `Try`/`Either`/`Option` over throwing for *expected* failure; exceptions are for the truly unrecoverable. | Idiomatic Python is EAFP ("easier to ask forgiveness than permission") — raising a plain exception for an expected failure and letting the caller `try/except` it is normal, encouraged style. | Building an unrequested `Result`/`Either` wrapper or a `(value, error)` tuple convention out of habit — more code, not what the interviewer expects to see, and it costs minutes the round doesn't refund. |

### 3.1 Run these once

The mutable-default trap — the single most common "Python looks fine but does something insane"
bug for anyone arriving from a language where default expressions are re-evaluated per call:

```python
def accumulate(x, acc=[]):     # acc is created ONCE, when this def runs
    acc.append(x)
    return acc

print(accumulate(1))           # [1]
print(accumulate(2))           # [1, 2]  <-- same list, carried over from the first call
```

```python
def accumulate_fixed(x, acc=None):
    if acc is None:
        acc = []
    acc.append(x)
    return acc

print(accumulate_fixed(1))     # [1]
print(accumulate_fixed(2))     # [2]
```

Dataclass hashability — the case-class instinct that doesn't transfer automatically:

```python
from dataclasses import dataclass

@dataclass
class Point:                   # eq=True (default) -> __hash__ set to None
    x: int
    y: int

hash(Point(1, 2))              # TypeError: unhashable type: 'Point'
```

```python
from dataclasses import dataclass

@dataclass(frozen=True)        # frozen -> Python restores a real __hash__
class FrozenPoint:
    x: int
    y: int

hash(FrozenPoint(1, 2))        # works; usable in a set() or as a dict key
```

Generators are not a memoized `lazy val` — they exhaust:

```python
def squares(n):
    for i in range(n):
        yield i * i

gen = squares(3)
print(list(gen))               # [0, 1, 4]
print(list(gen))               # []  -- already consumed, nothing cached
```

---

## 4 · The top 20 mistakes on day one

1. **Mutable default argument.** `def f(x, cache={}):` shares one `cache` across every call.
   Fix: default to `None`, create the mutable value inside the function body.

2. **`==` where you meant `is None`.** `if x == None:` works by accident (most objects don't
   override `__eq__` against `None`) until one does. Idiomatic: `if x is None:`.

3. **Off-by-one from 1-based habit.** `range(1, len(lst))` silently skips index `0`. Python
   ranges are `[start, stop)`, 0-based, stop-exclusive — `range(len(lst))` is what you want.

4. **`+=` on strings inside a loop.** Each `+=` conceptually builds a new string; do it `n`
   times and you're one accidental extra reference away from quadratic. Build a list, then
   `''.join(parts)` once. See [performance-notes.md](performance-notes.md).

5. **Mutating a list while iterating it.**
   ```python
   for x in items:
       if bad(x):
           items.remove(x)      # skips the element right after every removal
   ```
   Fix: iterate `items[:]` (a copy), or build a new list with a comprehension.

6. **Confusing `.sort()` with `sorted()`.** `x = lst.sort()` makes `x` **`None`** — `.sort()`
   mutates in place and returns nothing. `sorted(lst)` returns a new list and leaves `lst` alone.

7. **Shallow copy on nested data.** `new = old[:]` (or `list(old)`, or `dict.copy()`) copies one
   level. Nested lists/dicts are still the *same* shared objects. Use `copy.deepcopy` when the
   data has more than one level and you need real independence.

8. **Late-binding closures in a loop.** Covered above (§2.1) — the classic
   `[lambda: i for i in range(3)]` bug. Default-bind the loop variable: `lambda i=i: i`.

9. **Integer division direction.** `-7 // 2 == -4`, not `-3` — Python's `//` floors toward
   **negative infinity**; C#/Scala/Java integer division truncates toward zero. `5 / 2 == 2.5`
   always (true division); `//` is the only way to get an int-flavored result.

10. **Catching too broadly.** A bare `except:` (or `except Exception:` everywhere) swallows real
    bugs — `KeyboardInterrupt`, typos that raise `NameError`, everything. Catch the specific
    exception type the failure path actually raises.

11. **Comparing floats with `==`.** `0.1 + 0.2 == 0.3` is `False`. Use `math.isclose(a, b)`, or
    `decimal.Decimal`/`fractions.Fraction` when you need exactness rather than closeness.

12. **Forgetting `self`, or forgetting `super().__init__()`.** Every instance method's first
    parameter is `self`, written explicitly — Python does not inject it invisibly. A subclass
    that defines `__init__` and never calls `super().__init__(...)` silently skips the parent's
    setup.

13. **Using a mutable value as a dict key or set member.** `{[1, 2]: "x"}` raises
    `TypeError: unhashable type: 'list'`. Use a `tuple` (or `frozenset`) instead.

14. **Assuming dict order is either arbitrary or sorted.** Since 3.7 it's neither — dicts
    preserve **insertion order**, guaranteed. Don't defensively re-sort out of old Python-2
    habit, and don't assume insertion order means sorted order.

15. **`UnboundLocalError` from the assign-anywhere-is-local rule.** Reading a variable, then
    assigning to the same name later in the same function (without `global`/`nonlocal`) makes
    Python treat *every* reference to that name in the function as local — including the read
    that came first in program order.

16. **Unpacking the wrong number of values.** `a, b = f()` where `f` returns three values raises
    `ValueError: too many values to unpack`. Use starred assignment (`a, b, *rest = f()`) when
    the count is genuinely variable.

17. **`range(len(x))` when you meant `enumerate(x)`.** Both work; `enumerate` is what an
    interviewer expects to see when you need the value *and* the index.

18. **`input()` in a loop for bulk stdin.** Fine for one prompt; painfully slow and awkward for
    reading hundreds of tokens. Use `sys.stdin.read().split()` for bulk numeric input, or
    `for line in sys.stdin:` for line-oriented input. See
    [io-and-parsing.md](io-and-parsing.md).

19. **Manual string concatenation instead of an f-string.** `str(x) + ", " + str(y)` chains are
    slower to write and to read than `f"{x}, {y}"` — and readability is 35% of the grade here.

20. **Mixed indentation.** Python's block structure **is** the indentation — no braces to fall
    back on. A stray tab pasted in among spaces is a `TabError` at best, a silent logic change
    at worst. Configure your editor to insert spaces, and if something "impossible" is
    happening, suspect whitespace before you suspect the algorithm.

---

## Interview questions

1. **You port `for i=1,#t do ... end` from Lua. What are the two things you must change, and
   what happens if you only change one of them?**
   Change the start (`1` → `0`, or just drop it) *and* the stop (`#t` inclusive → `len(t)`
   exclusive). Changing only the start to `range(0, len(t))` is correct; changing only the stop
   to `range(1, len(t))` still skips index `0`.

2. **Why does `[lambda: i for i in range(3)]` return three closures that all print `2`, and how
   do you fix it without restructuring the loop?**
   Python's `for` loop reuses one variable `i`; the closures capture the *name*, resolved when
   called, by which point the loop has finished and `i == 2`. Fix by defaulting the loop
   variable into the closure at *definition* time: `lambda i=i: i`.

3. **A Scala `case class` and a Python `@dataclass` both look like "free equality and repr."
   What's the one behavioral difference that will bite you fastest?**
   Hashability. A `case class` instance is immutable and hashable by default. A plain
   `@dataclass` is **unhashable** the moment it gets an auto-generated `__eq__` (the default) —
   you must pass `frozen=True` to get a working `__hash__` back.

4. **You have `def f(x, opts={}):`. What's wrong, and what does "wrong" actually look like in
   production?**
   `opts={}` is created once, at function-definition time, and shared across every call that
   omits the argument — later calls silently see accumulated state from earlier ones. In
   production this shows up as inexplicable cross-request contamination, often intermittent
   depending on call order. Fix: `opts=None`, then `opts = opts if opts is not None else {}`.

5. **Why doesn't a Python type hint (`def f(x: int) -> str:`) protect you the way a Scala type
   signature does?**
   Hints are pure metadata — nothing in the interpreter checks them. `f("not an int")` runs
   without complaint unless the function body itself fails on that input. Type checking (mypy)
   is a separate, opt-in tool, and it is not installed on the grading machine.

6. **In Lua, closures created inside a `for` loop "just work" per-iteration. In Python they
   don't. What's the actual language-level difference?**
   Lua's `for` control variable is a fresh local binding on every iteration, so each closure
   captures its own copy. Python's loop variable is a single variable that gets reassigned; a
   closure captures the *variable*, not a value, so all closures see whatever it holds when
   they're finally called.

7. **What replaces Lua's metatables when you want `+` to work on your own class in Python?**
   Nothing separate — you define `__add__` (and friends: `__eq__`, `__repr__`, `__lt__`)
   directly on the class. Python does have a metaclass mechanism, but it customizes class
   *creation*, not operator behavior, and you will not need it in a laptop round.

8. **You're tempted to build a Scala-style `Result`/`Either` return type for a function that can
   fail. Should you, in a Python interview?**
   No — idiomatic Python for expected failure is `raise` plus `try/except` at the caller (EAFP).
   A hand-rolled `Result` wrapper is more code than the problem asked for and reads as
   unfamiliarity with the language, not rigor.
