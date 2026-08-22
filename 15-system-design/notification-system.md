# Multi-Channel Notification System — full worked design

> **Priority:** Recommended
> **Est. time:** 50 min
> **Track:** Server
> **HelloInterview:** System Design in a Hurry → Common Patterns → Real-time Updates, Multi-step Processes; Key Technologies → Kafka

A classic design, and a good vehicle for showing that the "exactly-once is a fiction" argument from
[idempotency-and-deduplication.md](idempotency-and-deduplication.md) is not a chat-specific fact but a
general property of delivering an effect across a network boundary — this file applies the identical
argument to push, email, and SMS, and shows where the *mechanics* of at-least-once delivery differ by
channel even though the guarantee does not.

---

## 1 · Frame the problem in one sentence

> "A service that turns an internal event into a rendered, preference-filtered notification, delivers it
> across one or more channels at least once, tracks what happened per channel, and never lets one
> channel's slow provider hold up the others."

---

## 2 · Requirements and scoping

### 2.1 Functional

| # | Requirement |
|---|-------------|
| F1 | Accept a notification trigger (an internal event or an explicit request) and render it from a template |
| F2 | Respect per-user, per-category channel preferences |
| F3 | Fan out across push, email, SMS, and in-app, independently per channel |
| F4 | Suppress duplicates and collapse rapid-fire near-duplicates into one send |
| F5 | Respect quiet hours, with a short, explicit override list for time-critical categories |
| F6 | Track delivery state per notification per channel, fed by provider callbacks where available |
| F7 | Retry transient failures with backoff; give up into a dead-letter path after a bounded number of attempts |

### 2.2 Non-functional (the ones that drive the design)

| # | Requirement | Consequence |
|---|-------------|-------------|
| N1 | At-least-once is the achievable guarantee, not exactly-once | Every downstream effect must be made idempotent by the receiver, not assumed safe by the sender — direct application of [idempotency-and-deduplication.md §2](idempotency-and-deduplication.md) |
| N2 | One channel's provider outage must not delay another channel | Channels are isolated queues/workers, not stages of one synchronous pipeline |
| N3 | A user must never be spammed by a retry or a rapid-fire event stream | Deduplication and coalescing are correctness requirements, not polish |
| N4 | A small, explicit list of categories may override quiet hours and preferences | Safety and account-security notifications must reach the user; that list must be short, reviewed, and impossible to accidentally extend |

### 2.3 Out of scope — say it and get agreement

Copywriting/localisation content pipelines and large-scale marketing campaign orchestration/segmentation —
both are real systems, both are adjacent, and both would consume the whole round if not explicitly fenced
off. Scope this file to: *given a triggering event and a template id, deliver it correctly.*

### 2.4 Scale assumptions

```
Assumption, stated: ~1M notification-triggering events/day platform-wide (ride status, account, support
  case updates), averaging 1.5 eligible channels each after preference filtering
-> ~1.5M send attempts/day =~ 17/s average
Assumption, stated: peak is not smooth -- a single event (a service disruption, a mass ride cancellation)
  can trigger a synchronised burst across a large user population in a narrow window
```

| Quantity | Answer | Design consequence |
|----------|--------|----------------------|
| Average send rate | ~17/s | Trivially small in steady state — same conclusion as every other file in this section |
| Peak burst | Potentially orders of magnitude above average, for minutes | The design has to survive a burst, not just an average — this is why fan-out goes through a durable queue (§4) instead of a synchronous call chain |

---

## 3 · API surface first

```
POST /v1/notifications
  { "user_id": "...", "category": "ride_status", "template_id": "driver_arriving",
    "data": {"eta_min": 3}, "dedupe_key": "trip-882:arriving" }
  -> 202 { "notification_id": "..." }        # fan-out happens async

GET  /v1/notifications/{id}                  -> per-channel delivery state

GET  /v1/users/{user_id}/notification-preferences
PUT  /v1/users/{user_id}/notification-preferences
  { "ride_status": {"push": true, "email": false, "sms": false},
    "promotions": {"push": false, "email": false, "sms": false} }
```

