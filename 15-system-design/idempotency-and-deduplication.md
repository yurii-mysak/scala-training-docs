# Idempotency & Deduplication — and why exactly-once is a fiction

> **Priority:** Required
> **Est. time:** 60 min
> **Track:** Server
> **HelloInterview:** System Design in a Hurry → Common Patterns → Multi-step Processes, Dealing with Contention; Key Technologies → Kafka

Reported at Lyft directly — *"idempotency keys and request deduplication"* — and as the design prompt
*"a donation platform with exactly-once payment guarantees"*. It also appears as a follow-up inside
almost every other design: any time you say "we retry", the next question is "and what stops the
duplicate?"

---

## 1 · Vocabulary — get these three apart

| Term | Definition | Where it lives |
|------|------------|----------------|
| **Idempotent** | Applying the operation N times leaves the same state as applying it once | A property of the *operation* |
| **Deduplication** | Detecting and discarding a repeat of a request you have already processed | A mechanism, usually storage-backed |
| **Exactly-once delivery** | Every message is delivered precisely once, no loss, no duplicates | Impossible across a network boundary |
| **Effectively-once** | At-least-once delivery plus an idempotent or deduplicating receiver | What you actually build |

Say "effectively-once" in the interview. It shows you know the difference and immediately signals where
the guarantee actually comes from.

---

## 2 · Why exactly-once is a fiction

The sender sends a request and the response never arrives. It cannot distinguish:

1. The request was lost — the operation never happened.
2. The request succeeded and the *response* was lost — the operation happened once.
3. The server crashed midway — the operation partially happened.

No protocol resolves this ambiguity, because resolving it would require a reliable message, which is
what we lack. This is the **Two Generals problem**. The sender's only choices are:

- **Retry** → at-least-once → possible duplicates.
- **Do not retry** → at-most-once → possible loss.

You choose which failure you can tolerate, and then you **make the receiver tolerant of the one you
chose**. For anything that matters — payments, messages, orders — you choose at-least-once and build an
idempotent receiver.

### 2.1 What about Kafka's exactly-once?

It is real, and it is bounded. Kafka EOS gives you:

- **Idempotent producer:** a producer ID plus a per-partition sequence number lets the broker discard a
  retried duplicate. Deduplication inside the broker, per session, per partition.
- **Transactions:** atomically commit produced records and consumer offsets together, so a
  read-process-write loop does not double-count on rebalance.

**The boundary:** the guarantee ends where Kafka ends. The moment your processor calls an HTTP API,
charges a card, sends an email, or writes to an external database not participating in the transaction,
you are back to at-least-once and you need idempotency at that call. Saying exactly this — "EOS is
exactly-once *within* the read-process-write boundary" — is one of the highest-signal sentences in a
streaming discussion.

Repo: [Delivery Guarantees (QoS), DLQs & HA](../07-messaging-and-streaming/Messaging-delivery_qos_dlq_ha.md) ·
[Kafka Advanced](../07-messaging-and-streaming/Messaging-kafka_advanced.md).

### 2.2 The end-to-end argument

Deduplication must happen where the **effect** is observed. A middlebox that dedupes cannot know
whether the downstream effect landed, so it can only be an optimisation, never the guarantee. In
practice this means: dedupe at the write to the system of record, and, where the user can perceive it,
at the client too.

---

## 3 · The idempotency-key protocol

### 3.1 Who generates the key

**The client.** Only the client knows whether this is a new intent or a retry of a previous one. A
server-generated key is useless: a retried request would get a fresh key and look new.

Corollary worth stating: the key must be generated **before the first attempt** and **reused for every
retry of that intent** — including retries after an app restart, which means it has to be persisted
locally with the pending request.

### 3.2 What a key covers

One **logical intent**, not one HTTP call. "Donate $25 to campaign 7 from card X" is one intent; the
client may send it five times.

