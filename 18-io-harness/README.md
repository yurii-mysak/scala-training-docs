# I/O Harness for the Laptop Round

> **Priority:** Required
> **Est. time:** 10 min
> **Track:** Both
> **HelloInterview:** none

---

## 1 · What this is

A genuinely runnable Python skeleton for the 90-minute laptop round: clone it, and inside a
minute you have a project that already reads input, parses it, calls a stub `solve()`, writes
output, and passes a test suite — all before you've written a line of problem-specific code.
Python 3.10+, standard library only, `unittest` for tests. No install step, ever.

## 2 · Why it exists

> "The dominant failure mode is input/output handling, not algorithms. Multiple candidates
> lost the round on stdin format, not logic. The expected I/O channel varies by problem
> (sometimes stdin/stdout, sometimes files) and must be confirmed in the first 15 minutes."
> — the programme spec

The round itself is unforgiving of exactly this failure: 15 minutes of discussion, ~60 minutes
of coding, 15 minutes of demo and Q&A, graded **correctness 45% / clean code 35% / performance
20%**, with an interviewer present but not screen-sharing or coaching. Every minute spent
re-deriving "how do I read stdin line by line without loading it all into memory" or "wait, why
did my dict lookup fail" (usually a stray `\r`) is a minute not spent on the actual problem —
and, per the grading weights, correctness and readability outweigh performance by more than
3-to-1. This project exists so I/O is never the reason the round is lost.

## 3 · 60-second clone-and-go quickstart

```bash
cd 18-io-harness
printf '1 2 3\n4 5\n\n6\n' | python3 solution.py     # -> 6 / 9 / 0 / 6, unmodified
python3 -m unittest discover tests                   # -> OK, well under a second
```

That's the whole quickstart. Both commands work with zero setup: no venv, no `pip install`,
nothing to download. If either one doesn't produce the output above, something is wrong with
the *environment* (wrong `python3`, wrong directory) — fix that before touching a single line
of interview logic. See [USAGE.md](USAGE.md) for the full 3-minute drill and the checklist for
wiring this to whatever I/O channel the interviewer actually names.

## 4 · What's in here

| File | Priority | Est. time | What it's for |
|---|---|---|---|
| [README.md](README.md) | Required | 10 min | this file |
| [USAGE.md](USAGE.md) | Required | 10 min | empty-dir-to-tested-project drill + first-five-minutes checklist |
| [RUNBOOK.md](RUNBOOK.md) | Required | 5 min | one-page card to keep open during the round |
| [SCALA.md](SCALA.md) | Recommended | 20 min | `scala-cli` fallback skeleton (not sbt) |
| [CSHARP.md](CSHARP.md) | Optional | 20 min | `dotnet new console` fallback skeleton |

Project layout (the part you actually clone):

```
18-io-harness/
├── solution.py           # the only file you edit during the round
├── harness/
│   ├── __init__.py
│   ├── io_utils.py       # stdin/file read+write, resolve_input(), field/command parsing
│   ├── records.py        # typed coercion, tolerant CSV splitting, a record factory
│   └── runner.py         # argparse CLI scaffold: --input --output --format --verbose
└── tests/
    ├── test_io_utils.py
    └── test_records.py
```

## 5 · How the pieces map to reported problem families

Per the programme spec, these problem families recur across independent laptop-round
reports. [17 — Lyft Laptop Round](../17-lyft-laptop-round/) works each one end to end; this is
the harness piece that matters most for each:

| Problem family (reports) | Worked problem | Harness piece |
|---|---|---|
| Stateful paginated fetch / read-N (7) | [01 — Stateful Paginated Fetch](../17-lyft-laptop-round/01-stateful-paginated-fetch.md) | `resolve_input()` + `iter_stdin_lines`/`iter_file_lines` — stream, don't buffer |
| Versioned/temporal KV store (6) | [02 — Versioned KV Store](../17-lyft-laptop-round/02-versioned-kv-store.md) | `io_utils.parse_command` for `SET key value` / `GET key` style lines |
| In-memory KV w/ begin-commit-rollback (4) | [03 — In-Memory KV Transactions](../17-lyft-laptop-round/03-inmemory-kv-transactions.md) | `io_utils.parse_command` for `BEGIN` / `COMMIT` / `ROLLBACK` |
| Trie typeahead / autocomplete / T9 (5) | [04 — Trie Typeahead / T9](../17-lyft-laptop-round/04-trie-typeahead-t9.md) | `io_utils.parse_command` / `split_fields` for query lines — the trie itself is algorithm-shaped, not I/O-shaped |
| Job scheduler / interval-to-worker (4) | [05 — Job Scheduler](../17-lyft-laptop-round/05-job-scheduler-workers.md) | `io_utils.parse_command`, same command-line shape |
| File / log / CSV parsing (4) | [06 — File/Log/CSV Parsing](../17-lyft-laptop-round/06-file-log-csv-parsing.md) | `records.split_csv_line`, `records.coerce`, `harness.io_utils.iter_file_lines` |
| Nested dot-path KV (2) | [07 — Nested Dot-Path KV](../17-lyft-laptop-round/07-nested-path-kv.md) | `records.coerce` for typed values off a raw string |

