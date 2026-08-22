# Driver Location Matching — full worked design

> **Priority:** Required
> **Est. time:** 75 min
> **Track:** Server
> **HelloInterview:** System Design in a Hurry → Advanced → Proximity Search; Key Technologies → Redis; Core Concepts → Sharding, Consistent Hashing

The closest reported prompt is *"How would you design an ETA system for Lyft drivers?"* — ETA depends on
knowing where drivers are, so this file is the load-bearing prerequisite for that question and for
[demand-heatmap-and-surge.md](demand-heatmap-and-surge.md). It is also where the **real** Lyft
architecture is the answer, not an inspiration for one:
[lyft-architecture.md §5–§6](lyft-architecture.md) states the facts — Redis Cluster sorted sets keyed by
timestamp with ~30 s expiry, S2 cells at level 5, a ~30-second batching window before re-matching. This
file is the worked design that arrives at those facts from the requirements, rather than reciting them —
recite the conclusion and an interviewer will ask "why", and this file is the "why".

---

## 1 · Frame the problem in one sentence

> "A system that ingests a continuous stream of driver location pings at scale, keeps a queryable,
> bounded-freshness index of who is nearby, and — on a ride request — finds a small set of good
> candidates, decides an assignment, and dispatches it with a response deadline."

Notice the sentence has three distinct sub-problems that a weak answer conflates into one: **ingestion**
(write-heavy, one driver at a time), **indexing** (a spatial query structure that stays cheap as drivers
move continuously), and **matching/dispatch** (a decision problem with its own timing and fairness
rules). Treat them as three components with different scaling knobs, because they are.

---

## 2 · Requirements and scoping

### 2.1 Functional

| # | Requirement |
|---|-------------|
| F1 | Ingest a location ping from every online driver on a regular interval |
| F2 | Answer "which drivers are near this point, and available" for a ride request |
| F3 | Select a driver for a request and dispatch the offer with a bounded response time |
| F4 | Reassign automatically if the offered driver does not accept in time |
| F5 | Stop matching a driver the instant they go offline, lose signal, or are already on a trip |

### 2.2 Non-functional (the ones that drive the design)

| # | Requirement | Consequence |
|---|-------------|-------------|
| N1 | Freshness bounded, not perfect | A driver's position may be a few seconds stale; it must never be *wrong* (i.e. a driver who went offline 5 minutes ago must never be offered a ride) |
| N2 | Availability over strict consistency for the position index | Losing the index must be recoverable from the ping stream, not catastrophic |
| N3 | No hot shard, ever | The index must survive a dense downtown at rush hour without one node absorbing all the write and query load |
| N4 | Matching latency: candidate generation in tens of milliseconds | It runs on the synchronous path of a rider staring at a spinner |
| N5 | A driver never gets two simultaneous offers | The assignment step needs a claim/lock, not just a scored list |

### 2.3 Out of scope — say it and get agreement

Pricing/surge computation (that is
[demand-heatmap-and-surge.md](demand-heatmap-and-surge.md)), turn-by-turn routing and true road-network
ETA (a routing-engine problem, distinct from "how far as the crow flies, roughly weighted"), and payment
capture on trip completion.

### 2.4 Scale assumptions

Lyft does not publish driver counts, so state assumptions plainly and move on — the reasoning is what is
graded, not the number:

```
Assumption: ~300k drivers with the app in "online/available" state, concurrently, at global peak
Assumption: location ping every 4s while online (adaptive: faster approaching a pickup, slower idle)
Assumption: one dense metro at its own local peak sees ~3 ride requests/second
```

| Quantity | Derivation | Answer | Design consequence |
|----------|------------|--------|---------------------|
| Peak ping writes/s, globally | 300k / 4 | **~75k/s** | Close to a single Redis node's stated ceiling of 50k–150k ops/s ([lyft-architecture.md §5](lyft-architecture.md)) — this is *why* it is a **Cluster**, not one node |
| Memory for the position index | 300k × ~100 bytes/member ([lyft-architecture.md §5](lyft-architecture.md)) | **~30 MB** | Trivially small. Say this contrast out loud: **write throughput, not memory, is the binding constraint** here — the opposite of the usual "will it fit in RAM" instinct, and worth naming because it redirects the design conversation to sharding the write path rather than sizing a cache |
| Riders accumulated in one metro's 30 s batch window | 3/s × 30s | **~90** | A bipartite assignment problem of size ~90×90 is sub-millisecond to solve exactly. Matching is **local** — it partitions by geography — so a global QPS number is the wrong sizing input; the per-region, per-window count is what matters, and it is small everywhere except the very largest cities |
| Drivers in one dense S2-level-5 cell at rush hour | Qualitative, not a specific figure — see the level-5 caveat in §5.3 | Dozens to low hundreds | Small enough that a per-cell range query is cheap; large enough that a coarser level would not meaningfully reduce query fan-out |

