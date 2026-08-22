# RAG and Retrieval

> **Priority:** Recommended
> **Est. time:** 40 min
> **Track:** Server
> **HelloInterview:** System Design in a Hurry → Advanced → Vector Databases

Background, not the main event. A support agent needs policy documents, help-centre articles and past
resolutions in its context, and getting the right ones in front of the model is a search problem, not
a model problem. Keep the file tight and hold one opinion firmly: **retrieval quality dominates
generation quality.** A strong model with the wrong three documents produces a fluent wrong answer.
A weak model with the right three documents usually produces a usable one.

---

## 1 · The pipeline

```
documents ──▶ chunk ──▶ embed ──▶ index
                                    │
query ──▶ (rewrite) ──▶ embed ──────┤
          └─────────▶ keyword ──────┤
                                    ▼
                            candidate set (k ≈ 50)
                                    │
                                 rerank
                                    │
                            top n (n ≈ 3-8) ──▶ context ──▶ model
```

Two-stage by design: a cheap high-recall retrieval followed by an expensive high-precision rerank.
The same shape as any search stack — candidate generation then ranking — and for the same reason: you
cannot afford the precise scorer over the whole corpus.

---

## 2 · Chunking

The most under-rated knob. A chunk is the unit of retrieval, so it must be simultaneously small enough
to be specific and large enough to be self-contained.

| Strategy | Notes |
|---|---|
| Fixed size with overlap (e.g. 500 tokens, 50 overlap) | The baseline. Overlap stops facts being split across a boundary |
| Structural (by heading, section, article) | Better for help-centre content, which is already written in retrievable units. Usually the right answer for support |
| Semantic (split where the topic shifts) | Marginal gains, real complexity |
| Sentence windows | Retrieve on the sentence, return the surrounding paragraph. Good precision-with-context trade |

Practical rules:

* **Preserve context in the chunk.** A chunk reading "This does not apply to scheduled rides" is
  useless without the section title. Prepend document title and heading path to every chunk.
* **Keep tables and lists intact.** Splitting a fee table across chunks reliably produces wrong answers.
* **Store metadata**: source, section, last-updated, locale, audience (rider/driver), policy-effective
  date. Metadata filters do more for real-world quality than embedding-model choice.
* **Stale content is the top production failure.** An answer citing a superseded policy is worse than
  no answer. Retrieval needs a freshness story — a `valid_until` filter, a re-index pipeline, and an
  alert when the index falls behind the source of truth.

---

## 3 · Embeddings and vector stores

* An embedding maps text to a vector; similarity is cosine distance. That is the whole idea.
* **Dimensionality** trades quality against index size and query latency. Larger is not automatically
  better for a specific corpus.
* **Model choice matters less than people expect** relative to chunking and reranking. Do not spend a
  week on it before you have measured retrieval quality.
* **Re-embedding on model change is a migration**, not a config edit: the whole corpus must be
  re-embedded, and mixed-model vectors in one index are meaningless. Plan for a dual-write and cutover.

| Index | Property |
|---|---|
| Flat / brute force | Exact, fine to millions of vectors if latency allows. Start here |
| **HNSW** | Graph-based ANN. Fast, high recall, memory-hungry. The default |
| **IVF** | Cluster-then-search. Lower memory, tunable `nprobe` for recall/latency |
| Product quantisation | Compresses vectors; trades recall for memory |

ANN means **approximate**: you accept a recall below 1.0 for latency. That is a tuning parameter with a
correctness consequence, and it should appear in the retrieval eval, not just in a latency dashboard.

**Do you need a dedicated vector database?** Often not. A vector index in PostgreSQL or Elasticsearch is
one fewer system to run, and at corpus sizes typical of a help centre (thousands to hundreds of
thousands of chunks) it is entirely adequate. Reach for a specialised store when scale, filtered-search
performance or index-update rate actually demands it. See
[Elasticsearch basics](../06-databases-and-distributed-data/Elasticsearch_Basics.md).

