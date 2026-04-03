# For‑Comprehensions: Desugaring and Patterns

This chapter reproduces our 2025‑05‑14 explorations of `for` syntax, generator patterns, and how it maps to `map`, `flatMap`, and `withFilter`.

---

## 1. Basic translation
```scala
for
  a <- Option(1)
  b <- Option(2)
yield a + b
```
desugars to:
```scala
Option(1).flatMap(a => Option(2).map(b => a + b))
```

---

## 2. Guards (`if` filters)
```scala
for
  x <- List(1,2,3)
  if x % 2 == 1
yield x
```
becomes `.withFilter(x => x % 2 == 1).map(x => x)`.

*We measured in REPL that `withFilter` is lazy and allocation‑free (chat).*

---

## 3. Pattern binding
```scala
for (User(name, age) <- users) yield name
```
If the pattern fails to match, that iteration is skipped (for collections) or becomes `None`/`Left` for monads that support failure.

---

## 4. `yield` vs `foreach`
Omit `yield` ⇒ return `Unit` via underlying `foreach`.  
We warned (2025‑05‑14): accidental side‑effect only loops when you forget `yield`.

---

## 5. Multiple independent generators (Cartesian product)
```scala
for
  x <- List(1,2)
  y <- List("a","b")
yield (x,y)
```
Gives 4 tuples; equivalent nested `flatMap`.

---

## 6. Using with `Future`
```scala
for
  u <- fetchUser(id)
  p <- fetchPosts(u.id)
yield (u,p)
```
Produces joined `Future` that completes when both async ops done sequentially.

---

## 7. Custom desugaring rules
Requires definitions:
```scala
def flatMap[B](f: A => F[B]): F[B]
def map[B](f: A => B): F[B]
def withFilter(p: A => Boolean): F[A]
```
We built a tiny `Box` monad to illustrate in REPL.

---

## 8. Pitfalls & best practices
| Pitfall | Tip |
|---------|-----|
| Nested effects leading to `Future[Option[A]]` | Consider `OptionT` / `EitherT`. |
| Heavy logic in guards | Move to separate `val` for readability. |
| Forget `.withFilter` laziness when converting to Scala 2.12 | Use `collect` instead if you need partial patterns. |

---

## 9. Quick reference table

| Feature | Needs `map` | Needs `flatMap` | Needs `withFilter` |
|---------|-------------|-----------------|--------------------|
| Single generator + `yield` | ✔ | ✖ | ✖ |
| Multiple generators | ✔ | ✔ | ✖ |
| `if` guard | ✔ | ✔ | ✔ |

