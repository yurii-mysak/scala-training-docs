
# HashSet & HashMap – A Practical Guide

## 1. What’s a *hash*?

A **hash function** deterministically turns any key into an integer — the *hash code*.  
Think of it as a lightning‑fast “index maker”:

```
hash("apple")   → 213423987
hash("banana")  → 6311074
```

### Goals of a good hash function

| Goal | Why it matters |
|------|----------------|
| **Uniformity** | Keys spread evenly across buckets → avoids hot spots |
| **Determinism** | Same input → same hash every time |
| **Speed** | Must be cheaper than a full equality check |
| **Low collision rate** | Fewer keys share buckets, preserving O(1) access |

---

## 2. Hash Table in 60 seconds 🚀

1. **Compute** `hashCode(k)` → `h`.  
2. **Map** `h` to a *bucket index* (often `h & (capacity‑1)` when capacity is a power of two).  
3. **Store / look up** the entry in that bucket.  
4. **Handle collisions** if multiple keys land in the same bucket:  
   * *Separate chaining* – bucket holds a linked list, tree or mini‑array (Java default).  
   * *Open addressing* – probe to the next free slot (C#/Go style).  
5. When the table is “too full” (exceeds *load factor*), allocate a bigger array and **rehash**.

Average‑case cost of `get`, `put`, `contains` ≈ **O(1)**; worst‑case **O(n)** if every key collides.

---

## 3. `HashMap<K,V>` — key‑value dictionary

| Operation | What happens internally |
|-----------|-------------------------|
| **put** | Find bucket → search chain for equal key → update or append `(key,value)` |
| **get** | Same search, but returns value |
| **remove** | Locate node, unlink it, maybe shrink chain |
| **resize** | Triggered when `size ≥ capacity × loadFactor` (0.75 in Java) |

```scala
val capitals = scala.collection.mutable.HashMap(
  "Berlin" -> "DE",
  "Paris"  -> "FR"
)
capitals("Berlin")            // "DE"
capitals += ("Madrid" -> "ES")
capitals.getOrElse("Rome", "??")  // "??"
```

---

## 4. `HashSet[E]` — uniqueness only

A **set** stores *keys only*. In Java/Scala it’s essentially a thin wrapper around a `HashMap[E, Unit]`, so all hashing rules are identical:

```scala
val visited = scala.collection.mutable.HashSet[String]()
visited += "node‑1"
visited.contains("node‑1")   // true
```

---

## 5. Why hashing *matters* for both

| Point | Implication |
|-------|-------------|
| **`hashCode` + `equals` contract** | Two *equal* keys **must** return the same hash; unequal keys *should* differ where possible. |
| **Poor hash ⇒ performance hit** | Many collisions collapse buckets into long chains, turning O(1) into O(n). |
| **Mutable keys danger** | If a key’s fields change *after insertion*, it “disappears” from the map/set. Use **immutable** keys. |
| **Load factor tuning** | Higher load factor saves memory; lower reduces collisions. |

---

## 6. Java vs. Scala implementation notes

| | **Java 21 `HashMap` / `HashSet`** | **Scala 3 collections** |
|--|-----------------------------------|--------------------------|
| **Mutable variant** | Arrays of Node → linked list → tree (deep buckets) | `mutable.HashMap/Set` use open addressing in 2‑D arrays (cache‑friendly) |
| **Immutable variant** | N/A (wrappers only) | `immutable.HashMap/Set` use **HAMT** (Hash Array‑Mapped Trie) → O(log₃₂ n) with structural sharing |
| **Thread‑safety** | None (`ConcurrentHashMap` instead) | None (`TrieMap` or Java’s `ConcurrentHashMap`) |

---

## 7. Common pitfalls & best practices

1. **Override `equals` *and* `hashCode` together** (case classes help).  
2. Avoid **mutable collection keys** (arrays, lists).  
3. Prefer **power‑of‑two capacities** if sizing manually.  
4. **Profile before tweaking** load factors — defaults are well‑balanced.  
5. For **high‑contention multithreading**, use `ConcurrentHashMap` (Java) or `TrieMap` (Scala).

---

## 8. Mental model cheat‑sheet

| Concept | Analogy |
|---------|---------|
| **hash function** | Turning a book’s title into a shelf number |
| **bucket array** | Rows of shelves in a library |
| **collision** | Two books mapped to the same row; you stack them together |
| **load factor** | How stuffed each shelf can get before buying new shelves |
| **rehash/resize** | Moving every book to a bigger library with new row numbers |

---

## 9. Key takeaways

* A *hash* is just a quick‑to‑compute index.  
* **HashMap** stores *(key, value)* pairs; **HashSet** stores *keys only*.  
* Performance hinges on good `hashCode` & `equals`, reasonable load factors, and immutable keys.  
* Scala’s immutable `HashMap`/`HashSet` use HAMTs but rely on the same hashing principles.

---

*Happy hashing!* 🔑
