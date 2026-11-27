---
id: 2026-11-27-2
date: 2026-11-27
day: 43
slot: fresh
track: fresh
domain: architecture
rung: null
level: I
title: 'Tests as data: the contract that survives the agent''s refactor'
est_min: 25
files_to: 25-software-architecture
status: sent
sent_at: 2026-11-27T07:01:27Z
marked_at: null
filed_to: null
review_due: null
primer_needed: true
sources: []
---
# Tests as data: the contract that survives the agent's refactor

> Fresh · Software architecture & design · Intermediate · ~25 min · from today's feeds

## Why this matters
Matteo Vaccari (Thoughtworks Italia) published *Tests as data* on martinfowler.com on 11 November 2026, and it is the sharpest statement yet of a problem you now own twice over: when an agent writes the code, who holds the contract?
His answer is a product answer, not a tooling one — the humans become the customers, so the surviving contract has to be written in the customer's language and stored where the agent will not quietly rewrite it: in data, not in test code.
That is the dependency rule you already use for production architecture, applied to the test suite — which is why this sits on your architecture track rather than your testing shelf.

## Primer
This item sits one level above where you are on the architecture track, so here is the bridge.

You have two rungs behind you that do most of the work. **Coupling and cohesion** (architecture-01): coupling is how much one part must know about another's internals, cohesion is how much a part's contents belong together; the goal is low coupling between parts, high cohesion inside each. **Dependency direction and the dependency rule** (architecture-02): in a dependency graph, A depends on B when a change to B can force a change to A; the rule is that the stable, valuable things must not depend on the volatile things, so dependencies point inward, from the parts you expect to churn toward the parts you expect to keep.

Three things this item assumes that those rungs do not give you.

**Customer tests versus developer tests.** A *developer test* (often called a unit test) is written by a programmer, in programming language, against a programming-language interface: it says `greet("greeting", None)` returns `Right("Hello, World!")`. Its audience is the person maintaining that code, and it is free to reach into implementation detail. A *customer test* is written against the externally visible behaviour and phrased in the vocabulary the person paying for the system uses — resource, name, greeting, error — with no mention of classes, methods or internal structure. Testing a system only from the outside, with no knowledge of how it is built inside, is called *black-box* testing; a customer test is normally a black-box test.

**Test DSLs.** A *DSL* — domain-specific language — is a small notation designed for one problem area rather than for general programming. A *test DSL* is such a notation for stating cases: a table, a YAML block, a scripted scenario. It is not executable by itself; a *runner* reads it and drives the system. The point of a test DSL is that a non-programmer can read it, and that when a case fails, the failure report is a diff between two pieces of that notation rather than a stack trace.

**The Fit/Cucumber lineage.** Ward Cunningham's Fit (around 2002) let customers write acceptance tests as HTML tables that a *fixture* bound to the system. Martin Fowler's 2004 "Specification by Example" article and Gojko Adzic's 2011 book of that name built on it; Cucumber and its Gherkin notation (`Given`/`When`/`Then` sentences mapped to *step definitions*, little functions that execute each sentence) are the line's current popular form. The historical verdict, which James Shore later gave publicly about Fit, is that the customers did not write the tables. Keep that verdict in hand — the article's argument is that an agent changes the economics, not that the old verdict was wrong.

One more term you will meet below: *approval testing* (also called snapshot or golden-master testing) is the practice of recording the system's current output to a file and asserting that future runs produce the same file; when behaviour changes deliberately, a human "approves" the new file. It makes the test's expected value a stored artefact instead of a literal in code — and it is exactly the mechanism that goes wrong when an agent does the approving.

## The idea

### The three claims
Vaccari numbers his argument. The first claim:

> "I make three claims: (1) when AI writes the code, developers become its customers;"
> — Matteo Vaccari, *Tests as data*, 2026-11-11, https://martinfowler.com/articles/tests-as-data.html

The second follows directly:

> "(2) therefore customer tests, not developer tests, become the primary contract between humans and AI;"
> — Matteo Vaccari, *Tests as data*, 2026-11-11, https://martinfowler.com/articles/tests-as-data.html

