# Generators & Coroutines

> **Priority:** Required
> **Est. time:** 40 min
> **Track:** Both
> **HelloInterview:** none

[oop-and-design-in-python.md §8](oop-and-design-in-python.md) covers the shape of a generator — a
function with `yield` is single-pass and doesn't build a list in memory. This file goes underneath that:
precisely how a generator works as a state machine, the two-way communication most people don't know
exists, and why this matters concretely for Lyft's laptop round. **The two highest-frequency problem
families reported** — stateful paginated fetch (7 independent reports) and file/log/CSV parsing (4
reports) — are both, underneath the specifics, an iterator problem: hold state between calls, hand back
items lazily, never materialize more than you need. See
[../17-lyft-laptop-round/01-stateful-paginated-fetch.md](../17-lyft-laptop-round/01-stateful-paginated-fetch.md)
and [../17-lyft-laptop-round/06-file-log-csv-parsing.md](../17-lyft-laptop-round/06-file-log-csv-parsing.md).

One naming note before starting: "coroutine" in this file means the classic, pre-3.5 sense — a
generator driven with `.send()`/`.throw()`, or chained with `yield from`. It is the direct historical
ancestor of `async def` coroutines, but it is not the same mechanism as `async`/`await` — that's
[async-and-concurrency.md](async-and-concurrency.md), whose history section leans directly on the
vocabulary built here (§10 there is the payoff).

---

## 1 · The iterator protocol, precisely

[oop-and-design-in-python.md §3](oop-and-design-in-python.md) already showed a hand-written
`__iter__`/`__next__` class. The protocol underneath it, precisely: `iter(obj)` calls `obj.__iter__()`
and expects back an object with a `__next__()` method — call that the *iterator*. `next(it)` calls
`it.__next__()`, which returns the next value or raises `StopIteration` to signal there are no more.
`StopIteration` is not an error in the usual sense here — it's the protocol's designated "done" signal,
and every consumer of an iterator is expected to catch it. A `for` loop is exactly this, desugared:

```python
data = [10, 20, 30]

it = iter(data)
while True:
    try:
        value = next(it)
    except StopIteration:
        break
    print(value)
# is what `for value in data: print(value)` actually does underneath
```

A generator object satisfies this protocol automatically — it has both `__iter__` (returning itself) and
`__next__` (resuming the function body to the next `yield`) for free, which is the whole reason `yield`
is faster to write than a hand-rolled class for a one-shot iterator.

One corner worth knowing exists: `iter()` also takes a **two-argument form**, `iter(callable, sentinel)`,
which calls `callable()` repeatedly and stops the moment it returns `sentinel` — a compact way to turn
"keep calling this until it returns a specific value" into a normal iterable, without writing a `while`
loop by hand:

```python
import io

buf = io.StringIO("a\nb\nSTOP\nc\n")
for line in iter(lambda: buf.readline().strip(), "STOP"):
    print("line:", line)
# line: a
# line: b
```

---

## 2 · Why a generator function returns a generator, rather than running

Any function whose body contains `yield` is compiled as a **generator function** — calling it never
runs a single line of the body. It only constructs a generator object: a paused state machine holding
the function's local variables, its instruction pointer, and nothing else yet computed.

```python
def make_squares(n):
    print("generator body starting")
    for i in range(n):
        yield i * i

gen = make_squares(3)     # nothing printed -- the body has not run at all
print(gen)                 # <generator object make_squares at 0x...>
print(next(gen))            # NOW the body starts: prints "generator body starting", then yields 0
print(next(gen))            # resumes right after the yield, prints 1
```

This is the same "returns an inert object" shape `async def` uses for coroutine objects — see
[async-and-concurrency.md §4](async-and-concurrency.md) — and it's not a coincidence; `async def` was
built directly on this mechanism (§7 below).

---

## 3 · Generator state machines

Between calls, a generator is genuinely **suspended**, not re-entered from scratch: local variables,
the current position in the function body, and the state of any `for`/`while` loop it's inside all
survive exactly as they were at the `yield`. `inspect.getgeneratorstate()` names the states explicitly,
if you want to see it rather than take it on faith:

```python
import inspect

def gen():
    yield 1
    yield 2

g = gen()
print(inspect.getgeneratorstate(g))   # GEN_CREATED -- constructed, never started
next(g)
print(inspect.getgeneratorstate(g))   # GEN_SUSPENDED -- paused at a yield
list(g)                                 # drains it to exhaustion
print(inspect.getgeneratorstate(g))   # GEN_CLOSED -- StopIteration raised, done for good
```

