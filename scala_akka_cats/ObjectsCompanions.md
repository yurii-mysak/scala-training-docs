# Singleton, Companion, and Extractor Objects

This chapter consolidates everything we discussed about Scala’s `object` keyword, including **companion objects**, **extractor objects**, and initialization order quirks.

---

## 1. The `object` keyword in a nutshell
* Creates a **singleton** instance eagerly on first access.
* Compiles to a Java class named `Foo$` with a static `MODULE$` holding the instance.
* Members are accessed as `Foo.bar`.

Example from our 2025‑03‑17 project bootstrap:
```scala
object Config:
  val dbUrl = sys.env.getOrElse("DB_URL", "jdbc:postgres://localhost")
```

---

## 2. Companion objects
A companion shares the same *name* and *file* as a class/trait and can access its `private` members.

```scala
class Counter private (val n: Int)
object Counter:
  val zero = Counter(0)
  def apply(n: Int) = new Counter(n)
```
### 2.1 Generated `apply` for case classes
`case class User(name:String)` automatically gets `object User { def apply(name:String):User = new User(name) }`.

### 2.2 Holding type‑class instances
In the Tagless‑Final chapter we placed
```scala
given Show[User] with
  def show(u:User) = u.name
```
inside `object User` so the compiler finds it via **companion‑scope implicit resolution**.

---

## 3. Extractor objects
Provide an `unapply` (or `unapplySeq`) to participate in pattern matching.

```scala
object RGB:
  def unapply(hex: String): Option[(Int,Int,Int)] = …
```
Usage:
```scala
"#ff00aa" match
  case RGB(r,g,b) => …
```
We derived this during the Pattern Matching deep‑dive (chat 2025‑05‑14).

---

## 4. Initialization order
Order is **left‑to‑right**, **top‑to‑bottom** in the file:
```scala
object A:
  println("A loaded")
object B:
  println("B loaded")
```
But when you reference `B` first, only `B` gets initialised, `A` remains dormant.

For mutually‑referencing companions:
```scala
object Foo:
  val id = Bar.name          // may throw NPE if Bar not yet initialised
object Bar:
  val name = "bar"
```
Guideline (chat 2024‑11‑11): avoid cross‑object eager references; use `lazy val` or methods.

---

## 5. Lazy vs eager singletons
```scala
lazy val log = Logger(getClass)   // evaluated once on first call
```
Combines with object fields for caching heavy resources.

---

## 6. Best practices summary
| Practice | Reason |
|----------|--------|
| Keep companion minimal (factories, constants, type‑class instances). | Easier testability |
| Use `lazy` for heavyweight vals. | Avoid class‑loading cost |
| Put extractors in companion when they map 1:1. | Discoverability |

---

## 7. Interview flashcards
* Companion shares private scope with its class.  
* Extractor = `unapply`; `unapplySeq` for var‑arg patterns.  
* Initialisation order = referenced‑object first; beware cross‑refs.  
* Objects compile to `MODULE$`; method calls become static dispatch for speed.