| Property | Rule |
|----------|------|
| Scope | Namespaced per endpoint and per authenticated principal: `(user_id, operation, key)`. Otherwise one user's key can collide with another's |
| Format | UUIDv4 or ULID from the client; validate length and charset |
| Placement | `Idempotency-Key` header for HTTP, a dedicated field for gRPC/proto |
| Applies to | Non-idempotent operations: `POST`, and `PATCH` where it is a delta. `PUT`/`DELETE`/`GET` are already idempotent by contract |
| Lifetime | A TTL exceeding the client's maximum retry horizon — see §6 |

### 3.3 The state machine

```
        begin(key, fingerprint)
              │
   ┌──────────┴──────────┐
   │ no row (or expired) │──▶ conditional insert ──▶ IN_PROGRESS ──▶ execute
   └─────────────────────┘                                │
                                              ┌───────────┴───────────┐
                                              │                       │
                                     success: store response    retryable failure:
                                     state = COMPLETED          delete the row
                                              │                (so a retry re-executes)
   ┌─────────────────────┐                    │
   │ row exists          │                    ▼
   │  · COMPLETED, same  │──▶ return the stored response, 200 (a retry must look like success)
   │    fingerprint      │
   │  · COMPLETED, diff  │──▶ 422 Unprocessable — key reuse with different content
   │    fingerprint      │
   │  · IN_PROGRESS      │──▶ 409 Conflict + Retry-After (a concurrent duplicate)
   └─────────────────────┘
```

### 3.4 The three details most candidates miss

1. **The request fingerprint.** Store a hash of the canonicalised request body alongside the key. Same
   key + different body is a client bug or an attack, not a retry — reject it with 422 rather than
   silently applying either version. Without this, an idempotency key is a way to *lose* a request.
2. **Concurrency.** Two retries can arrive simultaneously. `SELECT` then `INSERT` is a race; the
   guarantee must be a **conditional write** — a unique index, `INSERT ... ON CONFLICT DO NOTHING`, or
   DynamoDB's `attribute_not_exists`. The second request loses the race and gets 409, and 409 is the
   correct answer: the caller retries and then gets the stored response.
3. **Storing the response.** A retry after completion must return the *original* response — the same
   IDs, the same amounts. Returning a fresh 201 with a new ID means the client now believes two things
   happened. Persist the status code and body with the key.

---

## 4 · Implementing the store

### 4.1 Postgres

```sql
CREATE TABLE idempotency_keys (
  scope           text        NOT NULL,          -- user_id + operation
  key             text        NOT NULL,
  fingerprint     bytea       NOT NULL,          -- sha256 of the canonical request
  state           text        NOT NULL,          -- IN_PROGRESS | COMPLETED
  response_status int,
  response_body   jsonb,
  created_at      timestamptz NOT NULL DEFAULT now(),
  expires_at      timestamptz NOT NULL,
  PRIMARY KEY (scope, key)
);
-- claim: whoever wins the insert executes; everyone else reads the row
INSERT INTO idempotency_keys (scope, key, fingerprint, state, expires_at)
VALUES ($1, $2, $3, 'IN_PROGRESS', now() + interval '24 hours')
ON CONFLICT (scope, key) DO NOTHING;
```

### 4.2 DynamoDB

```
PutItem  Item = {pk: "IDEMP#<scope>", sk: "KEY#<key>", fingerprint, state, ttl}
         ConditionExpression = "attribute_not_exists(sk)"
         # ConditionalCheckFailedException => someone else owns it: read and branch
```

Per-item TTL removes the cleanup job entirely. See
[DynamoDB Refresher](../06-databases-and-distributed-data/dynamodb_refresher.md).

### 4.3 The better option when it exists: a natural business key

If the operation has a natural unique identity — one vote per user per poll, one message per
`(conversation_id, client_msg_id)`, one settlement per `(provider_id, provider_txn_id)` — then a
**unique constraint on that key is strictly better** than a separate idempotency table:

- It cannot drift out of sync with the data it protects.
- It survives TTL expiry of the idempotency record.
- It enforces the invariant even for writers who forget to send a key.

Say this. Reaching for a generic idempotency table when the domain already offers a uniqueness
invariant is a design smell, and noticing it is a Staff-level observation.

---

