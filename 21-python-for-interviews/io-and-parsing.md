# I/O and Parsing

> **Priority:** Required
> **Est. time:** 40 min
> **Track:** Both
> **HelloInterview:** none

**The dominant failure mode in Lyft's laptop round is input/output handling, not algorithms.**
Multiple candidates have lost the round on stdin format, not logic. The expected channel varies
by problem — sometimes stdin/stdout, sometimes files — and has to be confirmed with the
interviewer in the first 15 minutes, before you commit to a shape. This file is the concrete
Python for every I/O shape that comes up, so the 15-minute discussion produces working code
instead of a guess. For the harness that exercises these patterns end-to-end, see
[../18-io-harness/](../18-io-harness/README.md).

---

## 1 · `sys.stdin` patterns

Three shapes cover nearly everything a laptop-round problem asks for:

```python
import sys

# 1. Bulk-read everything, split on ANY whitespace -- the fastest way to grab a flat
#    stream of numbers/tokens regardless of how they're spaced or newlined:
data = sys.stdin.read().split()
nums = list(map(int, data))

# 2. Line-oriented: the problem cares about individual lines (commands, log entries, CSV rows).
#    Iterating sys.stdin directly is lazy -- it does not read the whole input into memory first.
for line in sys.stdin:
    line = line.rstrip("\n")          # the trailing newline is included; strip it yourself
    if not line:
        continue                       # skip blank lines rather than crashing on them
    handle(line)

# 3. A known, fixed number of lines up front (a common competitive-programming convention:
#    first line is a count N, followed by exactly N lines of data):
n = int(sys.stdin.readline())
rows = [sys.stdin.readline().rstrip("\n") for _ in range(n)]
```

**Why not `input()`?** `input()` is built for one interactive prompt at a time — it works, but
reading hundreds of tokens through repeated `input()` calls is slower (per-call overhead) and
more awkward to structure than a single bulk read. Under a clock, prefer pattern 1 for
whitespace-separated data and pattern 2 for line-oriented data; reach for `input()` only if the
problem is genuinely interactive (prompt, read one line, respond).

**Confirm before coding, not after:** does the harness pipe input via stdin, or pass a file
path as an argument? Getting this wrong costs more of the round than any algorithm choice will.

---

## 2 · Reading files

```python
with open("data.txt", encoding="utf-8") as f:   # `with` closes the file even if the body raises
    text = f.read()                               # whole file, as one str

with open("data.txt", encoding="utf-8") as f:
    for line in f:                                # lazy -- one line resident in memory at a time
        process(line.rstrip("\n"))
```

Always pass `encoding="utf-8"` explicitly. Python 3's default text-mode encoding is
platform-dependent (`locale.getpreferredencoding()`) — it usually happens to be UTF-8 on Linux,
which is what the grading machine almost certainly is, but "usually happens to be" is exactly
the kind of assumption that isn't worth carrying into a graded round when the fix is one keyword
argument.

**Streaming a large file** — the recurring "file/log/CSV parsing" problem family, and the
pattern that keeps memory use flat regardless of file size — is exactly the line-iteration form
above, never `f.read().splitlines()` for anything you suspect might be large:

```python
count = 0
with open("access.log", encoding="utf-8") as f:
    for line in f:                    # never holds more than one line in memory
        if "ERROR" in line:
            count += 1
```

