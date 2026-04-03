# Type‑Classes & Category‑Theory Primitives

Functional programming libraries in Scala (Cats, ZIO‑Prelude, Scalaz) model *generic algebraic capabilities* as **type‑classes**—traits whose behaviour is supplied for particular types by *instances*. Those instances often correspond to basic category‑theory constructs like **Functor**, **Monoid**, or **Monad**.

---

## 1 · What Is a Type‑Class?

A type‑class is a trait with at least one *type parameter* and no fixed super‑type hierarchy. The compiler selects a given/implicit instance based on that parameter, enabling ad‑hoc polymorphism—similar to Rust’s *traits* or Haskell’s *type‑classes*.citeturn0search0turn0search8

```scala
trait Show[A]:
  def show(a: A): String

given Show[Int] with
  def show(i:Int) = i.toString
```

Calling `show` requires *evidence*:

```scala
def print[A: Show](a: A) = println(summon[Show[A]].show(a))
print(42)        // "42"
```

---

## 2 · Monoids

A **Monoid** is a `Semigroup` (`combine`) plus an **identity element** `empty`. Laws: *associativity* and *left/right identity*.citeturn0search1turn0search9

```scala
trait Monoid[A] extends Semigroup[A]:
  def empty: A
```

*Examples*: `Int` with `(+,0)`, `String` with `(++, "")`, `List[A]` with concatenation.

---

## 3 · Functors & Applicative Functors

* **Functor**: provides `map` lifting pure functions into a context.citeturn0search4turn0search10  
* **Applicative**: adds `pure` and `ap` to apply wrapped functions to wrapped values; supports independent effects.citeturn0search2

```scala
trait Functor[F[_]]:
  extension[A](fa:F[A]) def map[B](f:A=>B):F[B]

trait Applicative[F[_]] extends Functor[F]:
  def pure[A](a:A):F[A]
  extension[A,B](ff:F[A=>B])
    def ap(fa:F[A]):F[B]
```

`Option`, `List`, `Future` are all functors; `Option` and `Future` are applicatives and monads.

---

## 4 · Monad

A **Monad** adds `flatMap` (bind) enabling sequential composition where later steps depend on earlier results. Laws: left identity, right identity, associativity.citeturn0search3turn0search11

```scala
trait Monad[F[_]] extends Applicative[F]:
  extension[A,B](fa:F[A])
    def flatMap(f:A=>F[B]):F[B]
```

`for`‑comprehensions in Scala desugar to nested `flatMap` + `map`.

---

## 5 · Foldable & Traverse

`Foldable` abstracts summarising structures with `foldLeft`. `Traverse` combines `map` and folding, sequencing effects in a container—a generalisation of `traverse` from Haskell.citeturn0search6

---

## 6 · Automatic Instance Derivation

Scala 3’s *type‑class derivation* generates instances for product/sum ADTs if the type‑class follows a simple template.citeturn0search5

```scala
case class Person(name:String, age:Int) derives CanEqual, Show
```

Under the hood the compiler synthesises a given `Show[Person]` by recursively combining `Show[String]` and `Show[Int]`.

### shapeless & Magnolia

Before Scala 3, `shapeless.Generic` + Magnolia macros derived instances generically, used by Circe and Tapir.citeturn0search3

---

## 7 · Category Theory Primer

* An **object** is an abstract “type”; a **morphism** is a function between objects.  
* A **Functor** maps objects → objects and morphisms → morphisms, preserving identity and composition.citeturn0search7

Understanding category‑theory vocabulary helps reason about generic libraries: Functor (map), Applicative (product + map), Monad (Kleisli composition).

### Kleisli
Kleisli wraps an effectful function A => F[B].

Provides .andThen, .compose, and monadic chaining (flatMap) to build complex pipelines.

It’s ubiquitous in libraries like Cats and is the foundation for things like ReaderT and various monad transformer stacks.

#### Why Use Kleisli?
Composing effectful functions in a type-safe way, allowing for modular and reusable pipelines.

Modularity: Build small effectful steps and then wire them together.

Reusability: Compose the same pieces in different pipelines.

Abstraction: Work generically over any F[_] that has a Monad[F] (or FlatMap[F]).

```scala 3
case class User(id: Int, name: String)
case class Address(street: String)

val findUser: Kleisli[Option, Int, User] =
  Kleisli(id => if (id > 0) Some(User(id, s"User-$id")) else None)

val userAddress: Kleisli[Option, User, Address] =
  Kleisli(user => if (user.id % 2 == 0) Some(Address("Even St")) else None)

// Compose them into one pipeline:
val findAddress: Kleisli[Option, Int, Address] =
  findUser andThen userAddress

// Use it:
findAddress.run(2)  // Some(Address("Even St"))
findAddress.run(1)  // None  (either user not found or address lookup failed)

```

---

## 8 · Putting It Together — Example: JSON Encoding

```scala
trait JsonEncoder[A]:
  def json(a:A): Json
object JsonEncoder:
  given JsonEncoder[String] with json(JsString.apply)
  given JsonEncoder[Int]    with json(JsNumber.apply)
  given[A,B](using JsonEncoder[A], JsonEncoder[B])
    as JsonEncoder[(A,B)] = (t:(A,B)) => JsArray(
      summon[JsonEncoder[A]].json(t._1),
      summon[JsonEncoder[B]].json(t._2)
    )
```

Instances compose automatically thanks to implicit resolution.

---

## 9 · Key Takeaways
* Type‑classes enable ad‑hoc polymorphism decoupled from subtyping.  
* Monoids, Functors, Applicatives, and Monads form a **layers of power** hierarchy.  
* Automatic derivation removes boiler‑plate, now first‑class in Scala 3.  
* Category theory supplies the naming and laws behind these abstractions.

---

### Further Reading
* Typelevel Cats documentationciteturn0search0  
* Bartosz Milewski Functor & composition postsciteturn0search4turn0search7  
* Scala 3 Type‑Class Derivation guideciteturn0search5  
* “Scala with Cats” book  
