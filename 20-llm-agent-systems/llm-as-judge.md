# LLM as Judge

> **Priority:** Recommended
> **Est. time:** 40 min
> **Track:** Server
> **HelloInterview:** none

Using a model to grade another model's output. It is how most teams make agent evaluation affordable,
and it is the single most under-validated component in a typical LLM stack. The engineering position
to hold: **a judge is a measurement instrument, so it needs calibration, a known error rate, and a
scope beyond which you do not trust it.** Companion to
[evaluating-agents.md](evaluating-agents.md).

---

## 1 · When a judge earns its place

| | Human label | LLM judge | Deterministic check |
|---|---|---|---|
| Cost per label | Dollars | Fractions of a cent | ~Zero |
| Latency | Hours to days | Seconds | Milliseconds |
| Throughput | Tens per hour | Thousands per minute | Unbounded |
| Consistency | Moderate; drifts, disagrees | High run-to-run at temperature 0 | Perfect |
| Trustworthy on | Anything | Things you have calibrated it on | Exactly what it checks |

Order of preference, and it does matter:

1. **Deterministic check** wherever the property is checkable. Valid JSON, schema conformance, the
   refund amount matching the ride total, a required disclaimer present, no forbidden tool called.
   People reach for a judge for things a regex or an assertion answers exactly. Do not.
2. **LLM judge** for graded qualities at volume: helpfulness, tone, faithfulness to retrieved context,
   whether an answer addresses the question asked.
3. **Human** for the calibration set, the ambiguous tail, anything safety-critical, and periodic audit.

The judge does not replace humans. It **amortises** them: humans label a few hundred examples, that set
calibrates the judge, and the judge scales to tens of thousands — with humans re-auditing on a schedule.

---

## 2 · Pointwise, pairwise, reference-based

| Mode | Form | Strengths | Weaknesses |
|---|---|---|---|
| **Pointwise** | Score one output against a rubric | Absolute scores; comparable across releases; needs no baseline | Poorly calibrated on a numeric scale; drifts over time; clusters on a few values |
| **Pairwise** | "A or B, which is better?" | Much higher agreement with humans; robust to scale drift | Only relative; needs a baseline; O(n) comparisons per candidate; position bias |
| **Reference-based** | Compare against a known-good answer | Closest to a unit test; high agreement | Requires references; penalises correct answers that differ from the reference |

**Rule of thumb:** pairwise for "is the new prompt better than the old one", pointwise for "how are we
doing this week", reference-based for the subset where a golden answer genuinely exists. Reporting
a pointwise absolute score as though it is a stable quantity across months is where most judge-based
dashboards go wrong.

---

## 3 · Rubric design

The rubric does more for judge quality than the choice of judge model. Rules that hold up:

* **Decompose into binaries.** Five yes/no criteria beat one 1-10 score. Models are far better at "does
  this answer state the refund amount? yes/no" than at "rate the helpfulness 1-10", and binaries give
  you per-criterion diagnostics instead of a mush number.
* **Never a 1-10 scale.** If you must have a scale, use three or four levels with explicit anchors, each
  described by what it looks like. Ten-point scales collapse onto 7 and 8 in practice.
* **Independent criteria.** Correctness, completeness, tone and safety are separate questions.
  Bundling them lets a beautifully-worded wrong answer score well.
* **Evidence before verdict.** Require the judge to quote the specific span it is judging, then give the
  label. This measurably improves accuracy and, more importantly, makes disagreements auditable — you
  can read why it said what it said.
* **Provide the context the judge needs and nothing more.** To judge faithfulness it needs the retrieved
  documents. It should not see which system produced the answer, which variant is the new one, or any
  metadata that lets it infer the expected answer.
* **Give it an "insufficient information" option.** Without one, a judge forced to choose invents a
  justification, and you have converted "I do not know" into a confident wrong label.
* **Write the rubric from disagreements.** Start with human labels, find the cases humans disagreed on,
  and the rubric writes itself out of those boundaries. A rubric written in the abstract encodes the
  author's assumptions and nothing else.

---

## 4 · Biases, and what to do about them

