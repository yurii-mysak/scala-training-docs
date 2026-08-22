# Async & Concurrency in Python

> **Priority:** Required
> **Est. time:** 60 min
> **Track:** Both
> **HelloInterview:** none

Lyft's product backend is **Python (primary) and Go** — no JVM in product engineering — and the target
team's own platform is async Python end to end: a stateful meta-agent router dispatching to specialist
subagents, **safety checks fanned out in parallel before any LLM reasoning runs**, and every tool call
along the way is I/O. See [20-llm-agent-systems](../20-llm-agent-systems/README.md) for the platform
itself. The job posting for this role asks, verbatim, for "a solid understanding of performance,
concurrency, and reliability tradeoffs." This file is that understanding, built from the ground up: what
the GIL actually does, when threads help and when they don't, and the concurrency model — `asyncio` —
that the platform above, and most production Python services, actually run on.

This is the largest single gap in a JVM/Akka background. Akka gives you real preemptive concurrency
across cores for free; Python's story is different in ways that matter for both the laptop round and the
design rounds, and §11 is a direct bridge from what you already know to what's different here.

---

## 1 · The GIL — what it actually protects

The GIL (Global Interpreter Lock) is a single mutex inside CPython — the reference implementation
everyone means by "Python" unless stated otherwise — that only one thread may hold at a time while
executing Python bytecode. However many OS threads a process has, at most one of them is ever running
Python bytecode at any given instant.

**Why it exists.** CPython manages memory largely through reference counting: every object carries a
count of how many references point at it, incremented and decremented as code runs, freed the instant
the count hits zero. Without a lock around that bookkeeping, two threads incrementing or decrementing
the same object's refcount concurrently could interleave and corrupt it — a lost update that shows up
as memory freed while still referenced (a crash) or never freed at all (a leak). The GIL is the cheapest
fix that guarantees that never happens: one global lock, instead of a lock per object. Fine-grained
per-object locking has been attempted more than once (§1.1) and is genuinely hard to do without slowing
down the common case, which is single-threaded code.

**What it makes atomic:** any single bytecode operation. In practice, a lot of individual, one-step
operations on built-in types are safe to touch from multiple threads without your own locking —
appending to a list, setting one dict key, rebinding one name.

**What it does *not* make atomic: a compound operation spanning more than one bytecode instruction.**
This is the part that trips people up, because "the GIL means only one thread runs at a time" sounds
like it should mean "my code is safe from races" — it doesn't. `counter += 1` is a **load, add, store**
— three separate bytecode instructions. The GIL guarantees each of those three runs without another
thread's bytecode interleaving mid-instruction, but it guarantees nothing about the three running back
to back as one atomic unit; control can switch to another thread between them. In practice, a bare tight
loop like `counter += 1` rarely shows a visible loss at small scale, because CPython's GIL-switch check
tends to land at loop and call boundaries far more often than truly mid-expression. The moment there is
any real gap between the read and the write, the race is not theoretical at all:

```python
import threading
import time

counter = 0

def increment(n):
    global counter
    for _ in range(n):
        current = counter
        time.sleep(0)          # yields to another thread right between the read and the write
        counter = current + 1

threads = [threading.Thread(target=increment, args=(50,)) for _ in range(8)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(counter)                 # reliably well short of 400 -- lost updates, despite the GIL
```

Run that and `counter` lands somewhere around 55-65, not 400. A `threading.Lock` around the read-modify-
write restores correctness. **The GIL was never a substitute for your own locking on multi-step
invariants** — it protects CPython's internals, not your program's.

### 1.1 What changed in 3.13+ — free-threading, accurately

- **PEP 703** ("Making the Global Interpreter Lock Optional in CPython") was accepted for Python 3.13
  (released October 2024). It shipped an **experimental** free-threaded build — a distinct build
  variant of the interpreter, installed and invoked as `python3.13t` (built with `--disable-gil`), **not**
  the default `python3.13` a normal install gives you.
- The free-threaded build replaces the single global lock with per-object locking and biased reference
  counting, so multiple threads can genuinely run Python bytecode in parallel across cores.
