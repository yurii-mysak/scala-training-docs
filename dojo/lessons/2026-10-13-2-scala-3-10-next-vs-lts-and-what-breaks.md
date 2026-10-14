---
id: 2026-10-13-2
date: 2026-10-13
day: 8
slot: fresh
track: fresh
domain: fp-scala
rung: null
level: I
title: 'Scala 3.10: Next vs LTS and what breaks'
est_min: 30
files_to: 02-functional-programming
status: sent
sent_at: 2026-10-13T06:18:13Z
marked_at: null
filed_to: null
review_due: null
primer_needed: true
sources:
- title: Scala 3.10 released!
  url: https://www.scala-lang.org/news/3.10/
- title: Scala 3.9 LTS released!
  url: https://www.scala-lang.org/news/3.9/
- title: Scala 3.10.0 release thread (Scala Contributors)
  url: https://contributors.scala-lang.org/t/scala-3-10-0-release-thread/7546
- title: scala/scala3 releases
  url: https://github.com/scala/scala3/releases
- title: Long-term compatibility plans for Scala 3
  url: https://www.scala-lang.org/blog/2022/08/17/long-term-compatibility-plans.html
---
# Scala 3.10: Next vs LTS and what breaks

> Fresh · Functional Programming in Scala (red book) · Intermediate · ~30 min · from today's feeds

## Why this matters
Scala 3.10.0 was announced yesterday, 2026-10-12, on the official scala-lang.org news page, and it is the first release of a second, parallel release line. That turns "should we upgrade?" into a different and more durable question: which of the two lines does each of your artifacts belong on, and who gets locked out when you choose wrong. For your Scala/Akka services the answer is not a matter of taste — the compiler's own interchange format makes it for you, in one direction only. Thirty minutes now saves you an aborted upgrade later, because the expensive mistake is publishing a shared library on the wrong line, not bumping an application's compiler.

## Primer
You passed rung fp-scala-01, "What is FP: referential transparency and the substitution model", so you have the language's semantics but not its release machinery. Here is only what this lesson needs.

