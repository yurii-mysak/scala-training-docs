# Rate Limiter — full worked design

> **Priority:** Required
> **Est. time:** 60 min
> **Track:** Server
> **HelloInterview:** System Design in a Hurry → Common Patterns → Dealing with Contention; Key Technologies → Redis; Core Concepts → API Design

Not a verbatim reported design prompt, but required for three concrete reasons stated in this program's
own material rather than asserted on faith: it is a named building block of
[lyft-architecture.md §8](lyft-architecture.md) (rate limiting at **both** edge and service-mesh layers is
one of the facts on the stack-at-a-glance table); it is exactly the shape of *"a web application with a
lot of third-party dependencies that have a variety of failure modes"*, reported at Lyft, viewed from the
provider's side instead of the caller's side; and it is named directly as a plausible coding pivot inside
[realtime-chat-delivery-guarantees.md §15.3](realtime-chat-delivery-guarantees.md). Expect it as a 15-20
minute sub-question inside a bigger design at least as often as a standalone prompt.

---

## 1 · Frame the problem in one sentence

> "A mechanism that decides, for a given key and in bounded time and memory, whether the next request
> should proceed — accurately enough to protect the backend, cheaply enough to run on every request, and
> consistently enough that it means the same thing on every node enforcing it."

The exam inside this one is the **memory/accuracy trade-off** (§3) and **what happens when the limiter
itself is the thing that is down** (§9) — both of which separate a working answer from a good one.

---

## 2 · Requirements and scoping

### 2.1 Functional

| # | Requirement |
|---|-------------|
| F1 | Allow up to N requests per key per time window; reject the rest |
| F2 | Return a machine-readable signal on rejection: `429`, `Retry-After`, and remaining-quota headers |
| F3 | Support different limits per scope — per user, per API key, per IP, per calling service |
| F4 | Allow a controlled burst above the steady-state rate, where the algorithm chosen supports it |

### 2.2 Non-functional (the ones that drive the design)

| # | Requirement | Consequence |
|---|-------------|-------------|
| N1 | The limiter runs on **every** request | Its own latency budget is sub-millisecond to low-single-digit milliseconds; anything slower defeats its purpose |
| N2 | Correct under concurrent access | Two requests arriving at the same instant must not both be admitted past the limit — this is an atomicity requirement, not just a data-structure choice (§5) |
| N3 | Bounded memory regardless of traffic volume | The algorithm choice in §3 is fundamentally a memory-vs-accuracy trade, and the wrong choice at high cardinality (millions of keys) is an outage of its own |
| N4 | The limiter must have an explicit answer for "what happens when the limiter's own store is unavailable" | A rate limiter that fails by taking down the service it protects has made things worse, not safer (§9) |

### 2.3 Out of scope — say it and get agreement

Billing-grade quota tracking (a durable ledger with exact accounting — a different, stricter problem
related to but distinct from rate limiting; name the difference: a rate limiter enforces a technical
ceiling approximately and cheaply, a quota system tracks an entitlement exactly and durably). DDoS
mitigation at the network layer (that is infrastructure the platform provides, not application code).

---

## 3 · Algorithms compared

| Algorithm | Memory per key | Accuracy | Burst behaviour | Typical use |
|-----------|------------------|----------|--------------------|--------------|
| **Fixed window** | O(1) — one counter, one expiry | Poor at the boundary — see §3.1 | Allows up to **2x** the limit across a window edge | Simple abuse protection where the boundary flaw is acceptable |
| **Sliding log** | **O(limit)** — every request timestamp kept | Exact | None by construction; a hard ceiling | Low-limit, high-value endpoints where exactness is worth the memory |
| **Sliding window counter** | O(1) — two counters plus a window index | A close approximation, weighted by how much of the previous window still overlaps | Smooths the fixed-window edge case to a small fraction of one extra window's worth | **The usual production default** — the accuracy of a sliding log at close to the memory of a fixed window ([lyft-architecture.md §8.2](lyft-architecture.md) names this as the typical choice) |
| **Token bucket** | O(1) — token count plus a last-refill timestamp | Exact against its own model | **Deliberately allows a burst** up to the bucket's capacity, then throttles to the refill rate | The right default when legitimate clients are bursty by nature — a page load firing several requests at once |
| **Leaky bucket** | O(1) (as a rate) or O(queue) (as a literal queue) | Exact against its own model | **Smooths bursts away** — output is a constant rate regardless of input burstiness | Traffic *shaping* (pacing outbound calls to a fragile downstream), not admission control at an API edge |

