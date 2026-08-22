# Laptop Round Runbook

> **Priority:** Required
> **Est. time:** 5 min
> **Track:** Both
> **HelloInterview:** none

One page. Keep it open during the round. Full explanations live in [README.md](README.md) and
[USAGE.md](USAGE.md) — this is the condensed, glance-at-it version.

---

## 1 · Commands

```bash
cd 18-io-harness

python3 -m unittest discover tests          # whole suite
python3 -m unittest tests.test_io_utils     # one file
python3 -m unittest tests.test_records      # the other file

python3 solution.py                                        # stdin -> stdout
python3 solution.py --input in.txt --output out.txt         # file -> file
python3 solution.py --format csv --verbose                  # CSV records; log to stderr
```

## 2 · Five-second channel check

Input: stdin or file? Output: stdout or file? Record shape: raw line / whitespace / CSV /
`CMD arg1 arg2`? Header or count line first? Can a line be blank? Full checklist:
[USAGE.md §2](USAGE.md#2--first-five-minutes-checklist-once-the-interviewer-states-the-problem).

## 3 · Python gotchas under time pressure

**Mutable default argument** — created once, shared across every call:
```python
def add(item, bucket=[]):        # WRONG: same list object every call
    bucket.append(item); return bucket

def add(item, bucket=None):      # RIGHT
    if bucket is None: bucket = []
    bucket.append(item); return bucket
```

**Integer division floors toward `-inf`, not toward zero:**
```python
5 / 2    # 2.5   (true division, always float)
5 // 2   # 2     (floor division)
-5 // 2  # -3    (floors, not truncates — surprising if you know C/Java/Scala's `/`)
```
Need truncation toward zero on possibly-negative operands: `int(a / b)` or `math.trunc(a / b)`,
not `//`.

**`sort()` vs `sorted()`** — the classic bug is `xs = xs.sort()`, which sets `xs` to `None`:
```python
xs.sort()             # in place, returns None
ys = sorted(xs)        # new list, xs untouched
xs.sort(key=fn, reverse=True)   # both accept key= / reverse=
```

**Dict ordering** — insertion order is guaranteed since Python 3.7 (language guarantee, not an
implementation detail) — safe to rely on for deterministic output. `set`/`frozenset` still have
**no** guaranteed order — never rely on set iteration order for output.

**`copy.deepcopy` cost** — recursively copies every nested object; fine once, expensive in a
loop. The KV-store-with-transactions family is the classic trap: deepcopy-per-`BEGIN` on a long
trace turns an O(1)-ish op into O(store size) each time. Prefer `copy.copy` (shallow), or an
undo-log, unless you actually need a full deep snapshot.

**`is` vs `==`** — `is` checks identity, not value. Small ints (-5..256) happen to be cached, so
`a is b` can accidentally look right in a quick test and then fail for larger numbers. Always
use `==` for value comparison; use `is None`, never `== None`, for the None check specifically.

**Truthiness on legitimate zero/empty values** — `if x:` is `False` for `0`, `''`, `[]`, `{}`,
and `None` alike:
```python
if record.get("count"):         # WRONG if count == 0 is a valid, meaningful value
    ...
if record.get("count") is not None:   # RIGHT
    ...
```

## 4 · What to do when you have 15 minutes left

1. **Stop adding new logic.** Freeze scope — no new edge cases you haven't already hit.
2. **Get the common case running end to end on the real channel.** A correct answer for most
   inputs via the harness beats a half-built handler for the last edge case — finishing is not
   strictly required, and correctness (45%) is graded on what runs, not what's ambitious.
3. **Delete dead/experimental code**, don't leave it commented out. Half-finished alternate
   approaches read as messy, and clean code is 35% of the grade.
4. **Re-run the tests and re-run `solution.py`** against the interviewer's actual sample input,
   exactly as it will be graded. Catch a crash now, not during the demo.
5. **Add short comments on anything non-obvious.** A one-line reason beats a clever line with
   none — readability is graded; cleverness on its own is not.
6. **Sweep the obvious I/O traps**: empty input, a blank line, the last line missing a trailing
   newline, an off-by-one on a count/header line. This round's failure mode is I/O — spend the
   last minutes here, not on a further algorithmic optimization.
7. **Do not start a rewrite.** A working O(n²) beats a broken/incomplete O(n log n); performance
   is 20% of the grade, correctness and clean code are 80% combined.
8. **Prepare your 60-second explanation for the demo**: what it does, one deliberate tradeoff
   and why, and the one thing you'd fix with more time.

---

## Interview questions

**You're at minute 45 of 60 and only half done — what do you do?**
Freeze scope, get the common case running end to end through the real I/O channel, strip dead
code, re-test against the actual sample input, and prepare a short explanation of what's done
and what isn't — correctness and clean code are 80% of the grade combined, so a smaller working
submission beats a larger broken one.

**What's wrong with `def f(x, cache=[]):`?**
The default list is created once, at function-definition time, and shared across every call
that doesn't pass its own — so appends silently accumulate across unrelated calls. Use
`cache=None` and create the list inside the function body instead.

**What does `-7 // 2` evaluate to, and why might that surprise someone coming from Java or C#?**
`-3`. Python's `//` floors toward negative infinity rather than truncating toward zero, so it
disagrees with most C-family languages' `/` on negative operands.

**Does Python's `dict` preserve insertion order? Since when?**
Yes, guaranteed since 3.7 (it was a CPython implementation detail in 3.6). Plain `set` and
`frozenset` still do not guarantee any order.

**`xs.sort()` vs `sorted(xs)` — what's the difference, and what's the classic bug?**
`.sort()` mutates in place and returns `None`; `sorted()` returns a new list and leaves the
original alone. The classic bug is `xs = xs.sort()`, which silently sets `xs` to `None`.

**When does `copy.deepcopy` become a real performance problem in an interview solution?**
Anywhere it's called once per operation on a large or deeply nested structure — e.g.
snapshotting an entire KV store on every `BEGIN` across a long transaction trace — which turns
what looks like a cheap operation into one that's O(store size) every time it runs.