---

## 3 · API surface first

```
POST /v1/drivers/{driver_id}/location
  { "lat": 40.7128, "lng": -74.0060, "heading": 87, "speed_mps": 6.2, "client_ts_ms": ... }
  -> 202 (fire-and-forget from the driver's point of view; see §4)

POST /v1/drivers/{driver_id}/availability   { "state": "online" | "offline" | "on_trip" }

POST /v1/match
  { "rider_location": {...}, "radius_hint_m": 3000 }
  -> 202 { "request_id": "..." }             # matching + dispatch happen async, see §8-9
  # result delivered over the same push channel as the dispatch offer (§4), not in this response

POST /v1/dispatch/{offer_id}/respond   { "driver_id": "...", "response": "accept" | "reject" }
```

**Location writes are `202`, not `200` with a body.** A driver's own app does not need to wait on the
write finishing — it needs the ping accepted and moving on, which is exactly the "durable path, not the
hot path" instinct that shows up throughout this program. `POST /match` is the same shape for the
opposite reason: the actual matching decision takes up to the batching window (§8), so the caller gets a
handle immediately and a push notification when there is a result, rather than holding a connection open
for up to 30 seconds.

---

## 4 · Transport: reuse the chat design, do not redesign it

A driver's app needs to **send** location pings and **receive** dispatch offers with a response deadline
— a genuinely bidirectional, low-latency channel. That is exactly the shape
[realtime-chat-delivery-guarantees.md §4–§5](realtime-chat-delivery-guarantees.md) already solved: a
stateful gateway tier holding a WebSocket (or gRPC bidi stream) per connected driver, a connection
registry in Redis keyed by driver id with a heartbeat TTL, and delivery as an optimisation over a durable,
pollable API. Say that explicitly rather than re-deriving it — **the only two things that differ here**:

| | Chat | Driver location |
|---|---|---|
| Payload direction that matters most | Both ways, symmetric | Mostly up (pings); down only matters for dispatch pushes, which are rarer and higher-stakes |
| What "the socket is disposable" buys | A dropped socket costs a resync | A dropped socket costs one missed ping — the *next* ping in ~4s repairs freshness; nothing to resync, because §7's staleness bound already tolerates a gap |
| The down-direction payload's failure cost | A missed message, recovered by sync | A missed dispatch offer if the driver is unreachable — recovered by cascading to the next candidate (§9), not by retrying delivery |

---

## 5 · Geospatial indexing

### 5.1 The access pattern that decides everything

The query that matters is **"who is within roughly R metres of this point, and fresh?"** — a radius
query against a store that must absorb ~75k writes/second (§2.4). That access pattern, not "what is the
most geometrically precise representation of the Earth", is what should drive the choice.

### 5.2 Geohash vs S2 vs H3 — the comparison, and why it is not close for this problem

| Scheme | Cell shape | Containment | Neighbour lookup | The failure mode that matters here |
|--------|-----------|-------------|--------------------|--------------------------------------|
| **Geohash** | Lat/lon rectangles, base-32 string | Prefix = containment — convenient in a string-keyed store | Adjacent cells can differ in their *first* character (an edge-of-the-world artefact of the encoding), so "give me the 8 neighbours" is not a trivial string operation | Rectangles distort badly toward the poles; a fixed-length prefix does not give a fixed-area cell globally |
| **S2** | Roughly square, equal-area-ish, integer 64-bit ids on a Hilbert curve | Cheap parent/child integer math | Well-defined neighbour and region-covering operations (a "give me the cells covering this disc" query is a first-class library operation) | None at this scale — this is why it is the right tool |
| **H3** (Uber) | Hexagons | Approximate — hexagons do not tile a sphere hierarchically without occasional pentagons | Every neighbour is equidistant, which is genuinely nicer for diffusion/smoothing (this is why [demand-heatmap-and-surge.md](demand-heatmap-and-surge.md) leans toward it for the *display* layer) | Imperfect parent/child containment makes exact hierarchical bucketing fussier than S2 for a hard sharding decision |