`POST` returns `202` for the same reason every fan-out or slow-path write in this program does: the
caller does not need to wait on channel delivery, only on the request being durably accepted.

---

## 4 · Multi-channel fan-out

```
event/trigger ─▶ [ Notification Service: render template, resolve preferences,
                     dedupe (§6), quiet-hours check (§6) ]
                             │
              ┌──────────────┼──────────────┬───────────────┐
              ▼              ▼              ▼               ▼
        [ push queue ] [ email queue ] [ SMS queue ]  [ in-app queue ]
              │              │              │               │
              ▼              ▼              ▼               ▼
        APNs / FCM        SES/etc        Twilio/etc     write to the
                                                          user's feed
```

**Each channel is an isolated queue and worker pool, not a stage in one synchronous pipeline.** This is
the same structural reasoning the crawler gives for separating fetch, parse, and store
([distributed-web-crawler.md §3](distributed-web-crawler.md)): different external dependencies, different
failure modes, different latency profiles. A push-provider outage must not add latency to email, and an
email-provider rate limit must not stall an in-app write, which only touches your own database.

**Push specifically reuses the design already built for it.** The transport, token lifecycle, silent-vs-
alert payload trade-off, and badge-count-from-watermark decisions are exactly
[realtime-chat-delivery-guarantees.md §10.3](realtime-chat-delivery-guarantees.md)'s push section — do not
re-derive it. What is new in *this* file is treating push as one interchangeable channel behind a common
fan-out, preference, and template layer that email, SMS, and in-app also sit behind.

---

## 5 · Template and preference management

### 5.1 Templates

Versioned, per-locale, parameterised by the `data` payload on the triggering request. Rendering is a pure
function of `(template_id, locale, data) -> content` — keep it that way, because a template that reaches
out to other services during rendering turns a cheap operation into one with its own failure modes, and
those failure modes now sit in front of every channel's fan-out instead of contained within one.

### 5.2 Preferences

A small per-user document: category → per-channel boolean. Resolved once, before fan-out, with a cheap
point lookup — this table is read far more than written, and belongs behind the same kind of cache-aside
layer as [url-shortener.md §6](url-shortener.md), for the identical reason.

**A short list of categories is not subject to the preference table at all** — account security and
safety notifications ship regardless of what the user has toggled off, the same non-negotiable-override
principle as [support-case-routing.md §6](support-case-routing.md)'s P0 safety tier bypassing every normal
queueing rule. Keep that list short, reviewed, and encoded as an explicit allowlist in code, never as an
implicit "if preference lookup fails, send anyway" fallback — the two look similar and are not: one is a
deliberate policy, the other is a bug that happens to fail toward over-sending.

---

## 6 · Deduplication and quiet hours

### 6.1 Two different kinds of duplicate

| Kind | Cause | Fix |
|------|-------|-----|
| **Exact duplicate** | The triggering event is redelivered (a retried publish, a replayed message) | Idempotency key = `(user_id, category, dedupe_key)`, enforced with the identical conditional-write protocol as [idempotency-and-deduplication.md §3](idempotency-and-deduplication.md) — do not invent a second mechanism for the same problem |
| **Rapid near-duplicate** | The same *logical* notification updates several times in a short window (an ETA ticking down every few seconds) | **Coalescing**, not deduplication — collapse into one send carrying the latest data, implemented in §9 |

The chat design's receipt batching makes the identical point in a different domain: *"receipts are the
highest-volume, lowest-value traffic... coalesce... and send only the maximum"*
([realtime-chat-delivery-guarantees.md §9.2](realtime-chat-delivery-guarantees.md)). Sending one
notification per underlying event, when several arrive within seconds of each other, is the same mistake
in a new place.

### 6.2 Quiet hours, and the override that must stay narrow

Non-urgent notifications queue rather than send during a user's local quiet hours (a stored preference or
a sane default window). Two details that separate a working answer from a good one:

- **The same short override allowlist from §5.2 bypasses quiet hours too** — a security alert at 3 a.m.
  is not optional, for the same reason a P0 support case is never queued behind normal routing.
