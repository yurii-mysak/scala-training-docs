# Nested Dot-Path Key-Value Store

> **Priority:** Optional
> **Est. time:** 40 min
> **Track:** Both
> **HelloInterview:** DSA — Trie (structural analogy); Low-Level Design in a Hurry

**2 independent first-hand reports** — the least-reported family in this section,
but a good synthesis drill: it combines the dict-of-dicts manipulation from
[trie typeahead](04-trie-typeahead-t9.md) with the "confirm behavior on ambiguous
inputs" discipline the whole round rewards.

---

## 1 · Problem, Built in the Order It Escalates

This family is typically asked as an escalating sequence — treat each stage as a
natural follow-up to the one before it, and narrate that structure to the
interviewer as you go (it demonstrates you see where the problem is headed, not
just where it currently is):

1. `set(path, value)` / `get(path)` / `delete(path)` — dot-delimited paths
   (`"a.b.c"`), intermediate segments auto-created on `set`.
2. `children(prefix)` — sorted immediate child segment names under a path.
3. `flatten()` — every stored value as a flat `{"a.b.c": value}` dict.
4. Strict type checking: a path cannot simultaneously be a **branch** (has
   children) and a **leaf** (holds a value) — reject a `set` that would overwrite a
   branch with a leaf, **and** reject one that would descend into an existing leaf
   as though it were a branch. Both directions, not just the one usually stated.

---

## 2 · Approach

Represent every node — root, intermediate, or terminal — as a plain `dict`. A
**leaf** node is `{_LEAF: value}` and nothing else, using a sentinel key that can
never collide with a real path segment. A **branch** node maps `segment name ->
child node` and never contains `_LEAF`. This representation makes "is this a
branch or a leaf" a single `_LEAF in node` check, and makes the mutual-exclusion
rule structural rather than something you have to remember to enforce separately.

- `set`: walk/create intermediate branch dicts for all but the last segment
  (raising if an intermediate is already a leaf); at the last segment, raise if a
  branch already exists there, otherwise write `{_LEAF: value}`.
- `get`: navigate to the node; if it's missing or isn't a leaf, return "not found."
- `delete`: navigate to the parent, remove the last segment, then **prune upward**
  — if removing that entry left its parent branch empty, remove the parent too, and
  keep walking up as long as pruning keeps producing empty branches. This keeps
  `children()`/`flatten()` from surfacing dangling former-branches with nothing
  under them.
- `children(prefix)`: the sorted keys of the node at `prefix`, excluding the `_LEAF`
  sentinel. A leaf path legitimately has zero children — return `[]`, don't raise.
- `flatten()`: DFS from root, building dot-joined path strings, emitting one entry
  per leaf found.

See [`07-nested-path-kv.py`](07-nested-path-kv.py) for the full reference
implementation (`NestedPathKV`).

---

## 3 · Complexity

- `set` / `get` / `delete`: O(depth of the path) — each dot-segment is one dict
  lookup/creation.
- `children`: O(depth of prefix + number of immediate children), dominated by the
  sort of the children (O(c log c) for c children).
- `flatten`: O(total nodes in the store) — has to visit everything once.

---

## 4 · Edge Cases

| Case | Expected behavior |
|---|---|
| `set("a.b.c", v)` with no prior `set` on `"a"` or `"a.b"` | Intermediates auto-created as branches |
| `get` on an intermediate branch path (never itself `set`) | Not found — a branch is not a leaf |
| `delete` on a path that doesn't exist | No-op, not an error |
| `delete` of the only leaf under a chain of branches | Prunes the whole now-empty chain, not just the immediate parent |
| `children("")` | Top-level keys |
| `children` on a nonexistent prefix | `[]` |
| `children` on a leaf path | `[]` — a leaf has no children, this isn't an error case |
| `set(path, v)` where `path` is currently a leaf's ancestor-to-be (i.e., leaf → branch conflict) | Raise — cannot descend into an existing leaf |
| `set(path, v)` where `path` is currently a branch (i.e., branch → leaf conflict) | Raise — cannot overwrite an existing branch with a leaf |
| Empty path string | Raise — not a valid path in either direction |

---

## 5 · Follow-ups

- How would you support **wildcard** children queries (e.g., `"a.*.c"`)? Would need
  to walk multiple branches at the wildcard level instead of a single dict lookup —
  a meaningfully different traversal, not a small tweak.
- How would you make `flatten()` lazy (a generator) instead of building the whole
  dict up front, for a store too large to flatten all at once?
- How would this change if paths could contain a literal dot inside a segment name
  (needing an escape character)? The `_split` implementation would need real escape
  handling instead of a bare `str.split(".")`.

---

## Interview questions

1. Implement `set`/`get`/`delete` for dot-path keys with auto-created intermediates.
   *Model answer:* represent every node as a dict; walk/create one dict level per
   path segment on `set`, navigate the same way on `get`/`delete`, and on `delete`
   walk back up pruning any branch left empty by the removal.

2. How do you represent "this path holds a value" versus "this path is a
   container for other paths" in the same dict-of-dicts structure?
   *Model answer:* a leaf is a dict containing only a reserved sentinel key mapped
   to the value; a branch is a dict of child-segment-name to child-node and never
   contains that sentinel — the two shapes are structurally distinguishable with a
   single membership check.

3. What does `children()` return for a path that holds a value directly (a leaf)?
   *Model answer:* an empty list — a leaf has no children by definition; this is
   expected behavior, not an error condition worth raising on.

4. Why prune empty branches on delete instead of leaving them?
   *Model answer:* an empty branch left behind would make `children()` report a
   segment that has nothing under it and `flatten()` correctly ignore it anyway —
   pruning keeps the tree's shape consistent with "what's actually stored" rather
   than accumulating dead structure from every delete.

5. What happens if you try to `set` a value at a path that's currently a branch
   with children under it?
   *Model answer:* reject it — overwriting a branch with a leaf would silently
   discard everything under that branch, which is exactly the ambiguity "strict
   type checking" exists to catch instead of allowing.

6. What about the reverse: setting a deeper path under something that's already a
   leaf?
   *Model answer:* also reject it — a leaf has no children to descend into, and
   silently converting it into a branch would just be the same ambiguity from the
   other direction.

7. What's the complexity of `flatten()`, and when would you avoid calling it?
   *Model answer:* O(total nodes in the store), since it has to visit every branch
   and leaf once — avoid it on a hot path for a large store; it's a debugging/export
   operation, not something to call per-request.

8. How is this structurally related to the trie in the
   [typeahead family](04-trie-typeahead-t9.md)?
   *Model answer:* both are trees keyed by a sequence of discrete tokens (characters
   there, dot-segments here) where a node can mark "something terminates here" —
   the traversal, insertion, and DFS-collection patterns are the same shape, just
   with a different alphabet and a different per-node payload.