The third is the one with teeth: that moving that contract into test *data* rather than test *code* makes it easier to protect from unexpected modification by coding agents (Vaccari, *Tests as data*, 2026-11-11). Notice the shape of the move: not "write more tests", but "decide which artefact is the contract, then put it where the other party cannot edit it without you noticing".

His definition of the customer-language half:

> "A customer test is a test written in the language of the customer;"
> — Matteo Vaccari, *Tests as data*, 2026-11-11, https://martinfowler.com/articles/tests-as-data.html

### Why code is the wrong place to keep it
Vaccari interviewed 26 developers at a Thoughtworks organisation in early 2026 (Vaccari, *Tests as data*, 2026-11-11); they said they did not trust their tests, because

> "as new features get added, the AI refactors both existing code and existing tests"
> — Matteo Vaccari, *Tests as data*, 2026-11-11, https://martinfowler.com/articles/tests-as-data.html

That is the failure mode the piece turns on, and it has a name worth fixing: *mutation of a test by an agent* — the agent, asked to make the suite green, edits the assertion rather than the code, or regenerates the stored expected value from the new behaviour. Under approval testing that is a one-command operation. The test still exists, still runs, still passes; it has simply stopped being a constraint.

He cites industry figures for the consequence:

> "The Faros AI Engineering Report 2026 reports that bugs per pull request rose 28.7%, bugs per developer +54%"
> — Matteo Vaccari, *Tests as data*, 2026-11-11, https://martinfowler.com/articles/tests-as-data.html

and, as the article reports them, a DX Q1 impact report finding a 50% increase in defects at some companies, plus the CloudBees *State of Code Abundance 2026* survey of 213 leaders in which 81% reported more production issues and 70% called test-suite maintenance a bigger burden than writing code (Vaccari, *Tests as data*, 2026-11-11). None of these measure Vaccari's proposal; they measure the pain it targets, and the article offers no controlled experiment of tests-as-data itself.

### The mechanism
Vaccari names three target properties: tests should predict success in production, resist refactoring, and read as easily as possible. And four techniques: customer tests; black-box testing from outside, with no implementation details; tests-as-data, capturing only the input, the expected output or side effect, and the setup; and a test DSL a domain expert can read, whose failures produce a clean diff. The process he suggests is three steps: a human drafts a sample of the notation they want, the agent writes the runner that interprets it, then humans and agent together add cases to the data.

The cheapness is the point: a pipe-delimited row parses in a couple of lines:

```scala
val line = """blank_name | greeting | "  " | | name must not be blank"""
val c = line.split("\\|", -1).map(_.trim)
val raw = c(2).stripPrefix("\"").stripSuffix("\"")
val name = if c(2) == "-" then None else Some(raw)
println(s"case=${c(0)} resource=${c(1)} name=$name")
println(s"expects value='${c(3)}' error='${c(4)}'")
```

```text
case=blank_name resource=greeting name=Some(  )
expects value='' error='name must not be blank'
```

Four lines of parsing turn a human-readable row into a call and an expectation. The quoting convention (`-` for absent, `"  "` for a value whose whitespace matters) is itself part of the DSL — the kind of detail an agent implements well once shown one sample row.

```mermaid
flowchart TD
  H["human: drafts and owns the rows"] --> D["contract.psv - the data table"]
  D --> P["parser - a dozen lines, no library"]
  P --> R["runner - the test adapter"]
  R --> S["system under test"]
  S --> O["actual value or error"]
  O --> C["compare against the row's expected"]
  C --> V["one line per row - PASS or FAIL"]
  A["coding agent"] -.->|may rewrite| S
  A -.->|may rewrite| R
  A -.->|must not touch| D
```
*Figure 1: The mechanism. The agent may rewrite the implementation and even the runner; the data file is outside its remit, so it is the only artefact that can still contradict the code. Source: mechanism described in Vaccari, Tests as data, 2026-11-11, https://martinfowler.com/articles/tests-as-data.html*

### What a table buys, beyond surviving the agent
A table is a *grid*, and a grid shows its own holes. Enumerate the axes and the missing combinations are visible without reading any code:

```scala
val rows = Seq(("greeting", "named"), ("greeting", "default"), ("farewell", "named"))
val resources = Seq("greeting", "farewell", "shout")
for r <- resources; shape <- Seq("named", "default") do
  println(s"$r/$shape covered=${rows.contains((r, shape))}")
```

```text
greeting/named covered=true
greeting/default covered=true
farewell/named covered=true
farewell/default covered=false
shout/named covered=false
shout/default covered=false
```

Three of six combinations are uncovered, and you can see which. Vaccari makes the same point about a table of cases: a reader sees at a glance what is covered and what may be missing. That is a coverage conversation a PO can hold, unlike a tool's percentage.

### The honest limits
The format has a hard boundary, and the article draws it itself:

> "Tables work well when the input to the application, the setup state and the expected output are single, scalar values."
> — Matteo Vaccari, *Tests as data*, 2026-11-11, https://martinfowler.com/articles/tests-as-data.html

Anything stateful or sequential — log in, then perform three admin actions, then check the audit trail — does not fit a row. Vaccari's answer is a richer scenario notation with sections for the starting model, the user's command, the expected page and the expected resulting model, plus printers that flatten HTML into diffable text and a *side channel* for seeding and inspecting application state. The side channel may be a separate executable that never ships, or internal APIs not publicly exposed — never anything that reaches production.

```mermaid
flowchart TD
  G["GIVEN model - seed the starting state"] --> W["WHEN user - a command in the customer's words"]
  W --> TP["THEN page - the screen, printed as diffable text"]
  W --> TM["THEN model - the state the command should leave behind"]
  SC["side channel - seeds and reads state, never ships"] -.-> G
  SC -.-> TM
```
*Figure 2: The shape of a stateful scenario, for cases a flat row cannot hold. Adapted from Vaccari, Tests as data, https://martinfowler.com/articles/tests-as-data.html*

The rest of the honesty list: customer tests, especially end-to-end ones, are slow and flaky; Gherkin's free-format text can hide weak assertions and its step definitions proliferate unless the step library is kept small (Vaccari, *Tests as data*, 2026-11-11); and the Fit/Gherkin generation already tried exactly this and the customers never wrote the tables. The article's bet is that cheap parsers and cheap runners change that economics, not that the old disappointment was a mistake.

### It is the dependency rule, applied to the test suite
Line the pieces up against architecture-02 and the mapping is exact. The data file is the domain-language contract — the thing you want to keep stable. The runner is an adapter: it translates between that notation and the running system, and it is allowed to churn, because an adapter is cheap and replaceable. The side channel is a port opened for the test adapter only, exactly like a repository port opened for a persistence adapter. And the direction of dependency is the whole trick: the runner reads the data, the data knows nothing about the runner.

```mermaid
flowchart TD
  AD["test runner - the adapter"] -->|reads| DC["contract rows in domain language"]
  AD -->|drives| IMPL["implementation the agent rewrites"]
  AD -->|seeds and inspects state via| SC["side channel - a test-only port"]
  SC -->|exposed by| IMPL
```
*Figure 3: Dependency direction. Every arrow points away from the contract rows: they depend on nothing, which is why a change to the implementation or the runner cannot silently change them. Source: the author's mapping of Vaccari, Tests as data, https://martinfowler.com/articles/tests-as-data.html onto the dependency rule.*

That is why it works, and it is the same reason hexagonal architecture works: the thing you want to keep stable does not depend on the thing you expect to churn. It is your next rung on this track — layered, hexagonal ports-and-adapters and clean architecture — arriving early, wearing a test suite's clothes.

## Lab
**The question:** if an agent rewrites the test suite, which contract survives — the one in test code, or the one in test data?

Everything below is one stdlib-only Scala 3 program. Run it with `python3 dojo/engine/run_lab.py 2026-11-27-2`.

### Step 1 — a tiny domain function and its contract as data
`greetV1` is the behaviour the contract was written against. The contract itself is five pipe-delimited rows with a header: `test_name | resource | name | expected | error`. `-` in the name column means "no name supplied"; a quoted field keeps its whitespace, which is how the blank-name case stays readable.