- **A held notification can go stale.** "Your driver arrived" delayed eight hours by quiet hours and
  delivered the next morning is not late, it is *wrong* — it describes a moment that has passed and no
  longer means anything. Every held notification needs a **relevance window**; on expiry it is dropped,
  not delivered late. This is a different failure than the push-dedup case in
  [realtime-chat-delivery-guarantees.md §10.3](realtime-chat-delivery-guarantees.md) (where a duplicate is
  suppressed because the client already has the content) — here the content itself has expired, and the
  correct action is silence, not delayed delivery.

---

## 7 · Delivery tracking

### 7.1 Why this file does not need the chat design's watermark trick

[realtime-chat-delivery-guarantees.md §9.2](realtime-chat-delivery-guarantees.md) replaces a per-message
receipt row with a per-participant watermark specifically because chat message volume makes a
row-per-message-per-recipient a real write-amplification problem. **Notification volume per user is
orders of magnitude lower** — per §2.4, roughly 1.5 sends a day platform-wide per triggering event, not
per user; even an active user sees a handful of notifications a day. At that volume, a plain row per
`(notification_id, channel)` tracking its own state is simply not expensive, and building a watermark
abstraction here would be solving a write-amplification problem that does not exist at this scale. **Name
this contrast explicitly if asked** — it is the more valuable answer than reflexively reapplying the
chat design's optimisation, and it is the same "does the numbers justify the machinery" discipline every
napkin-math section in this program asks for.

```
QUEUED ──▶ SENT ──▶ DELIVERED ──▶ OPENED/CLICKED (push, email; optional, provider-dependent)
   │           │
   └── FAILED ─┘   (retry with backoff, §8; DLQ after N attempts)
```

### 7.2 Feeding the state machine

`SENT` is set the moment the channel worker hands the payload to the provider. `DELIVERED` and
`OPENED/CLICKED` come from **provider callbacks** — APNs/FCM delivery feedback, an email open pixel or
provider webhook, a carrier delivery receipt for SMS — each a small, isolated adapter translating a
provider-specific callback into the same internal state transition, so the rest of the system never has
three different state machines to reason about.

---

## 8 · Retry with backoff

### 8.1 The mechanism

Per-channel, per-provider: a bounded number of retries with the same full-jitter exponential backoff
formula used everywhere else in this program
([realtime-chat-delivery-guarantees.md §5.4](realtime-chat-delivery-guarantees.md),
[rate-limiter.md §7](rate-limiter.md)) — restated here only to apply it, not to re-derive it — and a
circuit breaker per provider so a provider outage degrades to "stop trying for a cooldown window and queue
for later" rather than hammering a dead endpoint (the identical breaker shape as
[support-case-routing.md §13.2](support-case-routing.md), guarding a third unreliable third-party
dependency). Exhausted retries land in a dead-letter queue for operator inspection, the same pattern the
crawler uses for a parser that keeps failing on one URL
([distributed-web-crawler.md §10.1](distributed-web-crawler.md)).

### 8.2 Cross-channel fallback is a per-category policy, not a global rule

Should a failed push retry escalate to SMS? **It depends on the category, and that has to be an explicit,
per-category decision, not a blanket rule:**

| Category | Fallback across channels? | Why |
|----------|------------------------------|-----|
| Time-critical safety/account alert | Yes — push, then SMS if undelivered within a short window | The cost of under-delivery is high enough to justify a more intrusive, costlier channel |
| Ordinary ride-status update | No | A failed push simply queues normally; escalating to SMS for "your driver is 2 minutes away" is disproportionate cost and intrusion for the value of the message |
| Promotional | No, and arguably no retry at all | The lowest-value category in the system; it should be the first thing shed under load, echoing the shed-order discipline in [support-case-routing.md §11.3](support-case-routing.md) and [realtime-chat-delivery-guarantees.md §13](realtime-chat-delivery-guarantees.md) |

---

## 9 · At-least-once vs exactly-once — the cross-channel asymmetry

