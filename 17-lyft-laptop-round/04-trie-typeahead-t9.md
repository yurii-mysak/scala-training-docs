# Trie Typeahead / Autocomplete / T9

> **Priority:** Required
> **Est. time:** 50 min
> **Track:** Both
> **HelloInterview:** DSA — Trie (Implement Trie Methods, Prefix Matching)

**5 independent first-hand reports.** One of these reports is a near-exact match for
a specific known Kyiv-loop problem: **"word analyzer (T9)"** — the numeric-keypad
variant in Part 2 below is not a generic guess, build it, not just the plain
autocomplete.

---

## 1 · Problem

**Part 1 — typeahead:** given a stream of `add_word(word, frequency)` calls, answer
`suggest(prefix, k)` with the top-k known words starting with `prefix`, most frequent
first.

**Part 2 — T9:** given the same kind of dictionary, answer queries where the "prefix"
is a **digit sequence typed on an old phone keypad** (2=abc, 3=def, ..., 9=wxyz), and
the answer is the dictionary word(s) whose letters map to exactly that sequence.

---

## 2 · Approach

### Part 1

Standard trie: each node is a `dict[char, node]` plus `is_word` and `frequency`.
`add_word` walks/creates nodes per character and accumulates frequency at the
terminal node. `suggest(prefix, k)` walks to the prefix's node (or returns `[]` if
the prefix doesn't exist at all), then does a DFS collecting every word beneath it,
sorted by `(-frequency, word)` — **always pick an explicit tie-break rule**
(alphabetical here) so output is deterministic; "whatever `sort` happens to do with
no key" is not a rule and will bite you on the second run.

### Part 2 — T9

Reuse the exact same trie shape, but key nodes by **digit** instead of letter: encode
each dictionary word via the keypad mapping (`word_to_digits`), then insert along
that digit path. Because multiple words collide on the same digits (`"cab"` and
`"abc"` both encode to `"222"` — that is real T9 behavior, not a bug to fix), a
terminal node holds a **list** of `(frequency, word)` pairs, not a single word.

Two query modes, and you should ask which one is wanted rather than assume:
- **Exact-length lookup** (`suggest`): words whose digit encoding is *exactly* the
  query — classic multi-tap disambiguation, "I typed these digits, which words could
  that be."
- **Include-longer** (`suggest_including_longer`): also surfaces longer words that
  start with this digit sequence — live-completion UX, "I've typed this much so far."

See [`04-trie-typeahead-t9.py`](04-trie-typeahead-t9.py) for the full reference
implementation (`Typeahead`, `T9Typeahead`, `word_to_digits`).

---

## 3 · Complexity

- `add_word`: O(word length).
- `suggest` (Part 1, prefix-based): O(prefix length + words under that prefix), since
  the DFS visits every matching word to rank them. At real scale you'd cap this with
  a bounded top-k heap per node instead of collect-then-sort-everything — worth
  naming as the optimization if asked "how would this scale to a huge dictionary,"
  see [Binary Heap Summary](../08-algorithms-and-data-structures/binary_heap_summary.md).
- `suggest` (Part 2, exact T9): O(digit length) to walk down, plus O(collisions at
  that node) to rank — collisions are typically small (a handful of words at most),
  so this is effectively O(digit length).

---

## 4 · Edge Cases

| Case | Expected behavior |
|---|---|
| Prefix/digits not present in the trie | `[]`, not an error |
| `k <= 0` | `[]` |
| Empty prefix (Part 1) | Ranks across the *entire* dictionary |
| Ties in frequency | Broken by an explicit secondary key (alphabetical here) — must be deterministic |
| Same word added twice | Frequency accumulates, doesn't overwrite |
| T9 digit sequence containing `0`, `1`, or a non-digit | Invalid — raise, don't silently ignore |
| Two dictionary words collide on the same T9 digits | Both returned, ranked by frequency — this is correct T9 behavior, not a dedup bug |
| Case sensitivity | Normalize to lowercase on insert (`add_word` does this for T9; decide and state the same for Part 1 if the interviewer's dictionary is mixed-case) |

---

## 5 · Follow-ups

- How would you keep `suggest` fast without re-scanning every word under a prefix on
  every call? (Cache/maintain a small top-k list *at each trie node*, updated
  incrementally on `add_word`, rather than recomputing from scratch on every query —
  the LeetCode 642 "Design Search Autocomplete System" framing.)
- How would frequency updates work for a live system (e.g., "boost this word's score
  every time it's selected")? Same trie, `add_word` becomes an increment call.
- What if the T9 dictionary were too large to hold every word's full expansion in
  memory? Store just the digit-encoded trie (no separate letter trie), which is
  already what `T9Typeahead` does — call this out as a deliberate memory choice, not
  an accident.

---

## Interview questions

1. **[Reported at Lyft]** Implement a trie-backed autocomplete returning the top-k
   most frequent completions for a prefix.
   *Model answer:* trie keyed by character, frequency accumulated at terminal nodes,
   `suggest` walks to the prefix node then DFS-collects and sorts by
   `(-frequency, word)` for deterministic tie-breaking.

2. **[Reported at Lyft]** Implement a T9 "word analyzer": given digits typed on a
   phone keypad, return the matching dictionary word(s).
   *Model answer:* encode each dictionary word to its digit sequence via the keypad
   mapping and insert it into a trie keyed by digit; because multiple words can share
   a digit encoding, store a list of candidates at each terminal node, not a single
   word, and rank the list by frequency at query time.

3. Why can two different words map to the same T9 query?
   *Model answer:* several letters share a digit key (e.g., 2 = a/b/c), so any two
   words that are letter-for-letter "the same shape" under that many-to-one mapping
   collide — `"cab"` and `"abc"` both become `"222"`. This is inherent to T9, not a
   bug.

4. How do you keep suggestion order deterministic when frequencies tie?
   *Model answer:* sort by a compound key — frequency descending, then an explicit
   deterministic tiebreaker such as the word itself alphabetically. Relying on
   insertion order or hash order is not deterministic across runs.

5. How would you avoid re-scanning the whole subtree under a prefix on every query,
   for a very large dictionary?
   *Model answer:* maintain a small precomputed top-k list at each trie node,
   updated incrementally as words/frequencies are added, so `suggest` is a direct
   lookup rather than a fresh DFS each time — this is essentially LeetCode 642.

6. How is the T9 trie different from the plain-prefix trie in Part 1?
   *Model answer:* same structure and traversal, different alphabet — nodes are
   keyed by digit ('2'-'9') instead of by letter, and because the digit alphabet is
   lossy (many letters per digit), terminal nodes must hold a list of words instead
   of assuming uniqueness.

7. What's the complexity of building the trie for a dictionary of n words with
   average length L?
   *Model answer:* O(n · L) to insert everything, same for both the letter trie and
   the digit trie.

8. How would you validate a T9 query string?
   *Model answer:* reject any character outside `2`-`9` — `0` and `1` have no
   letters on a standard keypad, and a non-digit is not a keypad key at all; raise
   rather than silently treating it as "no match."
