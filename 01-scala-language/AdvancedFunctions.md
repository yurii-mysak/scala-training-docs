# Higher‑order, Curried, and By‑name Parameters

This chapter deep‑dives into function power features we analysed on 2025‑05‑14 and earlier.

---

## 1. Higher‑order functions (HOF)
“A function that takes/returns another function.”

```scala
def twice(f: Int => Int): Int => Int = x => f(f(x))
```
We recreated `foldLeft` from scratch during tail‑recursion chat.

---

## 2. Multiple parameter lists & currying

```scala
def add(x: Int)(y: Int) = x + y
val inc = add(1)        // Int => Int
```
*Currying* enables:
* partial application,
* implicit evidence injection (`using`),
* nicer DSLs (`Future.successful` vs `Future apply`).

---

## 3. By‑name parameters
```scala
def maybe[A](cond: Boolean)(thunk: => A): Option[A] =
  if cond then Some(thunk) else None
```
* Parameter not evaluated until used.  
* Use sparingly—can hide expensive computations.

---

## 4. Default values & named arguments
```scala
def greet(name: String = "Guest", loud: Boolean = false) =
  if loud then println(name.toUpperCase) else println(name)

greet(loud = true)      // named arg
```

---

## 5. Tail recursion & `@tailrec`
```scala
@annotation.tailrec
def gcd(a: Int, b: Int): Int =
  if b == 0 then a else gcd(b, a % b)
```
Compiler rewrites into iterative loop; fails if unsafe.

---

## 6. Self‑type & mixin requirement
Covered in Traits chapter, but recap:

```scala
trait Db
trait Service { self: Db => }
```
Forces `Service` to be mixed with `Db`.

---

## 7. Lazy evaluation & referential transparency
`lazy val` evaluated once on first use; useful for expensive DI graphs.  
In Cats Effect, `IO` defers evaluation guaranteeing referential transparency.

---

## 8. Packages & imports quick guide
* `import pkg.*`—wildcard.  
* `import pkg.{Foo as Bar}`—rename.  
* `given` imports for implicits.

---

## 9. Annotations worth remembering
| Annotation | Use |
|------------|-----|
| `@tailrec` | enforce tail recursion |
| `@deprecated` | mark API |
| `@targetName` (Scala 3) | nicer JVM method name |

---

## 10. Quick interview checks
* Difference between _by‑name_ (`=> A`) vs `() => A`.  
* Currying enables type‑class syntax.  
* `@tailrec` fails compilation if not optimizable → demo it.