### 3.1 The fixed-window boundary problem, concretely

A 100/minute fixed-window limit does not actually bound a client to 100 requests in any given minute of
wall-clock time: 100 requests at `0:59` and 100 more at `1:01` are both within their own windows and both
allowed, for **200 requests in a 2-second span** — exactly double the intended rate. This is the
single most-cited flaw of the simplest algorithm, and being able to construct the example live, not just
recite "it has a boundary problem," is the difference worth having ready.

### 3.2 Token bucket vs leaky bucket — the pair everyone mixes up

Both are O(1) and both are named "bucket," and that is roughly where the similarity ends. **Token bucket**
answers "how many requests may proceed right now," and lets a client spend a saved-up allowance all at
once. **Leaky bucket**, implemented as an actual queue draining at a fixed rate, answers "at what rate do
requests *leave*," and enforces that output rate regardless of how bursty the input was — it shapes
traffic rather than gating admission. **Reach for token bucket when protecting yourself from a bursty
caller; reach for leaky bucket when protecting a downstream from your own bursty traffic** — the two
solve the same-sounding problem from opposite sides of a connection, and naming that distinction crisply
is worth more than either implementation individually.

---

## 4 · Distributed enforcement

A single process can hold algorithm state in memory. The moment there is more than one app instance —
which is every real deployment — **local, per-instance state means the real limit is `n_instances ×
configured_limit`**, an approximation that gets worse as the fleet scales out. This is the exact local-vs-
global framing already established as Lyft's own two-tier decision in
[lyft-architecture.md §8.2](lyft-architecture.md):

| | Local (per-instance) | Global (shared store) |
|---|---|---|
| Accuracy | Approximate: `n_instances × per-instance limit` | Accurate fleet-wide |
| Extra latency | None | One round trip to the shared store per decision |
| Failure mode | Degrades gracefully — losing one instance loses only its slice | The store becomes a dependency of every rate-limited request (§9) |
| Right for | Coarse, high-volume protection where the exact number matters less than *some* ceiling | Precise per-key quotas, paid tiers, anything the number itself is a promise about |

**A shared store (Redis) is the default answer once accuracy matters**, which is most of the time this
question is actually asked — go there directly rather than presenting local-only as a serious final
answer, and cite the trade-off table above as the reason you considered and rejected it.

---

## 5 · Redis implementation with atomicity

### 5.1 The race the naive version has

```
INCR ratelimit:user42:2026-08-22T10:00
if result == 1: EXPIRE ratelimit:user42:2026-08-22T10:00 60
```

Two Redis commands, issued separately, are **not atomic together**. A crash, a deploy, or even ordinary
network jitter between them can leave a key incremented with **no expiry at all** — a slow, silent memory
leak of keys that never get cleaned up, discovered only much later as an unexplained memory growth curve.
The bug is not in the logic; it is in the gap between two round trips that looks atomic on the page and is
not atomic on the wire.

### 5.2 The fix: a Lua script

Redis executes a Lua script as a single atomic operation — no other command can interleave inside it. That
makes it the correct primitive for "read, decide, and update" in one step, for any of the algorithms in
§3:

