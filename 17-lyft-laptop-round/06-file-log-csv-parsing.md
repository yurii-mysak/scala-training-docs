# File / Log / CSV Parsing

> **Priority:** Recommended
> **Est. time:** 45 min
> **Track:** Both
> **HelloInterview:** none

**4 independent first-hand reports.** Three related sub-problems are bundled into
this one file because they're reported as a cluster and share the same underlying
lesson: **this round's dominant failure mode is input/output handling, not
algorithms.** Every sub-problem here is I/O-shaped on purpose. See
[00-protocol.md](00-protocol.md).

---

## 1 · Three Problems, One Family

| Sub-problem | Ask |
|---|---|
| (a) K-th non-empty line | Print the K-th non-empty line of a large UTF-8 file without loading it into memory |
| (b) CSV splitting | Split one line into fields, honoring a custom separator and quoted fields — hand-rolled, not `csv.reader` |
| (c) Log aggregation | Compute p50 / p95 over a log file of latency values |

Confirm which one is actually being asked before building all three — see the
first-five-minutes checklist in [00-protocol.md](00-protocol.md).

---

## 2 · (a) K-th Non-Empty Line

**Approach:** iterate the file object directly (`for line in f:`) — this is already
lazy and buffered in Python, it does *not* read the whole file into memory at once.
Count non-empty lines as you go; stop and return as soon as the count hits k.

**Complexity:** O(k) time in the best/typical case (stop as soon as you find it), O(n)
worst case if k is near the end or absent; O(1) space beyond the current line.

**Edge cases:**
- Fewer than k non-empty lines in the file → return "not found" (`None`), not an
  error and not a crash.
- Blank lines and whitespace-only lines — decide (and state) whether whitespace-only
  counts as "empty." This file treats it as empty; that's a convention, not a given.
- Missing trailing newline on the last line — needs no special-casing; Python's line
  iteration yields that line exactly once regardless.

---

## 3 · (b) CSV Splitting (Hand-Rolled)

**Approach:** a small state machine over the characters of one line: track whether
you're currently inside a quoted field, and build up the current field's characters.
A delimiter outside quotes ends a field. A quote character immediately followed by
another quote, while inside a quoted field, is an *escaped* literal quote (RFC 4180
`""` → `"`) rather than the end of the field.

**Complexity:** O(length of the line), single pass, no backtracking.

**Edge cases:**
- Delimiter inside a quoted field → not a field boundary.
- Escaped quote (`""`) inside a quoted field → literal `"` in the output, field
  continues.
- Custom delimiter (tab, pipe, anything) — parameterize it, don't hardcode comma.
- Empty line → one empty field (`['']`), not zero fields.
- Trailing delimiter → a trailing empty field.
- Unmatched quote at end of line — this implementation is permissive (just ends the
  field at end-of-line); flag this as a scope question if the interviewer wants
  strict validation instead.

**Why hand-roll it instead of `csv.reader(..., delimiter=...)`?** The stdlib module
would solve the real-world version of this in one line — but the point of the
exercise, as reported, is demonstrating you can write the parsing state machine
yourself. Say so out loud: mention you know `csv` exists and would use it in
production, then build the hand-rolled version because that's what's being tested.

---

## 4 · (c) Log Aggregation — p50 / p95

**Approach:** stream the file, parse a numeric latency value out of each line
(supporting both a bare number and a `timestamp,latency` row by always taking the
*last* comma-separated field), skip lines that don't parse rather than aborting the
whole run, sort what's left, and compute percentiles via nearest-rank
(`ceil(p/100 * n)`, 1-indexed).

**Complexity:** O(n log n) — dominated by the sort; computing both p50 and p95 from
an already-sorted list is O(1) each after that.

**Edge cases:**
- Malformed lines (non-numeric) → skip, don't crash the whole aggregation.
- Empty file, or a file that's entirely malformed → return a "no data" result
  (`count=0`, percentiles `None`), not an exception — "no data" is a normal outcome
  for a log tool, not an error condition.
- Single-element input → both p50 and p95 equal that one value.

**Follow-up worth naming, not building:** this holds every value in memory to
compute an *exact* percentile — fine for an interview-sized file, not for a
firehose. At real production log scale, name an approximate streaming structure
(t-digest, HdrHistogram, reservoir sampling) as the answer to "how would this scale."

---

## 5 · Follow-ups

- (a): how would K-th-line change if the file could be read from the *end*
  (K-th-from-last)? Without an index, you'd need either two passes (count total
  non-empty lines, then re-scan to the right offset) or a bounded ring buffer of
  the last K lines seen.
- (b): how would you extend this to full multi-line CSV records (a quoted field
  containing a literal newline, spanning multiple physical lines)? The state
  machine would need to operate over the whole file stream rather than one line at
  a time, since "end of line" is no longer "end of record."
- (c): how would you compute percentiles without ever holding the full dataset —
  i.e., true streaming? Name t-digest or a fixed-size reservoir sample as the
  answer.

---

## Interview questions

1. **[Reported at Lyft]** Print the K-th non-empty line of a large file without
   loading it into memory.
   *Model answer:* iterate the file object line by line (already lazy/buffered in
   Python), count non-empty lines, stop as soon as the count reaches K; return "not
   found" if the file runs out first.

2. Why doesn't `for line in f:` load the whole file into memory?
   *Model answer:* file objects are iterators backed by a buffered reader — each
   iteration pulls the next line via an internal read buffer, not by materializing
   the entire file content up front.

3. **[Reported at Lyft]** Split a CSV line into fields, handling quoted fields that
   may contain the delimiter.
   *Model answer:* a single-pass state machine tracking "am I currently inside a
   quotes" plus the characters accumulated for the current field; a delimiter only
   ends a field when not inside quotes, and a doubled quote inside quotes is an
   escaped literal quote, not the end of the field.

4. Why write this by hand instead of using the `csv` module?
   *Model answer:* the exercise is testing whether you can construct the parsing
   logic yourself; acknowledge the stdlib alternative exists (it's the right choice
   in production) and then build the hand-rolled version since that's the actual
   ask.

5. How would you compute p50/p95 over a log file efficiently?
   *Model answer:* parse and collect the numeric values (skipping malformed lines),
   sort once (O(n log n)), then use nearest-rank indexing into the sorted list —
   O(1) per percentile after the sort.

6. What would you do differently if the log file were too large to fit in memory at
   all?
   *Model answer:* an exact percentile then requires either an external sort or an
   approximate streaming sketch (t-digest, HdrHistogram, reservoir sampling) that
   never holds the full dataset — name the trade-off (approximate but bounded
   memory) rather than trying to force an exact in-memory answer.

7. How do you handle a malformed line in the middle of a large log file?
   *Model answer:* skip it and continue rather than letting one bad line abort the
   whole aggregation — a partial result from mostly-good data is almost always more
   useful than a hard crash on log data, which is rarely perfectly clean.

8. What's the difference between nearest-rank and linear-interpolation percentile
   methods, and which did you use?
   *Model answer:* nearest-rank picks an actual observed value at a computed index
   (simpler, what's implemented here); linear interpolation blends between the two
   nearest observed values for a smoother estimate. Ops dashboards commonly report
   nearest-rank; confirm which one is wanted rather than assuming.