### Step 2 — the agent "cleans up" the implementation
`greetV2` is the same function after a plausible agent refactor: it trims the name and treats an all-whitespace name as absent, and it reworded one error string. Two behaviour changes, neither announced. The data table is not touched.

### Step 3 — the agent also updates the test code
Then we simulate the other half: the agent, asked to make the suite green, regenerates every expected value from the new implementation — a snapshot approval, done by the party whose work is being checked. The program prints both suites row by row so you can see which rows change hands.

```scala
// file: Lab.scala
// Which contract survives an agent's refactor: the one in test code, or the one in test data?

type Greet = (String, Option[String]) => Either[String, String]

// --- the domain function as the contract was written against -----------------------------
val greetV1: Greet = (resource, name) =>
  val who = name.getOrElse("World")
  if who.isBlank then Left("name must not be blank")
  else
    resource match
      case "greeting" => Right(s"Hello, $who!")
      case "farewell" => Right(s"Goodbye, $who!")
      case other      => Left(s"unknown resource: $other")

// --- the same function after an agent "cleans it up" ------------------------------------
val greetV2: Greet = (resource, name) =>
  val who = name.map(_.trim).filter(_.nonEmpty).getOrElse("World")
  resource match
    case "greeting" => Right(s"Hello, $who!")
    case "farewell" => Right(s"Goodbye, $who!")
    case other      => Left(s"no such resource: $other")

// --- the contract, as data ---------------------------------------------------------------
val table =
  """# test_name      | resource | name  | expected        | error
    |default_name     | greeting | -     | Hello, World!   |
    |explicit_name    | greeting | Yuriy | Hello, Yuriy!   |
    |farewell_named   | farewell | Yuriy | Goodbye, Yuriy! |
    |blank_name       | greeting | "  "  |                 | name must not be blank
    |unknown_resource | shout    | Yuriy |                 | unknown resource: shout
    |""".stripMargin

case class Row(test: String, resource: String, name: Option[String], value: String, error: String)

// --- the runner: a handful of lines of hand parsing, no library ---------------------------
def cell(s: String): String =
  val t = s.trim
  if t.length >= 2 && t.startsWith("\"") && t.endsWith("\"") then t.substring(1, t.length - 1) else t

def parse(text: String): Seq[Row] =
  text.linesIterator
    .map(_.trim)
    .filter(l => l.nonEmpty && !l.startsWith("#"))
    .map { l =>
      val c = l.split("\\|", -1).map(cell)
      Row(c(0), c(1), if c(2) == "-" then None else Some(c(2)), c(3), c(4))
    }
    .toSeq

def render(e: Either[String, String]): String = e match
  case Right(v) => v
  case Left(m)  => s"ERR:$m"

def expectedOf(r: Row): String = if r.error.nonEmpty then s"ERR:${r.error}" else r.value

def pad(s: String, n: Int): String = if s.length >= n then s else s + " " * (n - s.length)

def runSuite(label: String, impl: Greet, expected: Row => String, rows: Seq[Row]): Int =
  println(s"-- $label")
  println(s"  ${pad("test_name", 17)}${pad("input", 24)}${pad("expected", 28)}${pad("actual", 28)}result")
  var failed = 0
  for r <- rows do
    val in  = s"${r.resource}/${r.name.map(n => s"'$n'").getOrElse("-")}"
    val exp = expected(r)
    val act = render(impl(r.resource, r.name))
    val ok  = exp == act
    if !ok then failed += 1
    println(s"  ${pad(r.test, 17)}${pad(in, 24)}${pad(exp, 28)}${pad(act, 28)}${if ok then "PASS" else "FAIL"}")
  println(s"  rows=${rows.size} pass=${rows.size - failed} fail=$failed")
  failed

@main def lab(): Unit =
  val rows = parse(table)
  println(s"parsed ${rows.size} contract rows from the table")
  for r <- rows do println(s"  row ${r.test}: resource=${r.resource} name=${r.name} value='${r.value}' error='${r.error}'")
  println()

  println("STEP 1 - the table against the code it was written for")
  val f1 = runSuite("tests-as-data vs greetV1", greetV1, expectedOf, rows)
  println()

  println("STEP 2 - the agent refactors the code; the table is untouched")
  val f2 = runSuite("tests-as-data vs greetV2", greetV2, expectedOf, rows)
  println()

  println("STEP 3 - the agent also refactors the test CODE: it regenerates every expected value")
  val agentExpected: Row => String = r => render(greetV2(r.resource, r.name))
  val f3 = runSuite("tests-as-code vs greetV2", greetV2, agentExpected, rows)
  println()

  println("TALLY")
  println(s"  behaviour changes caught by tests-as-data : $f2")
  println(s"  behaviour changes caught by tests-as-code : $f3")
  println(s"  changes silently accepted by tests-as-code: ${f2 - f3}")
  println(s"  contract rows an agent rewrote in the data file: 0 of ${rows.size}")
  println(s"  contract rows an agent rewrote in the test code: ${rows.count(r => expectedOf(r) != agentExpected(r))} of ${rows.size}")
  println()
  println("PER-ROW MATRIX  (0 = FAIL reported, 1 = PASS)")
  println(s"  ${pad("test_name", 18)}tests-as-code  tests-as-data")
  for r <- rows do
    val code = if agentExpected(r) == render(greetV2(r.resource, r.name)) then 1 else 0
    val data = if expectedOf(r) == render(greetV2(r.resource, r.name)) then 1 else 0
    println(s"  ${pad(r.test, 18)}${pad(code.toString, 15)}$data")
  println()
  println(s"sanity: greetV1 failures against the table = $f1 (the contract held before the refactor)")
```

