# Evaluating Agents

> **Priority:** Required
> **Est. time:** 90 min
> **Track:** Server
> **HelloInterview:** none

This is the file to know cold. Evaluation is where LLM systems stop being a demo and start being
engineering, it is the part most candidates handle badly, and Lyft has **published a failure of their
own agent evaluation** — an offline simulator reporting 90% pass rates while production told a
different story. Being able to discuss that failure properly, and to generalise it into a statement
about measurement validity, is a genuine differentiator in this loop. The behavioural round asks
"How did you measure?" verbatim; this is the technical version of the same question.

---

## 1 · Why agent evaluation is not model evaluation

Model benchmarks score a single input-output pair. An agent produces a *trajectory*: a sequence of
routing decisions, tool calls, observations and messages, over multiple turns, against mutable external
state. Four things change as a result.

| Property | Consequence for evaluation |
|---|---|
| **Non-determinism** | The same input yields different trajectories. Every measurement is a sample; every comparison needs a noise floor. |
| **Multi-step compounding** | A 95%-accurate step, five times, is 77% end-to-end. Per-step metrics look fine while the system fails. |
| **Path matters, not just the answer** | A correct answer reached by calling a write tool three times is not a pass. |
| **The environment has state** | Refunds get issued, tickets get created. Evaluation needs sandboxed or mocked tools, or you will pay real money to measure. |
| **No ground truth for the interesting cases** | "Was this a good support answer?" has no key. It has a rubric, and rubrics need their own validation. |

Corollary, and the thing to say first in an interview: **you are not writing tests, you are building a
measurement instrument.** Instruments have accuracy, precision, bias and drift, and they need to be
calibrated against something you trust. Most agent-eval disasters are instrument failures, not model
failures.

---

## 2 · The evaluation ladder

Five rungs, cheapest and most deterministic first. A mature platform runs all five; a team in trouble
usually has only rungs 1 and 5.

| Rung | What it tests | Determinism | Where it runs |
|---|---|---|---|
| **1. Unit** | Tool implementations, schema validation, reducers, budget enforcement, parsing | Fully deterministic | Every commit |
| **2. Node** | One model call in isolation: does the router classify this input correctly? does the extractor produce valid JSON? | Statistical, low variance, cheap | Every commit (small set), full set nightly |
| **3. Trajectory** | A whole conversation against mocked tools: did it take a sane path, call the right tools, respect safety gates? | Statistical, higher variance | On prompt/model/graph change |
| **4. Conversation / simulated user** | Multi-turn, with a simulated user pushing back, changing their mind, being terse | Highest variance, most expensive | Nightly and pre-release |
| **5. Online** | Real traffic: A/B, shadow, guardrail metrics | Ground truth, slow, risky | Continuous |

**Push work down the ladder.** Every check you can move from rung 4 to rung 2 gets cheaper, faster and
less noisy. A router that is 92% accurate is a rung-2 measurement with a tight confidence interval on
a few hundred labelled examples; discovering the same fact at rung 4 costs a hundred times as much and
tells you less about where it went wrong.

---

## 3 · Building the offline eval set

The eval set is an asset with a lifecycle, not a directory of JSON files someone made once.

**Sourcing.** Real production traffic is the only honest starting point. Sample it, de-identify it at
capture time (so it is not personal data by the time you depend on it), and label it. Synthetic cases
supplement — they are how you cover the rare and the dangerous — but a suite that is mostly synthetic
measures your imagination.

**Stratification.** Sample deliberately across the dimensions that matter, not uniformly:

* Intent / specialist agent — every route needs coverage, including the ones with low volume.
* Difficulty — easy, ambiguous, adversarial, out-of-scope. Uniform sampling from production produces a
  suite that is 80% easy, which is exactly how you get a 90% pass rate that means nothing.
* Rider versus driver.
* Turn count — one-shot questions behave differently from six-turn negotiations.
* Safety-relevant cases, deliberately over-sampled. Rare and expensive is the definition of what you
  over-sample.

**Freezing and versioning.** The set is versioned like code, in the repo or in a registry, with a
changelog. Every reported score names the eval-set version. Otherwise "we improved from 82% to 88%"
is uninterpretable, because someone may have removed the hard cases.

**Leakage.** If you tune prompts against the eval set — and you will — it stops being an unbiased
estimate. Keep a **holdout** you touch only at release, and rotate a fraction of the working set from
fresh production traffic every cycle. This is train/test discipline, and it is violated constantly
because prompts do not *feel* like fitted parameters. They are.

