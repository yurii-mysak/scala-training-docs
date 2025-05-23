# Scala Type Hierarchy & Advanced Type Relationships

This chapter gathers every discussion we had on bottom / top types, variance, upper‑/lower‑bounds, abstract types, and how they surface in **interview questions**.

---

## 1. Universal hierarchy refresher

```
          ┌─ AnyVal  ─ Byte, Int, …, Unit
Any ──────┤
          └─ AnyRef  ─ (all classes) … ─ Null
                        ▲
                        └─ Nothing
```

### 1.1 `Any`
* Root of everything; defines `==`, `hashCode`, `toString`.

### 1.2 `AnyVal`
* Unboxed primitives plus `Unit`, value classes.  
* We noted (chat 2025‑04‑25) that extending `AnyVal` lets you wrap an `Int` with **zero runtime overhead**.

### 1.3 `AnyRef`
* Alias for `java.lang.Object`; all reference types inherit.

### 1.4 `Nothing`
* Bottom type; subtype of _every_ other type.  
* Used for:
  * Empty collections: `Nil: List[Nothing]`
  * Non‑returning methods: `def fail(msg: String): Nothing = throw new RuntimeException(msg)`

### 1.5 `Null`
* Subtype of `AnyRef` only (for Java interop).  
* Rarely used in idiomatic Scala.

---

## 2. Variance (`+A`, `-A`, invariance)
| Mark | Meaning | Example |
|------|---------|---------|
| `+A` | Covariant – safe to read | `List[+A]` |
| `-A` | Contravariant – safe to write | `Function1[-T, +R]` |
| _none_ | Invariant | `Array[A]` |

> **Rule of thumb (chat 2025‑03‑20):**  
> *If you only **output** `A`, make it covariant; if you only **consume** `A`, contravariant.*

We demonstrated why `Array[+A]` would break type safety (mutable write).

---

## 3. Upper & Lower bounds
### 3.1 Upper bound
```scala
def printSize[A <: Iterable[_]](xs: A) = println(xs.size)
```
Accepts anything _that is an_ `Iterable`.

### 3.2 Lower bound
```scala
def prepend[A >: Int](elem: A, xs: List[A]) = elem :: xs
```
Common in producer methods (`foldRight`).

---

## 4. Abstract types vs type parameters
```scala
trait Buffer:
  type T                         // abstract type member
  def empty: T

class IntBuffer extends Buffer:
  type T = Int
  val empty = 0
```
*Pro:* better for cake pattern DI; *con:* less flexible than generics.  
We used this in a Doobie transactor wrapper (chat 2024‑11‑11).

---

## 5. Polymorphic methods
```scala
def identity[A](x: A): A = x
```
Method‑level generics vs class‑level. Compile‑time erased (see §6).

---

## 6. Type erasure & `ClassTag`
JVM discards generics → cannot pattern‑match on `List[String]`.  
Solution: require `ClassTag` evidence.

```scala
def firstOfType[A: ClassTag](xs: Seq[Any]): Option[A] =
  xs.collectFirst { case a: A => a }
```

---

## 7. Wildcards & Existentials (legacy)
```scala
val anyList: List[_] = List(1,2,3)
```
In Scala 3, _wildcard type_ becomes an **anonymous type parameter**.

---

## 8. Interview flashcards

* `Nothing` useful for covariance, `Nil` literal.  
* Covariance + mutability = ⚠️ unsound (explain `Array`).  
* Upper bound = *at most*; lower bound = *at least*.  
* `ClassTag` or `TypeTag` needed to keep runtime class info.