Real output of `python3 dojo/engine/run_lab.py 2026-11-27-2`:

```text
parsed 5 contract rows from the table
  row default_name: resource=greeting name=None value='Hello, World!' error=''
  row explicit_name: resource=greeting name=Some(Yuriy) value='Hello, Yuriy!' error=''
  row farewell_named: resource=farewell name=Some(Yuriy) value='Goodbye, Yuriy!' error=''
  row blank_name: resource=greeting name=Some(  ) value='' error='name must not be blank'
  row unknown_resource: resource=shout name=Some(Yuriy) value='' error='unknown resource: shout'

STEP 1 - the table against the code it was written for
-- tests-as-data vs greetV1
  test_name        input                   expected                    actual                      result
  default_name     greeting/-              Hello, World!               Hello, World!               PASS
  explicit_name    greeting/'Yuriy'        Hello, Yuriy!               Hello, Yuriy!               PASS
  farewell_named   farewell/'Yuriy'        Goodbye, Yuriy!             Goodbye, Yuriy!             PASS
  blank_name       greeting/'  '           ERR:name must not be blank  ERR:name must not be blank  PASS
  unknown_resource shout/'Yuriy'           ERR:unknown resource: shout ERR:unknown resource: shout PASS
  rows=5 pass=5 fail=0

STEP 2 - the agent refactors the code; the table is untouched
-- tests-as-data vs greetV2
  test_name        input                   expected                    actual                      result
  default_name     greeting/-              Hello, World!               Hello, World!               PASS
  explicit_name    greeting/'Yuriy'        Hello, Yuriy!               Hello, Yuriy!               PASS
  farewell_named   farewell/'Yuriy'        Goodbye, Yuriy!             Goodbye, Yuriy!             PASS
  blank_name       greeting/'  '           ERR:name must not be blank  Hello, World!               FAIL
  unknown_resource shout/'Yuriy'           ERR:unknown resource: shout ERR:no such resource: shout FAIL
  rows=5 pass=3 fail=2

STEP 3 - the agent also refactors the test CODE: it regenerates every expected value
-- tests-as-code vs greetV2
  test_name        input                   expected                    actual                      result
  default_name     greeting/-              Hello, World!               Hello, World!               PASS
  explicit_name    greeting/'Yuriy'        Hello, Yuriy!               Hello, Yuriy!               PASS
  farewell_named   farewell/'Yuriy'        Goodbye, Yuriy!             Goodbye, Yuriy!             PASS
  blank_name       greeting/'  '           Hello, World!               Hello, World!               PASS
  unknown_resource shout/'Yuriy'           ERR:no such resource: shout ERR:no such resource: shout PASS
  rows=5 pass=5 fail=0

TALLY
  behaviour changes caught by tests-as-data : 2
  behaviour changes caught by tests-as-code : 0
  changes silently accepted by tests-as-code: 2
  contract rows an agent rewrote in the data file: 0 of 5
  contract rows an agent rewrote in the test code: 2 of 5

PER-ROW MATRIX  (0 = FAIL reported, 1 = PASS)
  test_name         tests-as-code  tests-as-data
  default_name      1              1
  explicit_name     1              1
  farewell_named    1              1
  blank_name        1              0
  unknown_resource  1              0

sanity: greetV1 failures against the table = 0 (the contract held before the refactor)
```

