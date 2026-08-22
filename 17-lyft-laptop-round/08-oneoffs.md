# One-Offs: Lower-Frequency Reported Patterns

> **Priority:** Recommended
> **Est. time:** 30 min
> **Track:** Both
> **HelloInterview:** Low-Level Design in a Hurry (see per-item notes below for DSA-specific lessons)

---

## 1 · How to Use This File

Eight patterns, each reported but at lower individual frequency than the seven
families with their own files. Approach notes only — no full solutions, no test
files. Budget roughly 10-15 minutes per item if you're drilling: read the approach,
sketch the method signatures on paper or in a scratch file, and move on. The goal is
recognition speed under time pressure, not a polished implementation in hand.

---

## 2 · Max Stack (LC 716)

A stack supporting `push`, `pop`, `top`, `peekMax`, and `popMax` (remove the
maximum element, wherever it is in the stack — not just from the top).

**Approach:** two stacks — a main stack, and a second stack that tracks the running
maximum alongside each push (`max_stack.append(max(value, max_stack[-1] if
max_stack else value))`). `push`/`pop`/`top`/`peekMax` are all O(1). `popMax` is the
hard part: pop the main stack into a temporary buffer until you reach the max
value, remove it, then push the buffered items back (rebuilding the max stack as
you go) — O(n) worst case, but simple and correct, and a perfectly good answer for
this round.

**If pushed for better than O(n) `popMax`:** name the fully optimal design — a
doubly linked list for O(1) arbitrary removal, paired with a sorted map from value
to node references (`sortedcontainers.SortedList` in practice; stdlib-only, use a
max-heap with lazy deletion instead: push `(value, id)`, keep a `removed` id-set,
and skip stale heap entries on pop) — but don't build it live unless specifically
asked to go past the O(n) version.

Related: [Binary Heap Summary](../08-algorithms-and-data-structures/binary_heap_summary.md).

---

## 3 · LRU Cache Backed by an ArrayList

The catch is in the constraint: "backed by an ArrayList" (a plain Python `list`) is
a deliberate restriction, not an oversight — it rules out `collections.OrderedDict`
or a hand-rolled doubly linked list, the two structures that make LRU O(1). Build
what's asked: a list holding (key, value) pairs, with `get`/`put` doing a linear
scan to find the key, then a remove-and-re-append (or index-tracking) to move it to
the "most recently used" end.

**Approach:** `list.index()` + `list.pop()` + `list.append()` for the move-to-front
step — simple, correct, and O(n) per operation.

**Say this out loud:** name the complexity cost explicitly rather than let it pass
silently — "this is O(n) per access because of the ArrayList constraint; with
`OrderedDict` or a hashmap-plus-doubly-linked-list this would be O(1), but that's
not what was asked for." Recognizing and stating the cost of a constraint you were
handed is a stronger signal than quietly building the fast version nobody asked for.

Related: [Task 14 — LRU Cache](../09-coding-challenges/task14_lru_cache.md) (the
unconstrained O(1) version, for contrast).

---

## 4 · Union-Find with Same-Set Queries

Classic Disjoint Set Union: `union(x, y)` merges two sets, `connected(x, y)`
answers whether they're in the same set.

**Approach:** two dicts, `parent` and `rank` (or `size`). `find(x)` walks parent
pointers to the root **with path compression** (point every visited node directly
at the root on the way up). `union` attaches the smaller tree under the larger
tree's root (union by rank/size). Both amortize to O(α(n)) — effectively constant.

**The trap:** skipping path compression turns `find` into O(n) worst case on a
skewed chain — a DSU with `union` but no compression is a linked list wearing a
disguise. Implement both halves (path compression *and* union by rank/size), not
just one.

```python
parent = {}
rank = {}

def find(x):
    if parent[x] != x:
        parent[x] = find(parent[x])  # path compression
    return parent[x]

def union(x, y):
    rx, ry = find(x), find(y)
    if rx == ry:
        return
    if rank[rx] < rank[ry]:
        rx, ry = ry, rx
    parent[ry] = rx
    if rank[rx] == rank[ry]:
        rank[rx] += 1
```

