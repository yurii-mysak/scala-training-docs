# Data Structures & Idioms

> **Priority:** Required
> **Est. time:** 45 min
> **Track:** Both
> **HelloInterview:** none

The four containers you already know from every other language you've used — array, hash map,
set, and an immutable tuple — map cleanly onto `list`, `dict`, `set`, `tuple`. What doesn't
transfer automatically is *which operations are cheap*, because in Python that's an
implementation fact (CPython's C internals), not a language guarantee, and it doesn't match
Lua's single `table` type or Scala's default-immutable collections. This file is the real
complexity table, then the handful of idioms — comprehensions, slicing, unpacking, sorting,
string building — that separate code that reads as fluent from code that reads as translated.

---

## 1 · `list` vs `tuple` vs `set` vs `dict` — real complexities

| Operation | `list` | `tuple` | `dict` / `set` |
|-----------|--------|---------|-----------------|
| Index / lookup by position | `O(1)` | `O(1)` | n/a (no positional index) |
| Lookup by key/membership (`in`) | `O(n)` — scans | `O(n)` — scans | `O(1)` average, `O(n)` worst case (hash collisions) |
| Append at the end | `O(1)` amortized | n/a — immutable | `O(1)` average (insert) |
| Insert/delete at the **front** | `O(n)` — shifts everything | n/a — immutable | `O(1)` average (no positional shifting) |
| Insert/delete in the **middle** | `O(n)` | n/a — immutable | `O(1)` average |
| Mutable? | Yes | **No** | Yes |
| Hashable (usable as a dict key / set member)? | No | Yes, if all elements are hashable | `dict`: no. `set`: no (use `frozenset`). |

Consequences that actually come up:

- **`x in some_list` vs `x in some_set`.** Identical syntax, different complexity class. If
  you're checking membership more than once, convert to a `set` first — this single change
  turns an accidental `O(n²)` loop into `O(n)`.
- **`list.insert(0, x)` and `list.pop(0)` are `O(n)`**, not `O(1)` — every other element shifts.
  If you need queue-like behavior (push/pop from the front), use `collections.deque`, not a
  `list`. See [performance-notes.md](performance-notes.md) and
  [stdlib-for-interviews.md](stdlib-for-interviews.md#1--collections).
- **A `tuple`'s immutability is what makes it hashable** — and hashability is what lets you use
  a coordinate pair, a composite key, or a small fixed record as a dict key or set member:
  `visited = set(); visited.add((row, col))`. A `list` can never do this.
- **`dict`/`set` are both hash tables** under the hood — same average-case guarantees, same
  worst case if you defeat hashing (e.g. keys that all collide). A `dict` is a hash table of
  key→value; a `set` is the same table with no attached value.

Cross-reference for the underlying mechanism (open addressing, load factor, collision
resolution): [HashSet & HashMap](../08-algorithms-and-data-structures/hashset_hashmap.md).

---

## 2 · Dict and set comprehensions

The list-comprehension syntax you already know generalizes directly — swap the brackets:

```python
squares = {x: x * x for x in range(5)}          # dict comprehension
print(squares)                                   # {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}

inverted = {v: k for k, v in squares.items()}    # invert a dict in one line
print(inverted[16])                              # 4

lengths = {len(w) for w in ["a", "bb", "cc", "ddd"]}   # set comprehension -- dedupes for free
print(lengths)                                   # {1, 2, 3}

# nesting + filtering compose exactly like list comprehensions
matrix = [[1, 2, 3], [4, 5, 6]]
flat = [x for row in matrix for x in row]
evens = [x for x in range(10) if x % 2 == 0]

# a conditional EXPRESSION (ternary) is different from a filter clause -- it keeps every item:
labeled = ["even" if x % 2 == 0 else "odd" for x in range(4)]
print(labeled)                                   # ['even', 'odd', 'even', 'odd']
```

One trap: **there is no tuple-comprehension syntax.** `(x for x in range(3))` is a **generator
expression**, not a tuple — wrap it in `tuple(...)` if you actually want a tuple:

```python
maybe_tuple = (x for x in range(3))
print(type(maybe_tuple))          # <class 'generator'>
real_tuple = tuple(x for x in range(3))
print(real_tuple)                 # (0, 1, 2)
```

A generator expression (no brackets, just parens or bare in a function call) is lazy — it
doesn't build the collection at all. Feed it straight into `sum`, `any`, `all`, `''.join`, or a
`for` loop when you don't need the intermediate list in memory:

```python
total = sum(x * x for x in range(1_000_000))     # never materializes a million-element list
```

---

## 3 · Slicing — negative indices and step

```python
s = "abcdefgh"
s[2:5]      # 'cde'    -- start inclusive, stop exclusive, same as range()
s[-3:]      # 'fgh'    -- last 3 characters
s[:-3]      # 'abcde'  -- everything except the last 3
s[::2]      # 'aceg'   -- every second character
s[::-1]     # 'hgfedcba'  -- the standard idiom for "reversed"

lst = [0, 1, 2, 3, 4, 5]
lst[1:3] = [10, 20, 30]     # slice ASSIGNMENT -- can change the list's length
print(lst)                  # [0, 10, 20, 30, 3, 4, 5]

lst[:]                      # a shallow copy of the whole list (one common use of slicing)
```

Slicing never raises an index error, even out of range — `s[2:1000]` just returns whatever
exists. This is unlike plain indexing (`s[1000]`), which raises `IndexError` immediately. Both
behaviors are useful; know which one you're invoking.

---

## 4 · Unpacking and starred assignment

```python
a, b = 1, 2                      # tuple unpacking -- also how you swap: a, b = b, a
first, *middle, last = [1, 2, 3, 4, 5]
print(first, middle, last)       # 1 [2, 3, 4] 5

a, *rest = "hello"
print(a, rest)                   # h ['e', 'l', 'l', 'o']

def summarize(*args, **kwargs):  # *args collects positionals into a tuple,
    return args, kwargs          # **kwargs collects keyword args into a dict
print(summarize(1, 2, x=3))      # ((1, 2), {'x': 3})

# unpacking to call a function is the reverse operation
def add3(a, b, c):
    return a + b + c
nums = [1, 2, 3]
print(add3(*nums))               # 6 -- spread a list into positional arguments
```

A function returning `a, b` returns one tuple — unpacking `x, y = f()` is what turns it back
into two names. Assigning to a single name (`result = f()`) keeps it packed. This is the exact
spot where Lua muscle memory misleads you: see
[from-lua-and-scala-to-python.md, §2 row 10](from-lua-and-scala-to-python.md#2--transfer-errors--lua-to-python).

---

## 5 · `zip` and `enumerate`

```python
names = ["amy", "bob", "cory"]
scores = [90, 85, 70]

for i, (name, score) in enumerate(zip(names, scores)):
    print(i, name, score)
# 0 amy 90
# 1 bob 85
# 2 cory 70

list(zip([1, 2, 3], ["a", "b"]))     # [(1, 'a'), (2, 'b')] -- stops at the SHORTER iterable, silently
```

`zip` truncates silently to the shortest input — it does not raise or pad. If mismatched
lengths would be a bug in your problem (they usually are), assert the lengths match before
zipping, or use `itertools.zip_longest` if a padded result is genuinely what you want.

`enumerate(seq, start=1)` takes a starting index — useful when the problem wants 1-based
output but you're iterating a 0-based Python sequence.

---

## 6 · Sorting

```python
data = [("bob", 30), ("amy", 25), ("cory", 30), ("amy", 30)]

sorted(data)                                   # sorts by the WHOLE tuple, left to right
sorted(data, key=lambda p: p[1])               # sort by score only
sorted(data, key=lambda p: (p[1], p[0]))       # multi-key: score, then name, as a tie-break
sorted(data, key=lambda p: p[1], reverse=True) # descending

from operator import itemgetter, attrgetter
sorted(data, key=itemgetter(1))                # same as the lambda, marginally faster, reads clean
```

**`sorted(x)` returns a new list; `x.sort()` mutates in place and returns `None`.** Writing
`x = x.sort()` is a one-character difference from correct and makes `x` be `None` —
see [top mistake #6](from-lua-and-scala-to-python.md#4--the-top-20-mistakes-on-day-one).

**Python's sort (Timsort) is stable**: elements that compare equal keep their original relative
order. This is not a footnote — it's a technique. To sort by multiple keys where a later sort
should not disturb ties from an earlier one, sort by the *least* significant key first:

```python
data = [("bob", 30), ("amy", 25), ("cory", 30), ("amy", 30)]
by_name = sorted(data, key=lambda p: p[0])                 # secondary key first
by_score_then_name = sorted(by_name, key=lambda p: p[1])   # primary key second, stable sort
                                                              # preserves the by_name tie-break
```

Both approaches (a composite tuple key, or two stable sorts) reach the same answer; the tuple
key is almost always less code and is what to reach for first. For a comparator that isn't
expressible as "extract a value and sort by it" (pairwise comparisons, like arranging numbers
to form the largest concatenation), use `functools.cmp_to_key` —
[covered in stdlib-for-interviews.md](stdlib-for-interviews.md#5--functools).

---

## 7 · String building — why `+=` in a loop is a trap

Strings are immutable. Conceptually, every `s += chunk` builds an entirely new string and
discards the old one — do that `n` times and you've paid for `O(n²)` characters copied, not
`O(n)`. The idiomatic, always-safe fix is to accumulate pieces in a list and join once:

```python
parts = ["chunk1-", "chunk2-", "chunk3"]

# risk it under time pressure, and it can be quietly quadratic:
s = ""
for chunk in parts:
    s += chunk

# always linear, and reads as more deliberate:
s = "".join(parts)
```

The nuance worth knowing if asked: modern CPython has an internal optimization that resizes a
string **in place** when nothing else holds a reference to it, which makes the plain `s += chunk`
loop above run close to linear *in practice*, in this specific interpreter. It stops helping the
moment anything else keeps a reference to an intermediate value (e.g. you also append each `s`
to a list as you go) — at that point the real `O(n²)` cost reappears, and it reappears sharply.
This is a CPython implementation detail, not a language guarantee, and it doesn't apply on other
Python implementations (PyPy, etc.). `''.join()` is correct regardless of any of that, doesn't
depend on refcounting behavior, and is the answer an interviewer expects to see — use it as the
default, not the optimization you reach for only after profiling.

For building output line-by-line (a common shape in the recurring parsing/log problems), the
same idea applies: collect lines in a list, `'\n'.join(lines)` once at the end, rather than
concatenating a growing string every iteration.

---

## 8 · f-strings

```python
name, score = "amy", 91.5
f"{name}: {score:.1f}%"        # 'amy: 91.5%'       -- fixed decimal places
f"{1234567:,}"                 # '1,234,567'        -- thousands separator
f"{name!r}"                    # "'amy'"            -- repr() instead of str()
f"{name:>10}"                  # '       amy'       -- right-align, width 10
x = 5
f"{x=}"                        # 'x=5'              -- 3.8+ debug specifier, prints name AND value
```

f-strings are the default for building any string with an interpolated value — faster and more
readable than `%`-formatting, `.format()`, or manual `+`/`str()` concatenation, and readability
is 35% of the grade here. Reserve `''.join()` for accumulating many pieces in a loop (§7); use
an f-string for a single formatted line.

---

## Interview questions

1. **You need to check membership repeatedly inside a loop. What's the one-line change that
   turns an accidental `O(n²)` algorithm into `O(n)`?**
   Convert the thing you're checking membership against into a `set` once, before the loop,
   instead of checking `in` against a `list` on every iteration.

2. **Why can a `tuple` be a dictionary key but a `list` can't?**
   Dict keys must be hashable, and hashability requires immutability (a mutable object's hash
   would have to change if its contents changed, breaking the hash table's invariant). `tuple`
   is immutable, so it's hashable (as long as every element inside it is too); `list` is
   mutable, so Python refuses to hash it at all.

3. **What does `x = my_list.sort()` actually assign to `x`, and why?**
   `None`. `.sort()` mutates the list in place and returns nothing, matching the convention that
   in-place mutators return `None` (e.g. `list.append`, `dict.update`). `sorted(my_list)` is the
   one that returns the new, sorted list.

4. **How do you sort a list of records by score descending, then by name ascending as a
   tie-break, in one call?** `sorted(records, key=lambda r: (-r.score, r.name))` — negate the
   numeric key to flip its direction while keeping the secondary key ascending, or use two
   stable sorts (least-significant key first) if the fields aren't easily negatable.

5. **Is `s[10:20]` on a 5-character string an error?**
   No — slicing clamps silently to whatever exists (`s[10:20]` on a 5-char string returns
   `''`), unlike direct indexing (`s[10]`), which raises `IndexError`. Know which behavior your
   code is relying on.

6. **What's actually wrong with building a large string via `s += chunk` in a loop, and is it
   always as bad as people say?** Strings are immutable, so each `+=` conceptually allocates a
   new string — worst case `O(n²)` total work. In practice, CPython optimizes the single-owner
   case to near-linear, but that's an implementation detail that breaks the moment another
   reference to an intermediate string exists. `''.join(parts)` is the version that's correct
   regardless of interpreter internals, and is what to write under time pressure.

7. **What does `zip([1,2,3], [1,2])` do — raise, pad, or truncate?**
   Truncates silently to the shorter iterable's length, with no warning. If a length mismatch
   would indicate a bug, check the lengths explicitly before zipping.

8. **`(x for x in range(5))` — is that a tuple?**
   No — it's a generator expression; there is no tuple-comprehension syntax. Wrap it in
   `tuple(...)` if a tuple is actually what you want.