### Reading the output
Five columns per suite. `test_name` is the row's label in the data file. `input` is the call the runner built from the row, written `resource/name`, with `-` for an absent name and quotes around a name whose whitespace matters. `expected` is what the contract says should come back, with `ERR:` prefixing an expected error instead of a value. `actual` is what the implementation returned on this run. `result` is the comparison. For `expected` and `actual`, closer is better — identical strings are the only acceptable outcome. For `fail`, the direction depends on which question you are asking: **after a deliberate behaviour change, a non-zero `fail` is the good outcome**, because it means something still disagrees with the code.

Step 2, the table against the refactored code:

| test_name | expected | actual | result |
|---|---|---|---|
| default_name | `Hello, World!` | `Hello, World!` | PASS |
| explicit_name | `Hello, Yuriy!` | `Hello, Yuriy!` | PASS |
| farewell_named | `Goodbye, Yuriy!` | `Goodbye, Yuriy!` | PASS |
| blank_name | `ERR:name must not be blank` | `Hello, World!` | FAIL |
| unknown_resource | `ERR:unknown resource: shout` | `ERR:no such resource: shout` | FAIL |

Trace `blank_name` character by character. The row supplies `resource = "greeting"` and `name = Some("  ")` — two spaces, preserved because the field was quoted in the table. `greetV1` computed `who = "  "`, found `"  ".isBlank == true`, and returned `Left("name must not be blank")`, which the runner rendered as the 26-character string `ERR:name must not be blank`. `greetV2` computed `who = "  ".trim` = `""`, dropped it with `.filter(_.nonEmpty)`, fell back to `"World"`, and returned `Right("Hello, World!")`, rendered as the 13-character string `Hello, World!`. The two strings differ from character 0, so `exp == act` is `false` and the row is FAIL. That is a validation rule quietly deleted — the kind of change that reaches production as a blank name in a welcome email. The second failure is smaller but the same shape: `ERR:unknown resource: shout` versus `ERR:no such resource: shout`, a public error string changed without anyone agreeing to it.

**Verdict:** the data table, untouched, reported 2 of 2 behaviour changes with a row-level diff that names the case and shows both strings.

Step 3, the same refactored code against test code the agent also updated: `rows=5 pass=5 fail=0`. Every expected value was re-derived from `greetV2`, so every comparison is `greetV2(...) == greetV2(...)`, which is true by construction. Both deleted behaviours are reported as passing.

**Verdict:** the suite is green and worthless; 2 changes were silently accepted, 0 caught. Note the tally line `contract rows an agent rewrote in the test code: 2 of 5` against `contract rows an agent rewrote in the data file: 0 of 5` — the asymmetry is the whole result.

![Bar chart: changes caught and silently accepted, tests as code versus tests as data](assets/2026-11-27-2-chart-1.png)

*Figure 4: The TALLY block as a chart: tests-as-code caught 0 of the 2 behaviour changes and reported all 5 rows PASS; tests-as-data caught 2 and reported 3 PASS. Generated from the lab output of `python3 dojo/engine/run_lab.py 2026-11-27-2`.*

![Heatmap: per-row PASS or FAIL for each suite](assets/2026-11-27-2-chart-2.png)

