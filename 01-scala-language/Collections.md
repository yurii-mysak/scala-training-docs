# Collections in Scala

This chapter aggregates the detailed points we covered across the 2024‑11 and 2025‑05 chats, focusing on **immutable collections** (the default), performance trade‑offs, and interop notes.

---

## 1. Immutable vs Mutable

| Flavor | Package prefix | Thread safety | Typical use |
|--------|----------------|---------------|-------------|
| Immutable (default) | `scala.collection.immutable` | Safe by design | Functional code, actors, Cats Effect |
| Mutable | `scala.collection.mutable` | Caller responsibility | Hot‑loops, mutation inside a single fiber |

> **Tip (chat 2025‑03‑20):** Prefer building large data with a _mutable buffer_ (`ListBuffer`, `ArrayBuffer`) and **then** call `.toList` / `.toVector` for sharing.

---

## 2. Core immutable structures

| Structure | Complexity cheatsheet | Best for | Notes |
|-----------|----------------------|----------|-------|
| **`List`** | `::` prepend O(1) | Stack, pattern match | Linked nodes; random access O(N) |
| **`Vector`** | Index O(log32 N) | General purpose | Chunked 32‑ary tree |
| **`Array`** | Index O(1) | Interop, tight loops | Mutable, boxed unless specialization |
| **`Set`** (`HashSet`) | contains O(1) avg | Unique membership | Load factor ~0.65 |
| **`Map`** (`HashMap`) | lookup O(1) avg | Key‑value store | Iter order is hash‑bucket |

We benchmarked `Vector` vs `List` for 100k appends (chat 2024‑11‑11): Vector finished in ~2 ms, List in ~300 ms due to repeated copies.

---

## 3. Creating and transforming

```scala
val xs = List(1,2,3)
val ys = Vector.fill(5)("hi")
val zs = (1 to 100).toList

xs.map(_ + 1)            // List(2,3,4)
ys.filter(_.length == 2) // Vector("hi", …)
```

All collections share higher‑order ops (`map`, `flatMap`, `fold`).

---

## 4. Builders & performance trick

```scala
val lb = List.newBuilder[Int]
for i <- 1 to 1_000_000 do lb += i
val big = lb.result()             // single allocation for the spine
```

Using a builder avoids O(N²) linked‑list append cost.

---

## 5. Conversions & views

```scala
val arr: Array[Int] = xs.toArray
val view = xs.view.map(_ * 2)     // lazy, no alloc
view.force                       // materialise
```

`view` was introduced in Scala 2.13 redesign; it replaced `Stream` for most lazy bulk operations.

---

## 6. Java interop

* `Buffer` ↔ `java.util.List` via `import scala.jdk.CollectionConverters._`.
* Arrays are already JVM native, but beware of **boxing** for `Array[Int]` vs `Array[Integer]`.

---

## 7. Common pitfalls

| Pitfall | Mitigation |
|---------|------------|
| Accidentally using mutable collection in pure code | Always include immutable qualifier in imports. |
| Repeated `.:+` on `Vector` inside loops (O(N)) | Accumulate in a `ListBuffer`. |
| Forgetting `.view` for large chained transforms | Use `xs.view.map…filter…force` for big data sets. |

---

## 8. Cheat sheet for interviews

*Prefer `Vector` unless you have a prepend‑heavy workload (then `List`).*  
*Use `Set`/`Map` for membership; know Big‑O for hash vs tree.*  
*Remember immutability cost is shared structure not whole‑copy.*  