(There's a fourth state, `GEN_RUNNING`, that only exists while the generator's own frame is actively
executing — you'll never observe it from outside, since by definition nothing else can run while the
generator itself is running on that same thread.)

---

## 4 · `.send()` — two-way communication

`next(gen)` is really `gen.send(None)` in disguise. The general form, `gen.send(value)`, resumes the
generator and makes `value` the *result of the `yield` expression* that was paused — this is the part
most people never learn, because most generators are only ever driven with `next()`. A generator that
uses `yield` as an expression (`received = yield`), not just a statement, can receive data from its
caller on every resume, not just hand data out:

```python
def running_total():
    total = 0
    while True:
        value = yield total     # yields the current total, receives the next value to add
        total += value

gen = running_total()
print(next(gen))       # 0 -- primes it: runs to the first yield, gets the first yielded value
print(gen.send(5))      # 5  -- 5 is delivered as the result of `yield total`; total becomes 5
print(gen.send(10))     # 15
```

**The generator must be primed first** — with a bare `next(gen)` or `gen.send(None)` — before you can
send it a real value. Sending a non-`None` value to a just-created generator (one that hasn't reached
its first `yield` yet) raises `TypeError`, because there's no paused `yield` expression yet for that
value to become the result of.

---

## 5 · `.throw()` and `.close()`

`gen.throw(exc)` raises `exc` **inside the generator, at the exact point it's currently suspended** — as
if that `yield` expression had raised it. The generator can catch it and keep going (even `yield` again,
continuing the sequence), or let it propagate, which closes the generator.

```python
def worker():
    try:
        while True:
            yield "working"
    except ValueError as e:
        print("caught inside generator:", e)
        yield "recovered"
    finally:
        print("cleanup ran")

g = worker()
print(next(g))                        # working
print(g.throw(ValueError("bad input")))  # caught inside generator: bad input / recovered
g.close()                               # cleanup ran
```

`gen.close()` is a specific case of the same mechanism: it throws `GeneratorExit` at the suspension
point. The generator is expected to exit — either by not catching it (the default, and the common case),
or by catching it to run cleanup and then returning. **Yielding again after catching `GeneratorExit` is
an error** — the protocol's contract is "clean up and stop," not "keep producing":

```python
def stubborn():
    try:
        yield 1
    except GeneratorExit:
        print("declining to close cleanly")
        yield 2      # not allowed -- yielding again after GeneratorExit is a protocol violation

g = stubborn()
next(g)
try:
    g.close()
except RuntimeError as e:
    print("RuntimeError:", e)   # RuntimeError: generator ignored GeneratorExit
```

Python also calls `close()` automatically when a generator is garbage-collected before it's exhausted —
which is exactly the mechanism `contextlib.contextmanager` is built on
([oop-and-design-in-python.md §7](oop-and-design-in-python.md)): the code before `yield` is `__enter__`,
the code after is `__exit__`'s clean-exit path, and an exception raised inside the `with` block reaches
the generator as a `.throw()` at that same `yield`.

---

## 6 · `return` inside a generator, and `StopIteration.value`

A `return value` inside a generator does not hand `value` back the way it would from a normal function
— a generator's only way to signal "no more items" is `StopIteration`, so `return`'s value rides along
*inside* that exception, as its `.value` attribute:

```python
def gen():
    yield 1
    return "done"

g = gen()
next(g)                    # 1
try:
    next(g)
except StopIteration as exc:
    print(exc.value)        # done
```

Bare `return` (or falling off the end of the function) is exactly `return None` — `StopIteration.value`
is `None` in that case, same as any function that doesn't explicitly return something.

---

## 7 · `yield from` — delegation

`yield from other_gen()` transparently forwards `next()`, `send()`, and `throw()` between the caller and
the inner generator — the outer generator is effectively invisible while the inner one is running. As an
expression, `yield from` evaluates to whatever the inner generator eventually `return`s:

```python
def inner():
    inner_result = yield 2
    print("inner received:", inner_result)
    return 3

def outer():
    yield 1
    val = yield from inner()      # delegates entirely to inner() until it's exhausted
    print("outer got back:", val)
    yield 4

gen = outer()
print(next(gen))          # 1
print(next(gen))          # 2 -- came from inner(), via outer()
print(gen.send("abc"))    # inner received: abc / outer got back: 3 / then yields 4
```