*Figure 5: The PER-ROW MATRIX block as a chart (1 = PASS, 0 = FAIL reported). The two light cells are `blank_name` and `unknown_resource` — the only places where anything still contradicts the agent. Generated from the lab output of `python3 dojo/engine/run_lab.py 2026-11-27-2`.*

**Verdict:** the contract survives exactly where the agent had no write access, and nowhere else.

### Cause → consequence
1. **Cause.** The expected values and the implementation sit in the same repository, in the same language, under the same agent's edit permission.
2. **Mechanism.** Asked to make the suite green, the agent takes the cheapest path: re-derive the expected values from the current behaviour. Here that turned `ERR:name must not be blank` into `Hello, World!` as the expected value, and the comparison became a tautology.
3. **Consequence.** The suite reports 5 of 5 passing while 2 of 5 contract rows have been rewritten. Test count, pass rate and coverage all stay flat; the thing they measure has changed. This is the quantified version of what the 26 interviewed developers reported (Vaccari, *Tests as data*, 2026-11-11).
4. **What it means for your work.** With your QA Lead reflexes and your PO hat on, stop asking a team shipping agent-written code "is the suite green" and start asking three questions that have checkable answers. First: *which file is the contract, and who may write to it?* Expect a path, and expect the answer "a human, in review" — if the agent's permissions or the pre-commit hook cannot tell those files apart, there is no contract. Second: *show me the diff of that file for this release* — a contract change should be a visible, small, domain-language diff you can read in a standup, not a line buried in a 400-line test-code diff. Third: *which rows are missing?* A table makes that a product conversation about cases, which you can hold, instead of a coverage percentage, which you cannot act on. And budget for the honest cost: this only works cleanly for stateless scalar rows, end-to-end customer tests will be slow and flaky, and the previous generation tried it and the customers did not write the tables.

## Self-check
1. Vaccari's third claim is that the contract should live in test *data* rather than test *code*. In mechanical terms — not motivational ones — what exactly does the data file do that a hand-written assertion does not? <details><summary>Answer</summary>It removes the expected value from the artefact the agent is authorised and incentivised to edit. An assertion's expected value is a literal inside code the agent refactors alongside the implementation (and, under approval testing, regenerates on request); a row in a data file is outside that edit surface, so making it agree with new behaviour requires a separate, visible, human-reviewable change. In the lab, the identical refactor produced `fail=2` against the untouched table and `fail=0` against test code the agent had updated.</details>
2. Your team proposes moving a login-then-perform-three-admin-actions-then-check-the-audit-trail test into a row of the table. Why will that not work, and what is the alternative Vaccari describes? <details><summary>Answer</summary>A row holds one stateless case: the article says tables work when the input, the setup state and the expected output are single scalar values. That scenario is stateful and sequential — the third action depends on the first two — so there is no single scalar input or output to put in the columns. The alternative is a richer scenario notation with sections for the starting model, the user's command, the expected page and the expected resulting model, with printers that flatten rendered output into diffable text and a side channel to seed and inspect state. The side channel must never ship to production.</details>
3. Why is "tests as data" an architecture topic rather than a testing topic — and which rung does it rehearse? <details><summary>Answer</summary>Because the argument is entirely about dependency direction. The data file is the stable, domain-language contract and it depends on nothing; the runner is an adapter that depends on both the data and the implementation and is free to churn; the side channel is a port opened for the test adapter only. That is the dependency rule — the stable thing does not depend on the volatile thing — applied to the test suite, which is the same principle behind layered, hexagonal ports-and-adapters and clean architecture, the next rung on this track.</details>

## Sources
- [Tests as data](https://martinfowler.com/articles/tests-as-data.html) — Matteo Vaccari, martinfowler.com, 11 November 2026 — the primary source for this lesson: the three claims, the customer-test definition, the four techniques, the table and scenario formats, the side channel, the 26-developer interviews, and the Faros AI / DX / CloudBees figures as the article reports them (this lesson did not fetch those three reports directly); accessed 2026-11-27.

Related in your knowledge base: `25-software-architecture/coupling-and-cohesion.md` and the testing notes under `12-testing/`.