## 5 · Redis as a dedupe cache — and its trap

`SET key value NX EX 86400` is the fast path, and it is a legitimate first-line filter. But Redis is not
durable enough to be the *guarantee*:

- A failover can lose recent writes (asynchronous replication), so a key can vanish and a duplicate
  slip through.
- Eviction under memory pressure can drop keys silently unless the instance is configured `noeviction`.

**Use Redis as a fast-path filter in front of a durable check, never as the only check** — the same
two-tier pattern as the crawler's bloom filter plus exact store
([distributed-web-crawler.md §6.2](distributed-web-crawler.md)). If money is involved, the durable check
is mandatory.

---

## 6 · Dedup windows — how long to keep keys

Keys cannot be kept forever: the table grows without bound and the index degrades. Size the window
from the actual retry horizon:

| Source of a late duplicate | Typical horizon |
|----------------------------|-----------------|
| Client retry with backoff | Seconds to minutes |
| Mobile client retrying after coming back online | Hours |
| Queue redelivery / consumer restart | Minutes to hours |
| Operator replaying a DLQ | Hours to days |
| Backfill or disaster-recovery replay | Days |

| Window | Risk |
|--------|------|
| 1 hour | A phone that was offline overnight duplicates the request |
| **24 hours** | **The common default; covers client retries and most operational replays** |
| 7–30 days | Covers manual replays; costs storage and index size |
| Forever | Unbounded growth; only justified for a natural business key, which you would keep anyway |

**Say the failure explicitly:** "After the window expires, a replayed request is indistinguishable from
a new one. For a donation that means a possible double charge, so for money I keep the *business* key
— `(campaign_id, donor_id, provider_txn_id)` — unique forever, and treat the 24-hour idempotency table
as the fast path, not the guarantee." That sentence is the whole section.

---

## 7 · Making the downstream effects idempotent

The idempotency key protects **your** endpoint. It does nothing for what your handler does next. This is
where real systems break.

| Effect | How to make it idempotent |
|--------|---------------------------|
| Write to your own DB | Unique constraint on the business key; upsert rather than insert |
| Call a payment provider | Pass **your** idempotency key through to the provider (Stripe, Adyen, and Braintree all accept one); derive it deterministically from your own key so a retry reuses it |
| Publish an event | Deterministic event ID; consumers dedupe on it. Use the **outbox pattern** so the event and the state change commit together |
| Send an email or push | Dedupe key `(template, recipient, entity_id)` stored before sending; accept that at-most-once is sometimes the right choice for notifications |
| Increment a counter | Do not. `INCREMENT` is not idempotent; write an event row and aggregate, or use `SET absolute_value` |
| Update a balance | Append a ledger entry with a unique key and derive the balance, rather than mutating a number |

### 7.1 Idempotent by construction

The strongest move is to design operations that are naturally idempotent, so no bookkeeping is needed:

| Not idempotent | Idempotent equivalent |
|----------------|-----------------------|
| `balance += 25` | `INSERT ledger_entry(id=<deterministic>, amount=25)`, balance = sum |
| `status = next_state()` | `UPDATE ... SET status='PAID' WHERE status='PENDING'` — a conditional transition that is a no-op the second time |
| `append_to_list(x)` | `add_to_set(x)` |
| "send the message" | "ensure a message with this ID exists" |

Absolute assignments and set semantics are idempotent; deltas and appends are not. That one line is
worth memorising.

### 7.2 The outbox pattern

The classic failure: you commit a database transaction, then publish an event, then crash between the
two — the state changed and nobody was told. Or you publish first and the transaction rolls back — you
told everyone about something that did not happen.

**Fix:** write the event into an `outbox` table *inside the same transaction* as the state change, and
have a separate relay publish rows from the outbox and mark them sent. The relay is at-least-once, so
consumers dedupe on the event ID. Change data capture (DynamoDB Streams, Postgres logical decoding,
Debezium) is the managed version of the same idea.

