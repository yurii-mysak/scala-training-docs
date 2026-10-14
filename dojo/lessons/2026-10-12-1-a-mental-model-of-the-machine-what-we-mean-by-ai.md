---
id: 2026-10-12-1
date: 2026-10-12
day: 7
slot: core
track: claude-academy
domain: claude-academy
rung: claude-academy-01
level: B
title: 'A mental model of the machine: what we mean by AI'
est_min: 25
files_to: 24-ai-ml-foundations
status: sent
sent_at: 2026-10-12T05:55:34Z
marked_at: null
filed_to: null
review_due: null
sources:
- title: 'Claude Academy — AI Capabilities and Limitations: Intro to AI Capabilities and Limitations'
  url: https://academy.claude.com/courses/ai-capabilities-and-limitations/intro-to-ai-capabilities-and-limitations
- title: 'Claude Academy — AI Capabilities and Limitations: What We Mean by AI'
  url: https://academy.claude.com/courses/ai-capabilities-and-limitations/what-we-mean-by-ai
---
# A mental model of the machine: what we mean by AI

> Claude Academy · Beginner · ~25 min · rung 1 of 20 · needs: —

## Why this matters

You already drive Claude Code hard and ship MCP servers for other teams, so you have a working
intuition for where the machine helps and where it wanders off. What you do not have yet is a
shared vocabulary for *why* it wanders, and that is what every judgement call in the rest of this
ladder rests on. This rung gives you the four-word map — prediction, knowledge, memory,
steerability — that lets you say which axis a failure came from instead of saying "the model was
dumb today".

## The idea

### Two different questions

There are two separate questions about working with AI, and mixing them is the most common reason
people plateau. The first is **how you collaborate**: how you delegate, how you describe what you
want, how you judge the result, how you stay responsible for it. Claude Academy calls that the 4D
framework (Delegation, Description, Discernment, Diligence) and it arrives later on this ladder.
The second is **how the machine is able to work with you at all** — what it is doing when it
answers, what it knows, what it can hold in mind, how much your instructions actually bend it.
This rung and the twelve after it are about the second question (Claude Academy, *AI Capabilities
and Limitations*, lesson 1, "Intro to AI Capabilities and Limitations"). The order is deliberate:
collaboration habits built on a wrong model of the machine become superstition — prompt rituals
you repeat without knowing which part did the work.

The course roadmap behind this ladder is five steps: **what AI is** (this rung), **how it is
trained** (pretraining, fine-tuning, the fingerprints both leave), **its four properties**, **what
that means in real use**, and **safety** — what to do about the failure modes the four properties
guarantee.

### Narrowing "AI" to one thing

"AI" is a marketing word covering an enormous range of systems. This course means one slice of it:
**generative, transformer-based text models** — systems that produce new text (or code, which is
text) piece by piece (Claude Academy, lesson 2, "What We Mean by AI"). That slice is not where most
AI in production lives.

Count in your own platform. The card-fraud score on a POS payment takes a transaction and emits a
number. The licence-plate recognition at the wash gate takes an image and emits one string from a
constrained space. The support-inbox spam filter emits one bit. The demand forecast behind package
pricing emits a quantity. None of these write anything. They are **predictive** or
**classification** models: they map an input onto a label, a score, or a ranking over a fixed set
of options. Figure 1 shows that shape: a fixed row of outputs, one per allowed answer.

![A classifier: every input ends in exactly three output units, one per fixed class](assets/2026-10-12-1-fig-1.png)