**Size.** Big enough that the confidence interval is narrower than the effect you care about. For a
binary pass rate near 85%, the standard error on n examples is about `sqrt(0.85 x 0.15 / n)` — roughly
3.6 percentage points at n = 100, 1.6 at n = 500, 1.1 at n = 1,000. If you want to detect a 2-point
regression you need several hundred examples *and* repeats, because run-to-run variance stacks on top
of sampling variance. Knowing this arithmetic is what makes "our eval went from 88 to 86" a
conversation rather than a panic.

---

## 4 · Golden trajectories

A golden trajectory is a recorded reference run: input, the tool calls made, and the outcome.

**What to assert on:**

| Assert | Do not assert |
|---|---|
| The final outcome (refund issued / escalated / answered) | The exact wording of the reply |
| The set of write tools invoked | The exact ordering of independent read calls |
| That required tools were called at all (e.g. identity verified before account change) | The number of reasoning steps |
| That forbidden tools were *not* called | Intermediate scratchpad content |
| Structured fields in the answer (amount, ride id, policy code) | Token counts, unless budgeted |

The rule underneath: **assert on invariants and effects, not on the path.** A trajectory test that
breaks when the model reorders two independent read calls is a flaky test that will be deleted within
a month, taking its real coverage with it.

**Storing goldens.** Record the mocked tool responses alongside the trajectory so the run is
reproducible without live dependencies. This is VCR-style recording, and it makes trajectory tests
runnable in CI without network access — the same reasoning as
[mocks and stubs](../12-testing/Testing-mocks_stubs.md).

**Refreshing goldens.** They rot. A policy change makes yesterday's correct refusal today's wrong
answer. Treat a golden update as a reviewed change with a stated reason. "Updated goldens to match new
behaviour" in a diff with no explanation is how a regression ships.

---

## 5 · Trajectory versus outcome evaluation

| | Outcome eval | Trajectory eval |
|---|---|---|
| **Question** | Did it end up right? | Did it get there properly? |
| **Cheap to label?** | Often yes | No — needs step-level judgement |
| **Catches** | Wrong answers | Right answers for wrong reasons, wasted cost, unsafe paths, latent risk |
| **Misses** | Everything about *how* | Correct novel paths it marks as deviations |
| **Fails when** | The answer is a judgement call with no key | The task has many valid paths |

You need both, and the reason is a classic distributed-systems intuition: **outcome eval is a
black-box health check, trajectory eval is instrumentation.** A health check tells you the system is
up; it does not tell you that one dependency is retrying 40 times per request and you are one traffic
spike from an outage. An agent that reaches the right answer by calling six tools when two would do is
passing your outcome eval and quietly setting your cost and latency ceiling.

**Practical middle ground:** score outcome as the headline metric, and run a small set of *trajectory
invariants* as hard gates — verification before mutation, no write tool after a safety flag, no more
than N steps, no duplicate identical tool calls. Invariants are cheap, deterministic, and catch the
failure classes that actually hurt.

---

## 6 · Metrics that matter for a support agent

| Metric | Definition | Why |
|---|---|---|
| **Resolution rate** | Conversations resolved without human involvement | The headline business metric. Also the one most easily gamed by an agent that confidently closes things |
| **Escalation rate** | Handed to a human | Should be *high* for the right cases. Falling escalation is not automatically good |
| **False-resolution rate** | Marked resolved, user came back within N days | The counterweight to resolution rate. Never report resolution without it |
| **Routing accuracy** | Correct specialist chosen | Bounds everything downstream |
| **Tool-call precision / recall** | Right tools called; needed tools not skipped | Catches "right answer, wrong reason" |
| **Harmful-action rate** | Unsafe or unauthorised action taken | Target is zero; measured per-1000 and alerted, not averaged |
| **Turns to resolution** | Median and p90 | User-visible effort. Also a distribution-shift detector — see §9 |
| **Cost per resolved conversation** | Tokens x price, plus tools | The unit economics. Must be a tracked SLO, not a monthly surprise |
| **p50 / p95 latency, and TTFT separately** | | Perceived quality is dominated by time-to-first-token |
| **Containment cost delta** | Cost of agent handling versus human handling | The number that justifies the platform |