The guarantee is the same one this whole program keeps landing on: **at-least-once transport, made safe by
an idempotent receiver** — see
[idempotency-and-deduplication.md §2](idempotency-and-deduplication.md) and
[realtime-chat-delivery-guarantees.md §7](realtime-chat-delivery-guarantees.md) for the full argument,
which is not repeated here. **What is genuinely new in this file is that different channels put the
dedup burden in different places:**

| Channel | Where a duplicate gets suppressed |
|---------|--------------------------------------|
| Push | **The client**, per [realtime-chat-delivery-guarantees.md §10.3](realtime-chat-delivery-guarantees.md): the payload carries a stable id, and the OS/app layer can suppress a duplicate alert if it already has that id |
| In-app | The client's own feed rendering, keyed the same way |
| **Email** | **Nowhere downstream** — a recipient's mail client will not dedupe two emails on your behalf. The entire burden sits on the sender: the idempotency check in §6.1 must actually prevent the second send, because nothing catches it afterward |
| **SMS** | Same as email — no client-side safety net. A duplicate that reaches the carrier reaches the phone |

**State this asymmetry unprompted; it is the sharpest observation available in this file.** For push and
in-app, a dedup failure is recoverable at the edge, which is what makes at-least-once-plus-client-dedup an
acceptable, even elegant, design. For email and SMS, the exact same server-side bug produces a genuinely
duplicate, unrecoverable user-visible event, because the channel itself offers no downstream safety net —
which means the server-side idempotency check in §6.1 has to be treated as load-bearing for those two
channels in a way it is merely a nice-to-have for the other two.

---

## 10 · Storage model

```
notifications (PK = notification_id)
  user_id, category, template_id, data, dedupe_key, created_at

delivery_attempts (PK = notification_id#channel, or bucketed notification_id#yyyymm for a high-volume
                    user's full history, same month-bucketing reasoning as the chat design)
  channel, state, provider_message_id, attempt_count, last_attempt_at, delivered_at

preferences (PK = user_id)
  { category: {channel: bool} }
```

Point lookups by `notification_id` and by `user_id` cover every access pattern in §2.1 — no ad-hoc query
needs, which is the same signal that made DynamoDB a clean fit everywhere else in this section
([lyft-architecture.md §7](lyft-architecture.md)).

---

## 11 · Code the round may ask for

*"Five ETA updates arrive for the same trip within a minute. Send one notification, not five, without
delaying it indefinitely if updates keep trickling in."*

```python
import heapq
import itertools


class NotificationCoalescer:
    """Collapses rapid-fire updates for the same logical notification into
    one send -- five ETA updates in a minute becoming one push with the
    latest ETA, instead of five separate pings.

    A new update for a key that already has a pending send replaces its
    payload but does NOT push a new heap entry or reset the fire time --
    otherwise a steady trickle of updates could delay the send
    indefinitely, the same "must not starve forever" concern as the aging
    priority queue in support-case-routing.md.

    Each key has at most one live heap entry at a time (`update` only
    schedules one when the key is not already pending), so `due` needs no
    staleness check for a superseded entry -- unlike the connection
    registry or dispatch scheduler elsewhere in this program, there is no
    re-arm step here that could leave a stale entry behind.
    """

    def __init__(self, coalesce_window_s: float) -> None:
        self.coalesce_window_s = coalesce_window_s
        self._pending: dict[str, object] = {}      # key -> latest payload
        self._fire_at: dict[str, float] = {}         # key -> scheduled fire time
        self._heap: list[tuple[float, int, str]] = []
        self._counter = itertools.count()

    def update(self, key: str, payload: object, now: float) -> None:
        self._pending[key] = payload
        if key not in self._fire_at:                 # first update for this key starts its clock
            fire_at = now + self.coalesce_window_s
            self._fire_at[key] = fire_at
            heapq.heappush(self._heap, (fire_at, next(self._counter), key))

    def due(self, now: float) -> list[tuple[str, object]]:
        """Sends whose window has closed: (key, latest payload), in fire order."""
        ready: list[tuple[str, object]] = []
        while self._heap and self._heap[0][0] <= now:
            _, _, key = heapq.heappop(self._heap)
            ready.append((key, self._pending.pop(key)))
            del self._fire_at[key]
        return ready
```

