# Exceptions & Error Handling

> **Priority:** Recommended
> **Est. time:** 35 min
> **Track:** Both
> **HelloInterview:** none

Clean code is 35% of the laptop-round grade, and exception handling is one of the fastest places to look
either fluent or sloppy in a live round — a well-chosen `except`, a clear custom error type, or a
one-line comment explaining why a case is being skipped reads as engineering judgment; a bare
`except: pass` reads as hiding a bug you don't trust yourself to have gotten right. This file is the
depth behind [from-lua-and-scala-to-python.md](from-lua-and-scala-to-python.md)'s brief mentions of EAFP
and over-broad catching — expanded properly, plus the mechanics (chaining, `traceback`, `assert`,
exception groups) that file doesn't cover at all.

---

## 1 · The built-in exception hierarchy, and which base to catch

Every built-in exception descends from `BaseException`. `Exception` is a subclass of `BaseException` that
covers essentially everything you'd ever want to catch in application code — `KeyboardInterrupt`,
`SystemExit`, and `GeneratorExit` deliberately sit **outside** `Exception`, as direct children of
`BaseException`, specifically so a broad `except Exception:` cannot accidentally swallow "the user hit
Ctrl-C" or "the process is exiting":

```python
print(issubclass(KeyboardInterrupt, Exception))    # False
print(issubclass(KeyboardInterrupt, BaseException)) # True
print(issubclass(ValueError, Exception))            # True
```

The practical consequence: a **bare `except:`** (no type named at all) catches *everything*, including
those three — genuinely dangerous, since it can swallow a Ctrl-C or hide `SystemExit`. `except Exception:`
is the actual "catch anything reasonable" tool, and is a legitimate choice at a boundary (a top-level
request handler converting anything unexpected into a 500) — the trap
[from-lua-and-scala-to-python.md #10](from-lua-and-scala-to-python.md#4--the-top-20-mistakes-on-day-one)
already names is using it as a per-call habit rather than a deliberate boundary, which hides real bugs
(a typo raising `NameError`, an `IndexError` from a logic mistake) behind the same generic handling as a
genuinely expected failure.

The common built-in shape worth having a mental map of:

| Base | Covers |
|---|---|
| `LookupError` | `IndexError`, `KeyError` — "asked for something that isn't there, by position or key" |
| `ValueError` | Right type, wrong value (`int("abc")`) |
| `TypeError` | Wrong type entirely (`"a" + 1`) |
| `ArithmeticError` | `ZeroDivisionError`, `OverflowError` |
| `OSError` | Filesystem, network, permission failures — `FileNotFoundError`, `PermissionError`, `ConnectionError` are subclasses |
| `AttributeError` | The name isn't an attribute of this object |
| `RuntimeError` | The catch-all for "something went wrong that doesn't fit a more specific category" |

**Which base to catch**: as specific as the failure mode actually is. Catch `KeyError` for a dict lookup
you expect might miss, not `Exception`. The specificity does two things at once — it documents exactly
what you expected to go wrong, and it lets anything you *didn't* expect propagate and surface loudly,
which is what you want in a graded round with a Q&A afterward.

---

## 2 · EAFP vs LBYL

**LBYL** ("Look Before You Leap") checks a condition first, then acts:

```python
d = {"a": 1}
if "a" in d:
    print(d["a"])
```

**EAFP** ("Easier to Ask Forgiveness than Permission") just acts, and handles the failure if it happens:

```python
d = {"a": 1}
try:
    print(d["a"])
except KeyError:
    print("missing")
```

Idiomatic Python is EAFP, and it's worth being able to argue *why*, not just cite it as convention:

- **One operation instead of two.** LBYL's check and act are two separate lookups (or a `hasattr` plus
  the real access) doing overlapping work; EAFP does the lookup exactly once.
- **No gap for the world to change in.** LBYL has a genuine correctness hazard, not just a style one: the
  condition can become false *between* the check and the act — a file that exists at the `os.path.exists`
  check but is deleted before the subsequent `open()`, a dict key present at `in` but removed by another
  thread before the subscript. EAFP has no such window, because there's only one operation, not two.