---

## 5 · DAG Linearisation / Topological Sort

Order the nodes of a directed acyclic graph so every edge points from earlier to
later in the ordering; detect if it's not actually acyclic.

**Approach:** Kahn's algorithm (BFS by in-degree) is usually cleaner to explain out
loud than DFS-postorder-then-reverse, and it detects cycles for free: compute
in-degree for every node, queue every node with in-degree 0, repeatedly pop a node,
emit it, and decrement its neighbors' in-degrees, queueing any that hit 0. If the
final emitted count is less than the total node count, there's a cycle — some nodes
never reached in-degree 0. O(V + E).

Related: [Task 13 — Course Schedule (Topological Sort)](../09-coding-challenges/task13_course_schedule_topological_sort.md),
[Traversal & Graph Search](../08-algorithms-and-data-structures/Traversal_Graph_Search.md).

---

## 6 · Iterator Design Pattern over Sorted Arrays

Implement an iterator that merges K sorted arrays lazily, producing elements in
overall sorted order one at a time.

**Approach:** a min-heap seeded with the first element of each array as
`(value, array_index, element_index)`. Each `next()` pops the smallest, pushes that
array's next element (if any) back onto the heap, and returns the popped value.
Same core technique as "merge k sorted lists."

**Which API shape is actually wanted matters here — ask.** Python's native
iterator protocol (`__iter__` returns `self`, `__next__` raises `StopIteration`
when exhausted) is the idiomatic choice if the prompt is open-ended. If the prompt
literally says "implement `hasNext()` and `next()`" (the Java-style shape LC
iterator problems often use), build that instead — matching the literal ask beats
substituting what feels more Pythonic in your head. This mirrors the ArrayList-LRU
lesson above: build what's asked, then optionally mention the idiomatic
alternative.

---

## 7 · Grid / BFS Spread (LC 994, Rotting Oranges)

A grid where some cells start "active" (e.g., rotten) and spread to orthogonally
adjacent cells over discrete time steps; find the number of steps until nothing
more can spread, or -1 if some reachable cells never will be.

**Approach: multi-source BFS.** Seed the queue with *every* initially-active cell
at once, not one at a time — then do standard level-order BFS, where each queue
"layer" processed corresponds to one time step. The answer is the number of layers
processed, provided every reachable empty cell got covered; if any target cells
remain uncovered at the end, return -1.

**The trap:** running a separate single-source BFS per active cell is O(k · rows ·
cols) instead of O(rows · cols) — always seed all sources into the queue up front
and BFS once.

Related: [BFS vs DFS: Summary](../08-algorithms-and-data-structures/bfs_dfs_summary.md),
[Task 21 — BFS and DFS Graph Traversal](../09-coding-challenges/task21_bfs_dfs.md),
[Task 12 — Number of Islands](../09-coding-challenges/task12_number_of_islands.md)
(same grid-traversal family, single-source rather than multi-source).

---

## 8 · A Class with an `attack` Method, Game Ends at Zero Health

An object-oriented design prompt rather than an algorithmic one: model something
like a `Character` with `health` and an `attack(target, damage)` method, where the
"game" ends once a character's health reaches zero.

**Approach notes, not a full design:**
- Clamp health at zero on the way down (`self.health = max(0, self.health -
  damage)`) — never let it go negative.
- Make `is_alive` a property derived from `health > 0`, not a separately tracked
  flag that could drift out of sync.
- Validate before mutating: attacking with or as a character that's already dead
  should be rejected or be a no-op — decide which, and say so.
- `attack` should return or signal something meaningful (whether the target died as
  a result), not just mutate silently — a caller driving a game loop needs to know
  when the game ended.
- If multiple character types are implied (different attack behavior per type),
  that's a polymorphism ask — a small base class plus subclasses overriding
  `attack`, not a pile of `if isinstance(...)` checks in one method.
