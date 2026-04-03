
# Event Sourcing — In‑Depth Guide (CQRS + Functional Decider)

![CQRS overview](https://www.kurrent.io/static/fbc8b4a46c3066d8c3c7e17ffb88b9b4/30125/cqrs.png)

> Source: kurrent.io/event-sourcing citeturn0search0

---

## 1 · Why Event Sourcing?

* **Audit trail** – every change is an immutable event.
* **Time‑travel** – rebuild state at *t* for debugging or ML back‑fill.
* **Reactive streaming** – projections update in real‑time.
* **Decoupled models** – write model focuses on invariants; read model optimised for queries.citeturn0search0turn0search6

---

## 2 · Key Vocabulary

| Term | Meaning |
|------|---------|
| **Command** | Intent to change state — imperative, may be rejected. |
| **Event** | Fact that *something happened*; immutable. |
| **Aggregate** | Consistency boundary handling commands & emitting events. |
| **Projection** | Read‑side view built by folding events. |
| **Snapshot** | Periodic aggregate state checkpoint to shorten replay. |

---

## 3 · Functional Decider Pattern

![Decider Apply](https://thinkbeforecoding.com/public/FreshPaint-21-2014.01.04-10.55.10.png)

> Diagram by Jérémie Chassaing citeturn5view0

```scala
trait Decider[Cmd, Ev, S]:
  def decide(cmd: Cmd)(state: S): Either[Rejection, List[Ev]]
  def evolve(state: S, event: Ev): S
  val zero: S
```

### Workflow
1. **Load** event stream → fold with `evolve` into state `S`.
2. **decide** executes domain rules and returns new events or `Rejection`.
3. **Append** events atomically; publish to bus.
4. **Fold** new events into state or write a **snapshot** for fast future loads.

*Pure & deterministic*: side‑effects happen only at the application boundary.citeturn0search1

---

## 4 · Schema Evolution Strategies

* **Up‑cast** – convert old event to new schema on deserialisation.
* **Versioned event names** – `UserRegisteredV2`.
* **Translating projector** – legacy stream ➜ new read model.
* Never rewrite the log—append‑only ethic preserves audit.citeturn0search10

---

## 5 · Snapshots

Store `(lastSeqNr, state)` every *N* events or on schedule to cap load time on long‑lived aggregates.

---

## 6 · Projections (CQRS Read Models)

```
Events ─┬─▶ Postgres  (reports)
        ├─▶ Elastic   (search)
        └─▶ Redis     (low latency)
```

Projectors are idempotent; each maintains its own offset cursor.

---

## 7 · When (Not) to Use

| Good fit | Poor fit |
|----------|----------|
| Domain rich in behaviour & invariants | Simple CRUD admin apps |
| Mandatory audit & compliance | Small DB, no replay need |
| Many integrations need change feed | High write volume on single entity |

---

## 8 · Common Pitfalls & Fixes

| Pitfall | Fix |
|---------|-----|
| Hot aggregate stream | Partition by sub‑id; sharding |
| Projections lag behind | Emit update events or use synchronous handler for critical read |
| Event schema churn | Favour business‑fact naming, keep JSON flat |

---

## Further Reading

* Kurrent “Beginner’s Guide to Event Sourcing”citeturn0search8  
* Chassaing – *Functional Event Sourcing Decider* (2021) citeturn0search1  
* Event Modeling methodology (eventmodeling.org)