| Bias | What happens | Mitigation |
|---|---|---|
| **Position** | In pairwise, the first (or last) option wins more often than it should | Run both orders, average; discard examples where the verdict flips as ties (and count them — a high flip rate means the rubric is not discriminating) |
| **Verbosity / length** | Longer answers score higher regardless of content | Length-matched pairs where possible; an explicit rubric line that length is not a merit; report score against length and look for slope |
| **Self-preference** | A judge prefers text from its own model family | Use a different family for the judge than for the agent. Cheap, and it decorrelates blind spots |
| **Formatting** | Bullet points, bold text and headers read as higher quality | Normalise formatting before judging, or state explicitly that formatting is out of scope |
| **Sycophancy / leniency** | Judges skew generous, especially pointwise | Calibrate the threshold against human labels rather than using the raw score. If pass rates sit at 95%, suspect leniency before celebrating |
| **Anchoring on the reference** | With a reference answer present, anything different is marked wrong | Instruct explicitly that the reference is one valid answer, not the only one |
| **Authority / confidence** | Confidently-stated errors are scored above hedged correct answers | Add a factuality criterion checked against source material, not against tone |
| **Drift** | The judge model is updated by the provider; scores move with no change on your side | Pin the judge model version. Re-run the calibration set on every judge change and treat a shift as a release |

**Position and verbosity are the two that will actually bite you.** Both are cheap to control and both
are routinely ignored.

---

## 5 · Calibrating against human labels

This is the step that separates a judge you can quote from a number you made up.

1. **Build a gold set.** A few hundred examples, stratified like the eval set itself (§3 of
   [evaluating-agents.md](evaluating-agents.md)), labelled by humans. Multiple labellers on a subset so
   you can measure **inter-annotator agreement** — this is your ceiling. A judge cannot meaningfully
   agree with humans more than humans agree with each other, and if humans agree only 70% of the time
   your rubric is the problem, not the judge.
2. **Measure agreement, not accuracy.** Report Cohen's kappa (chance-corrected) and per-class precision
   and recall. Raw accuracy on an imbalanced set is meaningless: if 90% of answers are good, a judge
   that says "good" every time scores 90%.
3. **Look at both error directions.** False-pass and false-fail have different costs. A judge used as a
   release gate should be tuned for few false passes; a judge used to triage examples for human review
   should be tuned for few false fails.
4. **Choose the operating threshold from the data**, not from a round number. If the judge's score
   separates human-good from human-bad best at 0.62, use 0.62.
5. **Re-audit on a schedule.** Sample judge decisions, have a human review them, track agreement as a
   time series. Agreement decay is the alert.
6. **Re-calibrate whenever anything moves**: judge model version, rubric wording, the agent's own
   output style, or the input distribution. All four change the judge's behaviour.

**Report the judge's error bars alongside the metric it produces.** "Pass rate 84% (judge agreement with
humans: kappa 0.71)" is an engineering statement. "Pass rate 84%" alone is a vibe.

---

## 6 · Where a judge quietly fails

The dangerous cases are not the ones where the judge is obviously wrong. They are the ones where it
returns a plausible label with no signal in it.

| Situation | Why it fails |
|---|---|
| **Facts it cannot verify** | Whether a specific rider was actually charged twice is a database question. The judge will confidently score the *plausibility* of the answer and you will read it as correctness |
| **Domain policy** | Refund eligibility rules live in a policy document and change. A judge without the policy in context is grading against its priors |
| **Multi-turn attribution** | Given a whole conversation, judges struggle to attribute a failure to the turn where it happened. Judge turn-level where you can |
| **Tool-call correctness** | Whether the right tool was called with the right arguments is a deterministic check over the trace. Using a judge here is slower, costlier and less accurate |
| **Safety** | Never the sole gate. A judge is a defence-in-depth layer behind deterministic checks and human review, not a replacement for them |
| **Near-identical candidates** | Two prompts that differ slightly produce outputs the judge cannot separate; the verdicts become coin flips that look like measurements. The flip-rate-under-order-swap check catches this |
| **Out-of-distribution inputs** | The judge was calibrated on typical traffic. On the weird tail — the cases you most want graded — its agreement with humans is unmeasured |