This delegation chain — a generator `yield from`-ing another, which can `yield from` another — is
exactly the mechanism Python's first generation of coroutines was built on, years before `async`/`await`
existed as syntax. `await` is `yield from`'s direct descendant, with a dedicated keyword and a distinct
underlying type; full history in [async-and-concurrency.md §10](async-and-concurrency.md).

---

## 8 · Generator pipelines for streaming

Chain several generator functions and each stage pulls from the previous one lazily, one item at a
time — nothing downstream forces anything upstream to materialize a full list. This is the direct answer
to the file/log/CSV parsing family, and to any "process a file too large to hold in memory" prompt:

```python
from pathlib import Path

Path("demo.log").write_text(
    "10:01:00 INFO server started\n"
    "10:01:02 ERROR connection refused\n"
    "10:01:05 INFO request handled\n"
    "10:01:07 ERROR timeout waiting for upstream\n",
    encoding="utf-8",
)

def read_lines(path):
    with open(path, encoding="utf-8") as f:
        for line in f:                      # already lazy -- one line resident at a time
            yield line.rstrip("\n")

def parse_log_lines(lines):
    for line in lines:
        timestamp, level, message = line.split(" ", 2)
        yield {"timestamp": timestamp, "level": level, "message": message}

def only_errors(records):
    for record in records:
        if record["level"] == "ERROR":
            yield record

for record in only_errors(parse_log_lines(read_lines("demo.log"))):
    print(record["timestamp"], record["message"])
# 10:01:02 connection refused
# 10:01:07 timeout waiting for upstream
```

