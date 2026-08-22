# Sliding window — drill set around LC 76

> **Priority:** Required
> **Est. time:** 3 h across the programme
> **Track:** Server
> **HelloInterview:** DSA → Sliding Window (fixed-length and variable-length)

[LC 76 Minimum Window Substring](lc76-minimum-window-substring.md) is the single most-repeated Lyft
problem — four independent candidate reports across 2022–2026, in Kyiv, Mexico City and elsewhere, and in
one case explicitly human-proctored. One report has it in the CS-fundamentals slot "with minor
adjustments", which means recognising the *technique* matters more than having memorised the one problem.

This file is the drill set around it. Work it in three passes rather than once.

---

## 1 · The two shapes

Almost every sliding-window problem is one of two shapes, and naming which one you are in is the first
thing to say out loud.

**Fixed-length window.** The window size is given. Slide by one: add the entering element, remove the
leaving element, evaluate. O(n) with no inner loop.

**Variable-length window.** You expand the right edge until a condition is satisfied, then contract the
left edge while it stays satisfied, recording the best result. Each element enters and leaves at most once,
so it is still O(n) despite the nested `while`. **Being able to explain why the nested loop is not
quadratic is a standard follow-up.**

LC 76 is the variable-length shape with a "contains all required characters" condition, which is tracked
with a counter of how many required characters are currently satisfied rather than by re-checking the whole
requirement each step. That counter trick is the actual insight and it is what transfers to variants.

---

## 2 · Pass one — build the technique

Do these in order, timed at 20 minutes each. HelloInterview has all four.

| # | Problem | LC | What it trains |
|---|---|---|---|
| 1 | Longest Substring Without Repeating Characters | 3 | Variable window, set/dict for membership. Already in this repo: [task7](../task7_longest_substring_without_repeating_characters.md) |
| 2 | Maximum Sum of Subarrays of Size K | — | Fixed window, the simplest shape |
| 3 | Longest Repeating Character Replacement | 424 | Variable window with a "cost to fix" condition |
| 4 | Permutation in String | 567 | Fixed window plus frequency matching — one step from LC 76 |

---

## 3 · Pass two — LC 76 itself, three times

1. **Cold, 25 minutes, no notes.** Write it, test it on `s="ADOBECODEBANC", t="ABC"` expecting `"BANC"`.
2. **As production code.** Named helper for the match counter, type hints, docstring, a `unittest` file
   covering: `t` longer than `s`, no valid window, `t` with duplicate characters, `s == t`, empty inputs,
   window at the start, window at the end.
3. **Explaining out loud while writing.** This is how it will actually happen.

The runnable solution and tests are in [lc76_minimum_window_substring.py](lc76_minimum_window_substring.py)
and [test_lc76_minimum_window_substring.py](test_lc76_minimum_window_substring.py) — write yours first,
then compare.

**The edge case people miss:** duplicate characters in `t`. `t = "AABC"` requires two `A`s. If you track
"characters seen" rather than "counts satisfied", you will pass the common test and fail this one.

---

## 4 · Pass three — the variations

One report says LC 76 came "with minor adjustments". Prepare for the adjustment rather than the exact
problem. Give each 15 minutes.

- Return **all** minimum windows, not just the first.
- Return the minimum window **by number of distinct characters** rather than length.
- `t` is a set of required characters with **minimum counts supplied separately**.
- The input is a **stream** — you cannot index backwards, only consume forward. This one is genuinely
  different and it connects to the read-N family in [../../17-lyft-laptop-round/](../../17-lyft-laptop-round/).
- Case-insensitive matching, or matching over words rather than characters.
- **Minimum Window Subsequence** (LC 727) — order must be preserved. A different algorithm, and worth
  knowing you cannot reuse the counter approach.

---

## 5 · The adjacent problem you also need

[LC 480 Find Median from Sliding Window](lc480_sliding_window_median.py) was asked in Toronto in October
2025, to a candidate who had been told to expect mediums. It is a sliding window in name but a **two-heap**
problem in substance, so it does not fall out of the technique above.

Do HelloInterview's **Heap → Median from Data Stream** (LC 295) first — it is the same two-heap invariant
without the removal complication — then LC 480, where the hard part is lazy deletion from a heap.

---

## 6 · The five-line template

Internalise the shape, not a memorised solution:

```python
def variable_window(s: str) -> int:
    left = 0
    best = 0
    state = {}                      # whatever the condition needs
    for right, ch in enumerate(s):
        # 1. expand: incorporate s[right] into state
        while condition_violated(state):
            # 2. contract: remove s[left] from state
            left += 1
        # 3. record: window s[left:right+1] is valid here
        best = max(best, right - left + 1)
    return best
```

For LC 76 the condition inverts — you contract *while the window is still valid*, recording as you shrink,
because you want the minimum rather than the maximum. Being able to state that inversion clearly is worth
more than speed.

---

## Interview questions

**1. Why is the nested while loop not O(n²)? [Reported at Lyft]**
Because the left pointer only ever moves forward and never resets. Across the whole run each element is
added once and removed once, so the total work in the inner loop is bounded by n. The amortised cost is
O(n) even though the code looks nested.

**2. How do you handle duplicate characters in the target string?**
Track required counts in a dict and maintain a `formed` counter of how many distinct characters have
reached their required count. A character contributes to `formed` only when its window count exactly equals
its required count, so `t = "AABC"` correctly demands two `A`s.

**3. What changes if the input is a stream you cannot index backwards?**
You cannot random-access `s[left]`, so the window itself must be materialised — a deque of the characters
currently in the window, popping from the left as you contract. The complexity is the same; the space is
now proportional to window size rather than free.

**4. When is sliding window the wrong tool?**
When the property is not monotonic in the window — that is, when extending the window can make an invalid
window valid again. Order-preserving subsequence problems like LC 727 are the classic case, and they need
dynamic programming or a different two-pointer formulation instead.

**5. What is the complexity of your LC 76 solution?**
O(|s| + |t|) time, since each character of `s` enters and leaves the window at most once and building the
requirement map is linear in `t`. Space is O(|t|) for the requirement counts, or O(alphabet) if you bound
it by the character set.