```python
import unittest


class TestNotificationCoalescer(unittest.TestCase):
    def test_single_update_fires_after_the_window(self):
        c = NotificationCoalescer(coalesce_window_s=30)
        c.update("trip-1:eta", {"eta_min": 5}, now=0)
        self.assertEqual(c.due(now=20), [])
        self.assertEqual(c.due(now=30), [("trip-1:eta", {"eta_min": 5})])

    def test_rapid_updates_collapse_to_one_send_with_the_latest_payload(self):
        c = NotificationCoalescer(coalesce_window_s=30)
        c.update("trip-1:eta", {"eta_min": 8}, now=0)
        c.update("trip-1:eta", {"eta_min": 6}, now=5)
        c.update("trip-1:eta", {"eta_min": 3}, now=10)
        self.assertEqual(c.due(now=30), [("trip-1:eta", {"eta_min": 3})])

    def test_a_trickle_of_updates_does_not_delay_the_send_indefinitely(self):
        c = NotificationCoalescer(coalesce_window_s=30)
        c.update("trip-1:eta", {"eta_min": 10}, now=0)
        c.update("trip-1:eta", {"eta_min": 9}, now=20)     # before the original window closes
        # fires at the ORIGINAL window (30), not extended by the second update
        self.assertEqual(c.due(now=30), [("trip-1:eta", {"eta_min": 9})])

    def test_independent_keys_do_not_interfere(self):
        c = NotificationCoalescer(coalesce_window_s=30)
        c.update("trip-1:eta", {"eta_min": 5}, now=0)
        c.update("trip-2:eta", {"eta_min": 12}, now=0)
        self.assertEqual(c.due(now=30), [
            ("trip-1:eta", {"eta_min": 5}), ("trip-2:eta", {"eta_min": 12})])


if __name__ == "__main__":
    unittest.main()
```

**What to say while writing it:** the design choice worth narrating is *fixed* versus *reset* debounce —
resetting the window on every update is the more familiar debounce semantics, and it is wrong here,
because a busy trip with updates every few seconds would then never fire until updates stop entirely.
Anchoring the fire time to the *first* update in a burst bounds the worst-case delay to exactly one
window, which is what a caller actually needs.

---

## 12 · Failure modes

| Component | Failure | Detection | Mitigation | User sees |
|-----------|---------|-----------|------------|-----------|
| One channel's provider (APNs, SES, Twilio) | Down or rate-limiting | Error rate per provider | Circuit breaker opens for that channel only; queue and retry with backoff; other channels unaffected | Delayed delivery on one channel, not all |
| Preference lookup | Slow or down | Latency/error metric | Fail toward the *narrower* set — safety/security overrides still send; everything else queues rather than guessing a preference | Slight delay, never an incorrectly-sent promotional message |
| Coalescing window | A key never stops updating (a runaway event source) | Time-in-pending metric per key | The fixed-anchor design already bounds this to one window's delay — no additional mitigation needed, and saying so is the payoff of the design choice in §11 | One notification, on time, regardless of update rate |
| Dead-letter queue | Fills up | Queue-depth alert | Paged for operator review, same as the crawler's poison-URL handling | No user-visible effect unless the underlying failure is systemic |
| Quiet-hours store | Down | Error on lookup | Fail toward *not* delaying non-urgent sends rather than silently dropping them — a wrongly-timed notification is a smaller failure than a lost one | Occasional off-hours notification during an incident, not silence |

---

## 13 · Working design vs good design, for this problem

| Working | Good |
|---------|------|
| "Send a push, email, and SMS for every event" | Per-category preference resolution and a short, explicit override list for safety/security, checked before fan-out |
| "Retry on failure" | Full-jitter backoff, a per-provider circuit breaker, and a DLQ after bounded attempts — the same shape reused, not reinvented, from three other failure-mode tables in this program |
| "Hold notifications during quiet hours" | Held notifications carry a relevance window and are dropped, not delivered late, once that window passes |
| "Dedupe with an idempotency key" | Two distinct duplicate problems named separately — exact redelivery (idempotency key) versus rapid near-duplicates (coalescing) — because one mechanism does not solve both |
| "It's at-least-once, same as everything else" | The cross-channel asymmetry stated explicitly: push and in-app get a client-side safety net; email and SMS do not, which makes server-side dedup load-bearing specifically for those two |
| "Track delivery status per notification" | The chat design's watermark optimisation is explicitly *not* reused here, with the volume math showing why it would be solving a problem this system does not have |

