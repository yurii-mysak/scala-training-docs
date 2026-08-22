# Python performance notes — what is fast, what is not, and what an interviewer will ask

> **Priority:** Recommended
> **Est. time:** 35 min
> **Track:** Server
> **HelloInterview:** none

Performance is 20% of the laptop-round grade. That is not enough to justify micro-optimising, but it is
enough that a visibly quadratic solution or an obviously wrong container choice costs you. This file is
about knowing which choices matter and being able to defend them out loud.

The rule for the round: **get it correct, then make the complexity right, then stop.** Constant-factor
tuning is not what the 20% is measuring.

---

## 1 · Operation costs worth memorising

| Operation | Cost | Note |
|---|---|---|
| `list` index, append, pop from end | O(1) | append is amortised |
| `list.pop(0)` / `list.insert(0, x)` | **O(n)** | Shifts everything. Use `collections.deque`. |
| `x in list` | **O(n)** | The single most common accidental quadratic. Use a `set`. |
| `x in set` / `x in dict` | O(1) average | O(n) worst case under adversarial hashing |
| `deque.appendleft` / `popleft` | O(1) | The right queue |
| `heapq.heappush` / `heappop` | O(log n) | `heapify` is O(n) |
| `bisect.insort` | O(n) | The search is O(log n), the **insert is O(n)** — a real trap |
| `sorted()` / `list.sort()` | O(n log n) | Timsort; near-linear on nearly-sorted input |
| `str` concatenation in a loop | **O(n²)** | Strings are immutable. Collect into a list, then `"".join()`. |
| `dict`/`set` iteration | O(n) | Insertion-ordered since 3.7 |
| Slicing `a[i:j]` | O(j−i) | Copies. Slicing in a loop is a hidden quadratic. |
| `list.remove(x)` / `del list[i]` | O(n) | Scan plus shift |
| `min` / `max` / `sum` | O(n) | Repeated `min()` inside a loop is quadratic — use a heap |

The three that actually cost people the round: **`in` against a list**, **string `+=` in a loop**, and
**`pop(0)`**. If you avoid only those three, you have collected most of the available 20%.

---

## 2 · Choosing the container

| Need | Use | Not |
|---|---|---|
| Membership testing | `set` | `list` |
| Counting | `collections.Counter` | manual dict increments |
| Grouping | `collections.defaultdict(list)` | `dict` with `setdefault` in a loop |
| Queue / sliding window | `collections.deque` | `list` with `pop(0)` |
| Top-k / running min-max | `heapq` | sorting repeatedly |
| Sorted membership with lookups | `bisect` over a sorted list | re-sorting |
| Fixed record | `dataclass` or `NamedTuple` | dict with string keys |
| Insertion-ordered map | plain `dict` | `OrderedDict`, unless you need `move_to_end` |

`OrderedDict.move_to_end` is still the clean way to write an LRU cache, which is a reported Lyft problem —
see [../09-coding-challenges/task14_lru_cache.md](../09-coding-challenges/task14_lru_cache.md).

---

## 3 · Patterns specific to Lyft's problem families

**Versioned / temporal KV store.** Keep each key's history as a list sorted by version and use
`bisect.bisect_right` for the "latest version ≤ requested" lookup. Appends are O(1) if versions arrive in
order; `insort` is O(n) if they do not. Say which case you are assuming — that is exactly the read-vs-write
trade-off candidates reported struggling with.

**Job scheduler / intervals.** Sort by start, then a min-heap on end times. Do not hand-roll a heap: a
Toronto candidate ran out of time doing precisely that in Go. In Python `heapq` is stdlib and free.

**Trie typeahead.** A dict-of-dicts is fine and readable. Precompute top-k completions at each node if
lookups dominate; that is the classic read/write trade to name out loud.

**Stateful paginated fetch.** Buffer with a `deque` and `popleft`. Never `pop(0)` on a list.

**File and log parsing.** Iterate the file object directly rather than `readlines()` — it streams instead
of loading. `"Print the K-th non-empty line of a large file without loading it into memory"` is a reported
problem and this is the entire point of it.

**In-memory KV with transactions.** A stack of dicts holding the diff per open transaction gives O(1)
commit of the top frame and O(depth) reads. The alternative — copying the whole store per `begin` — is
simpler to write and much worse; name the trade.

---

## 4 · Things that are slower than they look

- **`try/except` is cheap to set up, expensive to raise.** Fine as control flow for the rare case, wrong
  for the common one.
- **Attribute lookup in a hot loop** costs more than a local. `append = result.append` before the loop is a
  real optimisation, but only mention it if asked — it hurts readability, which is worth more.
- **Recursion** has a default limit of 1000 and no tail-call optimisation. Convert deep recursion to an
  explicit stack.
- **Global interpreter lock.** Threads do not give you CPU parallelism for pure-Python work; they do help
  for I/O-bound work. `multiprocessing` gives real parallelism at the cost of serialisation.
- **`copy.deepcopy`** is far slower than people expect. In the transactional-KV problem this is the naive
  approach worth explicitly rejecting.

---

## 5 · What to say about performance in the round

Do not benchmark. Do state complexity. A useful three-sentence habit at the end of each part:

> *"This is O(n log n) time, dominated by the sort, and O(n) space. The lookup path is O(log n) via
> bisect. If writes were more frequent than reads I would flip that and keep an unsorted structure with an
> O(n) scan on read."*

That answers correctness, complexity, and the trade-off in one breath, which is what the 20% is for.

If asked to make it faster, ask first what the actual constraint is — input size, memory ceiling, or
latency target. Optimising without knowing which is the wrong instinct and interviewers notice.

---

## Interview questions

**1. Your solution uses `if x in results` inside a loop. What is wrong?**
If `results` is a list that is an O(n) scan inside an O(n) loop, so the whole thing is quadratic. Swapping
to a `set` for membership makes it linear. If order matters too, keep both — a list for order and a set for
membership.

**2. When is `bisect` the wrong choice?**
When you are inserting frequently. The binary search is O(log n) but `insort` shifts the underlying list,
so insertion is O(n). If writes dominate, a heap or a tree structure is better; if reads dominate and
inserts are append-ordered, bisect over a sorted list is ideal.

**3. Why is string concatenation in a loop a problem?**
Strings are immutable, so each `+=` allocates a new string and copies the old contents, making the loop
quadratic. Collect the pieces in a list and `"".join()` once, which is linear.

**4. You need a queue. Why not a list?**
`list.pop(0)` is O(n) because every remaining element shifts. `collections.deque` gives O(1) at both ends
and is the correct structure for a queue or a sliding window.

**5. How much should you optimise in the laptop round?**
Enough to have the right asymptotic complexity and no accidental quadratics, then stop. Performance is 20%
of the grade and clean code is 35%, so an optimisation that hurts readability is usually a net loss. State
the complexity and the trade-off out loud instead.