**For the hot-path index specifically, S2 wins on the property that matters most here: hot-shard
avoidance via a deliberately chosen, uniform cell granularity plus an integer id that hashes cleanly into
a shard space.** H3's equidistant neighbours are a real advantage for the smoothing problem in the
heatmap file; they do not help the ingestion/query problem this file is solving, which is why the two
files land on different tools for adjacent problems — say that contrast if asked, it shows the choice was
deliberate rather than "we picked the trendy one."

### 5.3 Why level 5, and the caveat about quoting it

Lyft's chosen level is **5** — a coarse level, roughly kilometre-scale cells.
**Verify the level-to-area mapping before quoting a specific area figure live**: each S2 level quarters
the area of the previous one, so the exact number is easy to misstate by an order of magnitude, and the
interviewer is testing whether you understand the *trade-off curve*, not whether you memorised a table.
The safe form of the answer: *"a coarse level — around 5 — because cell granularity is the direct
knob on hot-shard risk."* Full trade-off table and the Hilbert-curve reasoning for why the cell id must
be **hashed** into the shard space rather than range-sharded are in
[lyft-architecture.md §6](lyft-architecture.md) — do not re-derive it in the room, cite it and move to
what that file does not cover: the query mechanics in §6 below.

---

## 6 · The hot-path store: Redis sorted sets keyed by timestamp

### 6.1 The mechanism

```
key    = cell:<s2_cell_id>
member = driver_id
score  = last_ping_unix_ts

ZADD  cell:1234  1755859200  driver:42
ZRANGEBYSCORE cell:1234  (now-30)  +inf      # who is here AND fresh
ZREMRANGEBYSCORE cell:1234  -inf  (now-30)   # sweep the stale
```

Membership and freshness live in one structure because the score *is* the timestamp — a driver who goes
offline, crashes, or loses signal simply ages out of every query within the expiry window, with no
delete path and no cleanup job to fail. This is the **TTL-as-failure-detector** principle stated as a
general pattern in [lyft-architecture.md §5](lyft-architecture.md); the same idea reappears for the
connection registry and presence in
[realtime-chat-delivery-guarantees.md §5.2, §11](realtime-chat-delivery-guarantees.md) and for agent
availability in [support-case-routing.md](support-case-routing.md). Naming it once, as a pattern with
three independent applications in this program, is worth more than describing it three separate times.

### 6.2 The subtlety lyft-architecture.md does not spell out: cell-boundary transitions

A driver crossing a cell boundary writes their next ping to a **new** cell key. Their entry in the **old**
cell key is not removed — it simply stops being refreshed. For up to the expiry window (~30 s), that
driver can appear as a live candidate in **both** the old and the new cell.

**This is usually the right trade-off, not a bug to fix urgently:**

| Approach | What it costs | What it buys |
|----------|----------------|---------------|
| **Do nothing — let it age out** | A driver near a boundary is occasionally over-counted in the old cell for up to ~30 s; worst case, a match candidate list includes someone who just left that cell, which self-corrects on the next ~30 s matching cycle and only ever costs a slightly worse ETA estimate, never a wrong assignment | Zero extra Redis calls; the whole scheme stays exactly the two commands above |
| **Explicit move**: keep a small `driver:{id}:cell -> cell_id` lookup; on each ping, `ZREM` the old cell if it changed | Exact single-cell membership at all times | One extra read and a conditional `ZREM` on every ping — doubling the write-path cost for a correctness property that matching does not actually need, because §8's scoring step re-ranks by real distance anyway |

**State the conclusion, not just the table:** do nothing, because the cost of the stale membership is
absorbed by a downstream step (exact-distance filtering in §7) that already has to run regardless. Paying
for exactness earlier than the design needs it is the kind of "working but not good" decision the
protocol in [design-round-protocol.md §12](design-round-protocol.md) flags directly.

### 6.3 Sharding