- Ask whether attacks are one-directional per call or whether a counter-attack is
  expected — this is exactly the kind of ambiguity worth resolving before coding,
  not after.

---

## 9 · Matching a Shopping List Against Promotion Codes

Given purchased items (with quantities/prices) and a set of promotion rules (e.g.,
"buy 2 get 1 free" on an item, "10% off orders over $50," "buy A and B, get a
discount on C"), compute the applicable discount or final total.

**Approach notes:** this is a modeling problem more than an algorithmic one — the
interesting part is the object design, not a clever traversal.
- Model each promotion as a small unit with a predicate ("does this cart qualify")
  and an effect ("what discount does it produce") — e.g., a `Promotion` base class
  or a `(predicate_fn, effect_fn)` pair per rule, evaluated against the cart rather
  than a large branching `if/elif` chain per promotion type.
- **Ask, don't assume, whether promotions combine (stack) or only the single best
  one applies** — this materially changes the algorithm from "apply one" to "search
  over combinations" or "apply all, in a defined precedence order."
- Keep the cart-matching logic (does the customer have what a promo needs) separate
  from the discount-calculation logic (how much does qualifying save) — mixing them
  in one function is where this kind of exercise usually gets messy under time
  pressure.

---

## Interview questions

1. Implement a Max Stack supporting O(1) `push`/`pop`/`top`/`peekMax`. What about
   `popMax`?
   *Model answer:* a secondary stack tracking the running max alongside the main
   stack gives O(1) for everything except `popMax`, which needs an O(n) pop-buffer-
   -pop-again pass to remove an element that isn't at the top — a fully O(log n)
   `popMax` needs a heap-with-lazy-deletion or a linked-list-plus-sorted-map design.

2. Why would an interviewer ask you to build LRU on an ArrayList instead of letting
   you use `OrderedDict`?
   *Model answer:* to see whether you recognize and state the resulting complexity
   cost rather than silently accepting or silently "fixing" the constraint — the
   correct move is to build what's asked and name the O(n)-per-access trade-off
   explicitly.

3. What's the amortized complexity of union-find with both path compression and
   union by rank, and what happens if you only implement one of them?
   *Model answer:* O(α(n)) amortized, effectively constant, with both optimizations;
   with only union by rank (no compression) it's O(log n) per op; with neither,
   `find` degrades to O(n) worst case on a skewed tree.

4. How do you detect a cycle while computing a topological sort?
   *Model answer:* with Kahn's algorithm, if the number of nodes emitted is less
   than the total node count when the queue empties, the remaining nodes never
   reached in-degree zero — meaning they're part of a cycle.

5. What's the difference between Python's iterator protocol and a `hasNext()` /
   `next()` style API, and when would you use each here?
   *Model answer:* `__iter__`/`__next__` with `StopIteration` is the idiomatic
   Python shape; `hasNext()`/`next()` is the Java-style shape some prompts ask for
   literally — match whichever the prompt actually specifies rather than defaulting
   to what's idiomatic in your own head.

6. Why does multi-source BFS matter for the grid-spread problem, versus running BFS
   once per source?
   *Model answer:* seeding every source into the queue before the first BFS layer
   runs means each layer already represents "one time step across all active
   fronts simultaneously" — running BFS once per source instead multiplies the work
   by the number of sources and also miscounts the time steps.

7. In the `attack`/health class design, how do you keep `is_alive` from drifting out
   of sync with `health`?
   *Model answer:* derive it as a computed property (`health > 0`) rather than a
   separately assigned field — a derived value can't desync from the field it's
   derived from, whereas a manually maintained flag can be forgotten on some code
   path.

8. In the promotions-matching problem, how would your design change if promotions
   could stack versus only the single best one applying?
   *Model answer:* single-best is a straightforward "evaluate every qualifying
   promotion's effect, take the max discount"; stacking requires either a defined
   application order (apply in sequence, recomputing eligibility after each) or a
   search over subsets if promotions can interact — a materially larger problem,
   which is exactly why this is worth asking about before coding rather than
   guessing.