**A pair of metrics is almost always required.** Resolution rate alone is maximised by an agent that
never escalates. Escalation rate alone is minimised by the same agent. Cost alone is minimised by an
agent that answers "I cannot help" instantly. Every headline metric needs its adversarial twin, chosen
so that gaming one degrades the other. This is the same discipline as pairing throughput with error
rate in a service SLO.

Lyft's published figure is an **87% reduction in average resolution time** across **7 production
agents** and **~270k interactions/month** — see [lyft-scc-case-study.md](lyft-scc-case-study.md).
A good instinct to voice: resolution *time* is a latency metric, and the natural follow-up questions
are what happened to resolution *quality*, to repeat-contact rate, and to the distribution rather than
the average.

---

## 7 · Regression detection in CI

The goal is a gate that catches real regressions and does not cry wolf. Both halves are load-bearing:
a noisy eval gate gets bypassed within two weeks and then you have no gate.

**Establish the noise floor first.** Run the identical eval set against the identical unchanged system
five to ten times. The spread you observe is your noise floor. Any gate threshold tighter than that
floor fires on nothing. Teams skip this step and then argue about phantom regressions for a quarter.

**Reduce variance where you legitimately can:**

* Temperature 0 for anything you are gating on. It does not make the model deterministic — batching,
  hardware and provider-side changes still move it — but it removes the largest term.
* Pin the model version explicitly. A silent provider-side upgrade is an unannounced dependency
  release into production.
* Fix any sampling seeds you control.
* Repeat and average: k runs per example, report the mean and the interval. Cost scales with k, so
  spend it on the ambiguous examples, not the ones that pass every time.

**Tier the gates:**

| Tier | Runs on | Blocking? | Content |
|---|---|---|---|
| Smoke | Every commit | Yes | Rungs 1-2: unit, schema validity, router accuracy on ~50 examples, safety invariants |
| Full offline | Prompt / model / graph change, and nightly | Yes for prompt and model changes | Rung 3, few hundred trajectories |
| Simulated conversation | Nightly and pre-release | No — reported, not blocking | Rung 4 |
| Holdout | Release candidate only | Yes | Untouched set, run once |

**Safety invariants are always blocking and always deterministic.** "No write tool executed after a
safety flag" is a boolean over the trace, not a statistical claim. Do not put a safety property behind
a pass-rate threshold.

**Flake policy.** An example whose result flips across repeats on an unchanged system is not a
regression signal. Quarantine it, keep it in a "high-variance" bucket that gets reported separately,
and look at that bucket — high variance is itself information, usually about an ambiguous prompt or an
underspecified rubric.

**What to store per run.** Full traces, the eval-set version, model version, prompt version, and the
config hash. When a regression appears three weeks later you will want to bisect over prompt versions,
and you can only do that if the runs are addressable.

---

## 8 · Online evaluation

Offline eval is a proxy. Online eval is the measurement, and it is the only one that is not a
model of reality.

* **Shadow / replay.** Run the candidate on real traffic without showing anyone the output. Free
  distribution realism, zero user risk. It cannot measure anything interactive — the shadow agent's
  reply never influences the user's next message, so multi-turn behaviour is unmeasurable this way.
  Perfect for router accuracy, tool selection, cost and latency; useless for conversation quality.
* **A/B.** The real thing. Randomise at the conversation or user level, never at the turn level —
  turn-level randomisation splits a single conversation across two agents and measures nothing
  interpretable.
* **Guardrail metrics.** Every experiment carries metrics it is not trying to improve but must not
  break: harmful-action rate, escalation rate, false-resolution rate, p95 latency, cost per
  conversation. Automatic rollback on a guardrail breach.
* **Ramp plan.** 1% → 5% → 25% → 50%, with a defined observation window at each stage sized so the
  slowest metric (repeat contact within 7 days) has time to move. Ramping faster than your slowest
  guardrail metric can be measured is ramping blind.
* **Interleaving** is available for retrieval-style comparisons and needs far less traffic than A/B,
  but does not apply cleanly to agents, where you cannot interleave halves of a conversation.
* **Long-horizon effects.** Repeat-contact rate and CSAT move on a scale of days to weeks. An
  experiment concluded in 48 hours has measured the fast metrics only, and the fast metrics are the
  ones most easily gamed.

---

## 9 · Case study: the simulator that lied

