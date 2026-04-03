
# Functional Design Patterns

Functional design patterns capture **recurring solutions** to composition, modularity, and effect‑handling problems while preserving purity. This chapter covers five staples used in modern Scala libraries: the **Interpreter / Tagless‑Final** pattern, **Free & Free Applicative** monads, **Optics** (Lens & Prism), **Parser Combinators**, and quick pointers to other idioms such as functional domain modelling.

---

## Interpreter & Tagless‑Final

### Interpreter (classic)

Define an *algebra* as a plain ADT and supply one (or more) **interpreters** that fold it into an effect:

```scala
sealed trait Expr
case class Lit(n:Int)            extends Expr
case class Add(a:Expr, b:Expr)   extends Expr

def eval(e:Expr): Int = e match
  case Lit(n)     => n
  case Add(x, y)  => eval(x) + eval(y)
```

Pros: algebra is pure data; multiple interpreters possible (eval, pretty‑print). Cons: recursive data structure can be slow and unsafe if you forget a case.citeturn0search4

### Tagless‑Final

Encode algebra as **type‑class style trait** parameterised by a higher‑kinded `F[_]`. Implementations inject concrete effects (`IO`, `Task`, `Future`).citeturn0search5turn0search10

```scala
trait Console[F[_]]:
  def readln: F[String]
  def println(msg:String): F[Unit]
```

Benefits: *free for‑comprehension*, easy testing with `Id`, no pattern‑match boiler‑plate.

---

## Free & Free Applicative Monads

A **Free monad** turns any `Functor` into a monad, allowing you to build **embedded DSLs** as data then interpret them later.citeturn0search1turn0search6turn0search11

```scala
import cats.free.Free
sealed trait KV[A]
case class Put(k:String,v:String) extends KV[Unit]
type KVFree[A] = Free[KV, A]
```

* Free **Applicative** lets independent actions run in parallel because there’s no `flatMap`.

Use‑cases: batching DB writes, mocking side‑effects in tests.

---

## Functional Optics (Lens, Prism, etc.)

Optics provide composable accessors for nested immutable data. A **Lens[S,A]** focuses on a product field, while a **Prism[S,A]** focuses on a sum alternative. Libraries: **Monocle** & **ZIO Optics**.citeturn0search3turn0search8

```scala
val streetLens = Lens[Address, String](_.street)(s => a => a.copy(street = s))
(person &|-> addressLens &|-> streetLens).modify(_.capitalize)
```

---

## Parser Combinators

Scala’s historic `scala.util.parsing.combinator` and newer cats‑parse build parsers by **composing functions** that recognise tokens. Advantages: no external grammar files, grammars type‑check with your code.citeturn0search2turn0search7

```scala
val number: Parser[Int] = "\\d+".r ^^ (_.toInt)
val expr:   Parser[Int] = number ~ "+" ~ number ^^ { case a ~ _ ~ b => a + b }
```

---

## Other Patterns & Resources

* **Functional Domain Modelling** – separating data & verbs (ZIO design docs).citeturn0search9  
* **State Monad** – encapsulate mutable state in pure context (see Chapter B).  
* **Validation / Applicative Error** – accumulate errors without short‑circuit.

---

### Further Reading

* Typelevel Cats documentationciteturn0search0  
* Bartosz Milewski Functor & composition postsciteturn0search4turn0search7  
* Scala 3 Type‑Class Derivation guideciteturn0search5  
* “Functional Programming in Scala” Ch 9 & 12  