- Two real costs as of this writing: single-threaded code measurably slower on a free-threaded build
  than on the standard GIL build (the per-object locking machinery has overhead even with zero
  contention), and a C-extension ecosystem still catching up — many extensions assumed the GIL's
  protection and need real changes to be safe without it.
- Python 3.14 (released October 2025) moved the free-threaded build from "experimental" to officially
  supported, per PEP 703's own phased plan — still opt-in, still not the default build.
- **The honest, current answer:** free-threading is real, shipping, and the direction CPython is
  heading — but as of today it's an opt-in build with real trade-offs, not something you can assume
  under a plain `python3` you didn't specifically request. It's also irrelevant to code targeting 3.10,
  which this whole program does. The guidance in §2 holds for the interpreter you'll actually be handed
  in the laptop round.

---

## 2 · Threads vs processes vs `asyncio` — how to choose

| Workload shape | Reach for | Why |
|---|---|---|
| Many concurrent I/O waits (network calls, DB queries, sockets), one process is enough | `asyncio` | Cooperative, single-threaded scheduling — thousands of pending operations cost roughly one lightweight coroutine object each, not one OS thread each |
| I/O-bound, but calling a library that only blocks (no async version — a sync DB driver, `requests`) | `threading`, or `asyncio` + `run_in_executor`/`to_thread` (§8) | The GIL releases around the blocking call itself, so other threads (or the event loop) make progress while one waits |
| CPU-bound (parsing, hashing, numeric work, compression) in pure Python | `multiprocessing` | The only real path to more than one core for pure-Python computation — each process gets its own interpreter, its own GIL |
| CPU-bound work triggered *from* an async service | `asyncio` + `ProcessPoolExecutor` via `run_in_executor` | Keeps the event loop free to keep serving everything else while the heavy computation runs on another core |

Two things worth being able to say out loud, because "why not just always use threads, since the GIL
means only one runs at once anyway" is a fair question an interviewer might actually ask:

- **Threads still help I/O-bound work** because the GIL is released around blocking I/O calls (file and
  socket operations, `time.sleep`, and most C-extension calls that do real waiting). While one thread
  blocks waiting on a socket, another can hold the GIL and run Python. Net throughput improves even
  though only one thread ever executes bytecode at an instant.
- **`asyncio` beats threads for pure I/O fan-out at scale**, not because of the GIL, but because of OS
  cost: an OS thread needs a real kernel-scheduled stack and real context-switch overhead, which stops
  scaling well somewhere in the hundreds-to-low-thousands. An `asyncio.Task` is a lightweight Python
  object scheduled cooperatively by the event loop in user space — holding tens of thousands of pending
  coroutines is comparatively cheap. That's the concrete answer, not just "the GIL exists."
- **`multiprocessing`'s real parallelism has real costs**: arguments and results cross the process
  boundary by pickling (serialization overhead, and not everything is picklable), each process has its
  own memory and re-imports everything (higher baseline memory), and there's no shared memory by
  default — sharing state needs `multiprocessing.shared_memory`, `Value`/`Array`, or a `Manager`, each
  with its own overhead. "Just use multiprocessing, it's real parallelism" ignores all of that.

For request-handling capacity math specifically — how many worker processes a Flask/gunicorn deployment
actually needs given a CPU-bound-vs-I/O-bound request mix — see
[napkin-math.md §5.4](../15-system-design/napkin-math.md) and
[deploying-python-services.md §2](../14-cloud-and-infrastructure/deploying-python-services.md).

---

## 3 · The event loop model

`asyncio` runs on **one OS thread** by default. The loop repeatedly: picks the next coroutine step that's
ready to run, runs it until it yields control back (hits an `await` on something not yet ready, or
returns), then moves to whatever else is ready. Nothing runs "in the background" in the sense of a
second thread — concurrency here means many logical tasks interleaved on one thread, not many things
executing at the same literal instant.