**The facts, as published by Lyft.** Their offline agent simulator reported **90% pass rates**.
Production revealed a **distribution shift**: off-the-shelf LLM user simulators behave like *nice,
helpful assistants*, while real customers send **brief, impatient messages**. They fixed it by
**fine-tuning the simulators on real customer verbatims**.

**Why this is a much better story than it first looks.** Nothing was wrong with the agent, the eval
harness, the metric definitions or the sample size. Every piece of the machinery worked. The
measurement was invalid anyway, because the *population being measured* was not the population the
system serves.

Unpack what the simulated user was doing wrong, because the specifics are what make the story credible
in an interview. The published claim is the pair "nice, helpful assistants" versus "brief, impatient
messages"; the table below is the general shape of that gap in any support context, not a list of
Lyft's own findings — present it that way if you use it.

| Simulated user | Real user |
|---|---|
| Writes full sentences with context | "wheres my refund" |
| Answers clarifying questions cooperatively | Repeats the original question, louder |
| Supplies the ride id when asked | Does not know it, will not look it up |
| One intent per conversation | Three intents, one of which is emotional |
| Polite when the agent is wrong | Escalates immediately, sometimes abusively |
| Patient across many turns | Abandons, or demands a human on turn two |
| No typos, no code-switching, no slang | All three |

Now look at what that does to a support agent. An agent whose recovery strategy is "ask a clarifying
question" scores beautifully against a cooperative simulator and collapses against a user who answers
a clarifying question with "just fix it". The clarification strategy was never tested, because the
test population never triggered the case it fails on. The agent was over-fitted to a politeness
distribution nobody had noticed was a variable.

**And 90% should itself have been a warning.** A metric sitting at 90% has almost no headroom left to
detect a regression: nine tenths of the suite is no longer doing work. When an eval saturates, the
correct reaction is to suspect the eval, not to celebrate the system. Difficulty stratification
(§3) exists precisely to keep a suite from drifting into that state.

---

## 10 · The general lesson: simulator realism is an eval-validity problem

Generalise it properly, because the general form is what transfers to the rest of the job.

**An eval score is an estimate of production performance under the assumption that the eval
distribution equals the production distribution.** Break that assumption and the number does not become
noisy — it becomes *wrong in a specific direction*, and no amount of extra samples fixes it. Sampling
error shrinks as `1/sqrt(n)`. Validity error does not shrink at all.

Two kinds of validity, borrowed from experimental design and worth naming out loud:

* **Internal validity** — does the eval measure what it claims, consistently? Threats: leakage, flaky
  goldens, an uncalibrated judge, gaming.
* **External validity** — does the result transfer to production? Threats: distribution shift,
  synthetic inputs, sandboxed tools with unrealistic latency and error rates, a simulator that is nicer
  than reality.

Lyft's failure was purely external validity. Their instrument was precise and biased.

**The correlated-instrument trap, and why it should feel familiar.** If your user simulator, your judge
and your agent all come from the same model family, their blind spots are correlated. A simulator built
from the same model will not produce the inputs that model handles badly, because "what this model
finds hard" is not in its own generative distribution. That is a *systematic* error, and systematic
errors do not average out.

For a distributed-systems engineer this is a familiar rule wearing a new hat: **never monitor a system
with something that shares its failure domain.** You do not run the health checker inside the cluster
it checks. You do not build the alerting on the database it monitors. A simulator drawn from the same
model as the agent is monitoring inside the failure domain. Say this in the interview — it is the
sentence that shows the framing transferred.

### 10.1 Detecting the shift before production does

Compare distributions, not means. Cheap, high-signal features for a support context:

| Feature | Signal |
|---|---|
| Message length (chars, tokens) | The one Lyft's failure hinged on. Simulated users are verbose |
| Turns to resolution | Simulated conversations run long and civil |
| Question-mark and imperative rates | Real users command, simulated users ask |
| Typo, abbreviation and slang rate | Near zero in generated text |
| Profanity and escalation-demand rate | Structurally absent from an aligned simulator |
| Language mixing / code-switching | Present in real traffic, rare in generated |
| Intent count per conversation | Real conversations wander |
| Distribution over intents | Synthetic sets over-represent the interesting cases |

Then: two-sample tests on each feature (KS for continuous, chi-squared for categorical), or embed both
corpora and compare the embedding distributions. Do this **before** trusting an offline number, and put
it in a dashboard so drift is visible rather than discovered.

The sharpest single test: **train a classifier to distinguish simulated from real messages.** If it
reaches high accuracy on simple surface features, your simulator is not simulating. If it cannot do
better than chance, you have a realistic simulator. This is a discriminator check, and it is cheap.