*Figure 1: A classifier ends in a fixed row of output units (C0–C2), one per allowed class. Source: Daniel Voigt Godoy, [Deep Learning Visuals — Classification](https://dvgodoy.github.io/dl-visuals/Classification), book ch. 5 (CC BY 4.0).*

Generative models are different in kind, not degree. There is no fixed answer set: the output
space is every sequence of tokens the model could emit. So a generative model cannot be "right" or
"wrong" the way a classifier is; it can only be more or less **plausible**, and plausible is not
the same as true. Here is the same customer email sent to both kinds:

```text
Illustrative — written for this lesson, not quoted from the course.

Input:  "Hi, I was charged twice for the Premium wash on 3 Oct, can you refund one?"

spam filter   (classifier) → not_spam                   one of 2 fixed labels
intent router (classifier) → billing                    one of 6 fixed labels
Claude        (generative) → "Hi Olena, sorry about the double charge on 3 October.
                              I've asked billing to refund one of the two Premium
                              payments; you'll see it within 5 working days."
```

The classifiers can only pick from their lists, so you can score them right or wrong. The
generated reply is fluent and helpful — and it invented two things nobody supplied: the
customer's name and a 5-day refund policy. Every capability and every limitation in this course
follows from that one structural fact.

### How a generative model writes: one token at a time

A **token** is the unit a text model reads and writes — a word, part of a word, or a punctuation
mark. A generative model does one thing, over and over: given every token so far (the
**context**), it scores every token in its vocabulary and turns the scores into probabilities for
"what comes next". One token is picked, appended to the context, and the loop runs again until a
stop token. The **transformer** is the neural-network architecture that computes those
probabilities; for this course its contract matters more than its internals — context in,
next-token distribution out.

```mermaid
flowchart TD
  P["context so far<br/>'the basic wash includes'"] --> M["model scores every token<br/>in its vocabulary"]
  M --> D["next-token distribution<br/>wax 0.40 · foam 0.20 · rinse 0.20 · tyre 0.20"]
  D --> S["pick one token<br/>greedy: the most likely → wax"]
  S --> A["append it to the context<br/>'… includes wax'"]
  A -->|"repeat until a stop token"| M
  A -->|"stop token reached"| O["output text"]
```

*Figure 2: The generation loop — predict one token, append it, predict again. Numbers from the toy model below.*

![A decoder feeds its own prediction back in as the next input](assets/2026-10-12-1-fig-2.png)

*Figure 3: The decoder's prediction x2 is fed back as its next input ("Using Prediction"). Drawn with an RNN cell; a transformer keeps the same loop. Source: Daniel Voigt Godoy, [Deep Learning Visuals — Decoder](https://dvgodoy.github.io/dl-visuals/Decoder), book ch. 9 (CC BY 4.0).*

A nine-line Scala toy "model" learns from a five-sentence corpus by counting which word followed
`includes`:

```scala
// file: NextToken.scala
@main def nextToken(): Unit =
  val toks = """the basic wash includes foam . the premium wash includes wax .
    the premium wash includes wax . the premium wash includes tyre shine .
    the basic wash includes rinse .""".split("\\s+").toVector
  val next = toks.sliding(2).collect { case Vector(a, b) if a == "includes" => b }.toVector
  val probs = next.groupBy(identity).map((w, ws) => w -> ws.size.toDouble / next.size)
  for (w, p) <- probs.toVector.sortBy((w, p) => (-p, w)) do
    println(f"P($w%-5s | includes) = $p%.2f   (${(p * next.size).round} of ${next.size})")
```

```text
P(wax   | includes) = 0.40   (2 of 5)
P(foam  | includes) = 0.20   (1 of 5)
P(rinse | includes) = 0.20   (1 of 5)
P(tyre  | includes) = 0.20   (1 of 5)
```

Five words followed `includes`; `wax` did twice, so it gets 2 ÷ 5 = 0.40. A real model computes
its distribution with billions of learned weights instead of a count, but the output has the
same shape: a ranked bet over next tokens.

![Next-token probabilities after "includes" from the toy Scala model](assets/2026-10-12-1-chart-1.png)

*Figure 4: The toy model's bet after "includes" — the most frequent continuation wins. Generated from the example output.*

Now let it write. The loop below starts from `the basic` and feeds each prediction back in:

```scala
// file: Generate.scala
@main def generate(): Unit =
  val toks = """the basic wash includes foam . the premium wash includes wax .
    the premium wash includes wax . the premium wash includes tyre shine .
    the basic wash includes rinse .""".split("\\s+").toVector
  def predict(prev: String): String =        // sees ONLY the last token
    toks.sliding(2).collect { case Vector(a, b) if a == prev => b }.toVector
      .groupBy(identity).maxBy((w, ws) => (ws.size, w))._1
  var out = Vector("the", "basic")
  while out.last != "." do
    out = out :+ predict(out.last)           // the prediction becomes the next input
    println(out.mkString(" "))
```

```text
the basic wash
the basic wash includes
the basic wash includes wax
the basic wash includes wax .
```

The output is perfectly fluent and **false**: the corpus says the basic wash includes foam or
rinse; wax belongs to premium. The model was never asked about truth — `wax` was simply the most
popular word after `includes`, and its one-token window had already lost `basic`.

### The four axes

The course's central claim is that these models are not uniformly good or uniformly bad. They are
predictably strong and predictably weak along four axes:

> "AI isn't uniformly capable or uniformly unreliable. It's strong and weak along four predictable axes."
> — Anthropic, *Claude Academy — AI Capabilities and Limitations: What We Mean by AI*, lesson 2, §"Key takeaways", https://academy.claude.com/courses/ai-capabilities-and-limitations/what-we-mean-by-ai

The four, in the order the course takes them:

1. **Next-token prediction.** The loop above. *Capability:* fluent, idiomatic, structurally
   correct output in any register you ask for. *Limitation:* fluency is the objective, not truth —
   a confidently invented Lua function name reads exactly like a real one.
2. **Knowledge.** Everything the model knows about the world it absorbed during training.
   *Capability:* astonishing breadth, cheaply available. *Limitation:* a training cutoff, uneven
   depth (common things well, your niche badly), and no awareness of where the gaps are.
3. **Working memory.** Everything the model can attend to *right now* — the context window: your
   prompt, the files you fed it, the conversation so far. *Capability:* it can reason over material
   it has never seen before, which is why a code agent is useful at all. *Limitation:* the window
   is finite; what falls out of it is gone (the toy's window was one token), and attention over
   what remains is not uniform.
4. **Steerability.** How reliably your instructions change the output. *Capability:* a precise
   spec, examples, or a tool schema genuinely redirect it. *Limitation:* it is a tendency, not a
   guarantee; vague instructions produce vague compliance, and long instruction sets decay.

Knowledge, before → after. The model cannot know your private code; it fills the gap with the
most plausible shape, and becomes accurate once the facts sit in working memory:

```text
Illustrative — written for this lesson.

Before  Prompt:   What does our POS endpoint /refund_v2 return?
        Response: It returns {"status": "ok", "refund_id": "..."} with HTTP 200.   ← invented

After   Prompt:   [pasted refund_v2.lua handler] What does /refund_v2 return?
        Response: HTTP 202 with {"journal_id", "state": "pending"}; the refund is
                  queued, not executed, until the nightly settlement job runs.
```

Steerability, the same way — vague instruction, generic filler; precise spec, precise output:

```text
Illustrative — written for this lesson.

Before  Prompt:   Write release notes for this diff.
        Response: - Improved performance and stability
                  - Various bug fixes and UI polish

After   Prompt:   Write release notes for this diff. One bullet per merged PR: number,
                  PR title in quotes, nothing that is not in the diff.
        Response: - #412 "Split loyalty points per vehicle tier"
                  - #415 "Fix double refund on Premium wash"
```

The spec bent the output — but "nothing that is not in the diff" is a request, not a guarantee,
so you still check the bullets.

Those four are the spine of the course: one or two rungs per axis, capability side first, then
limitation side, then what to do about it (Figure 5).

```mermaid
flowchart TD
  A["AI in production"] --> B["Non-generative — predict, score or rank"]
  A --> C["Generative — produce new text, token by token"]
  B --> B1["spam filter — one bit"]
  B --> B2["recommender — rank a fixed catalogue"]
  B --> B3["fraud score — one number"]
  C --> C1["LLM chat"]
  C --> C2["code agent, e.g. Claude Code"]
  C1 --> D["Four property axes"]
  C2 --> D
  D --> X1["next-token prediction — capability: fluent draft · limitation: confident invention"]
  D --> X2["knowledge — capability: breadth · limitation: cutoff and blind gaps"]
  D --> X3["working memory — capability: reason over new material · limitation: finite window"]
  D --> X4["steerability — capability: specs redirect it · limitation: a tendency, not a guarantee"]
```

*Figure 5: The course's map — generative models and their four axes, each with two sides. Adapted from Claude Academy, AI Capabilities and Limitations, "What We Mean by AI", https://academy.claude.com/courses/ai-capabilities-and-limitations/what-we-mean-by-ai*

### Why this is worth learning now rather than next year

The obvious objection: models change every few months, so why learn properties at all? Because
what changes is the *position* on each axis, not the axis. Context windows grow; the window stays
finite. Cutoffs move forward; a cutoff still exists. Instruction-following gets tighter; it stays
a tendency.

> "This material is durable because the properties stay stable even as models improve. Boundaries shift but the properties remain the same."
> — Anthropic, *Claude Academy — AI Capabilities and Limitations: Intro to AI Capabilities and Limitations*, lesson 1, https://academy.claude.com/courses/ai-capabilities-and-limitations/intro-to-ai-capabilities-and-limitations

So when a Claude Code run mangles a refactor, ask "which axis" — ten seconds, and it tells you
the fix. Lost track of a file it edited twenty minutes
ago — working memory; fix the context, not the prompt wording. Invented a Lua stdlib call —
next-token prediction; add a check, not a scolding. Used an API shape from two years ago —
knowledge; paste the current docs. Ignored half your spec — steerability; shorten and sharpen the
spec.

## Lab

**The question:** across your real working day, how much of the "AI" you touch is actually
generative, and which of the four axes does each generative touch-point depend on most?

This is an inventory, so the program holds the inventory as data and does the counting. Keep the
output: rung 7 of this track comes back to this same list.

### Step 1 — write the inventory as data

Save this as `Axes.scala` anywhere outside the repo. Scala 3, standard library only, no
arguments. Each `Row` is one touch-point; `generative` answers "does it write new text?", and
`axis` names the property whose limitation would bite first.

```scala
// file: Axes.scala
// Inventory of AI touch-points, tagged by kind and by dominant property axis.

val Axes = Vector("next-token prediction", "knowledge", "working memory", "steerability")

// touch-point, generative?, dominant axis (only for generative rows), why
case class Row(name: String, generative: Boolean, axis: String, why: String)

val Rows = Vector(
  Row("card-fraud / anomaly score on POS payments", false, "-",
    "scores a transaction, emits a number, writes no text"),
  Row("licence-plate recognition at the wash gate", false, "-",
    "image in, one plate string out, fixed label space"),
  Row("support-inbox spam filter", false, "-",
    "binary classification over an email"),
  Row("wash-demand forecast for package pricing", false, "-",
    "regression over history, no language involved"),
  Row("'suggest next wash package' recommender", false, "-",
    "ranks a fixed catalogue, generates nothing"),
  Row("Claude Code: monorepo-wide Lua refactor", true, "working memory",
    "must hold many files at once; forgets what fell out of context"),
  Row("Claude Code: new POS module from a spec", true, "steerability",
    "output quality tracks how precisely the spec constrains it"),
  Row("MCP server over the POS database", true, "steerability",
    "must obey tool schemas and stay inside allowed queries"),
  Row("chat: drafting a product spec", true, "next-token prediction",
    "fluent plausible prose is the capability and the trap"),
  Row("chat: release notes from a diff", true, "next-token prediction",
    "plausible-sounding invented items read exactly like real ones"),
  Row("asking about Akka Streams operator semantics", true, "knowledge",
    "answer comes from training data, with a cutoff and gaps"),
  Row("summarising a 60-page vendor contract", true, "working memory",
    "accuracy depends on the whole document fitting and staying attended to"),
)

@main def lab(): Unit =
  // Step 1: the per-row table
  val w = Rows.map(_.name.length).max
  println(s"${"touch-point".padTo(w, ' ')}  gen?  ${"dominant axis".padTo(21, ' ')}  why")
  println("-" * (w + 2 + 4 + 2 + 21 + 2 + 30))
  for r <- Rows do
    val gen = if r.generative then "yes " else "no  "
    println(s"${r.name.padTo(w, ' ')}  $gen  ${r.axis.padTo(21, ' ')}  ${r.why}")

  // Step 2: the generative share
  val total = Rows.size
  val gen = Rows.filter(_.generative)
  println()
  println(f"rows total          : $total")
  println(f"generative          : ${gen.size}")
  println(f"non-generative      : ${total - gen.size}")
  println(f"generative share    : ${gen.size}/$total = ${100.0 * gen.size / total}%.1f%%")

  // Step 3: per-axis counts over the generative rows only
  val counts = gen.groupBy(_.axis).map((a, rs) => a -> rs.size)
  println()
  println("per-axis counts (generative rows only)")
  for a <- Axes do
    val n = counts.getOrElse(a, 0)
    println(s"  ${a.padTo(21, ' ')} $n  ${"#" * n}")
  println(s"  ${"sum".padTo(21, ' ')} ${counts.values.sum}")
```

### Step 2 — run it

```bash
scala Axes.scala
```

Real output:

```text
touch-point                                   gen?  dominant axis          why
---------------------------------------------------------------------------------------------------------
card-fraud / anomaly score on POS payments    no    -                      scores a transaction, emits a number, writes no text
licence-plate recognition at the wash gate    no    -                      image in, one plate string out, fixed label space
support-inbox spam filter                     no    -                      binary classification over an email
wash-demand forecast for package pricing      no    -                      regression over history, no language involved
'suggest next wash package' recommender       no    -                      ranks a fixed catalogue, generates nothing
Claude Code: monorepo-wide Lua refactor       yes   working memory         must hold many files at once; forgets what fell out of context
Claude Code: new POS module from a spec       yes   steerability           output quality tracks how precisely the spec constrains it
MCP server over the POS database              yes   steerability           must obey tool schemas and stay inside allowed queries
chat: drafting a product spec                 yes   next-token prediction  fluent plausible prose is the capability and the trap
chat: release notes from a diff               yes   next-token prediction  plausible-sounding invented items read exactly like real ones
asking about Akka Streams operator semantics  yes   knowledge              answer comes from training data, with a cutoff and gaps
summarising a 60-page vendor contract         yes   working memory         accuracy depends on the whole document fitting and staying attended to

rows total          : 12
generative          : 7
non-generative      : 5
generative share    : 7/12 = 58.3%

per-axis counts (generative rows only)
  next-token prediction 2  ##
  knowledge             1  #
  working memory        2  ##
  steerability          2  ##
  sum                   7
```

### Step 3 — make it yours

Edit `Rows`: delete what you do not have, add what I missed (the Skills you write for other
teams, the plate-matching that links a car to a loyalty account, anything your team shipped since).
For every row you mark `true`, you must name one of the four axes — forcing the choice is the whole
exercise. Re-run and keep the output.

### Reading the output

The per-row table has four columns. **touch-point** is the system or habit, named concretely enough
that you could point at the code. **gen?** is the structural question: does it produce new text
token by token (`yes`) or map an input onto a label, score or ranking (`no`)? Neither direction is
"better" — the column tells you which half of the course applies. **dominant axis** is, for
generative rows only, the property whose limitation would bite first if this touch-point went
wrong; non-generative rows carry `-` because the four axes are properties of generative models and
do not describe a classifier. **why** is the one-line justification, and it is the column to argue
with: if you cannot write it, your tag is a guess.

| counter | value | reads as |
|---|---|---|
| rows total | 12 | touch-points inventoried |
| generative | 7 | rows where the four-axis map applies |
| non-generative | 5 | rows where it does not |
| generative share | 58.3% | more than half, but far from all |

Trace the share with digits: 12 rows, 5 of them tagged `no` (fraud score, plate recognition, spam
filter, demand forecast, recommender), so generative = 12 − 5 = 7, and 7 ÷ 12 = 0.58333…, printed
as 58.3%. The per-axis block then counts only those 7: next-token prediction 2 (spec drafting,
release notes) + knowledge 1 (Akka Streams semantics) + working memory 2 (monorepo refactor,
contract summary) + steerability 2 (new POS module, MCP server) = 2 + 1 + 2 + 2 = 7, which is
exactly the `sum` line. That `sum` is a self-check: if it disagrees with the `generative` count,
a row carries an axis name that is not one of the four, or none at all.

![Touch-points by kind and dominant axis from the lab output](assets/2026-10-12-1-chart-2.png)

*Figure 6: The lab's counts — the tallest bar is the non-generative AI, and no axis dominates the generative rest. Generated from the lab output.*

**Verdict:** even in a platform run by someone who uses a code agent daily, 5 of 12 AI
touch-points are not generative at all, and the 7 that are spread evenly over all four axes — no
single axis dominates, so no single mitigation covers your exposure.

### Cause → consequence

1. **Cause.** A generative model's output space is unbounded: it emits whatever token sequence is
   most plausible next, rather than selecting from a fixed answer set the way a classifier does.
2. **Mechanism.** Plausibility is produced by four separable machineries — the token-by-token
   prediction loop, the knowledge frozen in the weights, the finite window of what it can attend
   to now, and the degree to which instructions bias the loop. Each has its own capability zone
   and its own failure zone.
3. **Consequence.** Failures are not random "bad days"; they sort cleanly into four buckets, and
   each bucket has a different fix: verification for invented detail, fresh context for stale
   knowledge, context management for forgetting, tighter specs for drift.
4. **What it means in practice.** When a Claude Code run on the Lua monorepo goes wrong, your first
   question is "which axis", not "which prompt". And when you write Skills or MCP servers for other
   teams, you are mostly engineering the memory and steerability axes on their behalf — the two
   you can actually control from outside the model.

## Self-check

1. Your POS fraud scorer and your chat-drafted product spec are both "AI". What is the structural difference, and why does only one of them get a four-axis diagnosis? <details><summary>Answer</summary>The fraud scorer is predictive: it maps a transaction onto a score drawn from a fixed output space, so it can be straightforwardly right or wrong and is evaluated with accuracy-style metrics. The spec draft comes from a generative model whose output space is every possible token sequence, so it can only be more or less plausible. The four axes (next-token prediction, knowledge, working memory, steerability) are properties of that generative machinery, so they describe the spec draft and say nothing useful about the scorer.</details>
2. Claude Code edits twelve Lua files, then re-introduces a bug it had fixed in the first file. Which axis, and what is the fix that follows from naming it? <details><summary>Answer</summary>Working memory. The first file's state fell out of the context the model can attend to right now, so the fix is a context fix, not a wording fix: smaller batches, re-read the file before touching it again, pin the invariant in a file the agent always loads, or add a test that fails if the bug returns. Rewriting the prompt more politely changes nothing, because the information was simply not in front of the model.</details>
3. Context windows have grown by orders of magnitude and will grow again. Why is the working-memory axis still worth learning? <details><summary>Answer</summary>Because growth moves the boundary, not the property. Claude Academy puts it as "Boundaries shift but the properties remain the same" (lesson 1, "Intro to AI Capabilities and Limitations"): a window ten times larger is still finite, attention across it is still uneven, and anything outside it is still invisible to the model. The reasoning you do about context management stays valid; only the threshold at which you start doing it moves.</details>
4. The toy generator printed `the basic wash includes wax .` although no sentence in its corpus says that. Which two axes explain the output, and what would fix each? <details><summary>Answer</summary>Next-token prediction: the model picks the most probable continuation (`wax`, 2 of 5 followers of `includes`), and probability is popularity, not truth — the fix is verification against a source. Working memory: its window is one token, so by the time it reached `includes` the word `basic` was no longer visible — the fix is a larger context (a real transformer conditions on the whole prompt), which would let `basic` steer the choice toward `foam` or `rinse`.</details>

## Sources

- [Claude Academy — AI Capabilities and Limitations: Intro to AI Capabilities and Limitations](https://academy.claude.com/courses/ai-capabilities-and-limitations/intro-to-ai-capabilities-and-limitations) — Anthropic, lesson 1 of *AI Capabilities and Limitations* (text plus a 4-minute video); gave the split between the collaboration question and the machine question, the five-step course roadmap, and the quoted claim about why the material is durable; accessed 2026-10-12.
- [Claude Academy — AI Capabilities and Limitations: What We Mean by AI](https://academy.claude.com/courses/ai-capabilities-and-limitations/what-we-mean-by-ai) — Anthropic, lesson 2 of *AI Capabilities and Limitations*, §"Key takeaways"; gave the narrowing of "AI" to generative transformer-based text models, the generative-versus-predictive distinction, the quoted four-axes claim, and the map replicated in Figure 5; accessed 2026-10-12.
- [Deep Learning Visuals](https://github.com/dvgodoy/dl-visuals) — Daniel Voigt Godoy, figures from *Deep Learning with PyTorch Step-by-Step*, licensed CC BY 4.0 (licence checked on the repository README); Figure 1 ([Classification](https://dvgodoy.github.io/dl-visuals/Classification), ch. 5) and Figure 3 ([Decoder](https://dvgodoy.github.io/dl-visuals/Decoder), ch. 9); accessed 2026-10-15.
- Provenance note: both course pages refused an automated fetch on 2026-10-12 (they are behind the Academy's sign-in), so the two blockquotes above are the passages captured and verified from those pages when this rung of the curriculum was built; open the links yourself to re-check them. The customer-email, refund-endpoint and release-notes examples and the five-sentence toy corpus were written for this lesson and are labelled as illustrative; the Scala outputs are real runs. No other source is quoted in this lesson.

## Next on this track
Next on Claude Academy: **How AI gets its character: pretraining, fine-tuning and fingerprints** (rung 2 of 20, Beginner).