Repo: [Event Sourcing & CQRS, Sagas](event_sourcing_cqrs_sagas_guide.md) ·
[Event Sourcing — In-Depth Guide](../06-databases-and-distributed-data/Event-Sourcing-Guide.md) ·
[Distributed Transactions](../06-databases-and-distributed-data/Distributed_Transactions.md).

**Why event sourcing makes this easier:** events are append-only and carry their own IDs, so replay is
inherently deduplicable, and the state is a fold over the event log rather than a mutable cell that can
be double-applied. The cost is projection lag and schema evolution — see the guides above.

---

## 8 · The donation platform: never lost, never duplicated, never the wrong amount

The reported prompt. Three requirements, three different mechanisms — say that up front, because
treating them as one problem is the mistake the question is designed to catch.

| Requirement | Mechanism | Failure it prevents |
|-------------|-----------|---------------------|
| Never **lost** | Durable intent recorded *before* the external call, plus reconciliation | A crash after charging the card and before recording it |
| Never **duplicated** | Idempotency key propagated to the provider, plus a unique business key in the ledger | A retry charging twice |
| Never the **wrong amount** | Integer minor units, amount inside the fingerprint, double-entry invariant, reconciliation against settlement | Float rounding, currency confusion, mutation after the fact |

### 8.1 Money representation — the "wrong amount" requirement is mostly this

- **Integer minor units only.** `2500` cents, never `25.00` as a float. `0.1 + 0.2 != 0.3` in binary
  floating point, and a fraction of a cent per transaction becomes a reconciliation nightmare.
- **Currency travels with the amount.** `{amount_minor: 2500, currency: "USD"}` as one value object.
  Never add two amounts without checking currency equality.
- **Minor-unit exponent is not always 2.** JPY has 0, KWD has 3. Store the exponent or derive it from a
  currency table; do not hardcode "divide by 100".
- **Rounding is a policy, decided once and written down** (split fees, FX conversion), and the residual
  cent must go somewhere explicit rather than vanishing.
- **The amount is part of the idempotency fingerprint**, so the same key with a different amount is
  rejected rather than silently applying one of them.

### 8.2 The flow

```
1. POST /donations  Idempotency-Key: K   {campaign, amount_minor, currency, payment_method}
2. Conditional insert of the idempotency row (claim K)                      -- §3
3. Write donation intent, state=PENDING, in the same transaction            -- durability
   + outbox row                                                             -- §7.2
4. Call the PSP with idempotency key derived deterministically from K
5. On success: append ledger entries (double entry), state=CAPTURED,
   store the response against K, emit donation.captured                     -- one transaction
6. On timeout/unknown: leave PENDING. A reconciler queries the PSP by the
   same idempotency key and resolves the true outcome                       -- never guess
7. Nightly: reconcile the ledger against the PSP settlement report
```

**Step 3 before step 4 is the entire "never lost" guarantee.** If you call the provider first and crash,
you have charged a card with no record of it, and the only recovery is a manual reconciliation against
a settlement file. If you record the intent first and crash, you have a `PENDING` row that a reconciler
can resolve deterministically by asking the PSP about that idempotency key.

### 8.3 The ledger

Double-entry, append-only, immutable:

```
ledger_entries
  entry_id        uuid PK
  txn_id          uuid              -- groups the debit and the credit
  account_id      text              -- 'donor:123', 'campaign:7', 'fees:stripe', 'cash:bank'
  direction       enum(DEBIT, CREDIT)
  amount_minor    bigint
  currency        char(3)
  donation_id     uuid              -- UNIQUE per (donation_id, account_id, direction)
  created_at      timestamptz
```

- **Invariant:** for every `txn_id`, `sum(debits) == sum(credits)`. A continuous auditor asserts this;
  a violation pages someone. This is the check that catches "wrong amount" bugs that every other layer
  missed.
- **Never update or delete an entry.** A refund is a *new*, compensating pair of entries. Corrections
  are new entries. The log is the truth, and balances are a fold over it — the same principle as event
  sourcing.
- **Uniqueness on `(donation_id, account_id, direction)`** makes the ledger write itself idempotent, so
  a retried step 5 is a no-op rather than a double credit.

