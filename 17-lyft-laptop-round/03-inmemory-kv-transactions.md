# In-Memory KV Store with Transactions (BEGIN / COMMIT / ROLLBACK)

> **Priority:** Required
> **Est. time:** 60 min
> **Track:** Both
> **HelloInterview:** DSA — Stack (incl. Monotonic Stack); Low-Level Design in a Hurry

**4 independent first-hand reports, including a 2026 pass** — and this is the family
with the clearest documented failure mode in the entire round.

---

## 1 · This Problem Has Two Parts. Both Are In Scope From The Start.

A candidate implemented SET/GET/DELETE, believed the problem was finished, and was
told **"we expect that part to be covered"** when transactions came up — meaning
BEGIN/COMMIT/ROLLBACK was never an optional stretch goal, it was assumed baseline
scope the whole time. Read the prompt as: *"build a transactional KV store"*, not
*"build a KV store, then maybe add transactions if there's time."*

Budget accordingly: spend at most 15-20 minutes getting Part 1 correct and clean, then
move to Part 2. See the general framing in [00-protocol.md](00-protocol.md) — this is
the family that makes that document's warning concrete.

---

## 2 · Part 1 — Plain KV

```text
SET key value
GET key
DELETE key
```

Nothing surprising: a dict. The only two decisions worth stating out loud are what
`GET` on a missing key returns (this file: `None` in code, printed as `NULL` for the
command-line format — pick a convention and say it) and whether `DELETE` on a missing
key is an error or a no-op (this file: no-op).

---

## 3 · Part 2 — Transactions, Including Nesting

```text
BEGIN       # opens a new transaction, possibly nested inside another
COMMIT      # ends the innermost open transaction, merging it into the parent
            # scope (or into the committed store, if this was the outermost)
ROLLBACK    # discards the innermost open transaction entirely
```

### Approach

A committed base dict, plus a **stack of frames**, one dict per currently-open
transaction, innermost last:

- **Write** (`SET`/`DELETE`) touches only the top frame if one is open, else the
  committed store directly.
- **Read** (`GET`) walks the stack **innermost to outermost**, returning the first
  frame that has an opinion about the key, falling back to the committed store only
  if no open frame mentions the key at all.
- **`COMMIT`** pops the top frame and merges it into the *parent* frame if one
  exists, or into the committed store if this was the outermost transaction. A
  nested commit is not durable by itself — it only survives if every enclosing
  transaction also eventually commits.
- **`ROLLBACK`** pops and discards the top frame outright — including any nested
  commits that happened inside it, since those were only merged into this frame,
  never past it.

The one implementation trap: a plain `dict` per frame can't distinguish "this key was
explicitly deleted in this frame" from "this frame has no opinion, keep looking
outward." Use a sentinel object (`_MISSING` in the reference code) as the frame's
value for a deleted key, distinct from Python's `None` (which is a legitimate stored
value in general, even if this file's convention treats `GET`-returns-`None` as "not
found" for the command output).

See [`03-inmemory-kv-transactions.py`](03-inmemory-kv-transactions.py) for the full
reference implementation (`TransactionalKVStore`, `run_commands`).

---

## 4 · Complexity

- `SET` / `DELETE`: O(1).
- `GET`: O(d) where d = current transaction nesting depth — walks the frame stack.
  In practice d is small (single digits); if it weren't, that itself would be worth
  raising with the interviewer as a design smell.
- `COMMIT`: O(size of the frame being merged).
- `ROLLBACK`: O(1) — discarding a frame is just popping it.

---

## 5 · Edge Cases