- **It composes with duck typing.** LBYL's `isinstance`/`hasattr` checks commit you to a specific type
  shape up front. EAFP just attempts the operation and lets anything that behaves correctly succeed,
  which is the same reason duck typing generally wins over nominal type checks in Python
  (see [oop-and-design-in-python.md §6](oop-and-design-in-python.md) on `Protocol` vs `ABC`).
- **It costs nothing extra on the success path.** [performance-notes.md §4](performance-notes.md) notes
  that `try/except` is cheap to *set up*, expensive to *raise* — which is exactly the case for EAFP: the
  common, no-exception path costs nothing beyond the `try` itself, and the exceptional path only pays
  when the exceptional thing actually happens. LBYL pays its "check" cost on every call, exceptional or
  not.

None of this means wrap everything in `try/except` — EAFP is about not pre-checking a condition your
attempted operation already has to check anyway, not about catching broadly. §9 covers where the line
actually is for a laptop-round project specifically.

---

## 3 · Designing a custom exception hierarchy for a library or service

One root exception per library or service, with meaningful subtypes underneath it, is the standard
shape — it lets a caller choose how broadly to catch: `except ServiceError:` for "anything this system
raises deliberately," or `except NotFoundError:` for one specific case, without ever needing to catch
plain `Exception` and risk swallowing an unrelated bug from somewhere else in the call stack.

```python
class ServiceError(Exception):
    """Base for everything this service raises deliberately."""

class NotFoundError(ServiceError):
    def __init__(self, resource_id):
        super().__init__(f"{resource_id!r} not found")
        self.resource_id = resource_id       # structured data, not just a message string

class ValidationError(ServiceError):
    def __init__(self, field, reason):
        super().__init__(f"{field}: {reason}")
        self.field = field

class UpstreamError(ServiceError):
    """Something downstream failed; see __cause__ for the original exception (SS4)."""

def get_user(user_id):
    if user_id != "u1":
        raise NotFoundError(user_id)
    return {"id": user_id}

try:
    get_user("u404")
except ServiceError as e:                     # catches NotFoundError, ValidationError, or UpstreamError
    print(f"{type(e).__name__}: {e}")
    print("resource_id:", e.resource_id)
```

Three design habits that hold up under time pressure:

- **A distinct class per meaningful failure mode**, not one exception type distinguished by parsing the
  message string. `if "not found" in str(e):` is a real anti-pattern — it breaks the moment the message
  wording changes, and it's not something `except` can dispatch on directly anyway.
- **Attach structured data as attributes** (`resource_id`, `field`) rather than only a formatted message
  — it lets a caller programmatically inspect what went wrong instead of re-parsing text meant for a
  human.
- **Don't build a hierarchy deeper than the problem needs.** A flat base plus a handful of direct
  subclasses, as above, covers the overwhelming majority of laptop-round-sized projects; a multi-level
  exception taxonomy is effort better spent elsewhere on the clock.

---

## 4 · Exception chaining — `raise ... from ...`, `from None`, `__context__` vs `__cause__`

When a `raise` happens **while already handling another exception**, Python automatically links them —
no `from` needed — via the new exception's `__context__`. This shows up in a traceback as "During
handling of the above exception, another exception occurred":

```python
def implicit_demo():
    try:
        {}["key"]
    except KeyError:
        raise ValueError("translated error")     # no `from` -- context still gets recorded automatically

try:
    implicit_demo()
except ValueError as e:
    print("cause:", e.__cause__)                  # None -- nothing explicit was set
    print("context:", type(e.__context__).__name__) # KeyError -- recorded automatically
```

**`raise NewError() from original`** additionally sets `__cause__` explicitly — and Python's traceback
wording changes to "The above exception was the direct cause of the following exception," a genuinely
different claim than `__context__`'s "this merely happened to be in flight." Use `__cause__` when you're
*deliberately* translating one exception into a more meaningful one for the caller:

```python
def explicit_demo():
    try:
        {}["key"]
    except KeyError as exc:
        raise ValueError("translated error") from exc   # deliberate translation

try:
    explicit_demo()
except ValueError as e:
    print("cause:", type(e.__cause__).__name__)   # KeyError -- explicit, deliberate
```

**`raise NewError() from None`** suppresses the chain from being *displayed* at all (it sets
`__suppress_context__ = True`; `__context__` is still recorded internally, just not shown) — the right
call when the original low-level exception is genuine noise to the caller, not useful context:

```python
class ConfigMissing(Exception):
    pass

def suppressed_demo():
    try:
        {}["key"]
    except KeyError:
        raise ConfigMissing("host") from None    # the KeyError is an implementation detail, not signal

try:
    suppressed_demo()
except ConfigMissing as e:
    print("cause:", e.__cause__)                    # None
    print("suppress_context:", e.__suppress_context__) # True -- traceback won't show the KeyError
```

The practical rule: use plain `raise NewError(...)` inside an `except` when the original exception is
useful debugging context and you're not claiming it *caused* the new one on purpose; use `from exc` when
you're deliberately translating a low-level failure into a more meaningful one for the caller; use
`from None` when the original is implementation noise nobody downstream should have to see.

---

## 5 · `try/except/else/finally` — what `else` is actually for

`else` runs only when the `try` block completes with **no exception**, and — this is the actual point of
it — code inside `else` is **not** covered by the `except` clauses above it. That separates "the risky
operation" from "what happens next only if it succeeded," so a bug in the success-path code doesn't get
misdiagnosed as the same failure the `except` was written for:

```python
def validate(value):
    if value == 0:
        raise ValueError("value cannot be zero")   # a SEPARATE failure, unrelated to parsing
    return 100 / value

def parse_and_use_bad(s):
    try:
        value = int(s)              # the risky operation this except is actually meant for
        result = validate(value)     # bug: a second, unrelated call sharing the same try block
    except ValueError:
        print("reported as 'could not parse' -- wrong diagnosis")
        return None
    return result

def parse_and_use_good(s):
    try:
        value = int(s)
    except ValueError:
        print("could not parse")
        return None
    else:
        return validate(value)      # only runs if parsing succeeded; a ValueError here is NOT
                                     # swallowed by the except above -- it propagates correctly
    finally:
        print("finally always runs, success or failure")

parse_and_use_bad("0")     # misdiagnosed: "could not parse" -- but parsing was never the problem
parse_and_use_good("0")    # correctly lets validate()'s ValueError propagate as its own error
```

`finally` runs unconditionally — success, handled exception, unhandled exception, even a `return` inside
`try` or `except` — which makes it the right place for cleanup that must always happen (closing a
resource, releasing a lock), and the wrong place for anything that should only happen on one specific
outcome.

---

## 6 · Traceback objects and the `traceback` module

`sys.exc_info()` returns `(type, value, traceback)` for whatever exception is currently being handled;
the traceback object chains stack frames via `.tb_next`. Day to day, the `traceback` module's formatting
helpers are what you actually reach for — turning an in-flight exception into a string suitable for
logging, rather than only ever letting it print to stderr and vanish:

```python
import traceback

def level_two():
    raise ValueError("deep failure")

def level_one():
    level_two()

try:
    level_one()
except ValueError:
    formatted = traceback.format_exc()      # the full traceback, as one string
    log_line = formatted.strip().splitlines()[-1]
    print("would log:", log_line)            # would log: ValueError: deep failure
```

`traceback.print_exc()` writes straight to stderr (the quick, no-string-handling version);
`traceback.format_exc()` gives you the string when something else — a logger, a bug report — needs to
consume it. For a laptop-round project, a bare unhandled exception's default traceback is normally
sufficient; reach for the module explicitly only when a caught exception needs to be logged with its
full context before your code decides how to recover or continue.

---

## 7 · `assert`, and why it must never validate runtime input