Nothing here holds more than one line, one parsed record, in memory at a time, regardless of whether
`demo.log` has four lines or four million — the whole point of choosing a pipeline of generators over
`read_lines()` → build a list → filter it → build another list. `io-and-parsing.md`'s streaming guidance
is the I/O half of this same idea:
[io-and-parsing.md §2](io-and-parsing.md#2--reading-files).

---

## 9 · `itertools.islice`, `tee`, and `chain` with generators

The base API for these three is in
[stdlib-for-interviews.md §4](stdlib-for-interviews.md#4--itertools--the-six-you-actually-reach-for) —
this section is what's specifically sharp about using them *with generators* rather than with a plain
list.

**`chain`** is how you stitch pipeline stages, or several sources, into one logical stream without
copying anything — `itertools.chain(read_lines("a.log"), read_lines("b.log"))` is a single lazy iterator
over both files in sequence, never one combined list.

**`tee`** splits one generator into several independent iterators over the same underlying sequence —
useful when two different consumers each need to walk the same stream. The gotcha: **`tee` buffers**.
Internally, it keeps every item the slowest consumer hasn't reached yet, for every faster consumer that's
already passed it. If one clone runs far ahead of another — or is fully drained before the other starts
at all — that buffer grows to hold the whole gap, silently defeating the memory benefit you split the
generator to get in the first place:

```python
import itertools

def numbers():
    for i in range(5):
        print(f"  producing {i}")
        yield i

a, b = itertools.tee(numbers(), 2)
print("first from a:", next(a))
print("first from a again:", next(a))
print("now draining b fully:", list(b))    # forces items 2,3,4 to be produced NOW, for b...
print("rest of a:", list(a))                # ...and buffered here, waiting for a to catch up
```

`b` running ahead of `a` doesn't lose anything — but it does mean `tee` had to hold items 2, 3, and 4
in memory until `a` got around to asking for them. If the two consumers are meant to run at wildly
different paces, or one might not run at all, don't reach for `tee`; materialize a list once instead and
hand both consumers a reference to it — at that point you've already paid the memory cost `tee` was
trying to avoid, so `tee` bought you nothing.

**`islice`** is the safe way to bound anything unbounded — see the trap in §11.

---

## 10 · Memory behavior vs building lists

A generator's whole value proposition is **O(1) memory per step, regardless of input size** — nothing is
held except the current position and whatever local state the function body needs. Building a list first
(`[x for x in source]`, `f.readlines()`, `list(gen)`) is O(n) memory, and that trade is invisible until n
is large enough to matter — which, in the laptop round, is exactly when the problem statement says
"large file" or "stream." Prefer a generator (or a plain lazy iteration like `for line in f:`) any time a
problem doesn't actually need random access or multiple passes over the data; reach for a list only when
you genuinely need to index into it, sort it, or iterate it more than once (§11 explains why the second
one specifically forces the issue).

---

## 11 · The classic traps

**A generator is single-use.** Once exhausted, it stays exhausted — calling `list()` on it again returns
`[]`, it does not restart or re-run the function body:

```python
def countdown(n):
    while n > 0:
        yield n
        n -= 1

gen = countdown(3)
print(list(gen))   # [3, 2, 1]
print(list(gen))   # []  -- already exhausted, not memoized, not restartable
```

If something needs to be iterated more than once, either call the generator function again for a fresh
generator (`countdown(3)` a second time), or materialize it into a list once and reuse the list — a
generator is not a substitute for a cached, replayable sequence.

**`list()` on an infinite (or merely unbounded) generator never returns.** A `while True: yield ...`
generator is a perfectly normal, useful thing to write — right up until something tries to fully
materialize it:

```python
import itertools

def naturals():
    n = 0
    while True:
        yield n
        n += 1

# list(naturals())            # DO NOT run this -- consumes memory until the process is killed
print(list(itertools.islice(naturals(), 5)))   # [0, 1, 2, 3, 4] -- take exactly what you need
```

`itertools.islice` (already covered in §9 and
[stdlib-for-interviews.md §4](stdlib-for-interviews.md#4--itertools--the-six-you-actually-reach-for)) is
the fix any time you have a generator that might be unbounded — a live feed, a `while True` polling loop,
a lazily-computed sequence — and need only the first `k` items.

---

## Interview questions

1. **What's the difference between an *iterable* and an *iterator*, precisely?** An iterable is anything
   `iter()` can be called on — it implements `__iter__`, which returns an iterator. An iterator is the
   object that actually implements `__next__` and raises `StopIteration` when exhausted. A `list` is
   iterable but is not itself an iterator (it has no `__next__`); `iter(a_list)` produces the iterator.

2. **Calling a generator function doesn't run its body. What does it actually do, and when does the
   first line run?** It constructs a generator object — a suspended state machine holding the function's
   locals and instruction pointer, nothing computed yet. The first line runs on the first `next()` (or
   `.send(None)`), and execution proceeds up to the first `yield`.

3. **What does `StopIteration.value` hold, and how do you get it?** The value from a `return` statement
   inside the generator — a generator can't "return" a value the normal way, since its return channel is
   already `yield`, so `return x` attaches `x` to the `StopIteration` exception's `.value` attribute,
   retrievable from a `try: next(gen) except StopIteration as exc: exc.value`.

4. **What's the practical difference between `gen.close()` and just letting a generator go out of
   scope?** Very little in CPython specifically — garbage collection calls `close()` automatically once
   a generator becomes unreachable, throwing `GeneratorExit` at its suspension point either way. Calling
   `close()` explicitly just makes the cleanup timing deterministic instead of tied to when the garbage
   collector happens to run.

5. **[Reported at Lyft]** Print the K-th non-empty line of a large file without loading it into
   memory. Why is `for line in f:` (not `f.readlines()`) the whole answer, and where does a generator
   pipeline come in if the problem also needs filtering or parsing?** File iteration is already lazy —
   one line resident at a time regardless of file size — so a plain counting loop over `for line in f:`
   solves the base problem directly. A generator pipeline (§8) is the natural extension the moment the
   real prompt adds a second or third step — parse each line, then filter, then take the k-th — since
   chaining generator functions keeps every stage just as lazy as the file iteration itself.

6. **Why does `list(some_generator)` return `[]` the second time it's called on the same object?** A
   generator is single-use — once it raises `StopIteration`, its state is `GEN_CLOSED` and it never
   resets. `list()` just drains whatever's left, which is nothing. Getting a fresh sequence means calling
   the generator *function* again, not re-consuming the same generator *object*.

7. **What's `yield from` actually doing, mechanically, and what does it evaluate to?** It delegates
   `next()`/`send()`/`throw()` transparently to an inner generator until that inner generator is
   exhausted, and the `yield from` expression itself evaluates to the inner generator's `return` value.
   It's the direct ancestor of `await` — see
   [async-and-concurrency.md §10](async-and-concurrency.md).

8. **`itertools.tee` splits a generator into two. Under what condition does that quietly cost you the
   memory you were trying to save by using a generator in the first place?** When the two resulting
   iterators are consumed at very different paces, or one is fully drained before the other starts —
   `tee` buffers every item the slower consumer hasn't reached yet, so a big enough gap between the two
   means the buffer ends up holding most or all of the sequence anyway.

9. **You need `.send()` to deliver a value into a running generator. What happens if you call
   `gen.send("value")` before ever calling `next(gen)`?** `TypeError` — a freshly created generator
   hasn't reached its first `yield` yet, so there's no in-progress `yield` expression for the sent value
   to become the result of. It has to be primed first, with a bare `next(gen)` or `gen.send(None)`.