Minimum window substring and LRU variants are the two reported families that are purely
algorithm-shaped, not I/O-shaped — once input is parsed into records, that work is genuinely
orthogonal to this project. See [08 — Algorithms & Data Structures](../08-algorithms-and-data-structures/)
and [09 — Coding Challenges](../09-coding-challenges/) for that side of the prep.

## 6 · Related material in this repo

- [21 — Python for Interviews](../21-python-for-interviews/) — if Python syntax itself is the
  friction, start there (`from-lua-and-scala-to-python.md`, `stdlib-for-interviews.md`). This
  project assumes you can already read and write basic Python; it solves the I/O-plumbing
  problem, not the rusty-syntax problem.
- [17 — Lyft Laptop Round](../17-lyft-laptop-round/) — the worked problems this harness is
  built to host; §5 above maps each one to the harness function it actually uses.
- [12 — Testing → Unit Testing Fundamentals](../12-testing/Testing-unit_testing.md) — the
  AAA pattern and test-isolation principles there apply to `unittest` exactly as they do to
  ScalaTest; only the framework syntax differs.
- [08 — Algorithms & Data Structures](../08-algorithms-and-data-structures/) and
  [09 — Coding Challenges](../09-coding-challenges/) — once I/O and parsing are handled by
  this harness, this is the rest of what the round grades.

---

## Interview questions

**Why does `solution.py` route all input through a small I/O layer instead of calling
`sys.stdin`/`open()` directly inside the problem logic?**
Separation of concerns: parsing/channel logic is isolated, tested once, and never touched
again, so `solve()` stays pure — a list (or iterator) of records in, strings out — and is
trivial to unit-test without stdin or a real file at all.

**How would this handle a 10 GB input file without running out of memory?**
`iter_file_lines()` streams one line at a time inside a `with open(...)` block and never
materializes the whole file; `solve()` should do the same — consume its input iterator and
`yield` output rather than building full lists — so memory stays O(1) in input size.

**Why standard library only — no `pandas` for the CSV parsing, no `click` for the CLI?**
No install step is allowed to exist between clone and running code: no internet dependency,
no version drift, no "works on my machine." The stdlib `csv` module already handles quoted
fields and embedded delimiters correctly; `argparse` already handles flag parsing correctly.
Reaching for a dependency here would be solving a problem stdlib already solves.

**Walk me through what happens if the input has Windows line endings.**
`open()` on a real file applies universal-newline translation automatically, but a piped
`sys.stdin` does not always get the same translation — a raw `\r` can survive a naive
`line.rstrip('\n')` and silently corrupt a dict-key lookup or an exact string comparison
downstream. `strip_line_ending()` strips `\r\n`, lone `\r`, or lone `\n` explicitly, so it's
correct regardless of what the underlying stream already did.

**Your `split_csv_line` uses the `csv` module — what does that buy you over `line.split(',')`?**
Quote-awareness: a field like `"Doe, John"` contains a comma that must not become a field
break, and an escaped quote (`""`) inside a quoted field must not end it early. Hand-rolling
that state machine is a correctness risk under time pressure for no benefit — `csv.reader`
already gets it right.

**Why does `resolve_input()` only close the file it opened, and never `sys.stdin`?**
Closing `sys.stdin` is a needless side effect on the process's own standard input; the
function only owns the resource it created. It's also what makes the same context-manager
call correct for both channels — a caller loop is identical either way.

**How would you test this without piping real files around by hand?**
Monkeypatch `sys.stdin` with an `io.StringIO` for stdin cases, `contextlib.redirect_stdout`
for output assertions, and `tempfile.mkstemp()` for file-based cases — all stdlib, all fast,
exactly what `tests/test_io_utils.py` does.

**What's the tradeoff of `record_factory`'s dataclass approach versus plain dicts or tuples
per row?**
Named attribute access (`row.age`, not `row["age"]` or `row[1]`) turns a typo into an
`AttributeError` at the point of use instead of a silent `KeyError` or wrong-index bug deep in
logic, and self-documents the schema — for a handful of extra characters versus a raw tuple.
