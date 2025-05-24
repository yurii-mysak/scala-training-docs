# Traits vs Classes in Scala

This chapter expands our 2024‑11 and 2025‑03 discussions, clarifying **interface vs implementation**, **multiple inheritance**, and the infamous **trait linearisation**.

---

## 1. Quick comparison table

| Feature                               | `trait`                       | `class`                |
|---------------------------------------|-------------------------------|------------------------|
| May be instantiated directly          | No (unless has parameters\*)  | Yes                    |
| Constructor parameters (Scala 3)      | ✔ (e.g. `trait T(x:Int)`)     | ✔                      |
| Abstract members                      | ✔                             | ✔                      |
| Concrete members/fields               | ✔                             | ✔                      |
| Multiple inheritance                  | ✔ (mix several)               | ✖ (single parent)      |
| Java interop                          | Compiles to interface + helper| Compiles to class      |

\* A `trait` with parameters can only be instantiated when mixed into a concrete class.

---

## 2. Syntax refresher

### 2.1 Classic abstract trait
```scala
trait Logger:
  def log(msg: String): Unit      // abstract
```

### 2.2 Trait with implementation
```scala
trait ConsoleLogger extends Logger:
  def log(msg: String) = println(s"LOG: $msg")
```

### 2.3 Mixing multiple traits
```scala
class UserRepo extends Service, ConsoleLogger, Serializable
```
> Note the comma‑separated list in Scala 3 (was `with` in Scala 2).

---

## 3. Trait linearisation (Diamond problem)

```
      Logger
     /      FileLogger  Timestamp
     \      /
      class Live
```

*Scala flattens* the hierarchy **right‑to‑left**.  
In
```scala
class Live extends FileLogger, Timestamp
```
`Timestamp`’s override wins if both define `def log`.

Chat highlight: On 2025‑04‑24 we traced `super.log` calls and saw the order `Live → Timestamp → FileLogger → Logger`.

---

## 4. Stackable behaviour pattern

```scala
trait UpperCase extends Logger:
  abstract override def log(msg:String) =
    super.log(msg.toUpperCase)

class Service extends Logger:
  def run() = log("hello")

val s = new Service with ConsoleLogger with UpperCase
s.run()   // prints HELLO
```

Requires `abstract override` because we are _stacking_ modifications.

---

## 5. State in traits

A trait can hold `val`/`var`, but beware a separate copy per instance:
```scala
trait Counter:
  private var n = 0
  def inc(): Int = { n += 1; n }
```
Mix into multiple objects → separate counters.

---

## 6. Trait parameters (Scala 3)

```scala
trait Greeting(name: String):
  def hello = s"Hi, $name"

class Greeter extends Greeting("Yuriy")
```

Under the hood, each mixin passes the param along the linearised chain.

---

## 7. Best practices from chats

| Advice | Origin chat |
|--------|-------------|
| Keep traits “capability‑oriented”; avoid morphing into half‑implemented classes. | 2024‑11‑11 |
| Prefer final classes + traits over deep class hierarchies. | 2025‑03‑17 |
| Document linearisation order if stacking overrides. | 2025‑04‑24 |