Under the hood, the loop uses the operating system's readiness-notification mechanism — `select`,
`poll`, `epoll`, or `kqueue` depending on platform, exposed uniformly through the stdlib `selectors`
module — to ask "which of these sockets are ready right now" without spinning a thread per socket. When
a coroutine awaits a socket operation that isn't ready yet, the loop registers interest in that socket
and moves on; it comes back to resume that coroutine only once the OS reports the socket is actually
ready.

This is the mechanical reason `asyncio` is fundamentally about **I/O** concurrency, not CPU concurrency:
the loop can multiplex *waiting*, not *computing*. A coroutine that never awaits anything blocks the
entire loop for as long as it runs — §8 makes this concrete. `asyncio.run()` is the usual entry point:
it creates a fresh loop, runs your top-level coroutine to completion, and tears the loop down.

---

## 4 · Coroutines are objects — `async def`, `await`, and the "never awaited" trap

`async def f(): ...` defines a coroutine *function*. Calling `f()` does **not** run the body — exactly
like calling a generator function doesn't run its body (see
[generators-and-coroutines.md](generators-and-coroutines.md), which this whole file leans on). Calling
it returns a **coroutine object**: an inert value describing work that hasn't started yet. It only
actually runs once something drives it — `await`ing it, wrapping it in `asyncio.create_task()`, or
handing it to `asyncio.run()`.

```python
import asyncio

async def greet():
    print("hello from inside the coroutine")
    return "hi"

coro = greet()              # nothing printed yet -- the body has not run
print(type(coro))           # <class 'coroutine'>
result = asyncio.run(coro)  # *now* it runs
print(result)                # hi
```

Forget to drive it at all, and CPython specifically detects the mistake and warns:

```python
async def unused():
    return 1

unused()   # created, never awaited, eligible for garbage collection immediately
# RuntimeWarning: coroutine 'unused' was never awaited
```

If you ever see that warning in your own code, the fix is never to silence it — it means real work you
intended to run never ran.

---

## 5 · Running coroutines — `asyncio.run`, `create_task`, `gather`, `wait_for`, `TaskGroup`

- **`asyncio.run(coro())`** — the top-level entry point. Creates a fresh event loop, runs the coroutine
  to completion, closes the loop. Call it once, from synchronous code, at the very top of a program —
  never from inside a coroutine (a loop is already running there; nesting raises `RuntimeError`).
- **`asyncio.create_task(coro())`** — schedules a coroutine to start running concurrently *right now*,
  and returns a `Task` you can await later, or not. This is where concurrency actually gets created —
  see §6.
- **`asyncio.gather(*aws)`** — runs several awaitables concurrently, returns their results in the same
  order once all are done. `return_exceptions=True` collects exceptions into the results list instead of
  raising the first one immediately while the rest keep running silently in the background — the
  default behavior, and a real gotcha (the worked example in §12 shows both).
- **`asyncio.wait_for(aw, timeout)`** — races one awaitable against a clock; cancels it and raises
  `TimeoutError` if the deadline passes first. 3.10-safe.
- **`asyncio.TaskGroup()`** (3.11+) — `async with asyncio.TaskGroup() as tg: tg.create_task(...)`. The
  modern, structured way to run several tasks together — full treatment in §9.

```python
import asyncio

async def fetch(n):
    await asyncio.sleep(0.05)
    return n * n

async def main():
    task = asyncio.create_task(fetch(2))         # started now, independently
    results = await asyncio.gather(fetch(3), fetch(4))  # these two run concurrently too
    return await task, results

print(asyncio.run(main()))   # (4, [9, 16])
```

---

## 6 · Futures vs Tasks vs coroutines — the distinction that gets fumbled

This is the single most commonly confused set of terms in `asyncio`, worth being precise about:

- **Coroutine object** — the inert, not-yet-running thing a call to an `async def` function returns.
  Nothing has been scheduled (§4).
- **Task** — a coroutine that has been *handed to the event loop to run concurrently, starting now*,
  independent of whoever created it. `asyncio.create_task(coro)` wraps a coroutine object and schedules
  it. A `Task` **is** a `Future` — it's implemented as a subclass — plus the machinery that drives the
  wrapped coroutine forward, one step at a time, every time the loop gets back around to it.
