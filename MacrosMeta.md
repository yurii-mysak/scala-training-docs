# Macros & Metaprogramming (Overview)

We only briefly touched on macros in the 2025‑04‑25 interview prep, but here’s a consolidated reference.

---

## 1. Inline & Macros in Scala 3
```scala
inline def debug[A](expr: => A): A =
  ${ debugImpl('expr) }
```
*Uses Tasty‑reflection API at compile time.*

### 1.1 Common use cases
* Automatic JSON codecs (e.g., Circe Magnolia).  
* Boiler‑plate free logging.  
* SQL string interpolators with compile‑time query validation.

---

## 2. Inline without full macro
```scala
inline def twice(inline x: Int): Int = x + x
```
The body is copied at call‑site, no reflection.

---

## 3. Macro pitfalls
* Harder debugging.  
* Binary compatibility.  
* IDE support lagging (chat note).

---

## 4. Resources
* `scala.compiletime.*` for erasedValue, summonInline.  
* Documentation: docs.scala‑lang.org/scala3/reference/metaprogramming.

