# URL Shortener — full worked design

> **Priority:** Recommended
> **Est. time:** 45 min
> **Track:** Server
> **HelloInterview:** System Design in a Hurry → Question Breakdowns → Bitly; Core Concepts → Caching, Database Indexing

**Reported at Lyft as `bit.ly/TinyURL`.** **[Reported at Lyft]** This is the most-rehearsed prompt in
system design, which cuts both ways: the interviewer has heard every generic answer, so the bar for
"generic" is higher here than anywhere else in this program. The way to clear it is the same instinct as
every other file in this section — go one level past the standard diagram on the three or four decisions
that are actually interesting: key generation, the redirect status code, and where analytics writes go
so they never sit on the read path.

---

## 1 · Frame the problem in one sentence

> "A service that maps a long URL to a short, unique code, redirects on that code with very low latency
> at very high read volume, and records that the click happened without ever slowing the redirect down
> to do it."

---

## 2 · Requirements and scoping

### 2.1 Functional

| # | Requirement |
|---|-------------|
| F1 | Shorten a long URL into a short code |
| F2 | Redirect a short code to its long URL |
| F3 | Support a user-chosen custom alias |
| F4 | Support an optional expiry on a link |
| F5 | Record click analytics (count, rough referrer/time) without it being visible to the redirecting user |

### 2.2 Non-functional (the ones that drive the design)

| # | Requirement | Consequence |
|---|-------------|-------------|
| N1 | **Read-heavy by a wide margin** — redirects vastly outnumber creates | The whole design optimises the read path; creation can afford a little more work |
| N2 | Redirect latency must be very low | This is on the critical path of someone else's page load; cache aggressively, and choose a store built for point lookups |
| N3 | No two active links share a short code | Collision-freedom is a correctness requirement, not a nice-to-have, and *how* it is guaranteed is the most interesting decision in this file (§4) |
| N4 | High availability for redirects, even if creation briefly degrades | A user who cannot shorten a link for 30 seconds is mildly annoyed; a link that 500s for everyone who already has it is a much bigger incident |

### 2.3 Out of scope — say it and get agreement

Malicious-URL / phishing detection at creation time (a content-moderation problem, not an infra one — name
it, do not design it), full-text search over a user's link history, and a public API rate-limiting policy
beyond "reuse [rate-limiter.md](rate-limiter.md)".

### 2.4 Scale assumptions

```
Assumption, stated: ~100 creates/second average, a generic assumption for a shortener at meaningful scale
Assumption, stated: a 100:1 read:write ratio -- widely cited for this product shape, and intuitive: one
  link gets clicked by everyone it was shared with
-> ~10,000 redirects/second average, several times that at peak
Corpus over 10 years: 100/s x 86,400 x 365 x 10 ~= 31.5 billion links
```

| Quantity | Answer | Consequence |
|----------|--------|--------------|
| Redirect QPS | ~10k/s average | This is the number the whole design serves — cache path, store choice, everything downstream of §6 |
| Corpus size | Tens of billions over a decade | Sizes the code space in §5 |
| Per-record size | A few hundred bytes (URL text, timestamps, a counter) | Tens of billions of records is a few terabytes — unremarkable for a keyed store, another "say the number is small" moment |

---

## 3 · API surface first

```
POST /v1/urls
  { "long_url": "https://...", "custom_alias": "optional", "expires_at": "optional" }
  -> 201 { "short_code": "aZ3xQ1", "short_url": "https://sho.rt/aZ3xQ1" }
  -> 409 (custom_alias already taken)

GET /{short_code}
  -> 302 Found, Location: <long_url>       # see §10 for why 302, not 301
  -> 404 (never existed)
  -> 410 Gone (existed, now expired/deleted -- a more honest status than 404, see §8)

GET /v1/urls/{short_code}/stats   -> { "clicks": 41232, "created_at": ..., "last_click_at": ... }
```

---

## 4 · Key generation strategies compared

This is the decision the rest of the design pivots on, and it is where a candidate distinguishes
themselves from a memorised answer.

