# LC 716 — Max Stack

> **Priority:** Required
> **Est. time:** 35 min
> **Track:** Both
> **HelloInterview:** DSA / Stack (incl. Monotonic Stack)

---

## 1 · Problem Statement

Design a stack supporting the usual `push(x)` / `pop()` / `top()`, plus:

- `peekMax()` — return the current maximum value without removing it.
- `popMax()` — remove **and** return the current maximum value. If the
  maximum occurs more than once, remove only the **top-most** occurrence
  (the one closest to the top of the stack). Every element that was above
  it must remain on the stack afterward, in its original relative order.

## 2 · Evidence

Flagged in the evidence behind this program as **easy-tagged, but actually
fiddly** — LeetCode itself lists LC 716 as Hard, and that gap between "an
interviewer expects this to be quick" and "the O(1)/O(log n) popMax
discussion is genuinely subtle" is exactly why it belongs in the Required
tier: it is a fast trap for a candidate who thinks a design problem this
short must be easy, ships the naive O(n) `popMax`, and then flounders when
asked to do better.

## 3 · Key Insight

**push/pop/top/peekMax are easy — `popMax` is the entire problem**, because
of one specific constraint: *remove the top-most occurrence, not any
occurrence.* A plain max-heap keyed only by value cannot express "which one
is closest to the top of the stack" — you need a secondary key that encodes
recency, and because `heapq` is a **min-heap**, that secondary key has to be
**negated insertion order**, not insertion order itself. Getting this
backwards is the single most common bug on this problem: it silently
returns the *right value* while removing the *wrong node*, which a shallow
test suite (one that never has duplicate values at different stack depths)
will not catch.

The second insight is **lazy deletion**: once you're maintaining a heap
alongside a linked structure, a plain `pop()`/discard-from-the-middle
doesn't need to touch the heap at all — just remove the node from the
linked list and leave its heap entry as "already dead." The next time that
entry would surface at the top of the heap, discard it and keep going.
Every id is pushed once and popped from the heap at most once over the
object's whole lifetime, which is what keeps this O(log n) *amortized*
rather than O(n).

## 4 · Approach & Complexity

Two implementations are given side by side in the reference file, on
purpose — this is the natural order to present them in an interview:

**`MaxStackSimple`** — a normal stack plus a parallel stack mirroring the
running max at each depth (identical idea to LC 155 Min Stack). `popMax`
has no way to jump to the target directly, so it pops into a buffer until
the top equals the current max, discards that element, then replays the
buffer back through `push`.

- **Time:** O(1) push/pop/top/peekMax; **O(n)** popMax (worst case, the max
  is at the bottom).
- **Space:** O(n) for the parallel max-stack.

**`MaxStack`** — a doubly linked list (sentinel head/tail) for O(1)
push/pop/top and O(1) removal of any node once you hold a reference to it,
plus a heap of `(-value, -id)` for O(log n) access to the max, with lazy
deletion resolving staleness.

- **Time:** O(1) pop/top; **O(log n) amortized** push/peekMax/popMax (a
  single call can do more work if many stale entries have piled up, but the
  total cleanup work across the object's lifetime is bounded by the total
  number of pushes).
- **Space:** O(n) — one linked-list node and one heap entry per live push.

Reference implementation: [`lc716_max_stack.py`](lc716_max_stack.py) (both
classes). Tests: [`test_lc716_max_stack.py`](test_lc716_max_stack.py).

## 5 · Edge Cases

- **Duplicate values at different stack depths** — the case that actually
  exercises the "top-most occurrence" rule; three `5`s at three different
  depths, `popMax()` must remove only the most-recently-pushed one, and the
  other two must survive in their original relative order. This is the
  primary test case in the reference suite.
- **`popMax` immediately followed by `push` of the same value, then
  `popMax` again** — checks that the heap/id bookkeeping doesn't confuse
  the freshly-pushed value with the just-removed one (they can share the
  same numeric value but must have distinct ids).
- **Negative values** — `max()` and the heap comparisons must not assume
  non-negative input; the reference implementation makes no such
  assumption, but it is worth stating explicitly, since a candidate who
  reaches for a sentinel like `float('-inf')` or `0` as an "empty" marker
  can introduce a subtle bug here.
- **Single-element stack** — `popMax`/`peekMax`/`pop`/`top` must all work
  without special-casing an "empty after this" state incorrectly.
- **Interviewer asks you to prove `popMax` removes the right node, not just
  the right value** — this is precisely why the reference test suite
  includes a case with three tied values at three depths, and why a
  differential/fuzz test (see below) is worth mentioning even if you don't
  have time to write one live.

