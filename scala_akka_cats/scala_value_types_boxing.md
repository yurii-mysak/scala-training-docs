# Scala Value Types, Primitive Types & Boxing

## 1  Why It Matters for Interview Preparation
Understanding how Scala represents data at the JVM level is crucial for:
* **Performance tuning** – avoiding unnecessary object allocation.
* **Interoperability** – writing seamless Java ↔︎ Scala code.
* **API design** – choosing between opaque/value classes vs. standard case classes.
Interviewers often probe your grasp of *boxing*, *specialisation*, and *value classes* to evaluate both language‑level and JVM knowledge.

---

## 2  Foundational Type Hierarchy

```
Any            // root of all types
├── AnyVal     // *value* types (stored directly on stack / in registers)
│   ├── Int         Byte   Short   Long
│   ├── Double      Float  Char    Boolean
│   └── Unit        // like `void`, only value is ()
└── AnyRef     // reference types (objects on the heap) – aliased to `java.lang.Object`
```

*All value types extend **AnyVal** and are **final**.*

---

## 3  Primitive vs. Boxed Types

| Scala source type | JVM primitive | JVM boxed class | When boxing occurs |
|-------------------|--------------|-----------------|--------------------|
| `Int`             | `int`        | `java.lang.Integer` | When an `Int` is used where an `Object` is expected (e.g. `val x: Any = 42`) |
| `Double`          | `double`     | `java.lang.Double`  | Passing to a generic method that erases to `Object` |
| `Boolean`         | `boolean`    | `java.lang.Boolean` | Storing inside a `List[Boolean]` (unless specialised) |

### Boxing/Unboxing Flow (ASCII diagram)

```
val p: Int = 7               // stored as primitive `int`
val boxed: Any = p           // `Integer.valueOf(7)`       ← boxing
val again: Int = boxed.asInstanceOf[Int]  // `Integer.intValue()` ← unboxing
```

*Cost*: extra heap allocation (+GC pressure) & virtual call on `Integer.intValue()`.

---

## 4  Generics & Specialisation

* **Type erasure** means `List[Int]` ∼ `List[AnyRef]` on the JVM, triggering boxing.
* **`@specialized`** (Scala 2) / **`-Yexplicit-nulls` & value‑class‑based inline loops** (Scala 3) generate bytecode versions for chosen primitives.

```scala
class FastPair[@specialized(Int, Long) A](var a: A, var b: A)
```

Generates *two* extra classes: `FastPairInt`, `FastPairLong` that use primitives directly.

> **Best practice**: Specialise performance‑critical generic collections, but avoid code bloat by limiting the set of primitives.

---

## 5  Value Classes & Opaque Types

### 5.1  Value Classes (Scala 2 / 3)

```scala
class UserId(val value: Int) extends AnyVal
```

*Compiles to*:
* at compile‑time: *zero‑overhead wrapper*;
* at runtime: same `int` when not stored in `Array[UserId]` or pattern‑matched.

Constraints:
* Only one `val` parameter.
* No additional fields.
* No `equals/hashCode` override allowed (they delegate to boxed value).

### 5.2  Opaque Types (Scala 3)

```scala
object domain:
  opaque type UserId = Int
  object UserId:
    def apply(raw: Int): UserId = raw
```

*Key differences*: no allocation *anywhere*, even inside collections; representation is *always* `int`.

> **Interview tip**: Be ready to compare value classes vs. opaque types and articulate when to migrate.

---

## 6  Performance Checklist

| Scenario | Risk | Mitigation |
|----------|------|-----------|
| Storing primitives in generic collections | Boxing each element | Use `Array[Int]`, specialised collections (`IntArrayBuffer`), or `Vector` with `@specialized` |
| High‑frequency numeric computation | GC pauses from boxed temporaries | Use value‑class domain types only where necessary; rely on `-opt:l:inline` |
| Cross‑module Scala ↔︎ Java calls | Surprising autoboxing when signature is `java.lang.Integer` | Declare overloaded methods with both primitive and boxed signatures if API is hot‑path |

---

## 7  Interoperability Corner Cases

1. **SAM types & Java functional interfaces**  
   ```scala
   val pred: java.util.function.IntPredicate = _ > 0   // specialised primitive bridge added
   ```

2. **Varargs** – `println(1, 2, 3)` creates `Seq[Any]` → boxed.

3. **Reflection** – runtime mirrors see boxed classes; watch out when using `ClassTag`.

---

## 8  Common Interview Questions & Model Answers

1. **“Why does `List[Int]` allocate?”**  
   Because generic parameter `A` is erased to `Object`; each `Int` must be boxed.

2. **“Explain the difference between value class & case class?”**  
   *Value class* compiles away (no runtime wrapper) but has severe restrictions; *case class* is a full‑blown heap object with rich semantics.

3. **“How would you design a domain wrapper around `Double` without allocations?”**  
   In Scala 3 prefer an *opaque type*; in Scala 2 use a *value class* + keep collections as `Array[Double]`.

---

## 9  Best Practices ✓

* Default to **primitive types** for internal algorithms and numeric computation.
* Wrap primitives with **opaque types** (Scala 3) or **value classes** (Scala 2) for domain‑safety **only** when the API is performance‑sensitive.
* **Benchmark** with JMH; confirm boxing via `-XX:+PrintCompilation` or `-prof perfasm`.
* Enable **`-opt:l:inline`** and `-Ybackend-parallelism` for hot builds.
* Avoid implicit conversions that trigger hidden boxing—use explicit `.toInt` etc.
* Document **public API** expectations (`@uncheckedVariance`, overloaded primitive signatures).

---

## 10  Further Reading

* Scala 3 reference: *Opaque Types & Value Classes* (§3.3.2)  
* EPFL blog, “Removing Runtime Overhead with Opaque Types”.
* JMH samples: `org.openjdk.jmh.samples.JMHSample_11_Loops`.
* N. Shcherbina, *Pragmatic Scala Performance* (chapter 2).

---

### Diagram – Boxing Impact on GC Throughput
```
Requests/sec  ─┐   no boxing
               │■■■■■■■■■■■■■■■■  1 950
               ├───────────────────
               │■■■■■■  740  ← boxed
               └───────────────────
                  ↑ GC pauses ↑
```
(Test run: 1 M additions of `Int` vs. `Integer` inside a `Vector`)
