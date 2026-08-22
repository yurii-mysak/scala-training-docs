# Timed Drill Log

> **Priority:** Optional
> **Est. time:** 10 min
> **Track:** Both
> **HelloInterview:** none

---

## 1 · How to Use This Log

Copy the table in §2 for each timed attempt and fill it in immediately afterward,
while it's fresh — not the next day. Be honest about a bad part-1 time; the point of
this log is pattern-spotting across several attempts, not scoring any single one.
Run attempts against the problems in this section using the protocol in
[00-protocol.md](00-protocol.md) — 15 minutes discovery, 60 minutes build, 15
minutes demo, timed for real.

A single drill tells you little. Five or six drills logged here will tell you
exactly where your process actually breaks, which is the more useful thing to know
going into the real round.

---

## 2 · Drill Log Template

| Date | Problem | Part 1 time | Part 2 reached? | I/O channel | What broke | Fix for next time |
|---|---|---|---|---|---|---|
| | | | | | | |
| | | | | | | |
| | | | | | | |
| | | | | | | |
| | | | | | | |
| | | | | | | |
| | | | | | | |
| | | | | | | |

Column notes:
- **Part 1 time** — wall-clock minutes from starting to write code to having a
  correct, working part 1 (not "clean," just correct).
- **Part 2 reached?** — yes / partial / no. "Partial" (started but didn't finish)
  still counts as reached — see [00-protocol.md](00-protocol.md) §7 on why
  attempting part 2 matters more than polishing part 1.
- **I/O channel** — stdin/stdout, file path, or "assumed wrong at first" — record
  when you guessed instead of confirming, that's a process bug worth catching.
- **What broke** — the specific thing that cost you time: a wrong assumption about
  output format, an off-by-one, forgetting to check for a part 2, over-polishing
  part 1, a test you didn't think to write.
- **Fix for next time** — one concrete change, not "be more careful."

---

## 3 · Target Times

Rough targets per family, assuming the [00-protocol.md](00-protocol.md) 15/60/15
split. "Hard stop" is the point past which you should move on regardless of whether
part 1 feels finished — see §5 on why blowing through a hard stop is itself the
signal worth logging.

| Family | Correct v1 | Refactored + tested | Hard stop before part 2 |
|---|---|---|---|
| [01 Stateful paginated fetch](01-stateful-paginated-fetch.md) | 15 min | 30 min | 40 min |
| [02 Versioned KV store](02-versioned-kv-store.md) | 15 min | 25 min | 35 min |
| [03 In-memory KV transactions](03-inmemory-kv-transactions.md) (part 1 only) | 10 min | 15 min | 20 min |
| [04 Trie typeahead / T9](04-trie-typeahead-t9.md) (part 1 only) | 15 min | 25 min | 35 min |
| [05 Job scheduler / workers](05-job-scheduler-workers.md) | 15 min | 25 min | 35 min |
| [06 File / log / CSV parsing](06-file-log-csv-parsing.md) (one sub-problem) | 15 min | 25 min | 35 min |
| [07 Nested dot-path KV](07-nested-path-kv.md) (stage 1 only) | 10 min | 20 min | 30 min |

These are targets for *reaching a working, reasonably clean part 1* — not the whole
problem. If you're consistently over the hard-stop column, that is the single most
actionable thing this log can tell you: it means part 1 is where your time is
leaking, and part 2 is never getting a fair shot in practice, exactly the failure
mode [00-protocol.md](00-protocol.md) §7 warns about.

---

## 4 · Reading the Pattern

After four or five logged drills, look across the rows, not just at any one of
them:

- **"What broke" clusters around I/O format** — the core lesson from
  [00-protocol.md](00-protocol.md) isn't sticking yet. Re-run the first-five-minutes
  checklist explicitly, out loud, on the next drill, rather than skipping it because
  you "know" the problem already.
- **Part 2 is rarely reached** — you're over-investing in part 1 polish. Set a
  visible timer at the hard-stop column above and move on when it goes off, even if
  part 1 feels unfinished.
- **Part 1 times are inconsistent across similar-difficulty families** — look at
  which specific families spike, and re-read that family's `.md` for the edge case
  or convention you keep missing.
- **The zip-and-run step keeps surfacing problems at demo time** — you're not
  testing the packaged artifact early enough; move that check earlier in your own
  process, not just in the last five minutes as [00-protocol.md](00-protocol.md) §6
  describes.

---

## Interview questions

1. How do you know when you're actually ready for a timed round like this, versus
   just having read the material?
   *Model answer:* a small number of drills logged with real wall-clock times and
   an honest "what broke" column — reading the approach for a problem family is not
   the same skill as producing working code against it under a visible clock.

2. What's the value of logging a *bad* attempt instead of just re-running until you
   get a clean one?
   *Model answer:* a bad attempt with an honestly recorded failure point is the
   input that reveals a real pattern (e.g., I/O assumptions, over-polishing part 1);
   discarding bad attempts in favor of only keeping clean runs erases the exact
   signal this kind of practice log exists to capture.

3. If your part 1 times are consistently within target but part 2 is never
   reached, what does that tell you?
   *Model answer:* the bottleneck isn't speed, it's a stopping-point discipline
   problem — time is being spent past where it should stop on part 1 (refining,
   re-optimizing, gold-plating) rather than moving on once "correct and reasonably
   clean" is reached.

4. How would you use this kind of log to decide what to study next, rather than
   just repeating the same drill?
   *Model answer:* look at which specific family or which specific column (time,
   part-2-reached, I/O channel) is the recurring outlier across several rows, and
   target that — re-reading a family's edge-case table if the same mistake shows up
   twice is a better use of time than a generic seventh attempt at a different
   problem.

5. Why time part 1 specifically, rather than just timing the whole 90 minutes as
   one block?
   *Model answer:* the whole-round time is set by the interview itself and isn't
   something a solo drill can fully replicate (no interviewer, no real stakes), but
   the part-1/part-2 split is exactly where the round is reportedly won or lost —
   isolating that boundary in the log turns a vague "did I finish in time" into a
   specific, trackable number.