### 10.2 Fixing it

| Fix | Notes |
|---|---|
| **Seed from real verbatims** | The lowest-effort large win: use real opening messages as simulator seeds instead of generated ones |
| **Fine-tune the simulator on real transcripts** | What Lyft did. Highest fidelity; needs data, de-identification, and a training pipeline |
| **Replay real transcripts** | Perfectly realistic inputs, but the user's turn *k+1* was a response to the old agent, so it is only valid for single-turn or shadow evaluation. Know this limitation |
| **Persona sampling** | Explicit personas — terse, impatient, confused, adversarial, non-native speaker — with a mixture weighted to match production, not to be interesting |
| **Adversarial and red-team personas** | Deliberate over-sampling of the dangerous tail |
| **Different model family for the simulator** | Decorrelates blind spots. Cheap, underused |
| **A permanent real-traffic holdout** | The ground truth against which offline numbers are validated |

### 10.3 The meta-metric: offline-to-online correlation

The measurement that would have caught this in a week:

> For each of the last N releases, plot the offline score delta against the observed online metric
> delta. Track the rank correlation.

A healthy eval suite has a strong positive correlation. When it decays, **the eval system is broken**
and that is a P1 on the eval system, independent of how the agent is doing. This turns eval validity
from a philosophical worry into a monitored number with an owner and an alert — and "we monitored the
correlation between our offline proxy and the online truth" is a very strong thing to be able to say
when someone asks how you measured.

---

## 11 · A practical eval architecture

```
   production traffic
          │
          ├──▶ sampler ──▶ de-identify ──▶ eval corpus (versioned, stratified)
          │                                     │
          │                                     ├──▶ node evals      (rung 2, every commit)
          │                                     ├──▶ trajectory sets (rung 3, prompt/model change)
          │                                     └──▶ simulator seeds (rung 4, nightly)
          │
          ├──▶ shadow runner ──▶ candidate agent ──▶ metrics only, no user impact
          │
          └──▶ A/B assignment ──▶ control / candidate ──▶ online metrics + guardrails
                                                              │
   traces (every run: rung 2-5) ──▶ trace store ──────────────┤
                                                              ▼
                                            offline-to-online correlation dashboard
```

Every arrow into the eval corpus carries a de-identification step. Every run writes a trace tagged with
eval-set version, prompt version and model version. Those two rules are what make the rest auditable.

---

## 12 · Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| Vibe-checking in a notebook | Not reproducible, not comparable, not a gate. Fine for exploration, never for a decision |
| One number for the whole system | Hides which specialist regressed. Report per-route |
| Eval set built entirely by the team that wrote the prompts | Measures their model of users, not users |
| Comparing runs across different eval-set versions | The single most common source of imaginary improvements |
| Tuning prompts against the holdout | It is now a training set. You have no estimate left |
| A judge with no human calibration | See [llm-as-judge.md](llm-as-judge.md) |
| Blocking CI on a noisy statistical gate | Gets bypassed, then removed, then you have nothing |
| Safety behind a pass-rate threshold | Safety properties are invariants. Assert them deterministically |
| Reporting an average and no distribution | An 87% average improvement is consistent with a tail that got much worse |
| Never refreshing goldens | They encode last quarter's policy |

---

## 13 · Cross-references

* [llm-as-judge.md](llm-as-judge.md) — calibrating the grader itself.
* [lyft-scc-case-study.md](lyft-scc-case-study.md) — the platform and the published numbers.
* [production-llmops.md](production-llmops.md) — traces are the raw material for all of this.
* [Testing: types and levels](../12-testing/Testing-types_levels.md) and
  [property-based testing](../12-testing/Testing-property_based.md) — invariant-style assertions
  transfer directly to trajectory invariants.
* [Load testing](../12-testing/Testing-load_testing.md) — same discipline for the cost and latency axes.

---

## Interview questions

**1. How do you evaluate an agent?** **[Reported at Lyft]** *("Tell me some experience related to ML or Gen AI" usually opens onto this)*
As a ladder, cheapest first: unit tests for tools and reducers; node-level evals for the router and any
extractor; trajectory evals against mocked tools with invariant assertions; simulated multi-turn
conversations; then online A/B and shadow. Push every check as far down the ladder as it will go,
because lower rungs are cheaper and less noisy. And treat the whole thing as a measurement instrument
that itself needs validating, not as a test suite.

