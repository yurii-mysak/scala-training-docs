# Pattern Matching in Scala

## Why we use it
Pattern matching is Scala’s _Swiss‑army knife_ for **deconstructing data** and replacing nested `if/else` chains with declarative logic.  
We leaned heavily on it in our May 2025 interview‑prep chats to show exhaustive handling of ADTs.

---

### 1. Basic value matches
```scala
val code = 200
val text = code match
  case 200 => "OK"
  case 404 => "Not Found"
  case _   => "Unknown"
```
* `_` is the wildcard (like Java’s default branch).  
* Order matters; first match wins.

---

### 2. Extracting fields from case classes
```scala
case class Person(name: String, age: Int)
val p = Person("Yuriy", 30)

p match
  case Person(n, a) => s"$n is $a years old"
```

---

### 3. Wildcards and ignored fields
```scala
p match
  case Person(_, age) if age > 18 => "Adult"
```
*We used this exact form in the 2025‑05‑23 Q&A to filter adults.*

---

### 4. Nested patterns
```scala
case class Address(city: String)
case class User(info: Person, addr: Address)

def livesInKyiv(u: User) = u match
  case User(Person(_, _), Address("Kyiv")) => true
  case _                                   => false
```

---

### 5. Custom extractors (`unapply`)
```scala
object CSV3:
  def unapply(str: String): Option[(String, String, String)] =
    str.split(',') match
      case Array(a,b,c) => Some(a,b,c)
      case _            => None

"host,port,username" match
  case CSV3(h, p, u) => println(s"host=$h, port=$p, user=$u")
```
This example came from our 2025‑05‑14 demo.

---

### 6. Exhaustiveness & sealed traits
With
```scala
sealed trait Color
case object Red  extends Color
case object Blue extends Color
```
the compiler will warn if a `match` forgets `Blue`.  
We used this to justify putting children in the same file (chat 2025‑05‑05).

---

### 7. Guards
```scala
n match
  case x if x % 2 == 0 => "even"
  case _               => "odd"
```

---

### 8. Performance notes
* A `match` on *sealed* hierarchies compiles to a jump‑table (`tableswitch`) or `lookupswitch`.
* Pattern guards are just extra `if`, so keep them simple.

---

### 9. Pitfalls & best practices
| Pitfall | Fix |
|---------|-----|
| Over‑lapping cases | Order from specific → general |
| Too many nested patterns | Extract helpers / use name binding |
| Throwing in extractor | Return `None` instead |

---

### 10. Cheatsheet
| Syntax | Meaning |
|--------|---------|
| `case Foo(x, y)` | Positional extractor |
| `case Foo(a, _*)`| Variable‑length sequence |
| `case x @ Foo(_,_)`| Name binding |
| `case _` | Wildcard / default |