---

## 4 · Hybrid search

Dense embeddings capture meaning; sparse keyword search (BM25) captures exact tokens. They fail in
opposite directions, which is why combining them is a reliable win rather than a fashion.

* Dense misses: product names, error codes, ride ids, rare acronyms, exact policy names.
* Sparse misses: paraphrase, synonyms, questions worded nothing like the document.

Combine with **Reciprocal Rank Fusion** — rank-based, so it needs no score normalisation between two
systems whose scores are not comparable:

```
score(d) = sum over retrievers of  1 / (k + rank_r(d)),   k ≈ 60
```

Also worth having: **metadata pre-filtering** (locale, audience, effective date) before the vector
search, and **query rewriting** — expanding "it charged me twice" into the terms the corpus actually
uses. In a multi-turn conversation, rewriting the query to be self-contained ("my refund" → "refund for
ride on 12 March") is often the single largest retrieval quality win available, because the raw last
message is frequently not searchable on its own.

---

## 5 · Reranking

A cross-encoder scores the query and each candidate *together*, rather than comparing two independently
computed vectors. Far more accurate, far more expensive — hence its position as stage two over ~50
candidates rather than the corpus.

* Typically the biggest single quality jump in the pipeline after fixing chunking.
* Adds latency (tens to low hundreds of milliseconds); budget it.
* An LLM can rerank, and it is expensive; a purpose-built cross-encoder is usually the better trade.

---

## 6 · Evaluating retrieval

**Build the retrieval eval before the generation eval.** If retrieval recall is 60%, no prompt work
will fix the answers, and you will waste weeks discovering that.

| Metric | Meaning |
|---|---|
| **Recall@k** | Is the right document in the top k? The number that matters most — generation cannot recover what retrieval missed |
| **Precision@k** | How much of the context is noise? Noise costs tokens and distracts |
| **MRR / nDCG** | Is the right document near the top? Position matters: models attend unevenly across a long context |
| **Context relevance** | Judged: does the retrieved set actually support answering? |
| **Faithfulness / groundedness** | Judged: is the answer supported by the retrieved text, or invented? |
| **Answer relevance** | Judged: does it address the question asked? |

The last three are judge-scored — [llm-as-judge.md](llm-as-judge.md). The first three need labelled
query-document pairs, which you can bootstrap by generating questions from documents (cheap, and
biased toward questions the document answers well) and then correcting with real queries from
production logs. Real queries are the ones that count.

**Faithfulness and recall are different failures with different fixes.** An unfaithful answer over
correct documents is a prompting problem. A faithful answer over wrong documents is a retrieval
problem. Diagnose which before changing anything.

---

## 7 · Agentic retrieval versus one-shot RAG

| | One-shot RAG | Agentic retrieval |
|---|---|---|
| Shape | Retrieve once, generate | Model decides whether and what to search, possibly several times |
| Latency | One extra call | Unbounded without a budget |
| Quality on simple lookups | Equal | Equal, at higher cost |
| Quality on multi-hop questions | Poor | Much better |
| Debuggability | Easy | Needs trajectory tracing |

Default to one-shot; make retrieval a tool when questions genuinely need several hops or when most
turns need no retrieval at all (searching unconditionally wastes tokens and injects noise). This is the
same "is an agent the right answer" judgement as
[agent-architectures.md](agent-architectures.md#6--when-an-agent-is-the-wrong-answer), scoped to search.

---

## 8 · Failure modes

| Failure | Symptom | Fix |
|---|---|---|
| Chunk too small | Retrieved text lacks the qualifier that changes the answer | Larger chunks, overlap, prepend heading path |
| Chunk too large | Right document, wrong section, diluted embedding | Structural chunking, sentence windows |
| Stale index | Confidently cites superseded policy | Freshness filter, re-index pipeline, staleness alert |
| No metadata filter | Driver policy answered to a rider | Filter on audience and locale before search |
| Dense-only | Misses exact codes and product names | Hybrid with BM25 |
| Too many chunks in context | Cost up, quality down, key fact buried mid-context | Rerank and cut to 3-8 |
| Missing document | Fluent, wrong, confident answer | Recall@k monitoring; and an explicit "I could not find this" path |
| No abstention | Answers anyway | Instruct and evaluate refusal; a support agent that escalates is behaving correctly |

That last row is the one worth arguing for: **a retrieval system needs a defined behaviour for "not
found".** Escalating to a human is a correct outcome, and it must be evaluated as one rather than
counted as a failure.

---

## 9 · Cross-references

* [Elasticsearch basics](../06-databases-and-distributed-data/Elasticsearch_Basics.md) — the sparse half.
* [Indexing and optimisation](../06-databases-and-distributed-data/Indexing_Optim.md).
* [evaluating-agents.md](evaluating-agents.md) — retrieval eval is a rung on the same ladder.
* [production-llmops.md](production-llmops.md) — embedding caches, index freshness, latency budget.

---

## Interview questions

**1. Why does retrieval quality dominate generation quality?**
Because the model can only reason over what it is given. A strong model with the wrong documents
produces a fluent, confident, wrong answer — the worst failure mode, since it is not obviously broken.
A weaker model with the right documents usually produces something usable. So retrieval recall is the
ceiling on system quality, and it is the first thing to measure and the first thing to fix.

**2. How would you chunk a help centre for a support agent?**
Structurally, by article and section, because that content is already written in retrievable units.
Prepend the document title and heading path to each chunk so a fragment like "this does not apply to
scheduled rides" is interpretable on its own. Keep tables and fee lists intact. Attach metadata —
audience, locale, effective date — because filtering on those does more for real quality than the
choice of embedding model.

**3. Why hybrid search rather than just embeddings?**
They fail in opposite directions. Dense retrieval misses exact tokens: product names, error codes, ride
ids, rare acronyms. Sparse BM25 misses paraphrase and synonyms. Fusing them with Reciprocal Rank Fusion
works on ranks rather than scores, so you do not have to normalise between two systems whose scores are
not comparable. It is a consistent win rather than a marginal one.

**4. What is a reranker and where does it go?**
A cross-encoder that scores query and candidate together instead of comparing independently computed
vectors — much more accurate, much more expensive. So it goes in stage two: retrieve ~50 candidates
cheaply with high recall, rerank to the top 3-8 with high precision. Same candidate-generation-then-
ranking shape as any search stack, for the same reason: you cannot run the precise scorer over the
whole corpus.

**5. How do you evaluate retrieval separately from generation?**
Recall@k and nDCG over labelled query-document pairs, built from production queries rather than only
from questions generated off the documents, which are biased toward what the documents answer well.
Then judge-scored context relevance, faithfulness and answer relevance. Separating them matters because
an unfaithful answer over correct documents is a prompting problem while a faithful answer over wrong
documents is a retrieval problem, and the fixes are unrelated.

**6. When would you make retrieval a tool instead of always retrieving?**
When many turns need no retrieval at all — searching unconditionally wastes tokens and injects noise
that can degrade the answer — or when questions need several hops and the second query depends on what
the first returned. The cost is an unbounded number of searches without a budget, and a trajectory you
now have to trace to debug. Default to one-shot retrieval and promote to a tool when the multi-hop case
is real.

**7. Your agent cites an outdated policy. What went wrong and how do you prevent it?**
The index is stale relative to the source of truth, or the chunk lacks an effective-date filter.
Prevention is a pipeline concern, not a model concern: re-index on document change, carry validity
dates as metadata and filter on them at query time, and alert when index lag exceeds a threshold. It is
worth treating index freshness as an SLO, because a confidently-cited superseded policy is worse for a
support org than no answer at all.
