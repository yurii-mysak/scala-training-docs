# The 90-Minute Laptop Round Protocol

> **Priority:** Required
> **Est. time:** 30 min read (+ 90 min per timed drill)
> **Track:** Both
> **HelloInterview:** none

This is the round with the highest failure rate in the loop, and it fails on
mechanics as often as it fails on algorithms. Everything in this file is a
repeatable drill, not just background reading — run it against every problem in
this section before you consider yourself ready. See
[09-timed-drill-log.md](09-timed-drill-log.md) to track your attempts.

---

## 1 · What This Round Actually Is

Own laptop, own IDE. The interviewer is on the call with video/audio off and no
screen share — you are genuinely alone with the problem for the coding block.
Internet access is allowed. At the end, you zip your project and email it. Graded:

| Dimension | Weight |
|---|---|
| Correctness | 45% |
| Clean code | 35% |
| Performance | 20% |

Notice what that ordering implies: **readable, working code beats complete-but-ugly
code**, and finishing the whole problem is explicitly not required. Performance is
the smallest slice of the three — it is not nothing, but it is not where most of
your time should go either.

No heavy frameworks. Don't reach for Spring, Jersey, or an equivalent — this is
meant to be a small, self-contained program, and pulling in a framework to scaffold
routing or DI for a single-file exercise reads as poor judgment, not sophistication.

**The dominant reported failure mode is input/output handling, not algorithms.**
Multiple candidates have lost this round on stdin format, not logic. The expected
I/O channel varies by problem — sometimes stdin/stdout, sometimes file paths — and
is not something you should assume; confirm it in the first fifteen minutes, every
time, even when you think you already know.

---

## 2 · The 15 / 60 / 15 Split

| Phase | Minutes | Goal |
|---|---|---|
| Discovery | 0–15 | Understand the real scope: I/O channel, output format, whether tests are wanted, and — critically — whether there's a part 2 |
| Build | 15–75 | Working code first, then refactor, then tests, in that order (see §4) |
| Demo + Q&A | 75–90 | Run the zipped project from scratch, walk through it, answer design questions |

Treat the boundaries as real. Spending 25 minutes in discovery because you're
unsure of the I/O format is a worse outcome than confirming it in 3 minutes and
getting 12 extra minutes of build time.

---

## 3 · First Five Minutes Checklist

Ask these explicitly, out loud, before writing code — do not infer them from the
problem statement's phrasing:

- **Confirm the I/O channel.** stdin/stdout, or file paths passed as arguments? Do
  not assume either. Every solution file in this section supports both explicitly
  for exactly this reason — see any `main()` for the pattern.
- **Confirm the expected output format.** Exact strings? One result per line? A
  specific sentinel for "not found" (`null`, `NULL`, empty string, an exception)?
  Getting the *value* right and the *format* wrong still reads as a failure to a
  grading script or a skimming interviewer.
- **Confirm whether they want tests submitted.** If yes, budget time for it
  explicitly in the Build phase rather than bolting it on in the last five minutes.
- **Clarify the multi-part structure. Ask what part 2 is — even if no one has
  mentioned a part 2.** This is the single highest-leverage question in the whole
  round. See §7.
- **Restate the problem back in your own words.** This surfaces silent
  misunderstandings before you've written a line of code, when they're free to fix.
- **Ask about edge cases the interviewer actually cares about** — empty input,
  invalid input, expected scale — rather than guessing which ones matter to them.

---

## 4 · Sequencing: Working, Then Refactor, Then Tests

In that order, every time:

1. **Get something correct and compiling first**, even if it's the most naive
   approach that satisfies the example. A working brute force beats a half-built
   optimal solution when time runs out — and per §1, correctness is worth more
   than performance.
2. **Then refactor for clarity** — extract functions, name things honestly, add
   type hints, remove duplication. This is where the 35% clean-code weight is won
   or lost, and it is much cheaper to do once something already works than to try
   to write "clean" code you haven't validated yet.
3. **Then write tests** — even three or four cases covering the stated edge cases
   is a strong signal of engineering discipline. This is also naturally where you
   catch the bugs refactoring didn't.

Resist optimizing early. A premature optimization pass in step 1 is time spent
before you even know the naive version is correct.

---

## 5 · When to Stop Optimising

Correctness is 45%, clean code is 35%, performance is 20%. A correct O(n log n)
solution with clear names and no duplication **beats** a buggy or unreadable O(n)
one — the smallest-weighted dimension is not where a struggling attempt should be
spending its remaining time.

Practical rule: once you've hit the complexity class that's obviously appropriate
for the problem (each family's `.md` in this section states one — e.g. O(log n)
reads for [versioned KV](02-versioned-kv-store.md), O(n log n) for
[job scheduling](05-job-scheduler-workers.md)), **stop**. Spend what's left on
clarity, edge cases, and tests instead of shaving another constant factor.

---

## 6 · The Demo and Zip-and-Email Step

- **Test the exact zip-and-run path with five minutes still on the clock**, not
  after time is called. Unzip into a clean directory, run it exactly the way
  you're about to tell the interviewer to run it. A project that only runs from
  inside your IDE's cached state is a failure at this step, discovered too late to
  fix.