- **Future** — a lower-level "a result will show up here eventually" placeholder: pending, then done,
  with either a result or an exception — that is not necessarily backed by a coroutine at all. You
  rarely construct one directly; you get them back from things like `loop.run_in_executor()` (a
  thread-pool call wrapped as a `Future`) or library code bridging a callback-based API into the
  awaitable world.

**The concrete distinction that trips people up: `await` on its own does not create concurrency.**
`await coro_object` runs that coroutine to completion right there, in line, before the next statement
executes — sequential, despite the syntax "looking async." Concurrency happens at the moment you call
`create_task()` (or hand several awaitables to `gather`, which creates Tasks internally) — that's when
the loop starts making independent progress on more than one thing. `await` after that point just means
"block *this* coroutine until that already-independently-running piece of work finishes."

```python
import asyncio, time

async def work(n, delay=0.2):
    await asyncio.sleep(delay)
    return n

async def sequential():
    start = time.monotonic()
    a = await work(1)          # runs to completion...
    b = await work(2)          # ...before this one even starts
    return time.monotonic() - start

async def concurrent():
    start = time.monotonic()
    task_a = asyncio.create_task(work(1))    # scheduled now
    task_b = asyncio.create_task(work(2))    # scheduled now, alongside task_a
    await task_a
    await task_b
    return time.monotonic() - start

print(f"sequential: {asyncio.run(sequential()):.2f}s")   # ~0.40s
print(f"concurrent: {asyncio.run(concurrent()):.2f}s")   # ~0.20s -- both slept "at the same time"
```

---

## 7 · Cancellation and `CancelledError`

Calling `.cancel()` on a `Task` schedules a `CancelledError` to be raised **inside that coroutine, at
its next suspension point** — the next time it's paused at an `await`. Cancellation is cooperative and
asynchronous, not instantaneous: the coroutine keeps running until it actually reaches an `await`, where
the exception is then injected.