---

## Interview questions

**1. Design a multi-channel notification system.**
An event triggers a render from a template, a preference and quiet-hours check, and fan-out across
independent per-channel queues — push, email, SMS, in-app — each with its own worker pool so one
provider's outage cannot delay another channel. The guarantee is at-least-once with idempotent handling of
duplicates, plus coalescing for rapid near-duplicate updates, and delivery is tracked per notification per
channel from provider callbacks.

**2. Why does push handle duplicates differently than email or SMS?**
Push and in-app notifications carry a stable id the client can use to suppress a duplicate it has already
seen — the same mechanism the chat design uses for push dedup. Email and SMS have no such downstream
safety net: a recipient's mail client will not dedupe two emails, and a duplicate SMS that reaches the
carrier reaches the phone. That means the server-side idempotency check is merely a nice-to-have for push
and load-bearing for email and SMS, even though the failure that would cause a duplicate is identical.

**3. How do you avoid sending five separate notifications when an ETA updates five times in a minute?**
Coalescing, which is a different mechanism from deduplication: an update for a key that already has a
pending send replaces its payload without resetting the scheduled fire time, so a steady trickle of
updates bounds the worst-case delay to one window instead of resetting it indefinitely — the classic
debounce trap is resetting on every update, which this design deliberately avoids.

**4. How do you handle quiet hours?**
Non-urgent notifications queue until the user's local quiet hours end, except for a short, explicit
override list — safety and account-security categories, which ship immediately regardless. A held
notification also carries a relevance window; if that window passes before quiet hours end, the
notification is dropped rather than delivered stale, because a notification describing a moment that has
already passed is wrong, not merely late.

**5. Why not use the same read-receipt watermark trick from the chat design here?**
Because that optimisation exists specifically to avoid write amplification at chat message volumes, and
notification volume per user is orders of magnitude lower — a plain row per notification per channel is
not expensive at this scale. Reapplying the watermark pattern here would add an abstraction to solve a
write-amplification problem that does not actually exist for this workload.

**6. Should a failed push retry escalate to SMS?**
That has to be a per-category policy, not a global rule. A time-critical safety alert justifies escalating
to a costlier, more intrusive channel if push fails; an ordinary ride-status update does not, and a
promotional notification should not even retry aggressively, let alone escalate — it is the first thing
to shed under load.

**7. What happens if your preference-lookup store is down when a notification is about to send?**
Fail toward the narrower outcome: safety and security overrides still send regardless, since they bypass
preferences entirely by design, and everything else queues rather than guessing what the user's
preference might be. Guessing wrong in the direction of over-sending is a worse failure than a delayed
send.

**8. How would you prevent a duplicate notification if the triggering event gets redelivered?**
The same idempotency-key protocol used everywhere else in this program: a key derived from
`(user_id, category, dedupe_key)`, enforced with a conditional write, not a read-then-write check. This is
a different problem from coalescing rapid near-duplicates, and needs its own mechanism even though both
are colloquially "duplicates."

**9. How do you track delivery status across channels with different feedback mechanisms?**
A small per-channel adapter translates whatever the provider gives you — APNs/FCM delivery feedback, an
email webhook or open pixel, an SMS carrier delivery receipt — into the same internal state machine
(queued, sent, delivered, opened/clicked, failed), so the rest of the system reasons about one state
machine regardless of how many different provider integrations feed it.

**10. What would you cut first under a sudden load spike?**
Promotional notifications — no retry, dropped first — followed by relaxing non-critical channels' retry
budgets. Time-critical and safety/security categories are never shed, the same shedding discipline this
program applies everywhere a system has to degrade under load rather than fail uniformly.