- Walk through the demo in a fixed order: show the input, show the output, then
  narrate one or two design decisions — don't wait to be asked.
- Have two or three sentences ready per non-obvious design decision ("why a dict
  here instead of a sorted list" — see the read/write trade-off in
  [versioned KV](02-versioned-kv-store.md) for a worked example of exactly this
  kind of answer).
- **Know your Big-O cold.** You will be asked for the time and space complexity of
  what you just built, and "I'd have to think about it" is a worse answer here
  than in almost any other part of the round.

---

## 7 · Part 2 Is Not Optional

Read this twice if you only read one section of this file.

Every reported failure in this section that names a specific cause points at the
same thing: a candidate treated the stated problem as the *whole* problem, when
the interviewer's actual expectation included a follow-up extension that was
either mentioned in passing or never mentioned at all until the candidate said
they were done. The most direct case: a candidate finished a plain key-value store
and was told **"we expect that part to be covered"** when transactions — the
unstated part 2 — came up. See [in-memory KV transactions](03-inmemory-kv-transactions.md).

- "Finishing is not strictly required" (§1) means you don't have to complete
  *every* part fully — it does **not** mean part 2 is optional to attempt.
- **Always ask "is there a part 2?" in the first five minutes**, even when nothing
  has been offered. If the answer is yes, you now know the real scope before you've
  committed your time budget to the wrong problem.
- Budget time on that assumption: don't spend more than ~35-40 minutes polishing
  part 1 if a part 2 is likely — and for the families in this section, it usually
  is. A rougher part 1 plus a started part 2 demonstrates more than a polished part
  1 alone, given the grading weights in §1.

---

## 8 · Printable Pre-Flight Checklist

```
BEFORE YOU TYPE ANYTHING (0-15 min)
[ ] Confirmed I/O channel (stdin/stdout vs file path)
[ ] Confirmed exact output format (including the "not found" sentinel)
[ ] Confirmed whether tests are expected
[ ] Asked "is there a part 2?" -- even if unprompted
[ ] Restated the problem back in my own words
[ ] Asked which edge cases the interviewer cares about

WHILE BUILDING (15-75 min)
[ ] Naive-but-correct version working against the example first
[ ] Refactored for clarity: names, extracted functions, type hints
[ ] Wrote 3-5 tests covering the edge cases I identified
[ ] Started part 2 -- do not spend the whole block polishing part 1
[ ] Stopped optimising once I hit the obviously-right complexity class

BEFORE TIME IS CALLED (75-90 min)
[ ] Zipped the project and ran it fresh, from a clean unzip, exactly as I'll
    describe it to the interviewer
[ ] Can state time and space complexity without hesitating
[ ] Have 2-3 sentences ready per non-obvious design decision
[ ] Zip emailed
```

---

## Interview questions

These are not algorithm questions — they're the questions interviewers actually ask
*during* this round, about your approach and process, not about a specific data
structure. Have short, concrete answers ready before the round starts, not
improvised during it.

1. Walk me through your approach before you start coding.
   *Model answer:* restate the problem, confirm I/O channel and output format, ask
   whether there's a part 2 and whether tests are wanted, then describe the data
   structure and algorithm you're planning before writing a line — a spoken plan
   costs a minute and prevents a wasted rewrite.

2. Why did you choose this data structure over an alternative?
   *Model answer:* name the alternative specifically and state the trade-off in one
   sentence (e.g., "a sorted list plus binary search over a dict, because writes
   dominate and appends are O(1)") — see [versioned KV](02-versioned-kv-store.md)
   §4 for a fully worked version of this exact answer.

3. What's the time and space complexity of what you just built?
   *Model answer:* state both without hedging, and name what dominates (the sort?
   the per-call work? the recursion depth?) — "I'd need to check" is a weaker
   answer than a correct one with a small mistake in it.

4. How would you test this?
   *Model answer:* name the specific edge cases for *this* problem, not a generic
   "unit tests and integration tests" — empty input, boundary sizes, invalid input,
   and whatever this problem's own tricky case is (each family's `.md` in this
   section has an Edge Cases table for exactly this).

5. What would you do differently with more time?
   *Model answer:* name one concrete thing — the follow-up extension you didn't
   reach, a complexity improvement you deliberately deferred, or a validation gap
   you're aware of — not a vague "polish it more."

6. What's part 2 going to be, in your opinion — how would you design for it before
   I even tell you?
   *Model answer:* name the most natural extension of the stated problem (a
   reliability concern, a nesting/recursion concern, a scale concern) and note
   where your current design would or wouldn't accommodate it cleanly — this shows
   you're thinking one step ahead, which is the entire point of §7 above.

7. How do you decide when code is "clean enough" to stop refactoring?
   *Model answer:* once names are honest, duplication is gone, and a stranger could
   read the function without you narrating it — further polishing past that point
   trades away time better spent on tests or the next part of the problem.

8. Why didn't you finish the whole problem?
   *Model answer:* state the grading weights back plainly — correctness and clean
   code outweigh completeness — and point at what you prioritized and why, rather
   than treating an unfinished problem as something to apologize for.