| Strategy | Mechanism | Collision handling | Distributed generation | Cost |
|----------|-----------|----------------------|--------------------------|------|
| **Counter + base62** | A monotonically increasing integer id, base62-encoded | None needed — the counter guarantees uniqueness by construction | Needs a coordinated counter: either one centralised sequence (a bottleneck and a single point of failure) or **pre-allocated blocks per node** (each app instance reserves a range of ids, e.g. 10,000 at a time, so most requests never touch the shared counter) | Cheapest per-request once blocks are allocated; reveals creation order and approximate volume, which is an information leak worth naming |
| **Hash of the long URL, truncated** | MD5/SHA-256 of the URL, first N base62 characters | **Real and frequent at N small enough to be a short code** — truncating a good hash to 6-7 characters gives a genuine collision rate that must be handled: on collision, append a salt/counter and rehash, or fall back to a different strategy | Embarrassingly parallel — any node can compute a hash with no coordination | Same long URL always maps to the same code, which is a feature for deduplication and a bug if two people shortening the same URL should get independent codes (independent expiry, independent analytics) |
| **Pre-generated key pool** | A background job mints random, checked-unique codes ahead of time into a pool; a create request atomically checks one out | Solved entirely offline — every key in the pool is already guaranteed unique before a request ever sees it | Each generator worker owns a disjoint range or uses its own randomness with a uniqueness check against the store, so workers do not coordinate with each other, only with the store, and only during generation, never on the request path | The classic "Key Generation Service" pattern from the well-known Bitly system-design writeups: it moves all collision cost off the synchronous request path, at the cost of running and monitoring a separate pool-refill job |

**The answer worth defending, not just stating:** the **pre-generated pool** is the strongest default,
because it is the only option that makes the *request path* trivial — checkout is one atomic pop, with
zero collision-handling logic in the hot path — while pushing all the interesting complexity (uniqueness
checking, distributed range allocation) into an offline job that can be slow, retried, and monitored
without any user-facing latency budget. Counter+base62 is the simpler answer to *say* first, and it is a
legitimate choice at moderate scale; naming the pool as the refinement, and *why* it is a refinement, is
what raises this past a memorised diagram. Implemented in §12.2.

---

## 5 · Code length and alphabet

Base62: digits, uppercase, lowercase — 62 symbols, all URL-safe with no encoding needed.

```
62^6  ~= 56.8 billion
62^7  ~= 3.52 trillion
```

Against the §2.4 estimate of ~31.5 billion codes needed over a decade, 6 characters is *technically*
enough but leaves uncomfortably little headroom against the assumption being wrong; **7 characters** is
the standard choice, and the reason to say the arithmetic out loud rather than just stating "7" is that it
demonstrates the number came from somewhere, which is exactly the napkin-math instinct this whole program
asks for ([napkin-math.md](napkin-math.md)).

---

## 6 · The read-heavy cache path

### 6.1 Cache-aside in front of the store

```
GET /{code} ─▶ [ app tier ] ─▶ cache hit? ─▶ 302 immediately
                    │
                    └─▶ cache miss ─▶ [ store, PK = short_code ] ─▶ populate cache ─▶ 302
```

At a ~100:1 read:write ratio, a cache-aside layer (Redis, or even a local process cache with a short TTL
in front of Redis for the hottest links) turns almost every redirect into a memory lookup. **A cold cache
after a deploy is the only time the store sees real load** — size the store for that burst, not for
steady state, the same "size for the failure, not the average" instinct as the crawler's frontier
durability discussion.

### 6.2 Viral links are a hot-key problem, not a scaling problem

A single link going viral concentrates enormous read volume on one cache key. This is the same shape as
every other hot-key discussion in this program (a dense S2 cell in
[driver-location-matching.md §6.2](driver-location-matching.md), a hot conversation in
[realtime-chat-delivery-guarantees.md §6.2](realtime-chat-delivery-guarantees.md)): more shards do not
help a single key, only **replication of that one key** does — an in-process cache on every app instance
for the hottest N links, or a CDN edge cache for the redirect itself, both of which turn a single hot key
into something replicated everywhere it is read.

