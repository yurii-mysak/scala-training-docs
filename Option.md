# `Option` – The Null‑safety Workhorse

This chapter expands our multiple demos showing how `Option` eliminates `NullPointerException` and composes with other FP abstractions.

---

## 1. Creating options

```scala
Option("hi")          // Some("hi")
Option(null)          // None
Some(42)              // explicit Some
None                  // empty
```

---

## 2. Core combinators

| Method | Purpose | Example |
|--------|---------|---------|
| `map` | transform if defined | `Some(2).map(_*2)` → `Some(4)` |
| `flatMap` | chain possible failures | `getUser(id).flatMap(fetchAddr)` |
| `getOrElse` | default value | `opt.getOrElse("N/A")` |
| `fold` | dual of map + default | `opt.fold("empty")(_.toUpperCase)` |
| `orElse` | fallback option | `dbOpt.orElse(cacheOpt)` |
| `filter` | keep if predicate holds | `Some(5).filter(_>10)` → `None` |

---

## 3. For‑comprehension usage

```scala
for
  u <- userOpt
  a <- addrOpt(u.addrId)
yield (u,a)
```
Desugars to nested `flatMap` + `map`.

---

## 4. Interop with `Either`

From May 2025 Q&A:
```scala
def toEither[A](opt:Option[A], ifEmpty: => String): Either[String,A] =
  opt.toRight(ifEmpty)
```

---

## 5. When **not** to use Option

* Streaming large collections – prefer `Iterable.empty` to mean “none”.  
* Performance‑critical loop where `null` check is measurably faster (rare).  
* Over the wire (use protobuf `optional` instead).

---

## 6. Advanced – `OptionT` transformer

```scala
import cats.data.OptionT
val prog: OptionT[IO,User] =
  for
    id <- OptionT.liftF(getId())
    u  <- OptionT.fromOption[IO](lookup(id))
  yield u
```
Avoids nested `IO[Option[A]]`.

---

## 7. Quick quiz (from chat)

> **Q:** What does `Option.when(cond)(value)` return?  
> **A:** `Some(value)` if `cond` is true else `None`.

---