### 8.4 Failure matrix — walk this table out loud

| Crash point | State on disk | Money moved? | Recovery |
|-------------|---------------|--------------|----------|
| Before step 2 | Nothing | No | Client retries with K; treated as new |
| After 2, before 3 | `IN_PROGRESS` key only | No | Reaper deletes stale `IN_PROGRESS` rows past a timeout; client retry re-executes |
| After 3, before 4 | Intent `PENDING` | No | Reconciler asks the PSP about K, finds nothing, cancels or retries |
| **After 4, before 5** | Intent `PENDING` | **Yes** | **The dangerous one.** Reconciler queries the PSP by K, finds the charge, completes the ledger write. This is why the intent must exist before the call |
| After 5, before response | `CAPTURED` | Yes | Client retries K, gets the stored response — no second charge |
| Response lost in transit | `CAPTURED` | Yes | Same as above; the retry is indistinguishable from the original |
| Duplicate webhook from PSP | `CAPTURED` | Yes | Webhook handler dedupes on `provider_event_id`; a no-op |

### 8.5 Reconciliation is not optional

Idempotency prevents duplicates *you* cause. Reconciliation catches everything else: provider-side
retries, partial settlements, chargebacks, currency conversion differences, and your own bugs.

- Daily: pull the settlement report, match every provider transaction to a ledger entry, and alert on
  anything unmatched in either direction.
- Track two counters — donations recorded but not settled, and settlements with no donation — and treat
  a non-zero value older than the settlement window as a page.
- Say plainly: **"a payment system without reconciliation is a payment system that has undetected bugs."**

Repo: [Payments Interview Prep](payments_interview_prep_expanded.md).

---

## 9 · Consumer-side deduplication (queues and streams)

| Approach | How | Trade-off |
|----------|-----|-----------|
| Dedupe table keyed by message ID | Conditional insert before processing | Durable, exact; costs a write per message |
| Idempotent write | The processing itself is an upsert on a business key | Free; only possible if the effect is naturally idempotent |
| Bloom filter / rolling set | Probabilistic membership over a window | Cheap; false positives *drop* messages — usually unacceptable |
| Kafka transactions | Offsets and output committed atomically | Only within Kafka |
| Sequence-number watermark | Track the highest processed sequence per partition; discard anything below | Exact, O(1) state — the best option when the source assigns dense sequences |

**Ordering matters for the last one:** watermark dedupe is only correct if delivery is ordered per key.
Kafka gives per-partition ordering, so partition by the key you are deduping on.

Repo: [Point-to-Point vs Pub/Sub](../07-messaging-and-streaming/Messaging-point_to_point_pubsub.md) ·
[Messaging Fundamentals](../07-messaging-and-streaming/Messaging-Fundamentals.md).

---

## 10 · Code: an idempotency-key store

Stdlib-only, Python 3.10-compatible, models exactly the §3.3 state machine.

```python
import hashlib
from dataclasses import dataclass


class FingerprintMismatch(Exception):
    """Same idempotency key replayed with a different request body."""


class ConflictInProgress(Exception):
    """A concurrent request holds this key; the caller should retry later."""


@dataclass
class _Record:
    fingerprint: str
    state: str                 # "IN_PROGRESS" | "COMPLETED"
    response: object = None
    expires_at: float = 0.0


class IdempotencyStore:
    """In-memory model of a conditional-write idempotency table.

    Real deployment: DynamoDB PutItem with attribute_not_exists(pk), or
    Postgres INSERT ... ON CONFLICT DO NOTHING against a unique index, plus
    a TTL column. The state machine is what matters, not the engine.
    """

    def __init__(self, ttl: float = 24 * 3600) -> None:
        self.ttl = ttl
        self._rows: dict[str, _Record] = {}

    @staticmethod
    def fingerprint(body: bytes) -> str:
        return hashlib.sha256(body).hexdigest()

    def begin(self, key: str, body: bytes, now: float) -> tuple[str, object]:
        """Claim the key. Returns ("NEW", None) or ("REPLAY", stored_response)."""
        rec = self._rows.get(key)
        if rec is not None and rec.expires_at <= now:
            rec = None                                   # expired, treat as fresh
        fp = self.fingerprint(body)
        if rec is None:
            self._rows[key] = _Record(fp, "IN_PROGRESS", None, now + self.ttl)
            return ("NEW", None)
        if rec.fingerprint != fp:
            raise FingerprintMismatch(key)               # -> HTTP 422
        if rec.state == "IN_PROGRESS":
            raise ConflictInProgress(key)                # -> HTTP 409 + Retry-After
        return ("REPLAY", rec.response)

    def complete(self, key: str, response: object, now: float) -> None:
        rec = self._rows[key]
        rec.state, rec.response, rec.expires_at = "COMPLETED", response, now + self.ttl

    def abandon(self, key: str) -> None:
        """Handler failed with a retryable error: release the claim."""
        rec = self._rows.get(key)
        if rec is not None and rec.state == "IN_PROGRESS":
            del self._rows[key]
```