---

## 7 · Custom aliases

A user-chosen alias is just a short code the user picked instead of the generator — it goes through the
same table with a uniqueness constraint, checked at write time (`INSERT ... ON CONFLICT DO NOTHING`,
returning whether it succeeded). Two things worth adding unprompted:

- **A reserved-word list** (`admin`, `api`, anything matching an existing system route) checked before the
  uniqueness constraint, or a clever user claims `/api` as their alias and now shadows part of your own
  API surface.
- **Alias squatting is a rate-limiting problem, not a uniqueness problem** — reuse
  [rate-limiter.md](rate-limiter.md) per-account rather than inventing a second mechanism.

---

## 8 · Expiry

### 8.1 Lazy check, not a scheduled sweep, for correctness

Correctness only requires checking `expires_at` **at redirect time** — a link past its expiry simply
returns `410` instead of `302`, with no background job required for the system to *behave* correctly. A
periodic sweep still earns its keep for a different reason: reclaiming storage and keeping the analytics
table from growing forever, but it is a cost-and-hygiene job, not a correctness one — say that distinction
explicitly, because conflating "must run for correctness" with "must run for cleanliness" is a common
imprecision.

### 8.2 410, not 404, for an expired link

A link that never existed and a link that existed and is now gone are different facts, and HTTP already
has a status code for the second one. Returning `410 Gone` for an expired or deleted link instead of a
blanket `404` is a small, cheap piece of correctness that signals the same care this program asks for
elsewhere (the chat design's `422` for a same-key-different-body idempotency violation is the same
instinct: use the status code that is actually true, not the closest one you remember).

---

## 9 · Analytics ingestion — off the redirect's critical path

### 9.1 The mistake to avoid

Incrementing a `click_count` column synchronously, on the request that serves the redirect, does two bad
things at once: it adds a write — and a write to a **single hot row** for a viral link — to the latency
budget of N2, and it turns a read-path incident (someone shares a popular link) into a write-contention
incident on one row, which is precisely the kind of self-inflicted overload
[lyft-architecture.md §8.1](lyft-architecture.md) already warns about in a different context.

### 9.2 The fix: fire-and-forget into a stream

```
GET /{code} ─▶ 302 immediately
                  │
                  └─(async, does not block the response)─▶ [ click event ] ─▶ Kafka ─▶ aggregator ─▶ store
```

The redirect handler emits a click event and returns immediately; it does not wait for the event to be
durably written anywhere. A consumer aggregates click counts in windowed batches (the same tumbling-window
shape as [demand-heatmap-and-surge.md §4.1](demand-heatmap-and-surge.md)) rather than incrementing a row
per click. **State the trade-off plainly:** this makes click counts *eventually* consistent and
approximate under extreme load (a small number of events can be lost if the async emit itself fails, which
is an acceptable loss for a display counter and would not be acceptable for anything billed on). If exact
counts were a hard requirement — say, clicks are billed — the answer changes to a durable, deduplicated
event log with idempotent aggregation, at a real latency and complexity cost; naming that this system
deliberately does not pay that cost, and why, is the point.

---

## 10 · The redirect status code decision

This is the single most consequential and most under-discussed choice in the whole design.

| Code | Meaning | What it actually does |
|------|---------|--------------------------|
| **301 Moved Permanently** | "This resource has permanently moved" | **The browser itself caches the redirect target**, often indefinitely. After the first click, that browser never asks your server again for that code — no further analytics, and the link can never be repointed, expired, or A/B tested for that user again |
| **302 Found** | "This resource is temporarily at this other location" | The browser asks the server **every time**. Slightly more load on the redirect service; full control over analytics, expiry, and updating the target at any time |

