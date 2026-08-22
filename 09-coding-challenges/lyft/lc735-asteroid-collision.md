# LC 735 — Asteroid Collision

> **Priority:** Required
> **Est. time:** 30 min
> **Track:** Both
> **HelloInterview:** DSA / Stack (incl. Monotonic Stack)

---

## 1 · Problem Statement

An array of integers represents asteroids in a row. Each moves at the same
speed; the sign gives direction (positive = right, negative = left) and the
magnitude gives size. Same-direction asteroids never meet, since they move
at identical speed. When a right-moving asteroid is later followed (to its
right, in the array) by a left-moving one, they eventually meet and
collide: the smaller one explodes, equal sizes both explode, and a survivor
that is still moving left keeps colliding with whatever is now behind it in
the stack. Return the state of surviving asteroids, left to right, after all
collisions resolve.

## 2 · Evidence

Reported as sitting **at the top of the Lyft-tagged frequency list** for
LeetCode's own company-tag data — i.e. of the problems specifically tagged
as asked at Lyft, this one shows up most often by that independent signal,
separate from the first-hand interview reports backing the rest of this set.
It is also a clean single-topic monotonic-stack problem, which makes it an
efficient 30-minute drill even outside its reported frequency.

## 3 · Key Insight

Only a **right-moving asteroid can ever collide with something arriving
after it**, and only if that later arrival is moving **left**. That means a
stack is exactly the right structure: push right-movers and standalone
left-movers; when a new left-mover arrives, it can only possibly collide
with the *top* of the stack (never anything deeper, until the top is
resolved) — so the collision resolution is a `while` loop against the stack
top, not a scan. This is what makes it a "monotonic stack" problem in the
same family as Trapping Rain Water and Sliding Window Maximum already in
this repo: the stack only ever needs to look at its own top to make a local
decision, and that decision is enough to guarantee global correctness.

## 4 · Approach & Complexity

For each asteroid `a`, while `a` is moving left (`a < 0`) and the stack is
non-empty and its top is moving right (`stack[-1] > 0`):

- If `|stack[-1]| < |a|`: pop the top (it explodes), keep looping — `a` is
  still alive and may hit whatever is now on top.
- If `|stack[-1]| == |a|`: pop the top, mark `a` as destroyed too, stop.
- Else (`|stack[-1]| > |a|`): mark `a` as destroyed, stop (top is untouched).

After the loop, push `a` only if it was not marked destroyed.

- **Time:** O(n) amortized — every asteroid is pushed at most once and
  popped at most once across the whole run, so the total work across all
  the inner `while` loops is bounded by n, even though any single outer
  step can pop many elements.
- **Space:** O(n) for the stack in the worst case (no collisions at all).

Reference implementation: [`lc735_asteroid_collision.py`](lc735_asteroid_collision.py).
Tests: [`test_lc735_asteroid_collision.py`](test_lc735_asteroid_collision.py).

## 5 · Edge Cases

- **Equal-magnitude collision** — both explode; a common bug is popping the
  stack top but forgetting to also discard the incoming asteroid.
- **A left-mover meets a stack of several right-movers of increasing size**
  (`[1, 2, 3, -10]`) — the `while` loop must keep consuming survivors from
  the stack as long as the incoming asteroid is still bigger, not stop after
  one comparison.
- **All moving the same direction** — no collisions at all; the array is
  returned unchanged. Easy to verify but a good smoke test that the
  `while` guard conditions are all correctly `and`-ed together, not
  accidentally `or`-ed.
- **A right-mover immediately followed by a left-mover that is destroyed on
  the first comparison** (`top > -a`) — must not still push `a` afterward;
  the `alive` flag (or equivalent) has to gate the final push.
- **Negative-then-positive adjacency** (`[-2, 1]`) — never collides; moving
  apart, not toward each other. This is the single most common conceptual
  error: candidates sometimes think any sign change is a collision.
- **Empty input / single asteroid** — return as-is, no loop iterations
  needed for the latter.

## 6 · Follow-Up Variations

- **"What if asteroids can also start already overlapping / at the same
  position?"** — outside the problem's stated model (they're points moving
  at fixed uniform speed with distinct starting positions); worth
  explicitly noting the assumption rather than silently special-casing it.
- **"Different speeds per asteroid."** — breaks the simple left-to-right
  scan, since a slower right-mover could be caught by a faster right-mover
  behind it (a same-direction "collision" the base problem explicitly rules
  out); this becomes a genuinely different problem requiring a time-of-
  collision computation, good to name as out of scope for the stack
  approach rather than force-fit it.
- **"Return the full collision history (timestamps and pairs), not just
  survivors."** — record each pop event with what it collided against
  instead of silently discarding it; same algorithm, richer output.
- **"Do it online, one asteroid arriving at a time, with survivor queries
  in between."** — the stack approach already processes asteroids one at a
  time and is naturally online; a query for "current survivors" is just
  reading the stack at that moment, O(1) to expose.
- **Compare to Trapping Rain Water / Sliding Window Maximum** — good
  candidates can articulate the family resemblance: all three use a stack
  or deque where only the top (or both ends) is ever compared against the
  incoming element, and each element enters and leaves the structure at
  most once, which is what gives all of them O(n) despite an inner loop.

## 7 · Reference Solution

See [`lc735_asteroid_collision.py`](lc735_asteroid_collision.py) —
`asteroid_collision(asteroids) -> List[int]`, stdlib-only, with a
`__main__` demo covering the classic LeetCode examples. Tests in
[`test_lc735_asteroid_collision.py`](test_lc735_asteroid_collision.py)
cover equal-size collisions, chain reactions, and both all-same-direction
cases.

---

## Interview questions

1. **[Reported at Lyft]** (via LeetCode's own company-tag frequency data)
   **Walk me through your approach before you code anything.** State the
   monotonic-stack insight up front: only a right-moving top can collide
   with an incoming left-mover, so each new asteroid only ever needs to
   look at the stack's top, resolved with a `while` loop for chain
   reactions.
2. **Why is this O(n) overall, given the nested `while` loop inside the
   `for` loop?** Amortized analysis: every asteroid is pushed at most once
   and popped at most once across the *entire* run, so total pushes +
   pops is bounded by 2n regardless of how the pops are distributed across
   outer iterations.
3. **What's the bug if you forget the `alive`/destroyed flag and always push
   `a` after the while loop?** An asteroid that was just destroyed by a
   larger survivor gets incorrectly pushed onto the stack anyway, producing
   a result with more surviving asteroids than actually exist.
4. **Why doesn't `[-2, 1]` collide?** They're moving apart — the left one
   moves further left, the right one moves further right — so they never
   meet; a collision requires a right-mover *before* (to the left of, in
   array order) a left-mover.
5. **How would you adapt this if asteroids could have different, arbitrary
   speeds?** State that the stack approach relies on uniform speed to
   guarantee same-direction asteroids never meet; with variable speed you'd
   need to compute actual meeting times/positions, which is a materially
   different (geometry/simulation) problem, not a stack tweak.
6. **What's the worst-case space usage, and when is it achieved?** O(n),
   achieved when there are no collisions at all (e.g. all moving right, or
   moving-left-then-right with no right-then-left adjacency) — every
   asteroid ends up on the stack.
7. **How would you test this function well?** Equal-size collisions,
   chain reactions against a stack of several survivors, both
   all-one-direction cases, a left-mover immediately destroyed on first
   comparison, and empty/single-element input — see
   `test_lc735_asteroid_collision.py` for the concrete cases used here.
