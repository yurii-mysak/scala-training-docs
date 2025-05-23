# Shapeless HLists & Generic Programming

Although not core to the Scala standard lib, `shapeless` HLists popped up in our April 2025 curiosity chat. Here’s a concise refresher.

---

## 1. What is an HList?
Heterogeneous list where each element can have a different type and the **type encodes the length**:

```scala
import shapeless.{::, HList, HNil}
val h: Int :: String :: Boolean :: HNil = 42 :: "hi" :: true :: HNil
```

---

## 2. Benefits
* Type‑safe positional access (`h.head` gives `Int`).  
* Serve as generic representation of case classes.

---

## 3. `Generic` type‑class
```scala
case class Person(name:String, age:Int)
val gen = Generic[Person]
val hlist = gen.to(Person("Ann",30))      // String :: Int :: HNil
```
Enables automatic derivation for libraries like Circe, Doobie.

---

## 4. Mapping & poly functions
```scala
object inc extends Poly1:
  given Case.Aux[Int, Int]     = at(_+1)
  given Case.Aux[String,String]= at(_.toUpperCase)

val res = h.map(inc)   // 43 :: "HI" :: Boolean :: HNil
```

---

## 5. HList limitations
* Compilation time & error messages.  
* Replaced in Scala 3 by **tuple & inline** metaprogramming.

---

