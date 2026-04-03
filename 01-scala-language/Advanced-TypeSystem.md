# Advanced Type‑System Features & Automatic Type‑Class Derivation

Scala’s type system supports **higher‑kinded**, **dependent**, and **union**/`enum` types, enabling libraries like *shapeless* and *Magnolia* to derive boiler‑plate automatically.

---

## 1 · Higher‑Kinded & Dependent Types

A type taking a type parameter (`F[_]`) is *higher‑kinded*. Dependent types let a member type depend on a value or path. `shapeless` uses them extensively.citeturn0search9

---

## 2 · Scala 3 `Mirror` & `derives`

The compiler synthesises a generic `Mirror.Of[T]` for any product or sum. Type‑classes can offer a `derived` method to auto‑generate instances.citeturn0search3

```scala
case class User(name:String,age:Int) derives Eq
```

---

## 3 · shapeless `Generic`

`Generic.Aux[T, R]` converts between a case class `T` and its HList representation `R`. This enables generic transformations and automatic codec derivation.citeturn0search4

---

## 4 · Magnolia Macro

Magnolia uses macros to materialise type‑class instances for nested ADTs at compile‑time, sidestepping boiler‑plate.citeturn0search5

---

## 5 · Putting It Together: Automatic JSON Encoder

Libraries (Circe, Jsoniter) exploit generic derivation so `import io.circe.generic.auto._` materialises `Encoder[T]`/`Decoder[T]` via macro or Mirror.

---

## 6 · Linearizability & Serializability (Bonus)

*Linearizability* is an external consistency guarantee across nodes; see CAP chapter. *Serializable* is the strictest SQL isolation; the two are orthogonal but often confused.citeturn0search6

---