Redis Cluster requires multi-key operations to share a hash slot; a cell's `ZADD`/`ZRANGEBYSCORE` pair is
single-key, so this is naturally cluster-friendly with no hash-tag gymnastics needed. The cell id is
**hashed** into the cluster's slot space (never range-sharded — see §5.3's cross-reference for why),
which spreads both the ~75k/s write load and per-cell query load across nodes roughly evenly, and is the
concrete mechanism that makes N3 (no hot shard) true rather than aspirational.

---

## 7 · Candidate generation: radius queries over S2 cells

A ride request's radius rarely aligns with exactly one cell — the rider could be near a cell edge, or the
useful search radius could span several cells. The query:

1. Compute the set of S2 cells covering a disc of the search radius around the rider (a standard
   region-covering operation any S2 library provides — this is a "reach for the library" moment, not a
   "derive the Hilbert curve math live" moment, same advice as the crawler file gives for URL parsing).
2. Issue `ZRANGEBYSCORE` against each covering cell **in parallel** — the same scatter-gather shape used
   for safety pre-checks and context enrichment in
   [support-case-routing.md §4.4, §5.1](support-case-routing.md), applied here to cells instead of
   services.
3. Union the results, then apply an **exact** distance filter (haversine, or a flat-Earth approximation
   at this scale — both are cheap) — the cell membership is a candidate *filter*, not the final answer,
   because cells are not circles and a driver in a covering cell can still be outside the true radius.
4. If too few candidates come back, **widen**: fall back to the cell's immediate neighbours before
   failing the request. State the fallback explicitly; "no candidates found" in a dense area almost
   always means the covering set was too tight, not that no drivers exist.

**Why not just scan a bigger single cell instead of unioning several small ones?** Because that is
exactly the "too coarse" failure mode from §5.3's trade-off table restated as a query-time problem: one
big cell means every query — even a tight-radius one — pays the cost of a dense-cell scan. Several small
covering cells queried in parallel cost about the same in latency (they run concurrently) and dramatically
less in the amount of data moved and filtered.

---

## 8 · The matching loop: scoring and the batching window

### 8.1 Why not greedy, instant assignment

Greedy — assign the nearest available driver to each request the instant it arrives — is locally optimal
and globally poor: a driver two minutes away gets committed to rider A while rider B, who was around the
corner from that same driver, ends up walking a route to someone far away. This is stated as Lyft's own
design choice in [lyft-architecture.md §8.3](lyft-architecture.md), and it generalises into the sharpest
transferable line in this whole file: **a batching window converts a stream of greedy online decisions
into a sequence of small offline optimisation problems, trading latency for solution quality.**

### 8.2 What happens inside one ~30-second window

1. Accumulate ride requests and eligible driver candidates (from §7, re-run at window close so positions
   are current) for one local region.
2. Score every plausible (rider, driver) pair — ETA (not straight-line distance; a road-network estimate
   or a learned model), driver acceptance likelihood, and a **waiting-time term** so a rider already
   through one window is not perpetually outbid by newcomers.
3. Solve the assignment: the Hungarian algorithm for an exact optimum on ~90-sized problems (§2.4) is
   cheap enough to just run; a good greedy-on-a-scored-bipartite-graph is the pragmatic fallback at any
   scale where exactness stops being free.
4. Supply that becomes available **during** the window (a driver finishing a trip mid-window) is eligible
   for that window's solve — say this, it is a detail that shows you modelled the window as a collection
   window, not a synchronous barrier that blocks new arrivals.

### 8.3 What it costs, stated as plainly as the benefit

Up to 30 seconds of added latency before a rider sees a driver — a direct UX cost, mitigated by showing
progress (searching-for-driver animation) rather than a blank wait. It also introduces a stateful,
region-scoped scheduler and the fairness requirement in step 2 above; without the waiting-time term, a
batching window is *systematically* unfair to early arrivals, not just occasionally.

---

## 9 · Dispatch: offer, accept, reject, and the cascade

The assignment from §8 is a **proposal**, not a guarantee — N5 (no double-booking) means the driver must
explicitly accept, and the design has to handle "did not respond" as the common case, not the exception.

```
match decided ──▶ offer sent to driver (via the gateway push channel, §4)
                         │
             ┌───────────┼──────────────────┐
             ▼           ▼                  ▼
          ACCEPT       REJECT           no response within deadline (~10-15s)
             │             │                  │
      driver claimed   next-best        next-best candidate offered,
      (see §9.2)       candidate         original driver's window closes
                        offered
```