---

## 7 · Operational rules

* **Pin and version the judge** — model, prompt, rubric, threshold — exactly like a production
  dependency. A judge change invalidates comparisons across it; record the judge version with every
  score.
* **Judge model different from the agent model.** Removes self-preference and decorrelates blind spots.
* **Temperature 0**, and repeat on the ambiguous band if you need tighter estimates.
* **Store the judge's reasoning and the quoted evidence**, not just the label. Disagreements are the
  most valuable data you have and they are unusable without the reasoning.
* **Cheaper judge for volume, stronger judge for the boundary.** A small model handles the clear cases;
  route the uncertain band to a stronger judge or a human. This is a cascade, and it is where most of
  the cost saving lives.
* **Never let the judge be the only thing between a change and users.** Deterministic invariants gate
  safety; the judge grades quality; humans audit both.

---

## 8 · Cross-references

* [evaluating-agents.md](evaluating-agents.md) — where judge outputs get used.
* [production-llmops.md](production-llmops.md) — judge calls are model calls: they cost money, need
  tracing, and are subject to the same rate limits.

---

## Interview questions

**1. When would you use an LLM as a judge, and when not?**
For graded qualities at volume that no assertion can capture — helpfulness, tone, faithfulness to
retrieved context. Not for anything a deterministic check answers exactly: schema validity, whether a
required tool was called, whether the refund amount matches the ride total. And never as the sole gate
on safety. The judge amortises human labelling rather than replacing it — humans label a calibration
set, the judge scales it, humans re-audit on a schedule.

**2. What biases does a judge have and how do you control them?**
Position bias in pairwise comparisons — fix by running both orders and averaging, treating flips as
ties. Verbosity bias, where longer answers score higher — check by plotting score against length and
looking for slope. Self-preference for its own model family — use a different family for the judge.
Formatting bias toward bullets and bold. And leniency drift, which is why you calibrate the threshold
against human labels rather than trusting the raw score.

**3. How do you know your judge is any good?**
Calibrate it against a human-labelled gold set and report chance-corrected agreement, Cohen's kappa,
not raw accuracy — on an imbalanced set a judge that always says "good" scores 90%. Measure
inter-annotator agreement too, because that is the ceiling: if humans agree only 70% of the time, the
rubric is underspecified. Then choose the operating threshold from the data and re-audit on a schedule,
tracking agreement as a time series.

**4. Pointwise or pairwise?**
Pairwise agrees with humans much better and is robust to scale drift, so it is the right tool for "is
this prompt better than the one in production". Pointwise gives absolute scores comparable across
releases, which you need for a dashboard, but it is poorly calibrated and drifts, so its numbers are
only meaningful relative to a calibration you have re-run. Pairwise also costs a baseline run per
comparison and carries position bias.

**5. How do you write a good rubric?**
Decompose into independent binaries rather than a 1-10 scale — models are much better at "does this
state the refund amount, yes or no" and you get per-criterion diagnostics. Require the judge to quote
its evidence before giving a verdict, which improves accuracy and makes disagreements auditable. Give
it an explicit "insufficient information" option so it does not invent a justification. And write the
rubric from the cases where human labellers disagreed, because those are where the real boundaries are.

**6. Where does a judge fail without telling you?**
On facts it cannot verify — whether a rider was actually double-charged is a database question, and the
judge will grade the answer's plausibility while you read it as correctness. On domain policy it does
not have in context. On attributing a multi-turn failure to the turn where it happened. And on
near-identical candidates, where verdicts become coin flips that look like measurements — the tell is a
high flip rate when you swap the presentation order.

**7. Your judge-reported quality score jumped five points with no code change. What happened?**
Most likely the judge model was updated provider-side, which is why the judge version is pinned and
recorded with every score. Other candidates: the rubric or prompt was edited, the input distribution
moved so the mix of easy and hard cases changed, or the agent's output style changed in a way that
triggers a formatting or verbosity bias without the substance improving. Re-run the human calibration
set — if agreement moved, the instrument changed, not the system.