The coroutine may catch `CancelledError` to run cleanup — a `finally` block is the idiomatic place — but
is expected to let it propagate afterward. Swallowing it silently (catch it, don't re-raise) leaves the
`Task` looking cancelled from the outside while the coroutine actually kept running, which is confusing
and is explicitly discouraged.

Since 3.8, `CancelledError` inherits from **`BaseException`, not `Exception`** — deliberately, so a
broad `except Exception:` does not accidentally swallow a cancellation. See
[exceptions-and-errors.md §2](exceptions-and-errors.md) for why that hierarchy split exists generally.

```python
import asyncio

async def worker():
    try:
        await asyncio.sleep(10)
    except asyncio.CancelledError:
        print("worker: cleaning up")
        raise                      # re-raise -- swallowing this is the anti-pattern

async def main():
    task = asyncio.create_task(worker())
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("main: confirmed the task was cancelled")

asyncio.run(main())
# worker: cleaning up
# main: confirmed the task was cancelled
```

`asyncio.shield(aw)` is worth knowing exists: it protects an inner awaitable from being cancelled by an
outer cancellation (the shielded operation keeps running even if the code awaiting it gives up) — a
real but narrow tool, not something to reach for by default.

---

## 8 · Blocking the event loop, and how not to

Two ways to stall the loop, both meaning **nothing else it's managing makes any progress** for as long
as the call runs:

1. Calling a genuinely blocking function — `time.sleep()`, a synchronous DB driver, `requests.get()` —
   instead of its async equivalent.
2. Running CPU-heavy pure-Python code with no `await` inside a coroutine.

```python
import asyncio, time

def blocking_io(n):
    time.sleep(0.2)              # stands in for a slow sync call, e.g. a sync DB driver
    return n

async def bad():
    return [blocking_io(i) for i in range(3)]     # freezes the WHOLE loop, 0.2s at a time

async def good():
    return await asyncio.gather(*(asyncio.to_thread(blocking_io, i) for i in range(3)))

start = time.monotonic()
asyncio.run(bad())
print(f"direct calls: {time.monotonic() - start:.2f}s")     # ~0.60s -- 3 x 0.2s, sequential

start = time.monotonic()
asyncio.run(good())
print(f"to_thread:    {time.monotonic() - start:.2f}s")     # ~0.20s -- ran concurrently
```

**Fix for a blocking call you can't rewrite as async**: hand it to a thread.
`await asyncio.to_thread(fn, *args)` (3.9+, the convenient spelling) or the lower-level
`await loop.run_in_executor(None, fn, *args)` (`None` uses the loop's default `ThreadPoolExecutor`) —
both run `fn` on a separate OS thread and let the loop keep going while it waits, then deliver the
result back as a normal awaited value.

**Fix for CPU-heavy pure-Python work**: a thread does **not** help here (§1 — the GIL). Hand it to a
`concurrent.futures.ProcessPoolExecutor` via `run_in_executor` instead, so it genuinely runs on another
core while the loop stays responsive to everything else.

---

## 9 · Structured concurrency and timeouts

A bare `asyncio.create_task(coro())` with no reference kept anywhere is a real, documented footgun: the
event loop holds only a **weak** reference to it, so it can be garbage-collected mid-execution, silently,
with no error raised anywhere. More generally, a task created and forgotten inside a function can keep
running after that function returns, invisible to its caller, with no defined point at which "all the
concurrent work this function started" is guaranteed finished.

**`TaskGroup`** (3.11+) fixes this by tying every child task's lifetime to a lexical block:
`async with asyncio.TaskGroup() as tg:` does not exit until every task created inside it has finished —
successfully or not. If any child raises, the others are cancelled automatically, and once everything
has settled, the block raises an `ExceptionGroup` bundling what the children actually raised — not just
the first one, unlike `gather`'s default behavior.

```python
# 3.11+ (TaskGroup and except* both)
import asyncio

async def might_fail(n):
    await asyncio.sleep(0.05)
    if n == 1:
        raise ValueError(f"item {n} failed")
    return n

async def main():
    try:
        async with asyncio.TaskGroup() as tg:
            for n in range(3):
                tg.create_task(might_fail(n))
    except* ValueError as eg:
        print(f"caught {len(eg.exceptions)} failure(s): {[str(e) for e in eg.exceptions]}")

asyncio.run(main())
# caught 1 failure(s): ['item 1 failed']
```

`except*` and `ExceptionGroup` are covered on their own terms, beyond this `TaskGroup` trigger, in
[exceptions-and-errors.md §9](exceptions-and-errors.md).

**Timeouts.** `asyncio.wait_for(aw, timeout)` (§5, 3.10-safe) wraps one awaitable. `asyncio.timeout(s)`
(3.11+) is a context manager that applies a single deadline across a whole block of code, potentially
several awaits — composing better than wrapping each one individually:

```python
# 3.11+
async def fetch_and_process():
    async with asyncio.timeout(2.0):
        data = await fetch()
        return await process(data)   # the SAME 2-second budget covers both awaits
```

`async_patterns.py` (§13) uses `wait_for` rather than `asyncio.timeout()`, deliberately — it targets
3.10, this program's baseline.

---

## 10 · A short history — generators to coroutines, and what came before `asyncio`

`yield` gave functions the ability to pause and resume. `yield from` (3.3, PEP 380) added transparent
delegation to an inner generator — see [generators-and-coroutines.md §7](generators-and-coroutines.md).
That delegation mechanism turned out to be exactly what a scheduler needs: a generator that
`yield from`s another generator, which `yield from`s another, forms a chain a driving loop can step
through uniformly. That *is* how Python built its first generation of coroutines, years before
`async`/`await` existed as dedicated syntax.

`asyncio` itself landed in 3.4 (2014, PEP 3156) written in exactly that generator-based style — an
explicit `@asyncio.coroutine` decorator, `yield from` standing in for what is now `await`. Dedicated
`async def`/`await` syntax arrived a year later in 3.5 (PEP 492): a real, distinct type — a native
coroutine, not a generator, though implemented with much the same machinery — rather than a convention
layered on top of generators. The generator-based spelling was deprecated in 3.8 and removed in 3.11; if
you ever see `@asyncio.coroutine` or `yield from some_coroutine()` in old code, that's what it is —
pre-3.5 asyncio, not a bug. (One line on Python 2, since none of this exists there at all: libraries
solving this problem on Python 2 had to hand-roll delegation with plain `yield` and a manual driving
loop, no `yield from` available — a real part of why Twisted's and Tornado's older APIs look the way
they do.)

`asyncio` was not the first solution to "don't block on I/O" in Python, only the standard-library one.
**Twisted** (2002) built the same idea around explicit callback chains (`Deferred`). **Tornado** did much
the same with its own event loop and, later, generator-based coroutines nearly identical in shape to
early `asyncio`'s. **gevent** took a different approach entirely: `monkey.patch_all()` rewrites the
standard library's blocking calls at import time to cooperatively yield to other greenlets instead, so
ordinary synchronous-looking code becomes concurrent with no `async`/`await` anywhere — genuinely less
code to write, at the real cost that you can't see where your program might switch context just by
reading it, unlike `await`'s explicit markers. All three predate `asyncio` and are still deployed in
production today — gevent specifically shows up as one of gunicorn's worker classes for Flask, see
[deploying-python-services.md §2](../14-cloud-and-infrastructure/deploying-python-services.md).

---

## 11 · Mapping this onto your Akka background

Thirteen years of actor-system experience transfers here more than it might look like at first —
`asyncio`'s scheduler and Akka's dispatcher are solving a close cousin of the same problem — but the
guarantees differ in specific, nameable ways.

| Async Python | Akka analogue | The difference that matters |
|---|---|---|
| `asyncio.Task` | An actor processing its mailbox | A `Task` runs one coroutine to completion (or cancellation) and then it's done — it has no mailbox of its own and receives no further messages. Closer to a single `Future`-returning unit of work than a long-lived entity. |
| The event loop's ready queue | The dispatcher's run queue, shared across actors | Same idea: a scheduler multiplexing many logical units of work over few OS threads. `asyncio` uses exactly **one** OS thread by default; Akka's dispatcher fans out over a configurable thread pool. |
| `await` | `pipeTo` (the non-blocking choice inside an actor) | `await` suspends only the current coroutine and yields control back to the loop — structurally always "the non-blocking thing." In Akka you have to *choose* `pipeTo` over a blocking `ask`/`Await.result`; Python doesn't give you the blocking option inside a coroutine at all. |
| `TaskGroup` (§9) | A supervisor with an all-for-one strategy | Both fail the sibling set together on an unhandled child failure. `TaskGroup`'s default is closer to Akka's `Stop` directive than to `Resume`/`Restart` — there's no per-child restart policy, just "cancel the rest and propagate." |
| `asyncio.Queue` | An actor's mailbox | The actual close analogue to a mailbox — a standing, boundable buffer that producers `put()` into and a consumer `get()`s from, which is exactly a mailbox's shape (`asyncio.Task` above is not it). |
| `asyncio.Semaphore(n)` bounding a fan-out | `BoundedMailbox` / a router with bounded concurrency | Both cap in-flight work, but the semaphore is caller-side and cooperative — there's no "mailbox full" failure mode. A full, bounded Akka mailbox drops or blocks the sender, by configured policy. |
| `CancelledError` propagating through nested `await`s | A `stop()` propagating down an actor hierarchy | Structurally similar propagation, but Python delivers it by raising an exception *inside* the coroutine at its current suspension point — the coroutine can catch it, clean up in a `finally`, and (discouraged) even swallow it, much like intercepting `PreRestart`/`PostStop`. |

### 11.1 Mailbox vs task queue

The row above is worth stating plainly on its own: **an `asyncio.Task` is not the Python analogue of an
actor**, a bounded `asyncio.Queue` is closer to a mailbox. An actor is a long-lived address with a
standing inbox that keeps accepting new messages for its whole life; a `Task` is one scheduled coroutine
run that starts, finishes (or is cancelled), and is gone. The nearest thing to "a long-lived worker with
an inbox" in `asyncio` is a coroutine that loops `while True: item = await queue.get()` — a hand-built
worker reading a shared `Queue`, not any single primitive the library hands you for free. Building
several of those against one bounded `Queue` is the direct, idiomatic way to get an Akka-router-like
worker pool in `asyncio`.

### 11.2 Supervision vs `TaskGroup` cancellation

Akka supervision is a *policy space*: `Resume` (ignore the failure, keep the actor's state),
`Restart` (fresh state, same behavior), `Stop`, or `Escalate`, chosen per-exception-type and configurable
with backoff. `TaskGroup` gives you exactly one behavior: an unhandled exception in any child cancels
every sibling and the group re-raises as an `ExceptionGroup` once everything has unwound. There is no
built-in `Restart` — if you want retry-with-backoff semantics on a task, you write that yourself (a
loop around task creation, catching the specific exception, sleeping, re-entering a new
`async with TaskGroup()`), the way [01-stateful-paginated-fetch.md §5](../17-lyft-laptop-round/01-stateful-paginated-fetch.md)
already asks you to do for a flaky upstream, just without an actor system's `BackoffSupervisor` doing it
for you declaratively.

### 11.3 Backpressure in both models

Akka Streams gets backpressure as a first-class property of the abstraction: every stage speaks the
Reactive Streams `request(n)` protocol, so demand propagates end to end automatically — a slow sink
throttles the whole chain back to the source without anyone writing that logic by hand
([Akka Streams and Backpressure](../03-akka-ecosystem/akka_streaming_and_backpressure_detailed_guide.md)).
`asyncio` has no equivalent built into `await` itself. You get the *primitives* — a bounded `Queue`
whose `put()` blocks once full, a `Semaphore` capping concurrent in-flight work — but nothing propagates
that pressure automatically across a multi-stage pipeline the way Streams does; you wire each boundary
yourself:

```python
import asyncio

async def producer(queue, n):
    for i in range(n):
        await queue.put(i)          # blocks once 2 items are already waiting -- real backpressure
        print(f"put {i}")

async def consumer(queue, n):
    for _ in range(n):
        item = await queue.get()
        await asyncio.sleep(0.01)   # simulate slow processing
        print(f"  processed {item}")

async def main():
    queue = asyncio.Queue(maxsize=2)   # bounded -- the capacity IS the backpressure
    await asyncio.gather(producer(queue, 5), consumer(queue, 5))

asyncio.run(main())
# put 0
# put 1
# put 2      -- only after "processed 0" frees a slot; the producer was genuinely blocked
#   processed 0
# put 3
#   processed 1
# ...
```

That's real backpressure — the producer genuinely cannot outrun the consumer past the buffer size — but
it's local to one queue, not a demand signal automatically relayed across an arbitrary chain of stages
the way `Source.via(Flow).to(Sink)` gives you for free.

---

## 12 · Worked example — `async_patterns.py`

[`async_patterns.py`](async_patterns.py) in this directory is runnable end to end:

```
python3 async_patterns.py
```

It demonstrates the three patterns most laptop-round and design-round follow-ups actually ask for,
against a small deterministic `FlakyService` stand-in (no real network calls, no real randomness, so the
output is stable across runs):

- **`gather_with_error_handling`** — fans out several calls concurrently with `asyncio.gather(...,
  return_exceptions=True)`, then separates successes from failures itself, rather than letting the first
  failure blow up the whole batch while the rest keep running unseen in the background.
- **`fetch_with_timeout`** — wraps a single call in `asyncio.wait_for`, returning `None` on a timeout
  instead of leaking a `TimeoutError` to the caller (a deliberate, stated convention — see
  [exceptions-and-errors.md §10](exceptions-and-errors.md) on picking one and saying so).
- **`bounded_fetch_all`** — caps concurrent in-flight calls with a `Semaphore`, and tracks the observed
  peak concurrency to prove the cap actually held, instead of asserting it works and hoping.

The whole file is deliberately 3.10-compatible (`wait_for`, not `asyncio.timeout()`; no `TaskGroup`) —
§9's 3.11+ features are demonstrated in this file's prose instead, clearly labeled, since the program's
own baseline is 3.10.

---

## Interview questions

1. **What does the GIL actually make atomic, and what's a concrete proof it doesn't make `counter += 1`
   across threads safe?** It makes each individual bytecode instruction atomic with respect to other
   threads, not a whole compound statement. `counter += 1` is load-add-store, three instructions; force
   a yield point between the read and the write (even something as small as `time.sleep(0)`) across
   several threads and updates are reliably lost, because nothing guarantees those three run as one
   unit.

2. **Threads give zero speedup on a CPU-bound pure-Python workload. Why, and what's the fix?** Only one
   thread ever executes Python bytecode at a time regardless of core count, so adding threads to
   CPU-bound work adds context-switch overhead for no additional throughput. `multiprocessing` is the
   fix — separate processes, each with its own interpreter and its own GIL, genuinely run on separate
   cores.

3. **Is the GIL gone in Python 3.13+?** No, not by default. PEP 703's free-threaded build is real and
   shipped experimentally in 3.13, moved to officially supported (still opt-in) in 3.14 — but it's a
   separate build variant (`python3.13t`) with real single-threaded performance overhead and an
   extension ecosystem still catching up. The interpreter you get by default still has the GIL.

4. **What's the actual difference between a coroutine object, a `Task`, and a `Future`?** A coroutine
   object is inert — calling an `async def` function just constructs it, nothing runs. A `Task` wraps a
   coroutine and schedules it to run concurrently starting now; it's implemented as a subclass of
   `Future`. A `Future` is the more general "a result will land here eventually" placeholder, not
   necessarily backed by a coroutine at all. The practical trap: `await` alone never creates concurrency
   — only `create_task` (or `gather`, which creates Tasks internally) does.

5. **`asyncio.gather(*coros)` and one of them raises. What happens to the others by default, and how do
   you change it?** By default the first exception propagates immediately from `gather`, while the
   still-running coroutines keep executing in the background, unobserved, which is a real, easy-to-miss
   bug. `return_exceptions=True` collects every result — success or exception — into the results list
   instead, letting you decide what to do with partial failure yourself.

6. **A coroutine calls `time.sleep(1)` instead of `await asyncio.sleep(1)`. What actually happens to the
   rest of the program?** The entire event loop freezes for that full second — every other pending task,
   timer, and I/O callback stalls, because nothing yields control back to the loop. The fix for a
   blocking call you can't rewrite as async is `asyncio.to_thread(...)` or `run_in_executor`, which runs
   it on a separate OS thread so the loop keeps going.

7. **What problem does `TaskGroup` (3.11+) solve that plain `create_task()` calls don't?** Structured
   concurrency: a bare `create_task()` result that's never stored anywhere can be silently
   garbage-collected mid-run (the loop only holds a weak reference), and nothing guarantees "all the
   concurrent work I started" is actually finished by any particular point. `TaskGroup` ties every child
   task's lifetime to one `async with` block and fails the whole group together, loudly, via an
   `ExceptionGroup`, rather than letting a task quietly disappear.

8. Given that safety checks are fanned out in parallel before any LLM reasoning runs on a platform like
   this, how would you actually implement that fan-out in `asyncio` terms? *Model answer:* launch every
   safety-check coroutine concurrently — `create_task` for each up front, before awaiting any of them —
   then decide explicitly whether one failing should cancel the rest (`TaskGroup`'s default, fail-fast)
   or all checks should always run to completion and be evaluated together
   (`gather(..., return_exceptions=True)`); for a safety gate specifically, running every check to
   completion and looking at the full picture is usually the safer choice, not fail-fast on the first
   one.

9. **You've supervised actors for years. What's the one place `TaskGroup`'s cancellation semantics are
   genuinely *not* like Akka supervision?** No restart policy. Akka gives you `Resume`/`Restart`/`Stop`/
   `Escalate`, often with `BackoffSupervisor` doing retry-with-backoff declaratively. `TaskGroup` only
   knows one behavior — cancel the siblings and propagate as an `ExceptionGroup` — there's no built-in
   "restart this one child and keep the group alive." Retry has to be built by hand around task creation.
