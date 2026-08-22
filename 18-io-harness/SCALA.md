# Scala Fallback Skeleton

> **Priority:** Recommended
> **Est. time:** 20 min
> **Track:** Both
> **HelloInterview:** none

A minimal `scala-cli` equivalent of this project's Python skeleton, for use if the interviewer
is language-agnostic and Scala is the faster path on the day (13 years of JVM/Scala/Akka is
real leverage that rusty Python isn't). Deliberately short — this is a fallback, not a second
full harness. The Python skeleton in this directory (see [README.md](README.md)) is still the
primary plan; set this up once, ahead of time, and forget about it unless you need it.

---

## 1 · Why `scala-cli`, not `sbt`

`sbt` bootstraps a JVM, resolves the build definition, and pulls plugins before it runs a
single line of your code — a cold `sbt new`/first-`sbt console` commonly costs **5–10 minutes**
on a fresh project. Against a ~60-minute coding budget, that is not a startup cost, it's a
third of the round. `scala-cli` runs a single `.scala` file directly: no project file, no
plugin resolution, JVM startup only once its own cache is warm.

The tradeoff: `scala-cli` still needs network access **the first time** it runs, to populate
its local (Coursier) artifact cache with the compiler and standard library. Do that once, well
before interview day — not during the 15-minute discussion window.

```bash
scala-cli version              # confirms install + warms the cache; run this ahead of time
```
Install via your platform's package manager (Homebrew, Scoop, apt) or the installer at
`https://scala-cli.virtuslab.org` — whichever you already trust; verify `scala-cli version`
works well before the round, since that's the only step here with a network dependency.

## 2 · The skeleton

`solution.scala` — one file, pin the Scala version so `scala-cli` never has to guess:

```scala
//> using scala 3.3.1

import scala.io.Source

object Solution:
  // Worked example: sum whitespace-separated integers per line. Replace the body,
  // keep the signature — an iterator in, an iterator of output lines out (streaming,
  // same shape as the Python harness's solve()).
  def solve(lines: Iterator[String]): Iterator[String] =
    lines.map(line => line.trim.split("\\s+").filterNot(_.isEmpty).map(_.toInt).sum.toString)

  private def inputLines(args: Array[String]): Iterator[String] =
    val idx = args.indexOf("--input")
    if idx >= 0 && idx + 1 < args.length then Source.fromFile(args(idx + 1)).getLines()
    else Source.stdin.getLines()

  @main def run(args: String*): Unit =
    solve(inputLines(args.toArray)).foreach(println)
```

Run it:
```bash
printf '1 2 3\n4 5\n' | scala-cli run solution.scala          # stdin -> stdout
scala-cli run solution.scala -- --input in.txt                # file -> stdout
```

## 3 · Minimal tests, no framework

Adding MUnit/ScalaTest via a `//> using dep` directive works, but it's a dependency
resolution the first time it runs — the same cold-start risk `scala-cli` was chosen to avoid,
unless you've already warmed that specific dependency's cache ahead of time too. For a fallback
skeleton, a hand-rolled check is zero-risk and enough:

```scala
// test.scala — run: scala-cli run test.scala solution.scala
object Tests:
  def check(name: String, actual: Any, expected: Any): Unit =
    if actual == expected then println(s"OK   $name")
    else
      println(s"FAIL $name: expected $expected, got $actual")
      sys.exit(1)

  @main def runTests(): Unit =
    check("sum basic", Solution.solve(Iterator("1 2 3")).toList, List("6"))
    check("blank line", Solution.solve(Iterator("")).toList, List("0"))
    check("multi line", Solution.solve(Iterator("1 2", "3 4")).toList, List("3", "7"))
    println("all tests passed")
```

If MUnit is already warm in your local Coursier cache from prior work, it's a fine substitute —
just don't let adding it be the first network call of the round.

---

## Interview questions

**Why `scala-cli` instead of `sbt` for a 60-minute coding round?**
`sbt`'s cold JVM-plus-dependency-resolution startup commonly costs 5–10 minutes on a fresh
project; `scala-cli` runs a single file directly with a much smaller startup cost once its own
cache is warm — the difference between losing a third of the round and losing a few seconds.

**What's the cold-start risk with `scala-cli` itself, and how do you avoid it?**
The first run needs network access to populate the Coursier cache with the compiler and
standard library. Run `scala-cli version` (or a trivial `scala-cli run`) once, well before
interview day, so nothing downloads during the graded window.

**How do you run tests here without pulling in MUnit or ScalaTest?**
A tiny hand-rolled `check(name, actual, expected)` helper in a second `.scala` file, run the
same way (`scala-cli run test.scala solution.scala`) — zero dependency resolution, zero
network risk.

**If you do want MUnit, what's the risk of adding it mid-round?**
The `//> using dep` directive triggers a fresh Coursier resolution the first time that specific
dependency is used — fine if it's already cached from prior local work, risky as the first
network call of a timed round.

**How would you wire this skeleton to read from a file instead of stdin?**
Check for an `--input` flag in `args` and branch between `Source.fromFile(path).getLines()` and
`Source.stdin.getLines()` — the same resolve-input-by-channel shape as the Python harness's
`resolve_input()`.

**What does pinning `//> using scala 3.3.1` at the top of the file buy you?**
A reproducible build — `scala-cli` uses exactly that compiler version instead of resolving
whatever the latest is, so behavior (and startup time) doesn't vary by what happens to be
cached on the day.
