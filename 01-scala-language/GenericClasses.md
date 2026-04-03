# Generic & Higher‑Kinded Classes

This chapter expands our scattered notes on generics—specifically **type parameters**, **higher‑kinded types**, **polymorphic methods**, and how these play with variance.  

Reference chats: *2025‑03‑17 tagless demo*, *2025‑05‑23 HK algebra*, *2024‑11‑11 generics vs abstract types*.

---

## 1. Type Parameters – the basics
```scala
class Box[A](private val value: A):
  def get: A = value
```
* At **JVM bytecode** level, `A` is erased to `Object`; see §5 for `ClassTag`.

### 1.1 Instantiation
```scala
val intBox    = Box(42)           // Box[Int]
val stringBox = Box("hi")         // Box[String]
```
Scala infers the parameter from the constructor arg.

---

## 2. Variance revisited (quick)
*You met full theory in **TypeHierarchy.md**; here we see how to apply it.*

```scala
class Source[+A](value: A)      // covariant, safe for output
class Sink[-A]:
  def put(a: A): Unit           // consumes A
```
Attempting mutation in `Source` would fail to compile.

---

## 3. Higher‑Kinded Types (HKTs)
A type constructor that *itself takes a type parameter*.

```scala
trait Functor[F[_]]:
  extension [A](fa: F[A])
    def map[B](f: A => B): F[B]
```
Used heavily in **Cats** and our *tagless‑final* algebras.

### 3.1 Kind projector syntax (Scala 2)
```scala
type EitherT[F[_], E] = ({ type L[A] = EitherT[F, E, A] })#L
```
Scala 3 removes the need for the `#Lambda` hack; you can write:
```scala
type EitherT[F[_], E] = [A] =>> EitherT[F, E, A]
```

---

## 4. Polymorphic methods vs class parameters
Method‑level generics:
```scala
def swap[A, B](t: (A, B)): (B, A) = (t._2, t._1)
```
Unlike class generics, these cannot have variance annotations.

---

## 5. Type Erasure and `ClassTag`
Because generics are erased, pattern matching fails:
```scala
xs match
  case list: List[String] =>  // warning: unchecked
```
Fix via evidence:
```scala
import scala.reflect.ClassTag
def firstOf[A: ClassTag](xs: Seq[Any]): Option[A] =
  xs.collectFirst { case a: A => a }
```
Chat 2025‑04‑25: we saw `firstOf[Int](Seq("x", 1, 2))` returns `Some(1)`.

---

## 6. Abstract Types vs Generics (cake pattern)
```scala
trait Buffer:
  type T
  def empty: T
```
*Pros*: can be refined (`type T = Int`) in sub‑traits.  
*Cons*: cannot vary per‑method call.

---

## 7. Inner Classes
Each instance owns its own class:
```scala
class Graph:
  class Node(val id: Int)
  val root = new Node(0)
```
`new Graph().Node` is a _path‑dependent type_.  
In 2024‑11‑11 we used this to model an AST where `Tree#Node` was tied to a particular tree.

---

## 8. Self‑type revisited
Forcing dependency injection:
```scala
trait Dao
trait Service { self: Dao => }
```
Ensures any concrete `Service` mixes a `Dao`; used in our Doobie transactor example.

---

## 9. Interview crib sheet
* HKTs power Cats type classes.  
* Erasure ⇒ need `ClassTag` for run‑time checks.  
* Path‑dependent types arise from inner classes.  
* Self‑types ≠ inheritance; they express **requires**.