```lua
-- KEYS[1] = rate limit key
-- ARGV[1] = window length in seconds
-- ARGV[2] = limit
local current = redis.call("INCR", KEYS[1])
if current == 1 then
    redis.call("EXPIRE", KEYS[1], ARGV[1])
end
if current > tonumber(ARGV[2]) then
    return 0
end
return 1
```

Called via `EVAL`/`EVALSHA` from the application, this closes the race entirely: the increment, the
first-write expiry set, and the limit check happen as one indivisible step from every other client's point
of view. The same pattern generalises to the token bucket and sliding-window-counter algorithms — the
Lua script holds the read-modify-write logic; only the arithmetic inside changes. **If a rate-limiting
Redis module is available (`redis-cell`'s `CL.THROTTLE`, implementing GCRA), it is a legitimate
alternative to hand-rolled Lua** — say that reaching for a maintained implementation of a well-known
algorithm is usually the better call than hand-rolling one, the same instinct
[distributed-web-crawler.md §11.3](distributed-web-crawler.md) states for bloom filter sizing: know the
mechanism, do not necessarily hand-roll it under interview time pressure unless asked to.

### 5.3 Key design and memory sizing

```
key = f"ratelimit:{scope}:{identifier}:{window_start}"
  e.g. ratelimit:user:42:2026-08-22T10:00   or   ratelimit:svc:checkout->pricing:2026-08-22T10:00:15
```

At high key cardinality (a per-user limiter with millions of active users), size it the way
[napkin-math.md §6](napkin-math.md) sizes anything else: active keys × bytes per key. A few hundred bytes
per key at, say, a few million concurrently-active users is a few hundred megabytes to low gigabytes —
worth actually computing rather than assuming, the same "say the number, do not just gesture at it"
instinct running through every file in this section.

---

## 6 · Where limits live in Lyft's architecture specifically

[lyft-architecture.md §8.1](lyft-architecture.md) already states the two layers Lyft actually runs; this
section is what each layer is protecting against and why the split matters, one layer deeper than a
citation:

| Layer | Protects against | Keyed by | Why it cannot be the other layer's job |
|-------|--------------------|-----------|-------------------------------------------|
| **Edge (API gateway)** | The public internet: scrapers, credential stuffing, an abusive or buggy external client | IP, API key, authenticated user, endpoint | It runs before a request ever reaches the service mesh — the only layer that can reject before internal capacity is spent at all |
| **Service mesh (Envoy sidecar)** | The fleet's *own* traffic: a misbehaving internal caller, a retry loop amplifying across hops, one internal tenant starving another | Calling service identity, route, tenant | Edge limiting cannot see this traffic at all — it never crosses the edge, and this is precisely the layer that catches the retry-storm mechanics in §8, because a retry amplifying three services deep is entirely internal |

Both layers are Redis-backed configuration, per the same source, and Envoy natively supports both a local
rate-limit filter and a call to a global rate-limit service — which is the concrete implementation of the
local-vs-global choice in §4, not a separate mechanism.

---

## 7 · Client behaviour on 429

A well-behaved client, on receiving `429`:

1. **Honours `Retry-After` if present** rather than inventing its own delay — the server has more
   information about when capacity will actually free up.
2. **Otherwise backs off with full jitter**, not a fixed delay and not naive exponential backoff without
   jitter: `sleep = random(0, min(cap, base * 2^n))` — the exact formula already established for
   reconnect storms in [realtime-chat-delivery-guarantees.md §5.4](realtime-chat-delivery-guarantees.md).
   The jitter, not the exponential growth, is what actually prevents synchronisation — see §8.
3. **Caps retry attempts** and surfaces a real failure to its own caller past the cap, rather than
   retrying forever.
4. **If the request being retried is a `POST` or otherwise non-idempotent**, retries only with the same
   idempotency key it used the first time — see
   [idempotency-and-deduplication.md §3](idempotency-and-deduplication.md). A rate limiter and an
   idempotency layer are frequently needed on the exact same endpoint for related but distinct reasons,
   and conflating them is a common gap.
5. **Opens its own circuit breaker after repeated `429`s from the same dependency**, the same
   `AgentCallBreaker` shape already implemented in
   [support-case-routing.md §13.2](support-case-routing.md) — stop calling entirely for a cooldown window
   rather than continuing to generate load a server has already said it cannot handle.

---

## 8 · The retry-storm failure mode

### 8.1 The mechanism

A burst of `429`s hits a population of clients simultaneously (a deploy, a traffic spike, a downstream
blip). Clients without jitter — or worse, with a fixed retry delay — **retry in near-perfect
synchronisation**. The retry wave is not a smaller version of the original load; it can be **larger**,
because it now includes every client that would have succeeded on a slightly later, unsynchronised retry.
The system can end up rejecting the retry wave too, generating a second, synchronised wave — a
self-sustaining oscillation that persists well after whatever originally caused the first rejection has
resolved.

### 8.2 This is the same shape as two other files in this program — say so

This exact mechanism — a population reacting in bulk to a shared signal, with just enough lag that the
reaction overshoots and the signal is already stale by the time everyone acts on it — is the *same
general pattern* as the reconnect storm in
[realtime-chat-delivery-guarantees.md §5.4](realtime-chat-delivery-guarantees.md) and the heatmap
feedback loop in [demand-heatmap-and-surge.md §7](demand-heatmap-and-surge.md). Naming it once as a
pattern with three independent instances in this program — bulk synchronised reaction to a shared,
laggy signal — is a stronger answer than re-deriving jittered backoff from scratch as if it were specific
to rate limiting.

### 8.3 Mitigations, in the order they matter

1. **Full jitter on every client**, as in §7 — this is the single highest-leverage fix, because it is
   what breaks synchronisation in the first place; exponential growth alone does not.
2. **A retry budget/cap**, so a client gives up and surfaces failure rather than retrying indefinitely
   into a storm it is contributing to.
3. **Distinguish `429` (you, specifically, are over your limit — a normal, expected signal) from `503`
   (the service is overloaded regardless of who you are) at the server**, because the correct client
   response differs: a `429` says "back off and you personally will likely succeed soon"; a `503` says
   "the whole service is struggling, and hammering it faster with your own individually-well-behaved
   backoff still adds to a system-wide problem" — worth a longer, more conservative backoff.
4. **Server-side load shedding with a stated priority**, the same instinct as
   [realtime-chat-delivery-guarantees.md §13](realtime-chat-delivery-guarantees.md)'s shed order and
   [support-case-routing.md §11.3](support-case-routing.md)'s: reject cheap, low-value traffic first so
   the rejection itself does not consume more capacity than admitting a smaller amount of high-value
   traffic would have.

---

## 9 · Fail-open vs fail-closed

**When the store backing a global limiter is itself unavailable, the limiter has to have a default, and
that default is a real design decision, not an afterthought.**
[lyft-architecture.md §8.2](lyft-architecture.md) already states the resolution: **fail open for abuse
protection** (availability beats precision — better to let the fleet run briefly unthrottled than to
reject all legitimate traffic because the limiter's own dependency hiccuped) and **fail closed for
anything that costs money or represents a hard entitlement**, where letting an unbounded request through
is a worse outcome than a false rejection.

Implement the decision the same way [support-case-routing.md §13.2](support-case-routing.md) guards a
different unreliable dependency: wrap the store call in a timeout and a circuit breaker, and have the
breaker's open-state behaviour **be** the fail-open/fail-closed choice — for edge abuse protection, an
open breaker returns "allow"; for a paid-quota limiter, an open breaker returns "reject". Reusing that
exact breaker shape for a second unreliable dependency, rather than inventing a new one, is worth pointing
out explicitly if it comes up — it is the same component solving the same problem for a different call.

---

## 10 · Code the round may ask for

### 10.1 Token bucket

*"Implement a rate limiter that allows short bursts but enforces a steady long-run rate."*

```python
class TokenBucket:
    """Allows a burst up to `capacity`, then throttles to `rate` tokens/second.

    O(1) memory: a token count and a last-refill timestamp. Refill is
    computed lazily from elapsed time on each call, never a background
    timer -- the same "no polling, compute on demand" instinct as the
    heap-based expiry code elsewhere in this program.
    """

    def __init__(self, capacity: float, rate: float) -> None:
        self.capacity = capacity
        self.rate = rate
        self._tokens = capacity
        self._last_refill = 0.0

    def allow(self, now: float, cost: float = 1.0) -> bool:
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last_refill = now
        if self._tokens >= cost:
            self._tokens -= cost
            return True
        return False
```

```python
import unittest


class TestTokenBucket(unittest.TestCase):
    def test_allows_a_burst_up_to_capacity(self):
        b = TokenBucket(capacity=3, rate=1.0)
        self.assertTrue(b.allow(now=0))
        self.assertTrue(b.allow(now=0))
        self.assertTrue(b.allow(now=0))
        self.assertFalse(b.allow(now=0))          # capacity exhausted

    def test_refills_over_time(self):
        b = TokenBucket(capacity=3, rate=1.0)
        for _ in range(3):
            b.allow(now=0)
        self.assertFalse(b.allow(now=0.5))
        self.assertTrue(b.allow(now=1.0))          # ~1 token regenerated after 1s

    def test_never_exceeds_capacity_even_after_a_long_idle(self):
        b = TokenBucket(capacity=3, rate=1.0)
        b.allow(now=0)
        self.assertFalse(b.allow(now=1000, cost=4))   # cannot borrow beyond capacity
        self.assertTrue(b.allow(now=1000, cost=3))    # confirms it topped out at 3, not 1000+


if __name__ == "__main__":
    unittest.main()
```

### 10.2 Sliding window counter

*"Fixed windows let a client burst 2x at the boundary. Fix it without paying for a sliding log."*

```python
import math


class SlidingWindowCounter:
    """Approximates a sliding window from two fixed windows: the current
    one (exact) and the previous one, weighted by how much of it still
    overlaps the trailing window. O(1) memory per key -- two counters and
    a window index -- against the sliding log's O(limit).
    """

    def __init__(self, limit: int, window_s: float) -> None:
        self.limit = limit
        self.window_s = window_s
        self._current_window: int | None = None
        self._current_count = 0
        self._previous_count = 0

    def _window_index(self, now: float) -> int:
        return math.floor(now / self.window_s)

    def allow(self, now: float) -> bool:
        window = self._window_index(now)
        if self._current_window is None:
            self._current_window = window
        elif window == self._current_window + 1:
            self._previous_count = self._current_count
            self._current_count = 0
            self._current_window = window
        elif window > self._current_window + 1:
            self._previous_count = 0              # the whole previous window is out of range now
            self._current_count = 0
            self._current_window = window

        elapsed_in_window = now - window * self.window_s
        weight = max(0.0, (self.window_s - elapsed_in_window) / self.window_s)
        estimate = self._previous_count * weight + self._current_count

        if estimate >= self.limit:
            return False
        self._current_count += 1
        return True
```

```python
class TestSlidingWindowCounter(unittest.TestCase):
    def test_enforces_the_limit_within_one_window(self):
        c = SlidingWindowCounter(limit=3, window_s=60)
        self.assertTrue(c.allow(now=0))
        self.assertTrue(c.allow(now=10))
        self.assertTrue(c.allow(now=20))
        self.assertFalse(c.allow(now=30))

    def test_smooths_the_fixed_window_boundary_burst(self):
        c = SlidingWindowCounter(limit=10, window_s=60)
        for _ in range(10):
            self.assertTrue(c.allow(now=59))        # fill window 0 completely, right at its edge
        # A fixed-window counter would allow a fresh batch of 10 one second
        # later, in the new window. The weighted estimate should not.
        allowed_just_after_boundary = sum(c.allow(now=61) for _ in range(10))
        self.assertLess(allowed_just_after_boundary, 10)

    def test_old_window_fully_expires_once_truly_stale(self):
        c = SlidingWindowCounter(limit=3, window_s=60)
        for _ in range(3):
            c.allow(now=0)
        self.assertTrue(c.allow(now=1000))          # far beyond one window later: fully reset
```

**What to say while writing it:** the `elif` ladder is doing the entire "sliding" part of the algorithm —
advance one window and the old current becomes the weighted previous; skip more than one window and
there is nothing left to weight, so both counters reset. The estimate itself is one line
(`previous * weight + current`); the state-transition logic is where the algorithm actually lives, and
it is worth narrating that split while writing it, the same way the ordered-delivery buffer in
[realtime-chat-delivery-guarantees.md §15.1](realtime-chat-delivery-guarantees.md) is mostly about the
`while` loop, not the dict lookup.

---

## 11 · Failure modes

| Component | Failure | Detection | Mitigation | User sees |
|-----------|---------|-----------|------------|-----------|
| Shared store (Redis) | Down or slow | Timeout on the limiter call | Circuit breaker; fail open or closed per §9's stated policy | Either briefly unthrottled, or a clear rejection — never a hang |
| A single hot key | One user/IP/service dramatically over any reasonable limit | Per-key request-rate anomaly | The limiter itself handles this by design — that is its job; watch for it becoming a hot *Redis* key and needing the same replication mitigation as any other hot key | Consistently rejected past the limit, as intended |
| Client population | Retry storm after a burst of `429`s | Synchronised request-rate spikes at fixed intervals | Full jitter (client), retry budget (client), load shedding by priority (server) — §8 | Slower recovery without the fix; fast, smooth recovery with it |
| Lua script / EVAL | Script error or Redis version mismatch | Error rate on the limiter call path | Same breaker as the store-down case; do not let a scripting bug fail the whole request path silently | Same as store-down |
| Envoy local rate-limit filter | Config push is wrong (too strict) | Sudden 429 rate spike fleet-wide right after a config deploy | Canary the config change the same way any other Envoy config push is canaried ([lyft-architecture.md §3](lyft-architecture.md)) | A bad limiter config is a fleet-wide incident, same caution as any control-plane push |

---

## 12 · Working design vs good design, for this problem

| Working | Good |
|---------|------|
| "Use a fixed window counter" | Named, with its boundary flaw demonstrated by a concrete example, and the sliding window counter offered as the O(1)-memory fix |
| "INCR the counter and set an expiry" | Recognised as two non-atomic calls with a real failure mode (a key that never expires), fixed with a Lua script executed as one atomic step |
| "Rate limit at the API gateway" | Two layers named with different keys and different failure modes — edge for the public internet, mesh for internally-amplified traffic like retry storms |
| "Return 429 on rejection" | 429 vs 503 distinguished, because they call for different client backoff behaviour, and `Retry-After` is honoured rather than reinvented |
| "The client retries on failure" | Full jitter, a retry cap, and a client-side circuit breaker — because naive retries are what turn one rejection into a synchronised storm |
| "If Redis is down, block requests" (or the reverse) | An explicit, stated fail-open/fail-closed decision per use case, implemented as the open-breaker behaviour of the same guard pattern used for other unreliable dependencies in this program |

---

## Interview questions

**1. Compare fixed window, sliding log, sliding window counter, and token bucket.**
Fixed window is O(1) memory but allows up to double the intended rate across a window boundary. Sliding
log is exact but costs memory proportional to the limit itself, since every timestamp is kept. The
sliding window counter approximates a true sliding window with two O(1) counters, weighting the previous
window by how much of it still overlaps — close to sliding-log accuracy at close to fixed-window memory,
which is why it is the usual production default. Token bucket is a different shape entirely: it
deliberately allows a burst up to a capacity and then throttles to a steady refill rate, which is the
right model when legitimate traffic is bursty by nature rather than smooth.

**2. Walk through the fixed-window boundary problem with numbers.**
A 100-per-minute limit allows 100 requests at the last second of one window and 100 more at the first
second of the next, both individually within their own window's limit — 200 requests inside a two-second
span, double the intended steady rate. The sliding window counter fixes this by weighting the previous
window's count into the current estimate rather than discarding it entirely at the boundary.

**3. How do you make a Redis-backed rate limiter atomic?**
`INCR` followed by a separate `EXPIRE` is not atomic together — a crash between the two calls can leave a
key incremented with no expiry, which leaks memory silently over time. The fix is a Lua script, since
Redis executes a script as a single atomic step with no interleaving from other clients: the increment,
the first-write expiry, and the limit comparison all happen in one round trip.

**4. Where would you put rate limiting in a real production architecture?**
At least two layers, protecting different things. An edge layer, keyed by IP or API key, protects against
abusive or buggy external clients before they consume any internal capacity. A service-mesh layer, keyed
by calling service and route, protects the fleet from its own traffic — most production overload is
self-inflicted, and a retry loop amplifying across several internal hops is only visible to a layer that
sees internal calls, which the edge layer never does.

**5. What should a well-behaved client do on a 429?**
Honour `Retry-After` if the server sent one; otherwise back off with full jitter, not a fixed delay and
not exponential growth alone, since jitter is what actually prevents synchronised retries. Cap the number
of attempts and surface failure past the cap, and if the retried request is non-idempotent, retry with the
same idempotency key rather than a fresh one.

**6. Explain the retry-storm failure mode.**
A burst of rejections hits many clients at once; without jitter, they retry in near-synchronisation,
producing a second wave that can be larger than the original load, because it now includes clients that
would otherwise have succeeded on an unsynchronised retry. Left unfixed, this can oscillate and outlive
whatever originally caused the first rejection. It is the same bulk-synchronised-reaction-to-a-laggy-
signal pattern as a reconnect storm after a gateway failure or a heatmap-driven driver surge — one
mechanism, three contexts in this program.

**7. What happens if the store backing your rate limiter goes down?**
That has to be a stated policy, not an accident: fail open when availability matters more than precision,
such as abuse protection at the edge, where briefly running unthrottled is better than rejecting all
legitimate traffic. Fail closed when the limit represents a hard entitlement or something billed, where
letting unlimited requests through is the worse failure. I would implement the check itself behind a
timeout and circuit breaker, with the breaker's open-state behaviour *being* that fail-open or fail-closed
decision.

**8. When would you choose token bucket over leaky bucket, or the reverse?**
Token bucket when protecting yourself from a bursty caller and legitimate burstiness should be allowed up
to some ceiling — a page load firing several requests at once. Leaky bucket when shaping your own
outbound traffic into a fragile downstream at a strictly constant rate regardless of how bursty the input
is. They answer different questions — "how much may proceed right now" versus "at what rate does traffic
leave" — despite the similar names.

**9. How would you rate-limit by multiple dimensions at once — say, per user and per IP?**
Run independent limiter checks with independently-scoped keys and combine with a logical AND: a request
must pass both to proceed. Each check is the same primitive from §5 with a different key prefix; the
composition, not the primitive, is what changes.

**10. Your rate limiter's own store is slow, adding real latency to every request. What do you do?**
Put a tight timeout and a circuit breaker around the store call so a slow dependency cannot become an
unbounded tail latency on every single request — the same guard used elsewhere in this program for any
unreliable synchronous dependency. Past the timeout, the breaker's configured fail-open or fail-closed
behaviour takes over, and the incident becomes "the limiter is temporarily degraded to its fallback
policy," not "every request is now slow."