`assert condition, message` raises `AssertionError` if `condition` is falsy. The critical fact: **`assert`
statements are stripped entirely when Python runs with the `-O` flag** — not skipped, *removed*, along
with anything else gated on `__debug__`. Any validation logic living only inside an `assert` silently
stops running the moment someone runs the optimized interpreter:

```python
def validate(n):
    assert n > 0, "n must be positive"
    return n * 2

print("about to validate n = -1")
print(validate(-1))
print("still running -- assert had no effect")
```

```
$ python3 validate_demo.py
about to validate n = -1
Traceback (most recent call last):
  ...
AssertionError: n must be positive

$ python3 -O validate_demo.py
about to validate n = -1
-2
still running -- assert had no effect
```

The correct uses of `assert` are internal self-checks that document an assumption about your own code's
correctness — "this branch should be unreachable if my earlier logic is right" — never a check on
external input, user-provided arguments, or anything crossing a trust boundary. Those need a real
`raise ValueError(...)` (or a purpose-built exception, §3) that runs identically whether or not `-O` was
passed. A useful test: if the condition failing should ever be treated as *your caller's* bug rather than
*your own*, it's not an `assert`.

---

## 8 · Exception groups and `except*` — briefly (3.11+)

Concurrent code can fail in more than one place at once — several tasks in a
[`TaskGroup`](async-and-concurrency.md#9--structured-concurrency-and-timeouts) each raising their own
exception, for instance. `ExceptionGroup` bundles multiple exceptions into one object that can still be
raised and caught; `except*` (not `except`) is the matching syntax that catches only the exceptions in
the group matching a given type, letting the rest propagate as a smaller group:

```python
# 3.11+
def run_checks():
    errors = []
    for name, ok in [("rate_limit", True), ("fraud", False), ("blocklist", False)]:
        if not ok:
            errors.append(ValueError(f"{name} check failed"))
    if errors:
        raise ExceptionGroup("safety checks failed", errors)

try:
    run_checks()
except* ValueError as eg:
    print(f"handled {len(eg.exceptions)} check failure(s):")
    for exc in eg.exceptions:
        print(" -", exc)
```

This isn't yet part of the 3.10 baseline this program targets, but it's worth recognizing on sight —
`TaskGroup`'s own failure mode (§9 of [async-and-concurrency.md](async-and-concurrency.md)) is exactly
this mechanism, and it's precisely the shape of "run several independent checks, report every failure at
once instead of stopping at the first one."

---

## 9 · Error handling in the laptop round specifically

Grading is correctness 45% / clean code 35% / performance 20%, and exception handling is evidence for
the second number, not a category of its own — so the question is how much is *enough*, not how much is
possible.

**Enough**, concretely:

- Validate at the actual boundary between your code and the outside world — malformed input, an
  out-of-range argument, an unrecognized command — with a clear, specific exception, and **say out loud
  which convention you picked**: raise and let it propagate, or catch and skip with a comment explaining
  why. [io-and-parsing.md §6](io-and-parsing.md#6--parsing-command-string-protocols) already frames this
  exact decision for an unrecognized command in a dispatch parser — pick one on purpose, either is
  defensible, and say why.
- One `except` per genuinely distinct failure mode you've actually thought about, not a defensive wrapper
  around every internal call "just in case."

**Not enough — and actively costs you**, concretely: a bare `except: pass` (or `except Exception: pass`)
anywhere in a laptop-round submission. It reads as either "I don't trust my own code" or "I'm hiding
something," and it directly works against the demo-and-Q&A portion of the round — an interviewer probing
"what happens if the input is malformed" gets no useful answer from code that silently swallowed the
exact case they're asking about. Letting an unhandled exception crash loudly, with Python's own default
traceback, is a **better** outcome in a graded round than swallowing it silently — a crash is honest
about where the gap is; a silent catch hides it until the Q&A finds it anyway.

```python
def parse_entry(raw):
    return int(raw)   # raises ValueError on anything that isn't a plain integer string

entries = ["1", "2", "not-a-number", "4"]

print("bad -- swallows the failure silently:")
results_bad = []
for raw in entries:
    try:
        results_bad.append(parse_entry(raw))
    except Exception:
        pass                                   # "not-a-number" just vanishes, no trace
print(" ", results_bad)                          # [1, 2, 4] -- looks fine. it isn't.

print("good -- names the expected failure and says what happens on it:")
results_good = []
for raw in entries:
    try:
        results_good.append(parse_entry(raw))
    except ValueError as e:
        print(f"   skipping malformed entry {raw!r}: {e}")
print(" ", results_good)                         # same [1, 2, 4] -- but now there's a paper trail
```

Both versions produce the same `[1, 2, 4]` — the difference is entirely in whether anyone, including you
in the Q&A five minutes later, can tell that `"not-a-number"` was silently dropped rather than never
having been in the input at all.

---

## Interview questions

1. **What's the difference between a bare `except:` and `except Exception:`, and why does it matter?**
   A bare `except:` catches everything, including `KeyboardInterrupt` and `SystemExit`, which live
   outside `Exception` specifically so they aren't accidentally swallowed. `except Exception:` is the
   actual "catch anything reasonable" tool and is safe to use at a deliberate boundary; a bare `except:`
   is very rarely the right choice.

2. **Make the actual argument for EAFP over LBYL — not just "it's idiomatic."** It does the operation
   once instead of checking then doing it (two operations, overlapping work); it has no gap between a
   check and an act for the underlying state to change in, which LBYL genuinely does; and it costs
   nothing extra on the success path, since `try` is cheap to set up and only the actual failure path
   pays for raising.

3. **`raise NewError() from original_exc` versus a plain `raise NewError()` inside the same `except`
   block — what's the actual difference in the resulting exception object?** Both record the original as
   `__context__` automatically. The explicit `from` additionally sets `__cause__`, which changes the
   traceback's wording from "during handling of" to "was the direct cause of" — a real semantic claim
   that the translation was deliberate, not incidental.

4. **What does `raise X from None` actually do, and when would you use it?** It suppresses the original
   exception from being *displayed* in the traceback (`__suppress_context__ = True`), while still
   technically recording it in `__context__`. Use it when the low-level exception being replaced is
   implementation noise that would only confuse the caller, not context that helps them.

5. **What's `else` actually for in a `try/except/else` — how is it different from just putting that code
   at the end of `try`?** Code inside `try` is covered by the `except` clauses above it; code inside
   `else` is not. Putting "what to do after success" in `else` instead of at the end of `try` means an
   unrelated exception in that follow-up code propagates correctly instead of being misdiagnosed as the
   same failure the `except` clause was written for.

6. **Why must `assert` never be used to validate a function's runtime input?** `python3 -O` strips every
   `assert` statement from the compiled code entirely — not skips, removes — so any validation logic
   living only in an `assert` silently stops running under that flag. `assert` is for internal
   self-checks about your own code's assumed-correct logic; real input validation needs an actual
   `raise`, which runs identically regardless of `-O`.

7. **[Reported at Lyft]** A candidate wrapped the risky part of a laptop-round solution in
   `try: ... except Exception: pass` "to be safe." Why does that read badly to a grader, given clean code
   is 35% of the score?** It silently hides whatever the actual failure mode was, which is very likely
   the exact thing an interviewer probes in the follow-up Q&A — a candidate with no useful answer there
   looks worse than one whose code crashed loudly with Python's own traceback. A specific `except` for
   the one failure mode actually expected, with a comment on the convention chosen, reads as judgment;
   a blanket swallow reads as avoidance.

8. **What problem do exception groups and `except*` (3.11+) solve that a single `try/except` can't?**
   Concurrent code — several tasks running at once — can fail in more than one independent place in the
   same operation. `ExceptionGroup` bundles all of those failures into one object instead of losing all
   but the first; `except*` lets a handler catch only the exceptions of a given type from the group,
   letting the rest continue propagating as a smaller group instead of forcing one handler to sort
   through a single exception's type for what was really several unrelated failures.