**2. Your offline eval says 90% and production disagrees. What happened?**
Almost certainly a distribution shift between the eval population and the real one. Lyft published
exactly this: their simulated users behaved like nice, helpful assistants while real customers send
brief, impatient messages, so strategies like "ask a clarifying question" scored well offline and
collapsed on users who answer clarification with "just fix it". The fix was fine-tuning the simulators
on real customer verbatims. The 90% should also have been suspicious on its own — a saturated metric
has no headroom left to detect anything.

**3. Generalise that failure.**
It is an external-validity failure. An eval score estimates production performance *conditional on* the
eval distribution matching production; break that and the error is systematic, not random, so more
samples do not help. The sharpest version is the correlated-instrument trap: if the simulator, the
judge and the agent share a model family, their blind spots correlate, and a simulator cannot generate
the inputs its own family handles badly. It is the same rule as never monitoring a system with
something inside its failure domain.

**4. How would you have caught it before production?**
Compare distributions rather than means, on cheap surface features: message length, turns to resolution,
typo and slang rate, profanity, intent count per conversation, escalation demands. Two-sample tests, or
embed both corpora and compare. The sharpest single check is to train a classifier to distinguish
simulated from real messages — if it separates them easily on surface features, the simulator is not
simulating. Then track the rank correlation between offline score deltas and online metric deltas across
releases, and treat a decay in that correlation as a P1 on the eval system.

**5. Trajectory or outcome evaluation?**
Both, with different jobs. Outcome is the headline and is cheap to label; trajectory catches right
answers for the wrong reasons — six tool calls where two would do, a write before verification, an
unsafe path that happened to end well. Outcome eval is a black-box health check; trajectory eval is
instrumentation. In practice: outcome as the reported metric, plus a small set of deterministic
trajectory invariants as hard gates, because invariants are cheap and catch the failures that hurt.

**6. How do you gate CI on something non-deterministic?**
Measure the noise floor first by running the unchanged system against the unchanged suite five to ten
times; any threshold tighter than that spread is theatre. Then reduce variance where it is legitimate:
temperature 0, pinned model version, fixed seeds, k repeats on ambiguous cases. Tier the gates —
deterministic smoke tests block every commit, the statistical suite blocks prompt and model changes,
simulated conversations report but do not block. Safety invariants are boolean assertions over the
trace and always block.

**7. What metrics would you put on a customer-support agent?**
Resolution rate paired with false-resolution (came back within N days), because resolution alone is
maximised by an agent that confidently closes everything. Escalation rate, which should be high for the
right cases. Routing accuracy, since it bounds everything downstream. Harmful-action rate, targeted at
zero and alerted rather than averaged. Cost per resolved conversation as a tracked SLO, and p95 latency
with time-to-first-token separately. Every headline metric needs an adversarial twin so that gaming one
degrades the other.

**8. When is shadow evaluation the right tool and when is it not?**
Right when you want real input distribution with zero user risk: router accuracy, tool selection, cost,
latency, error rates on a candidate. Wrong for anything interactive, because the shadow agent's reply
never reaches the user, so the user's next message is a response to the *production* agent — multi-turn
behaviour is simply unmeasurable that way. Same limitation applies to replaying old transcripts, which
is why replay is valid for single-turn evaluation and misleading for conversation evaluation.

**9. How would you set up an experiment for an agent change?** **[Reported at Lyft]** *("How did you measure?" is asked verbatim in the behavioural round)*
Randomise at the conversation or user level, never per turn. Name the primary metric and the guardrails
before starting — harmful-action rate, escalation rate, false-resolution, p95 latency, cost — with
automatic rollback on a guardrail breach. Ramp 1/5/25/50 with observation windows sized to the *slowest*
metric that matters, because repeat-contact and CSAT move over days and the fast metrics are the ones
most easily gamed. Power the test up front so you know what effect size you can even detect.

**10. Your eval numbers have been flat for two quarters while users complain more. What do you do?**
Assume the instrument is broken before assuming the users are wrong. Check the eval-set version history
for silently removed hard cases; check the offline-to-online correlation across recent releases; check
whether the input distribution has moved — new markets, a new client, a new entry point sending
different traffic. Then resample the suite from recent production and re-stratify. A flat metric next
to a moving reality is the signature of a suite that has drifted out of the population it claims to
represent.