## 6 · Follow-Up Variations

- **"What's the actual complexity of `popMax`, precisely — not just
  O(log n)?"** — the honest answer is O(log n) *amortized*: an individual
  call can pop several stale heap entries before finding a live one, but
  each entry is created by exactly one push and destroyed by exactly one
  pop-from-heap over the object's life, so the total cleanup work across N
  operations is O(N log N), i.e. O(log N) amortized per operation. Good
  candidates state the amortized qualifier unprompted.
- **"Can you do it with `sortedcontainers.SortedList` instead?"** — yes, and
  it is simpler to write, but it is a third-party dependency; worth naming
  as the "if this were production code, not a stdlib-only screen" answer.
- **"What if `push` needs to support arbitrary comparable objects, not just
  ints?"** — the heap ordering already works on any `__lt__`-comparable
  type via the same `(-value, -id)` trick as long as negation is
  meaningful; for non-numeric types, wrap in a `functools.total_ordering`
  reverse-comparator instead of literal negation.
- **"Now make it thread-safe."** — same answer as the read4-II problem: a
  single lock around each public method is the honest minimal fix, at the
  cost of serializing all access.
- **"How would you test this beyond hand-written cases?"** — a randomized
  differential test that runs the same random operation sequence against
  both `MaxStackSimple` (obviously correct, easy to trust) and `MaxStack`
  (fast, easier to get subtly wrong) and asserts they agree at every step.
  See `TestDifferential` in the test file — this exact technique is what
  caught tie-break bugs during authoring of this reference solution and is
  worth naming out loud as a general strategy for "two implementations of
  the same contract, one fast and one obviously-correct."

## 7 · Reference Solution

See [`lc716_max_stack.py`](lc716_max_stack.py) — `MaxStackSimple` (O(n)
popMax baseline) and `MaxStack` (O(log n)-amortized version with a doubly
linked list + lazy-deletion max-heap), stdlib-only (`heapq`,
`itertools.count`). Tests in
[`test_lc716_max_stack.py`](test_lc716_max_stack.py) run the same contract
suite against both classes via a shared mixin, plus a 200-trial randomized
differential test that checks the two implementations never disagree.

---

## Interview questions

1. **Why is `(-value, id)` wrong as a heap key, and `(-value, -id)`
   correct?** `heapq` is a min-heap, so on a value tie it always returns
   the tuple with the smaller second element; `id` ascending would
   incorrectly favor the *earliest*-pushed element, while `-id` favors the
   *largest* id (most recently pushed) — the required top-most occurrence.
2. **What does "lazy deletion" mean here, and why is it safe?** `pop()`
   removes a node from the linked list without touching the heap; the
   heap keeps a now-invalid entry for that id. It's safe because every
   heap read (`peekMax`/`popMax`) first checks `id in id_to_node` and
   discards — permanently — any entry whose id no longer exists, so a
   stale entry can never be mistaken for a live one.
3. **Prove the amortized complexity claim.** Every id is inserted into the
   heap exactly once (during `push`) and removed from the heap at most once
   over the object's entire lifetime (either explicitly by `popMax`, or
   lazily while cleaning stale entries in some later call) — so total heap
   operations across N pushes is O(N), each O(log N), giving O(log N)
   amortized per push/peekMax/popMax even though any single call's cost is
   not individually bounded.
4. **Why does `pop()` not need to touch the heap at all?** Because the
   linked list already gives O(1) removal from the tail directly; the
   corresponding heap entry is simply abandoned and will be cleaned up
   lazily if and when it would otherwise surface — touching the heap here
   would only add an unnecessary O(log n) for no correctness benefit.
5. **How would you test that `popMax` removes the correct node, not just a
   node with the correct value?** Construct a case with the same value at
   multiple stack depths and assert on the *resulting stack order* after
   the call, not just the return value — a bug that swaps which occurrence
   is removed returns the right number but leaves the stack in the wrong
   state.
6. **When would you ship `MaxStackSimple` instead of `MaxStack` in a real
   review?** When `popMax` is rare relative to the other operations, or n
   is small enough that O(n) is irrelevant — the simpler implementation has
   less state to get wrong and is easier for a reviewer to verify by
   inspection, which matters given the laptop round grades clean code at
   35%.
7. **What's the space overhead of the fast version compared to the
   simple one, concretely?** The fast version stores one linked-list node
   (four references) and one heap tuple per live element, versus the
   simple version's two parallel Python-list slots per element — both are
   O(n), but the fast version has a larger constant factor, worth naming if
   asked to compare them precisely.