```python
import unittest


class TestIdempotencyStore(unittest.TestCase):
    def setUp(self):
        self.store = IdempotencyStore(ttl=100)
        self.body = b'{"amount_minor":2500,"currency":"USD"}'

    def test_first_call_is_new_then_replay(self):
        self.assertEqual(self.store.begin("k1", self.body, now=0), ("NEW", None))
        self.store.complete("k1", {"donation_id": "d1"}, now=1)
        self.assertEqual(self.store.begin("k1", self.body, now=2),
                         ("REPLAY", {"donation_id": "d1"}))

    def test_same_key_different_amount_rejected(self):
        self.store.begin("k1", self.body, now=0)
        self.store.complete("k1", {"donation_id": "d1"}, now=1)
        with self.assertRaises(FingerprintMismatch):
            self.store.begin("k1", b'{"amount_minor":9900,"currency":"USD"}', now=2)

    def test_concurrent_request_conflicts(self):
        self.store.begin("k1", self.body, now=0)
        with self.assertRaises(ConflictInProgress):
            self.store.begin("k1", self.body, now=0)

    def test_abandon_allows_retry(self):
        self.store.begin("k1", self.body, now=0)
        self.store.abandon("k1")
        self.assertEqual(self.store.begin("k1", self.body, now=1), ("NEW", None))

    def test_expired_key_is_fresh_again(self):
        self.store.begin("k1", self.body, now=0)
        self.store.complete("k1", {"donation_id": "d1"}, now=1)
        self.assertEqual(self.store.begin("k1", self.body, now=200), ("NEW", None))
```

Note what the last test asserts: **after the window, a replay is indistinguishable from a new request.**
That is not a bug in the code, it is the honest consequence of a finite window, and the test documents
it. Writing a test that pins down a known limitation is a strong code-quality signal.

**Two things to say while writing this in an interview:**

- `begin` must be a single conditional write in production; the in-memory `dict.get` then `dict[key] =`
  is a race that a real store closes with `ON CONFLICT DO NOTHING` or `attribute_not_exists`.
- `abandon` is what stops a transient failure from wedging the key until TTL. It must only run for
  *retryable* failures — after a non-retryable failure, keeping the record and returning the stored
  error is correct.

---

## 11 · Testing idempotency

| Property | Test |
|----------|------|
| Applying twice equals applying once | Property test: run the handler, snapshot state, run again with the same key, assert identical state |
| Concurrent duplicates | Fire N parallel requests with the same key; assert exactly one effect and N consistent responses |
| Crash between steps | Deterministic fault injection at each step of §8.2; assert the failure matrix |
| Duplicate delivery | Chaos mode that duplicates every queue message; the system must be indistinguishable |
| Window expiry | Time-travel the clock past the TTL and assert the documented behaviour, whatever it is |
| Ledger invariant | Continuous assertion that debits equal credits per transaction |

Repo: [Property-Based Testing](../12-testing/Testing-property_based.md) ·
[Unit Testing](../12-testing/Testing-unit_testing.md).

---

## Interview questions

