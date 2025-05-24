# Functional Data Structures

Functional data structures are **persistent**: every “mutation” returns a **new version** that shares structure with the old, so previous snapshots remain accessible without copying whole objects. This chapter surveys the core persistent collections in Scala, dives into algebraic data types (ADTs), and shows how generic representations (e.g., *shapeless* `Generic`) enable boiler‑plate‑free programming.

---

## 1 · Persistent Lists & Vectors
Scala’s `List` is a classic singly‑linked cons‑list: prepending via `::` is O(1) while random access is O(N). Persistent `Vector` uses a 32‑way tree (wide trie) which yields ~O(log₃₂ N) indexing but retains immutability.citeturn0search0turn0search8

```scala
val xs = List(1,2,3)     // prepend‑fast
val ys = Vector(1,2,3)   // random‑access
```

---

## 2 · Queues & Double‑List Trick
`immutable.Queue` stores two lists: **in** (enqueue) and **out** (dequeue). When *out* empties, the implementation pivots by reversing *in*. This yields amortised O(1) enqueue/dequeue while remaining purely functional.citeturn0search4turn0search12

---

## 3 · Trees & Maps
Chris Okasaki’s red‑black tree yields a purely‑functional `Map/Set` with logarithmic ops; Scala’s `TreeMap` adopts this design.citeturn0search5turn0search13  Binary trees illustrate recursion and structural sharing foundational to FP.citeturn0search7turn0search15

---

## 4 · Non‑Empty Collections
`NonEmptyList` guarantees at compile‑time that a list has at least one element—handy for validation errors where “no error” should be `Valid`, not `Invalid` with empty list.citeturn0search6turn0search14

---

## 5 · Algebraic Data Types (ADTs)
An **ADT** is a composite of product (AND) and sum (OR) types. For instance:

```scala
sealed trait Expr
case class Num(n:Int)                 extends Expr
case class Add(a:Expr,b:Expr)         extends Expr
case class Mul(a:Expr,b:Expr)         extends Expr
```

`Expr` is a *sum* of cases; each case’s fields form a *product* type. ADTs allow total pattern‑matching and exhaustive compiler checks.citeturn0search2turn0search10

---

## 6 · Generic Representations with *shapeless*
*shapeless*’s `Generic.Aux` converts any case class into an HList and back, enabling generic programming such as automatic CSV/parquet encoders:citeturn0search3turn0search11

```scala
import shapeless.{Generic, HList}
case class Person(n:String,a:Int)
val gen = Generic[Person]
val h: String :: Int :: HNil = gen.to(Person("Ann",30))
```

---

## 7 · Why Persistence Matters
Because old versions remain intact, you can:
* Implement **time‑travel / undo**.  
* Achieve **lock‑free concurrency**—readers never block writers.  
* Make algorithms easier to test (pure inputs ⇒ pure outputs).

---

## 8 · Guidelines for Choosing a Structure
| Need | Pick |
|------|------|
| Many prepends, pattern‑matching | `List` |
| Random access & updates | `Vector` |
| FIFO queue | `Queue` |
| Non‑empty guarantee | `NonEmptyList` |
| Ordered map/set | `TreeMap` / `TreeSet` |

---

### Further Reading
* *Functional Programming in Scala* Ch. 3 – Manningciteturn0search1  
* SoftwareMill blog — Persistent data structuresciteturn0search0  
* Okasaki, *Purely Functional Data Structures* (book)  