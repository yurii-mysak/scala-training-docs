# Implicits, Context Bounds & Type‑Class Pattern

This chapter expands all dialogues about **implicit parameters**, **given/using** syntax, and the type‑class abstraction that powers libraries like Cats, along with the full **resolution order** cheatsheet.

Reference chats: *2024‑05‑30 implicit‑class vs conversion*, *2025‑05‑23 tagless vs type‑class*, *2025‑05‑14 context‑bounds interview prep*.

---

## 1. Implicit / Given parameters (Scala 3)
```scala
def log[A](a: A)(using s: Show[A]) =
  println(s.show(a))
```
* In Scala 2: `implicit s: Show[A]`.  
* Call‑site inference:
```scala
given Show[Int] with
  def show(i:Int) = i.toString

log(42)   // compiler supplies Show[Int]
```

---

## 2. Context bounds sugar
```scala
def log[A: Show](a: A) = summon[Show[A]].show(a)
```
Equivalent to an explicit `using` param plus `summon`.

---

## 3. Implicit resolution order
1. **Local scope** – inside current method/block.  
2. **Imported scope** – `import foo.given`.  
3. **Companion objects** of:
   * the **type‑class** (`Show`)  
   * the **type** argument (`Int`)  
4. **Implicit scope of outer types** (for nested generics).

> We reproduced this chain in REPL (chat 2024‑05‑30) by intentionally shadowing instances.

---

## 4. Ambiguity & prioritisation
If two candidates are equally specific → compilation error.

*Work‑around*: define **low‑priority** given in a parent trait:
```scala
trait ShowInstancesLow:
  given Show[Int] with …

object ShowInstances extends ShowInstancesLow:
  given Show[User] with …
```

---

## 5. Implicit Conversions
```scala
import scala.language.implicitConversions
given Conversion[String, Email] with
  def apply(s:String) = Email(s)
```
* Rule: conversions only kick when type‑checking fails.  
* Avoid unexpected surprises; keep in a dedicated `object conversions`.

---

## 6. Type‑Class pattern step‑by‑step
1. **Trait defining ops**
   ```scala
   trait JsonEncoder[A]:
     def encode(a:A): String
   ```
2. **Instances** (`given`) for types.
3. **Syntax** via extension method:
   ```scala
   object syntax:
     extension [A: JsonEncoder](a:A) def toJson = summon[JsonEncoder[A]].encode(a)
   ```
4. **Generic algorithm** requiring evidence.

We built `Show`, `Eq`, `Functor` examples during tagless‑final sessions.

---

## 7. Derived instances (`derives`)
```scala
import io.circe.*
case class User(name:String, age:Int) derives Encoder, Decoder
```
Compiler auto‑generates given definitions.

---

## 8. Initialization order for implicits
* Lazy vals not initialised until first use → safe for expensive derivations.
* Chat caution: cross‑object circular implicit val can deadlock on initialisation.

---

## 9. Implicit search in Tagless‑Final
Interpreters rely on a **given Monad[F]**; missing import causes cryptic error `No given instance of type cats.Monad[F] was found`.

Fix: `import cats.syntax.all.*` or explicit `given`.

---

## 10. Cheat table: when to use
| Need | Use |
|------|-----|
| Provide type‑class instance | `given` |
| Require evidence | `using` param / context bound |
| Convert one type to another | `Conversion` |
| Ad‑hoc polymorphism over F[_] | Tagless‑final with implicit cats‑typeclasses |