**302 is correct for a URL shortener as a product, and 301 is the trap.** A candidate who reaches for 301
because "it's a permanent redirect and permanent sounds right" has picked the option that silently
disables three of this file's own requirements — F4 (expiry), F5 (analytics), and any future
retargeting — for every repeat visitor, the moment their browser caches it. The counter-argument for 301
is real and worth naming: it is marginally faster on repeat visits (no round trip at all) and is the
"correct" HTTP semantics if the mapping truly never changes — which is exactly why 301 is the right choice
for, say, a permanent domain migration, and the wrong choice for a product whose entire value includes
analytics and expiry.

---

## 11 · Storage model

```
urls (PK = short_code)
  long_url       text
  owner_id       text | null
  created_at     timestamp
  expires_at     timestamp | null      # TTL attribute if the store supports native per-item TTL
  click_count    int                   # eventually consistent, written by the aggregator, §9.2
```

**Point lookups by `short_code`, at very high read volume, with no ad-hoc query needs** is close to the
textbook access pattern for a managed KV store — DynamoDB fits cleanly, the same reasoning as
[lyft-architecture.md §7](lyft-architecture.md): known access pattern, small items, and **native per-item
TTL maps directly onto `expires_at`**, letting expired links fall out of the table without a cleanup job
at all. That is the same TTL primitive used elsewhere in this program for a *liveness* signal (a driver's
freshness, a connection's heartbeat); here it is reused for a *data lifecycle* signal instead — worth
noting as the same tool solving a different kind of problem, not a coincidence of naming.

A relational store is equally defensible at moderate scale and is the honest first answer if the
interviewer has not signalled they want the NoSQL depth probe — say so, the same way
[realtime-chat-delivery-guarantees.md §12.3](realtime-chat-delivery-guarantees.md) treats Postgres as
"genuinely sufficient" before reaching for anything else.

---

## 12 · Code the round may ask for

### 12.1 Base62 encode/decode

```python
class Base62:
    ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    BASE = len(ALPHABET)

    @classmethod
    def encode(cls, n: int) -> str:
        if n < 0:
            raise ValueError("n must be non-negative")
        if n == 0:
            return cls.ALPHABET[0]
        digits: list[str] = []
        while n:
            n, rem = divmod(n, cls.BASE)
            digits.append(cls.ALPHABET[rem])
        return "".join(reversed(digits))

    @classmethod
    def decode(cls, s: str) -> int:
        n = 0
        for ch in s:
            n = n * cls.BASE + cls.ALPHABET.index(ch)
        return n
```

```python
import unittest


class TestBase62(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(Base62.encode(0), "0")
        self.assertEqual(Base62.decode("0"), 0)

    def test_round_trip_over_a_range(self):
        for n in (1, 61, 62, 3844, 999_999, 56_800_235_583):
            self.assertEqual(Base62.decode(Base62.encode(n)), n)

    def test_encoding_is_shorter_than_decimal_at_scale(self):
        n = 56_800_235_583          # 62^6 - 1
        self.assertLess(len(Base62.encode(n)), len(str(n)))

    def test_negative_rejected(self):
        with self.assertRaises(ValueError):
            Base62.encode(-1)


if __name__ == "__main__":
    unittest.main()
```

### 12.2 The pre-generated key pool

*"How do you generate short codes without checking for a collision on every create request?"*

```python
class KeyPool:
    """Models the pre-generated-key-pool pattern: unique short codes are
    minted in bulk, ahead of demand, so the request path never has to
    check for a collision -- it only atomically claims one already-
    guaranteed-unique key.

    A production version splits generation across workers by handing each
    a disjoint numeric range (so no coordination is needed to avoid
    duplicate codes) and refills the pool asynchronously before it runs
    low; this models the checkout/refill contract those workers fill.
    """

    def __init__(self, low_watermark: int = 2) -> None:
        self.low_watermark = low_watermark
        self._available: list[str] = []
        self._used: set[str] = set()

    def refill(self, codes: list[str]) -> None:
        """Add newly minted, already-unique codes to the pool."""
        for code in codes:
            if code not in self._used and code not in self._available:
                self._available.append(code)

    def checkout(self) -> str | None:
        """Atomically claim one code. None means the pool is exhausted --
        the caller must trigger a refill and retry, never generate one ad
        hoc, or the uniqueness guarantee moves back onto the hot path."""
        if not self._available:
            return None
        code = self._available.pop()
        self._used.add(code)
        return code

    def needs_refill(self) -> bool:
        return len(self._available) <= self.low_watermark

    def release(self, code: str) -> None:
        """A checked-out code whose create request failed downstream (bad
        long_url, aborted request) goes back into the pool instead of
        being wasted."""
        if code in self._used:
            self._used.discard(code)
            self._available.append(code)
```

```python
class TestKeyPool(unittest.TestCase):
    def test_checkout_returns_an_available_code(self):
        pool = KeyPool()
        pool.refill(["aaa", "aab", "aac"])
        self.assertIn(pool.checkout(), {"aaa", "aab", "aac"})

    def test_checkout_never_returns_the_same_code_twice(self):
        pool = KeyPool()
        pool.refill(["aaa", "aab"])
        seen = {pool.checkout(), pool.checkout()}
        self.assertEqual(seen, {"aaa", "aab"})

    def test_exhausted_pool_returns_none(self):
        self.assertIsNone(KeyPool().checkout())

    def test_needs_refill_below_watermark(self):
        pool = KeyPool(low_watermark=2)
        pool.refill(["a", "b", "c"])
        self.assertFalse(pool.needs_refill())
        pool.checkout()
        pool.checkout()
        self.assertTrue(pool.needs_refill())

    def test_release_returns_a_code_to_the_pool(self):
        pool = KeyPool()
        pool.refill(["a"])
        code = pool.checkout()
        pool.release(code)
        self.assertEqual(pool.checkout(), code)

    def test_refill_does_not_duplicate_an_already_available_code(self):
        pool = KeyPool()
        pool.refill(["a"])
        pool.refill(["a", "b"])
        self.assertEqual(sorted([pool.checkout(), pool.checkout()]), ["a", "b"])
```

**What to say while writing it:** the interesting design property is not in this class at all — it is
that the *hard* part (uniqueness) has already happened by the time anything in this class runs. `checkout`
is intentionally boring: an `O(1)` pop and a set insert. That is the payoff of moving collision-handling
off the request path.

---

## 13 · Failure modes

| Component | Failure | Detection | Mitigation | User sees |
|-----------|---------|-----------|------------|-----------|
| Cache layer | Down | Connection errors, latency spike | Fall through to the store directly; the store is sized for a cold-cache burst (§6.1) | Slower redirects, not broken ones |
| Store | Down | 5xx rate | Cache still serves recently-seen codes; new/cold codes fail | Popular links keep working; brand-new links briefly fail |
| Key-pool generator job | Falls behind | Pool depth metric, `needs_refill` alert | Creation queues briefly or serves from a small emergency reserve; redirects are entirely unaffected | Create is slow; redirect is unaffected |
| Analytics stream (Kafka) | Down or lagging | Consumer lag metric | Click events buffer or drop at the edge; redirect is unaffected, click counts fall behind | No visible effect; internal metrics become stale |
| A single viral link | Massive concentrated read load | Per-key request-rate spike | Hot-key mitigation: in-process/edge caching of that one key, per §6.2 | No visible effect if caught before saturation |

---

## 14 · Working design vs good design, for this problem

| Working | Good |
|---------|------|
| "Generate a random string and check if it's taken" | A pre-generated key pool, so collision-checking happens offline and the request path is an atomic pop |
| "Base62 encode an auto-increment id" | Named as the simpler, legitimate default, with its cost stated explicitly: it reveals volume and needs coordinated or block-allocated counters across nodes |
| "Cache the mapping in Redis" | Cache-aside sized for a cold-start burst, plus a named hot-key mitigation for a viral link specifically, because more shards do not help one key |
| "Redirect with a 301" | 302, with the reasoning stated: a 301 gets cached by the browser itself, silently disabling analytics, expiry, and retargeting for every repeat visitor |
| "Increment a click counter on redirect" | Click events fired asynchronously into a stream and aggregated in windows, so a viral link cannot turn a read-path incident into write contention on one row |
| "Expired links get cleaned up by a cron job" | Expiry checked lazily at redirect time for correctness; the sweep job exists for storage hygiene, and the two are named as separate concerns |

---

## Interview questions

**1. Design a URL shortener.** **[Reported at Lyft]**
A pre-generated pool of unique short codes so the request path never checks for a collision, a
cache-aside read path in front of a keyed store sized for a cold-cache burst, and a 302 redirect —
deliberately not 301 — so the server sees every click and retains the ability to expire, retarget, or
measure the link later. Click analytics are emitted asynchronously so a viral link cannot turn a redirect
into a write-contention incident.

**2. How would you generate short codes at scale?**
Three real options: an auto-incrementing counter base62-encoded, which is simple but needs either a
centralised counter or block-allocated ranges per node to avoid a hot counter, and reveals creation
volume; a hash of the long URL truncated to a few characters, which needs real collision handling at that
length and gives a stable code per URL, which can be a feature or a bug; and a pre-generated pool of
already-unique codes checked out atomically, which is my default because it removes all collision logic
from the request path entirely.

**3. Why 302 instead of 301 for the redirect?**
Because a 301 is cached by the browser itself, not just an intermediate proxy — after the first click,
that browser never contacts the server again for that code, which silently breaks analytics, link
expiry, and the ability to ever retarget the link for that user. 302 costs one extra round trip per click
in exchange for keeping full control, which is the right trade for a product whose value is exactly those
capabilities.

**4. How do you keep click analytics from slowing down the redirect?**
The redirect handler emits a click event asynchronously and returns immediately without waiting on it; a
separate consumer aggregates counts in time windows rather than incrementing a row per click. That also
avoids turning a viral link's read spike into write contention on a single hot counter row. The cost is
that click counts become eventually consistent and can lose a small number of events under extreme
failure, which is an acceptable trade for a display counter and would not be for anything billed.

**5. How do you handle a viral link that gets a huge, sudden spike of traffic?**
It is a hot-key problem, not a scaling problem — sharding the store further does not help one key that
everyone is reading. The fix is replicating that one key everywhere it is read: an in-process cache on
every app instance, or a CDN edge cache in front of the redirect itself.

**6. How would you support custom aliases?**
The same table and the same uniqueness constraint as generated codes, checked at write time, plus a
reserved-word list checked first so a user cannot claim an alias that collides with an existing system
route. Abuse (alias squatting) is a rate-limiting problem on account creation, not a new uniqueness
mechanism.

**7. How do you handle link expiry?**
Lazily, at redirect time — checking `expires_at` against now is sufficient for correctness and needs no
background job. A periodic sweep still runs, but for a different reason: reclaiming storage, not
correctness, and conflating the two is a common imprecision worth avoiding out loud. An expired link
returns 410, not 404, because those are different facts about the resource.

**8. What store would you use, and why?**
A managed key-value store fits the access pattern cleanly — point lookups by short code at very high
volume, no ad-hoc queries — and native per-item TTL maps directly onto link expiry with no cleanup job at
all. A relational store is equally defensible at moderate scale, and I would say so rather than reaching
for NoSQL by default; the honest first answer depends on whether the interviewer is probing for that
depth.

**9. How many characters does the short code need?**
Sized from an explicit estimate, not a memorised number: at roughly 100 creates a second, a decade's
corpus is on the order of tens of billions of codes. Base62 at 6 characters gives about 57 billion
possible codes — technically enough but with little headroom — so 7 characters, giving trillions, is the
standard choice for comfortable headroom against the estimate being wrong.

**10. What would you change if click counts had to be exact rather than approximate?**
The asynchronous, eventually-consistent aggregation in question 4 would no longer be sufficient — exact
counts (for example, if clicks were billed) need a durable, deduplicated event log with idempotent
aggregation, which costs real latency and complexity. Naming that this design deliberately avoids that
cost, and precisely why the redirect's requirements do not need it, is the more useful answer than
building the expensive version by default.