**1. What is an idempotency key and how does it work?** **[Reported at Lyft]**
A client-generated identifier for one logical intent, sent with every retry of that intent. The server
claims it with a conditional write, executes, stores the response against it, and returns that stored
response on any replay. The three parts people forget are the request fingerprint so key reuse with a
different body is rejected, the in-progress state so concurrent duplicates get a 409 instead of
double-executing, and storing the response so a retry returns the original IDs.

**2. Design a donation platform where payments are never lost, duplicated, or recorded with the wrong
amount.** **[Reported at Lyft]**
Three requirements, three mechanisms. Never lost: write the donation intent durably before calling the
payment provider, so a crash leaves a PENDING row a reconciler can resolve by querying the provider
with the same key. Never duplicated: propagate the idempotency key to the provider and put a unique
constraint on the business key in an append-only double-entry ledger. Never the wrong amount: integer
minor units with the currency attached, the amount inside the idempotency fingerprint, a
debits-equal-credits invariant asserted continuously, and daily reconciliation against the settlement
report.

**3. Is exactly-once delivery possible?** **[Reported at Lyft]**
No, not across a network boundary — the sender cannot distinguish a lost request from a lost response,
which is the Two Generals problem. What is achievable is at-least-once delivery plus an idempotent
receiver, which produces effectively-once. Kafka's exactly-once is genuine but scoped to its own
read-process-write cycle; as soon as an effect leaves that boundary you need idempotency again.

**4. How long do you keep idempotency keys?**
Long enough to cover the longest realistic retry: client backoff is seconds, a mobile client returning
from offline is hours, an operator replaying a dead-letter queue is days. Twenty-four hours is the
common default. After the window, a replay is indistinguishable from a new request, so for money I keep
a permanent unique constraint on the natural business key and treat the idempotency table as the fast
path rather than the guarantee.

**5. Two identical requests arrive simultaneously. What happens?**
They race on the conditional insert. One wins and executes; the other sees an IN_PROGRESS row and gets
409 with a Retry-After, then retries and receives the stored response. The critical detail is that the
claim must be a single conditional write — a read followed by a write is a race, and under retry storms
that race fires often enough to double-charge.

**6. The same key arrives with a different request body. What do you return?**
422. That is not a retry, it is either a client bug reusing keys or an attack, and silently applying
either version would be worse than rejecting. This is why the stored record holds a hash of the
canonicalised request, not just the key.

**7. Your handler succeeds but the response is lost. What does the client see?**
It retries with the same key, hits the COMPLETED record, and gets the original response — same donation
ID, same amount, HTTP 200. From the client's perspective a retry is indistinguishable from the first
call succeeding, which is the entire point of storing the response rather than just the fact of
completion.

**8. How do you make the downstream effects idempotent, not just your endpoint?**
By pushing the key outward: pass a deterministically derived idempotency key to the payment provider,
use deterministic event IDs so consumers can dedupe, and prefer operations that are idempotent by
construction — absolute assignments and set insertions rather than increments and appends. For the
database, a unique constraint on the business key rather than application-level checking.

**9. Why is Redis alone not enough for deduplication?**
Because a failover can lose recent asynchronously replicated writes and eviction can drop keys under
memory pressure, so a duplicate can slip through exactly when the system is already stressed. Redis is
a good fast-path filter in front of a durable check, which is the same two-tier pattern as a bloom
filter in front of an exact store, but it cannot be the guarantee for anything involving money.

**10. How does event sourcing help here?**
Events are append-only and carry their own identifiers, so replay is naturally deduplicable and state is
a fold over the log rather than a mutable cell that can be double-applied. Combined with an outbox
written in the same transaction as the state change, it removes the classic crash-between-commit-and-
publish gap. The costs are projection lag and event schema evolution.

**11. How would you test that a system is genuinely idempotent?**
Property-based: apply an operation, snapshot the state, apply the identical request again, and assert
the state is byte-identical — including the response. Then fault injection at each step of the write
path against a documented failure matrix, and a chaos mode that duplicates every queue message so that
the duplicated run must be indistinguishable from the clean one.
