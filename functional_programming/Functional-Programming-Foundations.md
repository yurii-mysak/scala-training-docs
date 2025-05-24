# Functional‑Programming Foundations

## Overview
Functional programming (FP) treats **functions as values**, emphasises *immutability*, and relies on *referential transparency* to make code easier to reason about, test, and parallelise. This chapter walks through the bedrock concepts—first‑class and higher‑order functions, pure functions, strict vs lazy evaluation, recursion & tail‑rec optimisation, and Scala’s immutable collections model—grounding each idea in Scala 3 syntax and linking to classic FP literature.

---

## First‑Class & Higher‑Order Functions
A language supports *first‑class functions* when functions can appear anywhere other values can (assigned to variables, passed as arguments). A **higher‑order function (HOF)** either *takes a function* or *returns a function*. Scala enables both because every function literal compiles to an instance of `FunctionN` and is therefore a value.citeturn0search0turn0search7

```scala
val inc:  Int => Int    = _ + 1
val map: (Int => Int) => List[Int] = f => List(1,2,3).map(f)
```

---

## Pure Functions & Referential Transparency
A *pure* function’s output depends **only** on its inputs and has **no side‑effects** (no mutation, I/O, or hidden state). This implies *referential transparency*: you can replace a call with its result without changing program behaviour.citeturn0search2turn0search1

```scala
def add(a:Int, b:Int) = a + b          // pure
var total = 0
def impureInc(n:Int) = { total += n }  // impure (updates total)
```

---

## Strict vs Non‑Strict (Lazy) Evaluation
* **Strict (eager)**: arguments are evaluated **before** entering the function body (default in Scala).  
* **Non‑strict (lazy)**: argument evaluation is deferred until the value is actually needed.citeturn0search3

Scala offers:
```scala
def strictSum(a:Int, b:Int) = a + b
def lazySum(a: => Int, b: => Int) = a + b   // by‑name params
lazy val cached = computeHeavy()            // evaluated once on first access
```

---

## Recursion & Tail‑Rec Optimisation
FP replaces loops with recursion. Scala’s `@tailrec` annotation forces the compiler to optimise a self‑call into a **while loop**, guaranteeing stack‑safety.citeturn0search5

```scala
import scala.annotation.tailrec
@tailrec
def gcd(a:Int,b:Int):Int =
  if b==0 then a else gcd(b, a % b)
```

---

## Immutable Values & Collections
Immutability eliminates *aliasing bugs*. Scala encourages `val` over `var` and ships parallel hierarchies of **mutable** and **immutable** collections.citeturn0search4turn0search6

```scala
val xs  = List(1,2,3)          // immutable
var ys  = scala.collection.mutable.ListBuffer(1,2,3) // mutable
```
Immutable operations (`xs :+ 4`) return a *new* list sharing most structure with the old one.

---

## Lazy Evaluation in Scala
`lazy val` and by‑name (`=>`) params let you postpone expensive work:

```scala
lazy val config = loadFile()           // executed once
def debug(msg: => String) = if(logEnabled) println(msg)
```
This underpins libraries such as `LazyList` (formerly `Stream`) that model potentially infinite sequences.citeturn0search3

---

## Summary
With *first‑class* and *higher‑order* functions, Scala embraces FP’s core principle: **functions are data**. Purity, immutability, laziness, and compiler‑verified tail‑recursion combine to deliver referentially‑transparent code that scales from single‑core correctness to multi‑core parallelism.

---

### Further Reading
* Scala 3 Book — Higher‑Order Functionsciteturn0search0  
* “Why Functional Programming Matters” — Hughes (1989)citeturn0search1  
* Scala 3 Book — Immutable Valuesciteturn0search4  
* Saylor FP course — Strict vs Non‑Strict Evaluationciteturn0search3  
* Scala Collection Overviewciteturn0search6  