| Case | Expected behavior |
|---|---|
| `GET` on a key never set | Not found (`NULL` in the command format) |
| `DELETE` on a key that doesn't exist | No-op, not an error |
| `COMMIT` / `ROLLBACK` with no open transaction | This file: reports an error line and keeps processing the rest of the script, rather than crashing the whole run — confirm the interviewer's expected behavior, this is a convention choice |
| Nested `BEGIN`/`BEGIN`/`COMMIT`/`COMMIT` | Fully persists to the committed store |
| Nested `BEGIN`/`BEGIN`/`ROLLBACK`/`ROLLBACK` | Fully discarded |
| Nested `BEGIN`/`BEGIN`/`COMMIT`/`ROLLBACK` | The inner commit is undone too — it only reached the outer frame, never the committed store |
| A key deleted in an outer frame, read from an inner frame that never touches it | Read must walk *past* the inner frame and find the outer frame's deletion — not fall through to the (stale) committed value |
| `SET` then `DELETE` then `SET` again, all inside one transaction | Last write wins within the frame, same as outside a transaction |

---

## 6 · Follow-ups

- What if two transactions could be open on **different keys concurrently** (real
  concurrency, not just nesting on one thread)? This is a different problem —
  optimistic concurrency control / MVCC, or locking, and worth naming even if you
  don't implement it. See [SQL Transactions](../06-databases-and-distributed-data/SQL_Transactions.md)
  and [Distributed Transactions](../06-databases-and-distributed-data/Distributed_Transactions.md)
  for the vocabulary (isolation levels, 2PC) if this comes up in a design round.
- What if `COMMIT` needed to return which keys changed (a change-set), e.g. for
  triggering downstream notifications?
- How would you bound transaction nesting depth defensively, and what should happen
  if a script tries to exceed it?

---

## Interview questions

1. **[Reported at Lyft]** Implement SET/GET/DELETE with BEGIN/COMMIT/ROLLBACK,
   including nested transactions.
   *Model answer:* a committed dict plus a stack of per-transaction frames; writes go
   to the top frame, reads walk the stack outward, commit merges into the parent (or
   the committed store if outermost), rollback discards the top frame outright.

2. **[Reported at Lyft]** Is there a part 2 to this — and would you ask, even if I
   hadn't mentioned one?
   *Model answer:* yes — ask explicitly in the first five minutes regardless of
   whether transactions were mentioned up front; a plain KV store is a suspiciously
   small ask for a 60-minute round, which is itself a signal to ask what's next.

3. What happens if you `COMMIT` a nested transaction, then `ROLLBACK` the one
   enclosing it?
   *Model answer:* the nested commit is undone along with everything else in the
   outer frame — a commit is only durable once it reaches the outermost scope (the
   real committed store), not merely because `COMMIT` was called at some inner level.

4. How do you tell "this key was deleted in this transaction" apart from "this
   transaction never touched this key"?
   *Model answer:* a plain dict can't represent that distinction with `None` alone
   (since `None` might be a real stored value elsewhere in the system); use a
   dedicated sentinel object as the frame's marker for "deleted here."

5. What's the complexity of `GET` inside deeply nested transactions?
   *Model answer:* O(d), d = nesting depth, since a read may have to walk every open
   frame outward before falling back to the committed store.

6. How would you handle `COMMIT` or `ROLLBACK` called with no open transaction?
   *Model answer:* pick a convention — raise, or report a soft error and continue —
   and state it; this file reports an error line and keeps going, since crashing the
   whole run on one bad command in a longer script is usually the worse failure mode.

7. How is this related to real database transaction isolation?
   *Model answer:* this is a simplified single-threaded analog of read-your-own-
   -writes plus nested savepoints; it sidesteps concurrency entirely (no two
   transactions are ever open on separate threads competing for the same key), which
   real isolation levels (read committed, repeatable read, serializable) exist to
   handle — see [SQL Transactions](../06-databases-and-distributed-data/SQL_Transactions.md).

8. How would you test the nested-rollback-undoes-nested-commit case specifically?
   *Model answer:* set a baseline value, open two nested transactions, set a new
   value and commit only the inner one, then roll back the outer one, and assert the
   baseline value is what remains — that single sequence is the trap this whole
   family is designed to catch.