### 9.1 Why this is the "job scheduler / interval-to-worker" laptop-round family wearing a dispatch costume

Offer-with-a-deadline-and-cascade-to-the-next-candidate is structurally the same problem as
[the job scheduler / interval-to-worker family](../17-lyft-laptop-round/05-job-scheduler-workers.md) —
one of the most-reported laptop-round families. A timer per outstanding offer, a callback (or poll) on
expiry, and a "who's next" selection are the whole mechanism; §12.1 below implements it directly with a
heap of expiries, the same structural tool as the connection-registry TTL code in
[realtime-chat-delivery-guarantees.md §15.2](realtime-chat-delivery-guarantees.md). If you have practiced
that family, this code is close to free.

### 9.2 Claiming a driver without double-booking

An offer must **reserve** the driver the instant it is sent, not the instant it is accepted — otherwise
two concurrent matching runs in adjacent regions could offer the same driver to two riders. A conditional
write (`SET driver:42:status "offered" NX EX 15`) at offer time is the primitive: the first offer wins the
key, a second matching attempt for the same driver observes the reservation and skips them. On accept,
the status advances to `on_trip` (also removing them from every cell's sorted set, since an on-trip driver
should not surface as a match candidate at all — an explicit removal here, not a TTL expiry, because the
driver is still actively pinging location for the trip, just not for matching purposes).

---

## 10 · Consistency, durability, and the actual source of truth

**Redis is a cache of derived state, never the source of truth — say this before anyone asks.** The
source of truth is the **ping stream itself**: every location ping is also published to a durable log
(Kafka), and the Redis sorted-set structure is rebuildable from that stream within one ping interval if
the whole cluster is lost. This is the identical shape to the chat design's connection registry
([realtime-chat-delivery-guarantees.md §5.2](realtime-chat-delivery-guarantees.md)): losing the fast-path
index degrades the system (drivers look briefly unavailable) rather than corrupting it (no driver's true
position is ever lost, because the next ping repairs it, and the log has everything before that).

The Kafka stream is also what feeds:

- **Trip reconstruction and analytics** — a full-fidelity, append-only record the hot-path index
  deliberately does not keep.
- **ETA and demand models** — training data for the systems referenced in the ETA and
  [demand-heatmap-and-surge.md](demand-heatmap-and-surge.md) questions.
- **Rebuilding the index after a regional failover**, replaying from the last-known offset.

---

## 11 · Storage model for history — the NoSQL depth probe, briefly

If pushed on where the durable ping history lives (rather than the ephemeral Redis index), the answer
follows the same shape as every other worked design in this section:

```
driver_location_history
  PK = driver_id#yyyymmdd        # bucketed by day, same reasoning as the chat design's conv#yyyymm
  SK = ts_ms
  lat, lng, heading, speed
```

`driver_id#yyyymmdd` bounds the partition (a driver's history for one day, not an unbounded item
collection) the same way the chat design buckets `conversation_id#yyyymm` — cite that precedent rather
than re-deriving the reasoning; a bounded partition key is the answer to "what breaks" for any
high-frequency, long-lived write pattern in this program.

---

## 12 · Code the round may ask for

### 12.1 Dispatch offer scheduler with timeout cascade

*"A driver has 15 seconds to accept an offer. If they don't, offer the next-best candidate. Implement
it."*

