# LC 76 — Minimum Window Substring

> **Priority:** Required
> **Est. time:** 45 min
> **Track:** Both
> **HelloInterview:** DSA / Sliding Window (variable)

---

## 1 · Problem Statement

Given two strings `s` and `t`, find the smallest contiguous substring of `s`
that contains every character of `t`, **including duplicates** (`t = "AAB"`
needs two `A`s and one `B` inside the window, not just one of each). Return
`""` if no such substring exists. Assume a unique answer is expected when one
exists; ties on length may be broken by returning any minimal window.

## 2 · Evidence

This is **Lyft's single most-repeated coding-screen question** in the research
behind this program — four independent, separately-sourced reports: Kyiv
2022, Mexico City 2026 (Senior loop, human-proctored — not an automated
OA), a 2026 Senior candidate who went on to pass the loop, and a Glassdoor
review from July 2026. No other CoderPad problem in the evidence set has that
many independent confirmations. Treat this as the one problem in the whole
set you cannot afford to be slow on.

The repo already covers two other members of the sliding-window family —
[Longest Substring Without Repeating Characters](../task7_longest_substring_without_repeating_characters.md)
(LC 3) and [Sliding Window Maximum](../task20_sliding_window_maximum.md)
(LC 239) — but neither is this problem. LC 3 is a *fixed-target-free* window
(grow while valid, no explicit target multiset) and LC 239 is a
*fixed-size* window solved with a monotonic deque, not a counter. LC 76 is
the *variable-size, target-multiset* member of the family, and it is the one
that generalizes furthest — see the follow-ups below and
[`lc76-family-drills.md`](lc76-family-drills.md) for the full progression.

## 3 · Key Insight

Track two counters implicitly with one `dict`/`Counter`: for every character,
`need[c] = (occurrences required by t) - (occurrences currently in the
window)`. Also track a single scalar `missing` = total characters still owed,
counting multiplicity. Expand the window on the right until `missing == 0`
(the window is *valid*), then greedily contract from the left while it stays
valid, recording the shortest valid window seen. Because `need[c]` is allowed
to go negative (over-collected or never-required characters), you never need
a second "have" dict and never need to compare two counters character by
character — the single scalar `missing` tells you everything about validity
in O(1).

## 4 · Approach & Complexity

1. Build `need = Counter(t)`, `missing = len(t)`.
2. Walk `right` over `s`. If `need[s[right]] > 0` before decrementing, one
   fewer character is owed, so `missing -= 1`. Always `need[s[right]] -= 1`.
3. While `missing == 0`: the window `[left, right]` is valid.
   - Compare its length to the best seen; update if smaller.
   - Try to shrink: increment `need[s[left]]`; if that pushes it `> 0`, the
     window just became invalid, so `missing += 1`. Advance `left`.
4. Return the recorded best window, or `""` if none was ever valid.

Each index enters and leaves the window exactly once, so both pointers move
strictly forward across the whole run.

- **Time:** O(|s| + |t|) — one pass to build `need`, one two-pointer pass
  over `s` where `left` and `right` each advance at most `|s|` times.
- **Space:** O(|Σ|) where Σ is the alphabet of `t` (at most 128/256 for
  ASCII, unbounded but still O(distinct chars in t) for Unicode).

Reference implementation: [`lc76_minimum_window_substring.py`](lc76_minimum_window_substring.py).
Tests: [`test_lc76_minimum_window_substring.py`](test_lc76_minimum_window_substring.py).

## 5 · Edge Cases

- `t` longer than `s` → impossible, short-circuit to `""` before the main
  loop (a correct implementation would also just never find a valid window,
  but the early return avoids a wasted full pass).
- `t` or `s` empty → `""`.
- Duplicate characters in `t` (`t = "AABC"`) — the multiplicity is the entire
  point of using a counter instead of a set; a set-based "contains all
  distinct chars of t" solution silently gives a wrong, shorter answer here.
  This is the single most common bug candidates ship on this problem.
  **[Reported at Lyft]** — the human-proctored Mexico City report specifically
  flagged that the interviewer probed on repeated characters in `t` after
  the first working pass.
- No valid window exists at all (`t` has a character not in `s`) → `missing`
  never reaches 0 → return `""`.
- Multiple minimal windows of the same length → returning the first one
  found (leftmost) is accepted; the strict `<` comparison in step 3 already
  does this for free.
- Case sensitivity and non-alphabetic characters — the reference solution
  makes no assumption about the alphabet; `Counter` works over arbitrary
  hashable characters, so it is correct as written for Unicode input too.

## 6 · Follow-Up Variations

These are the standard extensions of this exact pattern used across the
industry to probe whether a candidate has the *template* or just memorized
one instance of it. None of these specific follow-ups are independently
confirmed as asked at Lyft — they are included because the sliding-window
family is confirmed as heavily drilled, and this is how interviewers
generically extend it once the base solution lands quickly:

- **"Return every minimal window, not just one."** Same scan; instead of
  tracking a single best, collect all windows tied for the current minimum
  length (reset the list when a strictly shorter one is found).
- **"What if you can't use extra space proportional to the alphabet?"** Not
  achievable in general for arbitrary alphabets without changing the
  complexity class — good candidates should say so rather than contorting
  the solution, and note the space is already O(|Σ(t)|), not O(|s|).
- **LC 3 (Longest Substring Without Repeating Characters)** — the
  "no-target" variant already in this repo; same two-pointer skeleton, no
  counter/`missing` needed, condition flips from "valid → shrink" to
  "invalid → shrink."
- **LC 239 (Sliding Window Maximum)** — the *fixed-size* variant, already in
  this repo, solved with a monotonic deque instead of a counter; useful to
  contrast why a deque is the right tool there but wrong here (no ordering
  relation to exploit on window contents, only membership counts).
- **LC 340 (Longest Substring with At Most K Distinct Characters)** — same
  skeleton as LC 76 but the validity condition is "distinct key count ≤ k"
  instead of "counter fully satisfied"; good gauge of whether the candidate
  understands `missing` as a *general validity signal*, not a special-cased
  trick.
- **Streaming input** ("what if `s` arrives as a stream and you can't
  index backward?") — the algorithm already never re-reads a character once
  `left` passes it, so it is naturally streaming-compatible if you buffer
  only the current window; a good answer identifies that the window itself
  is the only state that must be retained.
- **Multiple targets** ("smallest window containing all of `t1` OR any one
  of `t2`") — tests whether the candidate can adapt `need`/`missing` to a
  different validity predicate rather than being locked into "counter must
  hit exactly zero."

## 7 · Reference Solution

See [`lc76_minimum_window_substring.py`](lc76_minimum_window_substring.py) —
`min_window(s, t) -> str`, stdlib-only (`collections.Counter`), with a
`__main__` demo. Unit tests in
[`test_lc76_minimum_window_substring.py`](test_lc76_minimum_window_substring.py)
cover the duplicate-character trap, empty inputs, `t` longer than `s`, and
ties.

---

## Interview questions

1. **Why does `need[c]` need to be allowed to go negative? What breaks if you
   clamp it at zero?** **[Reported at Lyft]** If you clamp at zero you lose
   the information "this character is over-collected" — when you later
   remove one copy of an over-collected character while shrinking the
   window, you cannot tell whether the window is still valid without
   clamping causing a false transition to "missing" one step early or late.
   The unclamped negative value is exactly what makes the O(1) `missing`
   update correct.
2. **Walk through why the algorithm is O(n) and not O(n·k) for some k.**
   Both pointers are monotonically non-decreasing and each can advance at
   most `|s|` times total across the entire run (not per outer-loop
   iteration), so the total work across both pointers is O(|s|), not
   O(|s|) per position of the other pointer.
3. **How would you adapt this to at-most-K-distinct-characters (LC 340)
   instead of an exact target string?** Replace `need`/`missing` with a
   single `dict` of counts and track `len(dict)` as "distinct chars in
   window"; shrink while `len(dict) > k` instead of while `missing == 0`,
   and the "record the best" step moves to *after* the shrink loop instead
   of inside it (you want the longest valid window, not the shortest).
4. **What's the failure mode if you use a `set` of characters in `t` instead
   of a multiset?** It silently accepts a window with fewer occurrences of a
   repeated character than `t` requires — e.g. `t = "AA"` would be satisfied
   by a single `"A"`. This is the most common bug on this exact problem.
5. **Can you solve this without a hash map, given a bounded alphabet?**
   Yes — replace `Counter` with a fixed-size `list[int]` of length 128 (or
   256) indexed by `ord(ch)`; same algorithm, marginally faster constant
   factor, same asymptotic complexity. Worth mentioning if the interviewer
   pushes on performance (graded 20% on the laptop round, though this is a
   CoderPad screen where it matters less).
6. **How do you handle Unicode / multi-byte characters?** Python strings are
   already sequences of code points, so `Counter`/`dict` keyed on `str`
   characters works unchanged; the fixed-size-array optimization from the
   previous answer does not generalize without a much larger table or a
   fallback hash map, which is itself worth saying out loud.
7. **What's the space complexity, precisely?** O(|Σ(t)|) — the number of
   *distinct* characters in `t`, not O(|t|) and not O(|s|). Interviewers
   sometimes push on this distinction specifically.
8. **How would you test this function?** Empty `s`, empty `t`, `t` longer
   than `s`, no valid window, whole-string-is-the-answer, duplicate
   characters in `t`, and a case with two windows tied for shortest — see
   `test_lc76_minimum_window_substring.py` for the concrete cases used here.