A **release line** is a series of Scala 3 minor versions maintained together: 3.9.0, 3.9.1, 3.9.2 are one line, 3.10.x another. **LTS** means Long Term Support: a line that receives patches and no new features for a stated period — "Scala 3.9 LTS itself is guaranteed to be maintained for at least three years" (scala-lang.org, *Scala 3.9 LTS released!*, 2026-09-03, https://www.scala-lang.org/news/3.9/).

**Binary compatibility** on the JVM is about compiled classfiles: whether a `.class` file produced earlier still links against a new jar, because method names, parameter types and return types still match. Scala 3 adds a second artifact, **TASTy** — Typed Abstract Syntax Trees, a serialised form of the fully typechecked program that the compiler writes into `.tasty` entries next to the bytecode in every jar. The compiler reads a dependency's TASTy, not its bytecode, when it needs the Scala-level truth: full generic types, `given` instances, `inline` bodies and macro implementations. A **`given`** is Scala 3's term-level implicit value, the thing the compiler searches for to satisfy a context parameter. **TASTy compatibility** is therefore a separate, stricter question than binary compatibility: can *this* compiler parse TASTy written by *that* one.

A **SIP** is a Scala Improvement Proposal: the numbered, reviewed mechanism by which language changes enter the language (SIP-67, SIP-61, SIP-75 all appear in the 3.10 notes). **MiMa** is the Migration Manager, the sbt plugin that compares a new jar's signatures against a previously published one and fails the build on an incompatible change.

On the ladder, this sits beside the rung you passed, fp-scala-01, and previews two pieces of the next one, fp-scala-02, "Getting started: tail recursion, higher-order and polymorphic functions": extension methods (which 3.10 now uses for `->` and the primitive wrappers) and higher-order functions (which `inline` in the standard library changes the compilation of).

## The idea

### Two release lines, not one

Scala 3 now ships on two parallel lines; that is the structural change, not any one feature. The announcement names the new line in its first sentence:

> "We are happy to announce Scala 3.10.0, the first release of the new Scala Next series."
> — the Scala programming language, *Scala 3.10 released!*, 2026-10-12, https://www.scala-lang.org/news/3.10/

Scala Next is the feature line; Scala LTS is the stability line. The 3.9 LTS announcement of 2026-09-03 says what the feature line carries:

> "Scala Next receives regular minor releases with new language features, tooling work, and ecosystem changes."
> — the Scala programming language, *Scala 3.9 LTS released!*, 2026-09-03, https://www.scala-lang.org/news/3.9/

The LTS line gets the opposite deal: patches and tooling fixes only, under the three-year guarantee quoted in the primer. The plan dates from 2022; its roadmap picture, redrawn:

```mermaid
flowchart TD
  R30["3.0"] --> R31["3.1"] --> R32["3.2"] --> R33["3.3, late 2022"] --> R34["3.4"]
  HERE(["we are here: Aug 2022"]) -.- R31
  R34 --> RD1["…"] --> R3X["3.X"] --> RD2["… Scala Next continues"]
  R33 --> L33["3.3 LTS: fixes only<br/>at least 2 years, then at least 1 year<br/>after the next LTS appears"]
  R3X --> L3X["3.X LTS"]
```
*Figure 1: The 2022 roadmap: minor releases ride one Next track; LTS lines branch off at 3.3 and at a later "3.X" (now 3.9) and then get only fixes. Adapted from Paweł Marks (VirtusLab), "Long-term compatibility plans for Scala 3", scala-lang.org, 2022-08-17, https://www.scala-lang.org/blog/2022/08/17/long-term-compatibility-plans.html (redrawn; no open licence covers the artwork).*

Updated to October 2026:

```mermaid
flowchart TD
  N33["3.3.0"] --> N38["3.4 … 3.8"] --> N39["3.9.0, 2026-09-03"]
  N39 --> N310["3.10.0, 2026-10-12<br/>first 'Scala Next' release"] --> N311["3.11, ~ Mar/Apr 2027"]
  N33 --> L33["3.3 LTS line<br/>(3.3.8, Jun 2026)"]
  N39 --> L39["3.9 LTS line<br/>fixes only, at least 3 years"]
```
*Figure 2: Two lines today: 3.10 opens Scala Next, 3.9 is the current LTS. Drawn from the 3.9 and 3.10 announcements and scala/scala3 releases.*

For library code the announcement is unambiguous: "Scala 3.9 LTS remains the recommended version to build against" (scala-lang.org, *Scala 3.10 released!*, 2026-10-12). The `lts` tag now resolves to 3.9, and 3.11 is due around March or April 2027 (same source; 3.3.8 from the scala/scala3 releases page). The release thread opened six weeks earlier:

> "The first release candidate for Scala 3.10.0 is now available for public tests!"
> — Scala Contributors forum, *Scala 3.10.0 release thread*, 2026-09-03, https://contributors.scala-lang.org/t/scala-3-10-0-release-thread/7546

RC1 on 2026-09-03, stable on 2026-10-12: for the next minor, that window is your slot for a trial build.

### TASTy decides for you

A compiler reads TASTy produced by its own minor version or an earlier one, never by a later one, whose trees may have shapes it has no case for. The 2022 plan in one line:

> "That means that Scala `3.b.y` can consume the output of Scala `3.a.x` only if `b` is greater or equal to `a`."
> — Paweł Marks (VirtusLab), *Long-term compatibility plans for Scala 3*, scala-lang.org, 2022-08-17, https://www.scala-lang.org/blog/2022/08/17/long-term-compatibility-plans.html

```mermaid
flowchart LR
  L39["library built with 3.9 LTS"] --> A39["app on 3.9 LTS: reads it"]
  L39 --> A310["app on 3.10 Next: reads it"]
  L310["library built with 3.10 Next"] --> B310["app on 3.10 Next: reads it"]
  L310 -.-> B39["app on 3.9 LTS: cannot read it"]
```
*Figure 3: TASTy reads forward only: newer compilers read older libraries, never the reverse. Drawn for this lesson from the 2022 plan's rule.*

Precedent: "artifacts built with Scala 3.9 cannot be consumed by Scala 3.3 projects" (scala-lang.org, *Scala 3.9 LTS released!*, 2026-09-03).

**Seen on a real compiler.** `Money.scala` compiled with scalac 3.10.0, then `Report.scala` compiled against it with scalac 3.9.0 (official release tarballs):

```scala
// Money.scala: the library, compiled with scalac 3.10.0
package domain
final case class Money(cents: Long):
  def +(o: Money): Money = Money(cents + o.cents)

// Report.scala: the consumer, compiled with scalac 3.9.0
import domain.Money
object Report:
  val total = Money(150) + Money(250)
```

```text
error while loading Money,
TASTy file lib-3.10.0/domain/Money.tasty could not be read, failing with:
  Forward incompatible TASTy file has version 28.10, produced by Scala 3.10.0,
  expected stable TASTy from 28.0 to 28.9.
  To read this TASTy file, use a newer version of this tool compatible with TASTy 28.10.
-- [E050] Type Error: Report.scala:3:14 ----------------------------------------
3 |  val total = Money(150) + Money(250)
  |              ^^^^^
  |              object Money in package domain does not take parameters
2 errors found
```

The code is fine; the *file format* is refused. TASTy has its own version, 28.N, with N following the compiler's minor, and 3.9.0 accepts 28.0–28.9 only. The second error is fallout: the unreadable class was dropped, so `Money(150)` no longer type-checks. Swap the compilers (library 3.9.0, consumer 3.10.0) and both files compile silently. All nine combinations:

![Heatmap of 3 library compilers by 3 consumer compilers; the lower-left triangle fails](assets/2026-10-13-2-chart-1.png)

*Figure 4: 1 = `scalac` exit 0, 0 = TASTy version error; `Money.scala` built with the row's compiler, `Report.scala` with the column's (scalac 3.3.4, 3.9.0, 3.10.0, run 2026-10-15). Below the diagonal everything fails, however small the gap (3.3.4 says "TASTy signature has wrong version"). Generated from these compiler runs.*

So the policy writes itself. A **library** has consumers you do not control, so its compiler version is a floor imposed on all of them: publish on Next and every LTS consumer is locked out until it moves too. An **application** has no consumers; its compiler version constrains nobody. Libraries publish on LTS, applications ride Next. The lab counts the blast radius of breaking that rule.

One more boundary moved with 3.10:

> "Cross-compilation between Scala 2 and 3.10 is no longer supported because of the removed legacy features."
> — the Scala programming language, *Scala 3.10 released!*, 2026-10-12, https://www.scala-lang.org/news/3.10/

If a module still cross-builds 2.13 and 3.x from one source tree, 3.10 is closed to it; it stays on LTS, where "Scala 3.3 LTS and Scala 3.9 LTS put compatibility with Scala 2.13 first" (scala-lang.org, *Scala 3.10 released!*, 2026-10-12).

### What actually breaks, and the order to fix it

The migration headline is reassuring and precisely scoped:

> "Most projects can upgrade without code changes."
> — the Scala programming language, *Scala 3.10 released!*, 2026-10-12, https://www.scala-lang.org/news/3.10/

The exceptions cluster in code that reads types at compile time and syntax kept only for Scala 2. In the wrong order, each hides the next:

```mermaid
flowchart TD
  S1["Step 1: bump the libraries that read types, before the compiler"] --> S2["Step 2: compile on 3.10 with the migration rewrite"]
  S2 --> S3["Step 3: fix inaccessible companion givens and arrow DSLs"]
  S3 --> S4["Step 4: re-baseline signatures with MiMa 1.2.1 or later"]
  S4 --> S5["Step 5: libraries publish on 3.9 LTS, applications run on 3.10 Next"]
```
*Figure 5: The migration order; each step clears noise that would hide the next. Drawn for this lesson from the 3.10 announcement.*

**Step 1 — dependencies first.** 3.10 does stronger constant folding during inlining, which breaks libraries whose macros inspect inlined trees. The announcement is direct: "If you use the ZIO ecosystem, upgrade these libraries before upgrading the compiler" (scala-lang.org, *Scala 3.10 released!*, 2026-10-12): ZIO 2.1.26, zio-blocks 0.0.54, izumi-reflect 3.0.10 and neotype 0.7.2 — all four read types at compile time, the surface that moved.

**Step 2 — the mechanical rewrite.** `A with B` as a *type*, Scala 2 syntax kept for compatibility, is now an error (scala-lang.org, *Scala 3.10 released!*, 2026-10-12). It has warned since 3.4, and the fix is a flag: compile once with `-source:3.4-migration -rewrite` and every occurrence becomes the intersection type `A & B`. In a long-lived Akka codebase this is the largest, dullest diff: run it first so real errors are not buried. `With.scala`:

```scala
trait Reader { def read: String = "r" }
trait Writer { def write: String = "w" }
object Io extends Reader, Writer
val io: Reader with Writer = Io
```

```text
-- [E003] Syntax Error: With.scala:4:15 ----------------------------------------
4 |val io: Reader with Writer = Io
  |               ^^^^
  |with as a type operator has been deprecated; use & instead
  |This construct can be rewritten automatically under -rewrite -source 3.4-migration.
1 error found
```

That is scalac 3.10.0. 3.3.4 compiles the file silently (even with `-deprecation`); 3.9.0 prints the same message as a `Syntax Warning` and succeeds: 3.10 changed the severity, not the diagnosis. With `-source:3.4-migration -rewrite`, 3.10.0 prints `[patched file With.scala]`, line 4 becomes `val io: Reader & Writer = Io`, and the next plain compile is silent.

**Step 3 — the small semantic ones.** Implicits in an inaccessible companion object are no longer found — 3.9 only warned under `-deprecation`. In `Comp.scala`, `Box`'s companion is `private` to `shapes`, so `Use` cannot name it, yet older compilers still used its `given`:

```scala
object shapes:
  class Box(val n: Int)
  private object Box:
    given Ordering[Box] = Ordering.by(_.n)
object Use:
  val sorted = List(new shapes.Box(2), new shapes.Box(1)).sorted
```

```text
-- Deprecation Warning: Comp.scala:6:64 ----------------------------------------
  |Usage of implicit given instance given_Ordering_Box defined in object Box,
  |which is not accessible here. In Scala 3.10, this implicit will no longer be found.
```

```text
-- [E172] Type Error: Comp.scala:6:64 ------------------------------------------
  |No given instance of type Ordering[B] was found for parameter ord of method
  |sorted in trait StrictOptimizedSeqOps.
1 error found
```

First block: scalac 3.9.0 with `-deprecation` (still compiles); second: scalac 3.10.0 (both trimmed, long lines wrapped). 3.3.4 says nothing, so a 3.3 codebase gets no warning unless it passes through 3.9. Deleting `private` makes all three compile. Also: `->` became an inline extension method and `Predef.ArrowAssoc` is deprecated, so your own `->` DSL built on an implicit class should become an extension method (issue #26851). The primitive `Rich*` wrappers are extension methods now, and `this` is illegal in top-level definitions (PR #26448, scala-lang.org, *Scala 3.10 released!*, 2026-10-12).

**Step 4 — the compatibility gate.** 3.10 uses boxed types for primitive type arguments in Java generic signatures (PR #25944). Signatures change, semantics do not, so MiMa reports `IncompatibleSignatureProblem` (issue #27063); use MiMa 1.2.1 or later, which "adds Scala 3.9 and 3.10 support and fixes several false positives" (scala-lang.org, *Scala 3.10 released!*, 2026-10-12).

The upside is modest consolidation: SIP-67 is stable (matching under `strictEquality` needs no `CanEqual`; `==` stays strict); SIP-61 `@unroll`, SIP-75 relaxed lambdas and SIP-68 referenceable package objects sit behind `-preview`; Java records are matchable (PR #26497, same source). And the standard library:

> "The standard library also starts using more Scala 3 features, such as `inline` and extension methods."
> — the Scala programming language, *Scala 3.10 released!*, 2026-10-12, https://www.scala-lang.org/news/3.10/

None of that justifies moving a published library off LTS; all of it justifies moving applications.

## Lab

**The question:** for each (producer compiler, consumer compiler) pair, can the consumer read the producer's TASTy — and how many consumers does a library lock out by publishing on Scala Next instead of LTS?

### Step 1 — model the lines and the TASTy rule

Three lines are in play: 3.3 LTS, 3.9 LTS and 3.10 Next. The rule is one comparison: a consumer reads a producer's TASTy when the producer's minor version is less than or equal to the consumer's. The program prints every pair with the arithmetic shown, then the reach of each publishing choice, then two realistic dependency sets.

```scala
// file: Lab.scala

final case class Line(label: String, minor: Int, kind: String)
final case class Dep(name: String, builtWith: Line)

val lts33 = Line("3.3 LTS", 3, "LTS")
val lts39 = Line("3.9 LTS", 9, "LTS")
val next310 = Line("3.10 Next", 10, "Next")
val lines = List(lts33, lts39, next310)

def canRead(consumer: Line, producer: Line): Boolean =
  producer.minor <= consumer.minor

def pad(s: String, n: Int): String =
  if s.length >= n then s else s + " " * (n - s.length)

def checkApp(app: String, on: Line, deps: List[Dep]): Unit =
  println(s"-- $app, compiled with ${on.label} --")
  val blocked = deps.count(d => !canRead(on, d.builtWith))
  deps.foreach { d =>
    val gap = on.minor - d.builtWith.minor
    val ok = canRead(on, d.builtWith)
    println(
      "   " + pad(d.name, 28) + "built with " + pad(d.builtWith.label, 11) +
      pad("gap " + gap.toString, 8) + (if ok then "readable" else "BLOCKED")
    )
  }
  println(s"   blocked $blocked/${deps.size} -> " + (if blocked == 0 then "builds" else "does not build"))

@main def lab(): Unit =
  println("Table 1: can the consumer read the producer's TASTy?")
  println(pad("producer", 11) + pad("consumer", 11) + pad("p.minor", 9) +
          pad("c.minor", 9) + pad("c - p", 7) + "reads?")
  for p <- lines; c <- lines do
    val gap = c.minor - p.minor
    println(pad(p.label, 11) + pad(c.label, 11) + pad(p.minor.toString, 9) +
            pad(c.minor.toString, 9) + pad(gap.toString, 7) +
            (if canRead(c, p) then "yes" else "NO"))

  println("")
  println("Table 2: how many of the 3 consumer lines can use a library published on each line?")
  for p <- lines do
    val reachable = lines.filter(c => canRead(c, p))
    println(pad(p.label, 11) + pad("(" + p.kind + ")", 8) +
            s"reach ${reachable.size}/${lines.size}   " + reachable.map(_.label).mkString(", "))

  println("")
  println("Table 3: two realistic dependency sets")
  checkApp(
    "payments-api",
    next310,
    List(
      Dep("zio 2.1.26", lts39),
      Dep("izumi-reflect 3.0.10", lts39),
      Dep("neotype 0.7.2", lts39)
    )
  )
  checkApp(
    "reporting-api",
    lts39,
    List(
      Dep("zio 2.1.26", lts39),
      Dep("internal-domain 1.4.0", next310)
    )
  )
```

### Step 2 — run it

```text
Table 1: can the consumer read the producer's TASTy?
producer   consumer   p.minor  c.minor  c - p  reads?
3.3 LTS    3.3 LTS    3        3        0      yes
3.3 LTS    3.9 LTS    3        9        6      yes
3.3 LTS    3.10 Next  3        10       7      yes
3.9 LTS    3.3 LTS    9        3        -6     NO
3.9 LTS    3.9 LTS    9        9        0      yes
3.9 LTS    3.10 Next  9        10       1      yes
3.10 Next  3.3 LTS    10       3        -7     NO
3.10 Next  3.9 LTS    10       9        -1     NO
3.10 Next  3.10 Next  10       10       0      yes

Table 2: how many of the 3 consumer lines can use a library published on each line?
3.3 LTS    (LTS)   reach 3/3   3.3 LTS, 3.9 LTS, 3.10 Next
3.9 LTS    (LTS)   reach 2/3   3.9 LTS, 3.10 Next
3.10 Next  (Next)  reach 1/3   3.10 Next

Table 3: two realistic dependency sets
-- payments-api, compiled with 3.10 Next --
   zio 2.1.26                  built with 3.9 LTS    gap 1   readable
   izumi-reflect 3.0.10        built with 3.9 LTS    gap 1   readable
   neotype 0.7.2               built with 3.9 LTS    gap 1   readable
   blocked 0/3 -> builds
-- reporting-api, compiled with 3.9 LTS --
   zio 2.1.26                  built with 3.9 LTS    gap 0   readable
   internal-domain 1.4.0       built with 3.10 Next  gap -1  BLOCKED
   blocked 1/2 -> does not build
```

### Reading the output

**Table 1.** `p.minor` is the producer compiler's minor version, `c.minor` the consumer's, and `c - p` their difference. Higher (or zero) is better: a non-negative gap means the consumer is at or ahead of the producer and can parse its trees. A negative gap is the only failing case.

| producer | consumer | p.minor | c.minor | c - p | reads? |
|---|---|---|---|---|---|
| 3.3 LTS | 3.3 LTS | 3 | 3 | 0 | yes |
| 3.3 LTS | 3.9 LTS | 3 | 9 | 6 | yes |
| 3.3 LTS | 3.10 Next | 3 | 10 | 7 | yes |
| 3.9 LTS | 3.3 LTS | 9 | 3 | -6 | NO |
| 3.9 LTS | 3.9 LTS | 9 | 9 | 0 | yes |
| 3.9 LTS | 3.10 Next | 9 | 10 | 1 | yes |
| 3.10 Next | 3.3 LTS | 10 | 3 | -7 | NO |
| 3.10 Next | 3.9 LTS | 10 | 9 | -1 | NO |
| 3.10 Next | 3.10 Next | 10 | 10 | 0 | yes |

Trace the row that matters most. Producer 3.10 Next, consumer 3.9 LTS: `c - p = 9 - 10 = -1`, which is less than 0, so `canRead` is false and the row prints `NO`. One single minor version of difference, in the wrong direction, is as fatal as the seven-version gap on the 3.10-to-3.3 row. There is no "close enough".

The model is not just a story: its yes/NO column agrees, cell for cell, with the nine real compiler runs in Figure 4 (the three NO rows are exactly the three cells that failed with a TASTy version error).

**Verdict:** TASTy readability is a one-way relation, and the margin does not matter — only the sign does.

**Table 2.** The bracketed word is the line's kind, and `reach` counts how many of the three consumer lines can use a library published on that line; higher is better for a library author.

| published on | kind | reach | consumers that can use it |
|---|---|---|---|
| 3.3 LTS | (LTS) | 3/3 | 3.3 LTS, 3.9 LTS, 3.10 Next |
| 3.9 LTS | (LTS) | 2/3 | 3.9 LTS, 3.10 Next |
| 3.10 Next | (Next) | 1/3 | 3.10 Next |

Publishing on 3.10 Next drops reach from 2/3 to 1/3 — it cuts the audience to only those consumers who have themselves moved to Next. That is the arithmetic behind "Scala 3.9 LTS remains the recommended version to build against" (scala-lang.org, *Scala 3.10 released!*, 2026-10-12, https://www.scala-lang.org/news/3.10/).

**Verdict:** a library's compiler choice is an audience choice; Next halves it.

**Table 3.** `gap` is `app.minor - dependency.minor`, same sign rule. `payments-api` on 3.10 Next has gaps 1, 1, 1 against its three 3.9 LTS dependencies, so `blocked 0/3` and it builds — an application on Next consuming LTS libraries is the intended shape. `reporting-api` on 3.9 LTS has gap 0 against zio 2.1.26 (`9 - 9 = 0`, readable) and gap -1 against `internal-domain 1.4.0` built on 3.10 Next (`9 - 10 = -1`, BLOCKED), so `blocked 1/2` and it does not build. One team publishing one internal library on Next broke a consumer that was doing nothing wrong.

**Verdict:** the failure is not in the application that stayed on LTS; it is in the library that left it.

### Cause → consequence

1. **Cause.** Scala 3 ships a typed interchange format, TASTy, in every jar, and the compiler must parse a dependency's TASTy to typecheck against it.
2. **Mechanism.** A compiler only has cases for tree shapes that existed at or before its own minor version, so TASTy reads forward (older producer → newer consumer) and never backward; the gap `consumer.minor - producer.minor` must be ≥ 0.
3. **Consequence.** The compiler version of a *published* artifact is a hard floor on every consumer of it, while the compiler version of an *application* constrains nobody — which is why "Scala 3.9 LTS remains the recommended version to build against" (scala-lang.org, *Scala 3.10 released!*, 2026-10-12) and why 3.9 LTS carries a three-year maintenance guarantee (scala-lang.org, *Scala 3.9 LTS released!*, 2026-09-03).
4. **What it means in practice.** Split your estate in two. Every shared or published library — internal domain models included — pins 3.9 LTS in `build.sbt` and keeps MiMa 1.2.1 or later in CI. Every leaf application is free to move to 3.10, in the order the diagram gives: bump ZIO 2.1.26, zio-blocks 0.0.54, izumi-reflect 3.0.10 and neotype 0.7.2 first, then compile with `-source:3.4-migration -rewrite`, then fix companion-private `given`s and `->` DSLs. And any module that still cross-builds Scala 2.13 is out of scope for 3.10 entirely and stays on LTS.

## Self-check
1. Your team's internal `domain-model` library is consumed by six services, four of which you do not own. Which line do you publish it on, and what is the one-sentence reason? <details><summary>Answer</summary>3.9 LTS. A published artifact's compiler version is a floor on every consumer, because TASTy only reads forward — a 3.10 Next build would be unreadable by any of the four services you do not control until they also moved to Next, and "Scala 3.9 LTS remains the recommended version to build against" (scala-lang.org, *Scala 3.10 released!*, 2026-10-12).</details>
2. You bump one service straight to 3.10 and get a wall of errors about inlining inside a ZIO macro. What did you do in the wrong order, and what does the announcement say to do instead? <details><summary>Answer</summary>You upgraded the compiler before the libraries that read types at compile time. 3.10 does stronger constant folding during inlining, and the announcement says "If you use the ZIO ecosystem, upgrade these libraries before upgrading the compiler" (scala-lang.org, *Scala 3.10 released!*, 2026-10-12) — the named versions are ZIO 2.1.26, zio-blocks 0.0.54, izumi-reflect 3.0.10 and neotype 0.7.2.</details>
3. A 3.10 build fails on a type written `Reader with Writer`, and separately MiMa fails your library release with `IncompatibleSignatureProblem` even though you changed no public API. What fixes each? <details><summary>Answer</summary>The first: `A with B` as a type is an error in 3.10 (it has warned since 3.4), so compile once with `-source:3.4-migration -rewrite` and the compiler rewrites it to `Reader & Writer` in place. The second: 3.10 emits more precise Java generic signatures, using boxed types for primitive type arguments (PR #25944), which MiMa reports as a signature problem (issue #27063); upgrade to MiMa 1.2.1 or later, which per the announcement "adds Scala 3.9 and 3.10 support and fixes several false positives" (scala-lang.org, *Scala 3.10 released!*, 2026-10-12).</details>

## Sources
- [Scala 3.10 released!](https://www.scala-lang.org/news/3.10/) — the Scala programming language, 2026-10-12 — primary source: the Scala Next series, the `lts` tag resolving to 3.9, Scala CLI 1.17.1, the breaking-change list (inaccessible companion implicits, stronger constant folding and the ZIO/zio-blocks/izumi-reflect/neotype versions, `Rich*` wrappers as extension methods, `->` as an inline extension method, `A with B` as an error, `this` in top-level definitions, boxed Java generic signatures, `-Xmax-fuel` 550), MiMa 1.2.1, SIP-67 stable, the `-preview` SIPs, and the 3.10.1 / 3.10.2 / 3.11 roadmap; accessed 2026-10-13
- [Scala 3.9 LTS released!](https://www.scala-lang.org/news/3.9/) — the Scala programming language, 2026-09-03 — the LTS / Next split, what each line receives, the at-least-three-years maintenance guarantee, and the documented precedent that 3.9 artifacts cannot be consumed by 3.3 projects; accessed 2026-10-13
- [Scala 3.10.0 release thread](https://contributors.scala-lang.org/t/scala-3-10-0-release-thread/7546) — Scala Contributors forum, 2026-09-03 to 2026-10-12 — the release-candidate cadence: RC1 opened for public testing in early September, with the stable tag about six weeks later; accessed 2026-10-13
- [scala/scala3 releases](https://github.com/scala/scala3/releases) — the Scala 3 repository on GitHub — cross-check of the tags and labels: the 3.10.0-RC1 pre-release, and the `LTS` label on 3.9.0 and 3.3.8; also the source of the scalac 3.3.4, 3.9.0 and 3.10.0 tarballs that produced every compiler message and Figure 4 in this lesson; accessed 2026-10-15
- [Long-term compatibility plans for Scala 3](https://www.scala-lang.org/blog/2022/08/17/long-term-compatibility-plans.html) — Paweł Marks (VirtusLab), scala-lang.org, 2022-08-17 — the original LTS / Next plan, the "3.b.y can consume 3.a.x only if b ≥ a" rule, and the roadmap figure, redrawn as Figure 1 (adapted: the scala/scala-lang repo's license.md licenses the Scala code under Apache-2.0 and says nothing about the site's artwork); accessed 2026-10-15

## Next on this track
Fresh lessons sit outside the ladder; next on Functional Programming in Scala (red book): **Getting started: tail recursion, higher-order and polymorphic functions** (rung 2 of 26, Beginner).