```python
import heapq
from dataclasses import dataclass, field


@dataclass(order=True)
class _PendingOffer:
    expires_at: float
    seq: int
    request_id: str = field(compare=False)
    driver_id: str = field(compare=False)


class DispatchScheduler:
    """Offers a ride to one candidate at a time, per request, cascading to
    the next-ranked candidate on reject or on timeout.

    Structurally the laptop round's job-scheduler / interval-to-worker
    family: a timer per outstanding unit of work, and a "who's next" step
    on expiry. Here the "worker" is a driver and the "job" is a ride offer.
    """

    def __init__(self, offer_timeout_s: float = 15.0) -> None:
        self.offer_timeout_s = offer_timeout_s
        self._candidates: dict[str, list[str]] = {}      # request_id -> remaining driver_ids, ranked
        self._pending: dict[str, _PendingOffer] = {}      # request_id -> current outstanding offer
        self._expiry_heap: list[_PendingOffer] = []
        self._counter = 0

    def start(self, request_id: str, ranked_driver_ids: list[str], now: float) -> str | None:
        """Begin dispatch for a request; returns the first driver offered, if any."""
        self._candidates[request_id] = list(ranked_driver_ids)
        return self._offer_next(request_id, now)

    def _offer_next(self, request_id: str, now: float) -> str | None:
        queue = self._candidates.get(request_id, [])
        if not queue:
            self._pending.pop(request_id, None)
            return None                                   # exhausted: no driver accepted
        driver_id = queue.pop(0)
        self._counter += 1
        offer = _PendingOffer(now + self.offer_timeout_s, self._counter, request_id, driver_id)
        self._pending[request_id] = offer
        heapq.heappush(self._expiry_heap, offer)
        return driver_id

    def respond(self, request_id: str, driver_id: str, accepted: bool, now: float) -> str | None:
        """Driver's answer to the *current* outstanding offer for this request."""
        current = self._pending.get(request_id)
        if current is None or current.driver_id != driver_id:
            return None                                   # stale response to an already-superseded offer
        if accepted:
            del self._pending[request_id]
            return driver_id                               # matched
        return self._offer_next(request_id, now)

    def sweep_expired(self, now: float) -> list[str]:
        """Call periodically. Returns request_ids that were re-offered due to timeout."""
        reoffered = []
        while self._expiry_heap and self._expiry_heap[0].expires_at <= now:
            offer = heapq.heappop(self._expiry_heap)
            current = self._pending.get(offer.request_id)
            if current is not offer:
                continue                                    # stale heap entry: already answered
            self._offer_next(offer.request_id, now)
            reoffered.append(offer.request_id)
        return reoffered
```

```python
import unittest


class TestDispatchScheduler(unittest.TestCase):
    def test_accept_matches_immediately(self):
        s = DispatchScheduler(offer_timeout_s=15)
        first = s.start("req-1", ["d1", "d2", "d3"], now=0)
        self.assertEqual(first, "d1")
        self.assertEqual(s.respond("req-1", "d1", accepted=True, now=1), "d1")

    def test_reject_cascades_to_next_candidate(self):
        s = DispatchScheduler(offer_timeout_s=15)
        s.start("req-1", ["d1", "d2"], now=0)
        self.assertEqual(s.respond("req-1", "d1", accepted=False, now=1), "d2")

    def test_timeout_cascades_without_an_explicit_reject(self):
        s = DispatchScheduler(offer_timeout_s=15)
        s.start("req-1", ["d1", "d2"], now=0)
        self.assertEqual(s.sweep_expired(now=10), [])          # not due yet
        self.assertEqual(s.sweep_expired(now=16), ["req-1"])   # d1 timed out, d2 now offered
        self.assertEqual(s.respond("req-1", "d2", accepted=True, now=17), "d2")

    def test_stale_response_after_timeout_is_ignored(self):
        s = DispatchScheduler(offer_timeout_s=15)
        s.start("req-1", ["d1", "d2"], now=0)
        s.sweep_expired(now=16)                                 # d1 timed out, d2 offered
        self.assertIsNone(s.respond("req-1", "d1", accepted=True, now=17))  # d1's late answer

    def test_exhausted_candidate_list_returns_none(self):
        s = DispatchScheduler(offer_timeout_s=15)
        s.start("req-1", ["d1"], now=0)
        self.assertIsNone(s.respond("req-1", "d1", accepted=False, now=1))


if __name__ == "__main__":
    unittest.main()
```

**The detail worth narrating while writing it:** `respond()` checks identity (`current.driver_id ==
driver_id`), not just "is there a pending offer" — a driver's answer arriving just after their offer
timed out and cascaded must be rejected as stale, exactly like the `reap()` staleness check in the
connection registry ([realtime-chat-delivery-guarantees.md §15.2](realtime-chat-delivery-guarantees.md)):
a heap entry surviving past the point it stopped being current is expected, and the fix is an identity
check at pop time, not preventing stale entries from existing.

### 12.2 A simplified stand-in for S2 cell bucketing

Real S2 needs a library (`s2sphere` or similar) — not stdlib, and not something to hand-roll live. To
demonstrate the *candidate-generation mechanics* (bucket by cell, gather neighbours to cover a radius)
without an external dependency, a plain equal-angle grid stands in for it:

```python
import math


def cell_id(lat: float, lng: float, precision_deg: float) -> tuple[int, int]:
    """A crude equal-angle grid cell, standing in for an S2/geohash cell.
    Real code reaches for a geospatial library; this exists to show the
    shape of the bucketing and neighbour logic without one."""
    return (math.floor(lat / precision_deg), math.floor(lng / precision_deg))


def covering_cells(lat: float, lng: float, radius_cells: int, precision_deg: float) -> list[tuple[int, int]]:
    """All cells within `radius_cells` of the point's cell -- a stand-in for
    an S2 region covering. `radius_cells` is chosen from the search radius
    and the cell size, e.g. ceil(search_radius_m / cell_size_m)."""
    cy, cx = cell_id(lat, lng, precision_deg)
    return [(cy + dy, cx + dx)
            for dy in range(-radius_cells, radius_cells + 1)
            for dx in range(-radius_cells, radius_cells + 1)]
```

```python
class TestCellBucketing(unittest.TestCase):
    def test_same_cell_for_nearby_points(self):
        self.assertEqual(cell_id(40.7128, -74.0060, 0.05), cell_id(40.7130, -74.0062, 0.05))

    def test_covering_returns_a_square_of_cells(self):
        cells = covering_cells(40.7128, -74.0060, radius_cells=1, precision_deg=0.05)
        self.assertEqual(len(cells), 9)                        # 3x3 including the centre cell
        self.assertIn(cell_id(40.7128, -74.0060, 0.05), cells)
```

---

## 13 · Failure modes

| Component | Failure | Detection | Mitigation | User sees |
|-----------|---------|-----------|------------|-----------|
| Redis Cluster node | Down | Cluster health check, node marked failed | Replica promotion; the lost slots' cells rebuild from the next ping cycle (~4 s) | A few seconds of thin candidate lists in the affected cells |
| Whole Redis Cluster | Down | Connection errors fleet-wide | Matching degrades to "no fresh candidates" briefly; rebuilds from Kafka replay or simply from the next wave of pings | Delayed matching, not lost drivers |
| Driver's connection | Drops mid-session | Gateway heartbeat TTL | Driver reconnects; missed pings simply age their cell entry, self-healing on reconnect | Brief "driver location updating" state |
| Dispatch offer | Driver never responds | Expiry heap sweep | Cascade to next candidate (§9, §12.1) | Slightly longer match time, invisible cause |
| Matching batch window | One region's solve is slow (huge event, stadium letting out) | Solve-time metric per region | Cap solve time; fall back to greedy assignment for the overflow rather than blocking the whole window | Slightly worse assignments during a spike, not a stall |
| Location ingestion service | Down | 5xx rate, health check | Drivers buffer a few pings client-side and flush on reconnect (bounded buffer, oldest dropped first — freshness matters more than completeness here) | Brief staleness, no crash |
| A single dense cell | Genuinely overloaded (a stadium, an airport) | Per-cell query latency | Split the hot cell into `cell:1234:{0..n}` sub-keys and fan out reads — the same named escape hatch as [lyft-architecture.md §5](lyft-architecture.md) | No visible effect if triggered before saturation |

---

## 14 · Working design vs good design, for this problem

| Working | Good |
|---------|------|
| "Store lat/lng in a database and query with a bounding box" | S2 cell index in Redis, chosen because the cell id both bounds the query fan-out *and* hashes cleanly into a shard space — a database bounding-box query cannot give you the second property |
| "Geohash is fine, everyone uses it" | Named the geohash/S2/H3 trade-off and picked S2 specifically for hot-shard avoidance via hashable integer ids, while noting H3 is the better tool for the *heatmap's* smoothing problem |
| "Match the nearest driver instantly" | A bounded batching window that turns greedy online assignment into a small offline optimisation, with a stated latency cost and a fairness term so early arrivals are not perpetually outbid |
| "Send the offer to the best driver" | Offer-claim-cascade with a reservation at offer time (not accept time) so two regions can never double-book one driver |
| "Redis holds the driver locations" | Redis holds a *derived, rebuildable* index; the ping stream in Kafka is the source of truth, and losing Redis is a freshness blip, not data loss |
| "It scales because it's Redis" | 75k writes/s at 300k drivers is why it's a **Cluster** with cell ids hashed across shards — the specific number that forces the specific architecture, stated out loud |

---

## Interview questions

