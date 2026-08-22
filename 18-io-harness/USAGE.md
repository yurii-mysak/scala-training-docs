# Using the I/O Harness

> **Priority:** Required
> **Est. time:** 10 min
> **Track:** Both
> **HelloInterview:** none

---

## 1 · The 3-minute drill: empty directory to running, tested project

Run this once, before the round, so the steps are muscle memory — and again the moment the
laptop round actually starts, before the interviewer has finished describing the problem.

| Time | Step | Command |
|---|---|---|
| 0:00–0:30 | Get the project onto the machine (unzip / copy / clone) | — |
| 0:30–0:45 | Move into it | `cd 18-io-harness` |
| 0:45–1:15 | Confirm the interpreter — no venv, no install, ever | `python3 --version` (need 3.10+) |
| 1:15–1:45 | Prove the environment works, unmodified | `python3 -m unittest discover tests` |
| 1:45–2:15 | Prove the whole pipeline works end to end, unmodified | `printf '1 2 3\n4 5\n' \| python3 solution.py` |
| 2:15–3:00 | Open `solution.py`. You're ready to listen to the actual problem. | — |

Expected output at 1:15: `OK` (a few dozen tests, well under a second — see
[RUNBOOK.md](RUNBOOK.md) for exact counts). Expected output at 1:45: `6` then `9`.

The point of steps 1:15 and 1:45 isn't the code — it's proof. If either one fails, you've
found an *environment* problem (wrong `python3` on `PATH`, wrong directory, a corrupted clone)
with three minutes gone instead of finding it at minute 50 when your actual solution mysteriously
won't run. Every failure past this point is your logic, not your setup.

## 2 · First-five-minutes checklist, once the interviewer states the problem

This operationalizes the one instruction that matters most for this round: confirm the channel
before writing any logic (see [README.md](README.md) for why).

- [ ] **Input channel** — stdin, or a file? If a file, is the path fixed, or passed as an
      argument?
- [ ] **Output channel** — stdout, or a file? What exact shape (one result per line? a single
      value? something else)?
- [ ] **Record shape per line** — freeform text, whitespace-separated fields, comma/CSV, or a
      `CMD arg1 arg2` command line?
- [ ] **Leading header or count line?** — e.g. a first line `N` followed by exactly `N`
      records. Classic hidden trap; ask explicitly if the sample doesn't make it obvious.
- [ ] **Edge cases** — can input be empty? Can a line be blank? Any stated bound on size (does
      it need to stream, or is loading it all fine)?
- [ ] **Wire it** — set `--format` (or call the right `harness.records`/`harness.io_utils`
      function inside `solve()`) and confirm the `--input`/`--output` plumbing *before* writing
      any problem logic.
- [ ] **Smoke-test the wiring** — run `solution.py` through the *real* channel (piped stdin or
      a real file), not just `solve()` called from a REPL, on a tiny hand-typed example.

## 3 · Wiring cheatsheet

| Interviewer says | Do this |
|---|---|
| "Read from stdin" | Default — nothing to change; `python3 solution.py` with piped input |
| "Read from a file, pass the path as an argument" | `python3 solution.py --input path/to/file` |
| "First line is a record count `N`" | `count = int(records[0])`, then work over `records[1:]` |
| "Each line is comma-separated" | `python3 solution.py --format csv`, or call `records.split_csv_line(line)` inside `solve()` |
| "Lines look like `SET key value` / `BEGIN` / `COMMIT`" | keep `--format lines` (default), call `io_utils.parse_command(line)` inside `solve()` |
| "Write results to a file" | `python3 solution.py --output path/to/out.txt` |
| "Print progress/debug info" | write to `sys.stderr` (or use `--verbose`, which already does), never to stdout |

## 4 · What not to do in the first five minutes

- **Don't start the algorithm before the channel is confirmed and wired.** This round's
  documented failure mode is I/O, not logic — verify the plumbing works on a trivial example
  first.
- **Don't assume blank-line or trailing-newline behavior.** Ask if it's unclear, or rely on the
  harness's defaults, which already preserve blank lines and handle a missing final newline.
- **Don't `print()` for debugging if stdout is the graded output.** A stray debug line
  corrupts the exact output the interviewer diffs against. Use `--verbose` (writes to
  `sys.stderr`) instead.

## 5 · Practice the drill against a real problem

Run this drill against the actual worked problems in
[17 — Lyft Laptop Round](../17-lyft-laptop-round/) instead of a synthetic example — each one
states its own input/output channel, so treat the channel as unknown, run the checklist above,
then check your wiring against that file's own solution. Doing this once for real, before the
round, is what makes the 3-minute version fast under actual time pressure.

---

## Interview questions

**Walk me through the first five minutes of your process when you get a new problem.**
Confirm the I/O channel, format, and edge cases (the checklist above) before writing any
logic; wire the harness to match; run a trivial smoke test through the real channel; only then
start on the algorithm.

**Why confirm the I/O channel before the algorithm, specifically?**
Because the documented failure mode for this round is I/O handling, not incorrect logic — and
you cannot verify correctness against a channel that isn't wired yet, so skipping this step
risks discovering a format mismatch at minute 55 instead of minute 5.

**Halfway through, the interviewer clarifies the input format differently than you assumed —
what do you do?**
Because parsing is isolated behind a small number of functions and a `--format` flag, re-wiring
is a one-line change (or swapping which `harness.records`/`harness.io_utils` call `solve()`
makes), not a rewrite of the solution logic.

**How do you avoid debug output corrupting your submitted output?**
Route every diagnostic print to `sys.stderr` — the `--verbose` flag already does this — and
never put a bare `print()` inside `solve()` itself.

**What's the first thing you run after cloning, before touching the actual problem?**
The unmodified test suite and the unmodified `solution.py` worked example — this separates an
environment failure from a logic failure and costs under a minute.

**Why does the whole drill need to fit in 3 minutes, out of a 60-minute coding budget?**
Because 3 minutes is under 5% of the coding time, and the alternative — re-deriving stdin
handling live — is exactly the failure mode this round is documented to punish; the drill
converts a recurring risk into a fixed, small, rehearsed cost.