`pathlib.Path.read_text()` is a fine shortcut for small files you need whole, but it's exactly
`open(...).read()` under the hood — same all-in-memory tradeoff. See
[stdlib-for-interviews.md §11](stdlib-for-interviews.md#11--pathlib).

---

## 3 · `argparse`

```python
import argparse

parser = argparse.ArgumentParser(description="process a log file")
parser.add_argument("path")                          # positional, required
parser.add_argument("--limit", type=int, default=10)  # optional, with a default
parser.add_argument("-v", "--verbose", action="store_true")   # boolean flag
args = parser.parse_args()

print(args.path, args.limit, args.verbose)
```

For a laptop round, `argparse` is usually more ceremony than the problem needs — reading
`sys.argv` directly (`sys.argv[1]`, with a manual length check) is fine for one or two required
arguments and is faster to write correctly under a clock. Reach for `argparse` when the
interviewer explicitly wants a CLI with flags, help text, or several optional arguments; it pays
for itself once you're past two or three arguments with real validation needs.

---

## 4 · Encoding and newline handling

- **Always pass `encoding="utf-8"`** to `open()` for text you read or write — don't rely on the
  platform default (§2).
- **Universal newlines are on by default** in text mode: reading a file with `\r\n` line endings
  gives you back `\n` automatically, so `line.rstrip("\n")` is enough regardless of whether the
  source file came from Windows or Unix. Writing in text mode does the reverse translation using
  the platform's native line ending, unless you pass `newline=""` to `open()` and control it
  yourself — which is exactly what the `csv` module needs you to do (§5).
- **`str` vs `bytes`.** `open(path)` (no `"b"` mode) gives you `str`, decoded per `encoding=`.
  `open(path, "rb")` gives you `bytes`, no decoding at all. Mixing the two — concatenating a
  `str` and a `bytes`, or writing `str` to a binary-mode file — raises `TypeError` immediately;
  it doesn't silently do the wrong thing, which is one of the few forgiving failure modes here.

---

## 5 · `csv` module quirks

The core API (`reader`/`writer`/`DictReader`/`DictWriter`) is covered in
[stdlib-for-interviews.md §10](stdlib-for-interviews.md#10--csv). Three things that specifically
cost time under pressure:

- **`newline=""` on `open()` is not optional** when reading or writing CSV — the module owns
  line-ending handling itself and double-processes it otherwise.
- **Every value comes back as a `str`**, even ones that look numeric — `row["age"]` is `"30"`,
  not `30`. Convert explicitly (`int(row["age"])`) rather than assuming the type.
- **A field containing the delimiter must be quoted**, and the `csv` module handles this for you
  on write — but if you're hand-splitting a line with `line.split(",")` instead of using the
  module (tempting for "just one quick line"), an embedded comma inside a quoted field silently
  breaks your split. If the input is genuinely CSV, use the `csv` module even for a single line;
  don't hand-roll delimiter splitting once quoting is possible.

---

## 6 · Parsing command-string protocols

A recurring laptop-round shape: stdin (or a file) delivers one command per line — `SET key
value`, `GET key`, `BEGIN`, `COMMIT` — and you dispatch each to a handler. This exact shape
underlies the **in-memory KV store with begin/commit/rollback** family (reported independently
four times) and the job-scheduler family. The idiom is the same regardless of which commands are
involved: split the line, look the command up in a dict of handlers, call it.

```python
def run(lines, kv):
    out = []
    handlers = {
        "SET": lambda args: kv.set(args[0], args[1]),
        "GET": lambda args: out.append(kv.get(args[0])),
        "BEGIN": lambda args: kv.begin(),
        "COMMIT": lambda args: kv.commit(),
        "ROLLBACK": lambda args: kv.rollback(),
    }
    for line in lines:
        line = line.strip()
        if not line:
            continue
        cmd, *args = line.split()          # cmd first, everything else is arguments
        handlers[cmd](args)                # KeyError here means an unrecognized command --
                                            # decide up front whether that should crash or be ignored
    return out
```

Two edge cases worth handling explicitly, because they're exactly what an interviewer probes in
the Q&A after your demo: a **value containing spaces** (`line.split()` breaks it into extra
tokens — use `line.split(maxsplit=2)` to cap how many pieces you split into, or `shlex.split`
if values can be quoted, e.g. `SET key1 "hello world"`), and an **unrecognized command** (decide
and say out loud whether that's a `KeyError` you let propagate, or a line you skip with a
warning — either is defensible, but pick one on purpose).

```python
import shlex
shlex.split('SET key1 "hello world"')   # ['SET', 'key1', 'hello world'] -- respects the quoting
```

**Full worked example** — a transactional KV store, the exact recurring family, built with a
stack of undo-diffs so nested `BEGIN`/`COMMIT`/`ROLLBACK` are correct, wired to the dispatch
pattern above:

```python
class TransactionalKV:
    """SET/GET/BEGIN/COMMIT/ROLLBACK over a single dict, using a stack of
    undo-diffs so ROLLBACK restores exactly what its transaction changed.
    Writes apply eagerly to `_data`; GET always reads `_data` directly --
    the undo stack is write-only bookkeeping, never a read path. Nested
    BEGIN is supported: COMMIT merges a frame's undo-diff into its parent
    so an outer ROLLBACK still undoes it.
    """
    _MISSING = object()

    def __init__(self):
        self._data = {}
        self._undo_stack = []      # list[dict[key, old_value_or_MISSING]]

    def begin(self) -> None:
        self._undo_stack.append({})

    def set(self, key, value) -> None:
        if self._undo_stack:
            frame = self._undo_stack[-1]
            if key not in frame:                      # remember the pre-txn value ONCE per frame
                frame[key] = self._data.get(key, self._MISSING)
        self._data[key] = value

    def get(self, key):
        return self._data.get(key)

    def rollback(self) -> None:
        if not self._undo_stack:
            raise RuntimeError("no transaction in progress")
        for key, old in self._undo_stack.pop().items():
            if old is self._MISSING:
                self._data.pop(key, None)
            else:
                self._data[key] = old

    def commit(self) -> None:
        if not self._undo_stack:
            raise RuntimeError("no transaction in progress")
        frame = self._undo_stack.pop()
        if self._undo_stack:                          # merge into the parent transaction
            parent = self._undo_stack[-1]
            for key, old in frame.items():
                parent.setdefault(key, old)


def run_commands(lines):
    kv = TransactionalKV()
    out = []
    handlers = {
        "SET": lambda args: kv.set(args[0], args[1]),
        "GET": lambda args: out.append(kv.get(args[0])),
        "BEGIN": lambda args: kv.begin(),
        "COMMIT": lambda args: kv.commit(),
        "ROLLBACK": lambda args: kv.rollback(),
    }
    for line in lines:
        cmd, *args = line.split()
        handlers[cmd](args)
    return out


results = run_commands([
    "SET a 1",
    "GET a",
    "BEGIN",
    "SET a 2",
    "GET a",
    "ROLLBACK",
    "GET a",
])
print(results)      # ['1', '2', '1']
```

Wired to real stdin, the same function is `run_commands(sys.stdin)` — a file object (and
`sys.stdin`) is itself iterable line-by-line, so no explicit `.readlines()` is needed.

---

## Interview questions

1. **Why is I/O handling, not algorithm choice, the most common way to lose Lyft's laptop
   round?** Because the problem doesn't specify the channel and format up front — stdin vs a
   file, bulk vs line-oriented, whitespace vs a strict format — and a candidate who starts
   coding against a guessed format either wastes time re-deriving it mid-round or submits
   working logic against the wrong I/O shape, which grades as broken.

2. **You need to read a few hundred whitespace-separated integers as fast as possible. What do
   you write, and why not `input()` in a loop?** `sys.stdin.read().split()` then
   `map(int, ...)` — one bulk read and split, versus hundreds of individual `input()` calls each
   paying their own overhead.

3. **What does `newline=""` on `open()` actually do, and why does the `csv` module require it?**
   It disables Python's own newline translation in text mode, so the bytes on disk pass through
   unmodified. `csv` needs this because it does its own line-ending handling (`\r\n` by
   default) — without it, the text layer and the csv module can each try to translate line
   endings, potentially doubling them.

4. **A command-dispatch parser does `cmd, *args = line.split()`. What breaks it, and what's the
   one-line fix?** A value containing whitespace gets split into extra tokens instead of staying
   one argument. Fix: cap the split with `line.split(maxsplit=N)`, or use `shlex.split(line)` if
   values can be quoted.

5. **[Reported at Lyft]** The laptop round has repeatedly asked for an in-memory KV store with
   `begin`/`commit`/`rollback`. What's the core data structure that makes rollback correct for
   nested transactions?** A stack of "undo diffs" — one dict per open transaction, recording only
   the pre-transaction value of each key touched during that transaction (once, the first time
   it's touched). Rollback pops the top frame and replays it backwards; commit pops the top frame
   and merges its diff into the parent frame's, so an outer rollback still undoes it.

6. **Streaming a 2GB log file counting lines that match a pattern — what's the memory-safe
   pattern, and what's the trap?** `for line in f:` inside a `with open(...) as f:` block — each
   iteration holds one line, not the whole file. The trap is reaching for
   `f.read().splitlines()` (or `f.readlines()`) out of habit, which defeats the whole point by
   materializing every line as a list up front.

7. **Why explicitly pass `encoding="utf-8"` to every `open()` call rather than relying on the
   default?** The default text encoding is platform-dependent (`locale.getpreferredencoding()`);
   it's very likely UTF-8 on the Linux grading machine, but "very likely" is a needless risk to
   carry into a graded round when naming it explicitly costs nothing.

8. **How do you handle an unrecognized command in a dispatch-dict parser, and why does it
   matter which way you choose?** Either let the `KeyError` propagate (fail loud, correct if
   malformed input should be a hard error) or catch it and skip/log the line (fail soft, correct
   if the input may legitimately contain noise). Either is defensible; picking one and saying
   why out loud is what the interviewer is actually listening for.