**1. How would you design an ETA system for Lyft drivers?** **[Reported at Lyft]**
ETA depends on knowing current driver positions, which is this file's design: a hot-path spatial index
(S2 cells in Redis, scored by last-ping timestamp) gives current candidates near a point; true ETA then
needs road-network distance or a learned travel-time model on top of that raw proximity, not straight-line
distance. I would scope the round toward whichever half the interviewer cares about and say so explicitly
— proximity indexing versus travel-time estimation are different engineering problems that happen to
share an input.

**2. Why store active drivers in a Redis sorted set scored by timestamp instead of using a database with
a spatial index?**
Because the access pattern is "who is here and fresh right now", not "give me an exact geometric query",
and a sorted set answers both halves of that with one structure at Redis latency — a database round trip
per request at ~75k writes/second of ingest would not keep up, and a driver who disappears needs to
vanish from the index without a delete path, which the TTL-like score expiry gives for free.

**3. Why S2 over geohash or H3 for this specific problem?**
S2 cell ids are integers on a Hilbert curve with well-defined region-covering and neighbour operations,
and — critically for hot-shard avoidance — they hash cleanly into a shard space while staying spatially
coherent for query purposes. Geohash rectangles distort near the poles and have first-character
neighbour discontinuities; H3's hexagons are the better choice for the heatmap's diffusion/smoothing
problem, not for a sharded hot-path index, which is why the two adjacent designs in this program use
different tools deliberately.

**4. What cell level would you choose, and why?**
A coarse one — Lyft uses level 5 — because cell granularity is the direct knob on hot-shard risk: too
fine and a radius query fans out across too many cells while per-cell overhead dominates; too coarse and
a whole dense district becomes one key on one node. I would not quote an exact area figure without
double-checking it live, because each level quarters the previous one's area and misquoting by an order
of magnitude is an easy, visible mistake.

**5. A driver crosses a cell boundary. What happens to their old cell entry?**
It is not explicitly removed — it ages out on the existing TTL-like expiry within the normal freshness
window, so for a short overlap the driver can appear as a candidate in both cells. That is an acceptable
trade because the downstream exact-distance filter already has to run regardless of cell membership, so
the stale entry costs nothing beyond a slightly wider candidate set for a few seconds — cheaper than
paying for an extra read-and-remove on every single ping to guarantee exact single-cell membership.

**6. Why does matching wait roughly 30 seconds instead of assigning instantly?**
Because instant greedy assignment is locally optimal and globally poor — it can commit a nearby driver to
one rider while a closer rider ends up with someone far away. Batching turns a stream of greedy decisions
into a small offline assignment problem solved with real optimisation, at the cost of added latency and
the need for a waiting-time fairness term so early arrivals are not perpetually outbid by new ones.

**7. How do you prevent two riders from being matched to the same driver?**
A conditional reservation at **offer** time, not at accept time — the first matching attempt to write a
"this driver is offered" key with a short expiry wins it; a concurrent attempt for the same driver in an
adjacent region observes the reservation and moves to its next candidate. Waiting until accept to
reserve would leave a race window between two concurrent offers.

**8. What happens if the whole Redis cluster holding driver locations goes down?**
Matching degrades — candidate lists go thin or empty — but no data is actually lost, because Redis holds
a derived index, not the source of truth. Every location ping is also published to a durable log, so the
index rebuilds itself within roughly one ping interval as pings continue arriving, and can be replayed
from the log if a faster rebuild is needed.

**9. How would this scale to 10x the driver count?**
Memory is a non-issue even at 10x — tens of megabytes either way. Write throughput is the actual
constraint, and it scales by adding Redis Cluster shards, since cell ids are already hashed (not
range-sharded) into the slot space specifically so that adding capacity spreads load rather than
concentrating it. The one thing that does not scale by adding shards is a single genuinely hot cell — an
airport or a stadium — which needs the explicit sub-key-splitting escape hatch rather than more shards.

**10. What data structure or algorithm would you use to solve the actual assignment inside a batch
window?**
The Hungarian algorithm for an exact optimum when the batch is small — and because matching is scoped per
region, batches here are typically tens to low hundreds of riders and drivers, well within where an exact
solve is cheap. At a size where that stops being true, a greedy assignment over pairs sorted by score is
the standard fallback, accepting a slightly worse total outcome for a much cheaper solve.
