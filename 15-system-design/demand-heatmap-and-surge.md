# Demand Heatmap and Surge Signal — full worked design

> **Priority:** Recommended
> **Est. time:** 45 min
> **Track:** Server
> **HelloInterview:** System Design in a Hurry → Advanced → Proximity Search, Time Series DBs; Common Patterns → Real-time Updates

**Reported at Lyft, close to verbatim:** *"How would you design a feature that tells Lyft drivers where in
the city has highest demand, and therefore higher fares?"* **[Reported at Lyft]** This file builds on
[driver-location-matching.md](driver-location-matching.md) rather than repeating it — read that one
first. The supply signal here is a read of the exact same index that file already built; what is new is
the demand side, the aggregation, the read path for a driver's map, and a genuinely interesting failure
mode: **the feature changes the thing it measures.**

---

## 1 · Frame the problem in one sentence

> "A pipeline that aggregates demand and supply per area over a short time window into a per-area 'heat'
> score, serves it to the driver app as a map layer refreshed every tens of seconds, and does not
> oscillate when drivers act on what it shows them."

The scoping trap: this sounds like the same real-time indexing problem as the previous file, and a
candidate who treats it that way rebuilds §5–§6 of
[driver-location-matching.md](driver-location-matching.md) and never reaches the part that is actually
being tested — the aggregation, the staleness/cost trade-off, and the feedback loop.

---

## 2 · Requirements and scoping

### 2.1 Functional

| # | Requirement |
|---|-------------|
| F1 | Aggregate a demand signal (ride requests, and unmatched search/app-open events) per area, over a rolling window |
| F2 | Aggregate a supply signal (available, online drivers) per area, from the existing location index |
| F3 | Derive a per-area score from the two and expose it as a map layer in the driver app |
| F4 | Refresh the layer on a cadence that is cheap, not on every underlying event |

### 2.2 Non-functional (the ones that drive the design)

| # | Requirement | Consequence |
|---|-------------|-------------|
| N1 | This is a **dashboard, not a matching decision** | Staleness of tens of seconds is acceptable and should be spent deliberately to buy cost — a very different latency budget from [driver-location-matching.md](driver-location-matching.md)'s milliseconds |
| N2 | The displayed signal must not oscillate | A flapping heatmap is worse than a slightly stale one — see §7 |
| N3 | Availability over freshness | Serve the last-known-good aggregate with an "as of" time rather than a blank map on a pipeline hiccup |
| N4 | Cost scales with area-time buckets, not with raw event volume, once past the aggregation stage | The read path must never recompute from raw events per request |

### 2.3 Out of scope — say it and get agreement

The actual **pricing function** that turns a heat score into a fare multiplier — that is a pricing/economics
model, not an infrastructure design, and conflating the two burns round time on the wrong problem. Scope
this file to: *produce the signal, reliably and without a feedback spiral*. What downstream pricing does
with the signal is a different system with a documented contract (a score in, a multiplier out).

### 2.4 Scale assumptions

```
Reuse driver-location-matching.md's supply-side numbers directly: ~300k online drivers, S2 level-5 cells
Assumption, stated: demand events (ride requests + unmatched searches) run ~3-5x ride-request volume,
  since most "I looked for a ride" moments do not become a request
Assumption, stated: a driver's map refreshes on a ~15-30s cadence -- a driver reading a phone mounted on
  a dashboard does not need, and should not get, per-second updates
```

| Quantity | Derivation | Answer | Design consequence |
|----------|------------|--------|---------------------|
| Aggregation buckets, citywide | ~thousands of level-5-ish cells per metro × a handful of active metros | Low tens of thousands | Trivially small to hold in memory or Redis — this is not a storage problem |
| Read QPS | 300k drivers polling/subscribing on a 15-30s cadence | ~10-20k/s **if done naively, per-driver** | The number that actually matters — see §5, this is exactly why the read path is pre-aggregated tiles, not per-request computation |
| Write-side aggregation rate | Demand + supply events, citywide | Tens of thousands/second at absolute peak | Handled by a streaming aggregator (§4), not by the read path |

**The number worth calling out explicitly:** the *write* side (ingesting events) is a well-understood
streaming-aggregation problem at a scale this program has already sized before
([driver-location-matching.md §2.4](driver-location-matching.md)). The *read* side is the one candidates
under-price — 300k drivers checking a map is a much bigger number than 300k drivers pinging a location,
because reads happen on every refresh whether or not anything changed, and that is what pushes this
design toward heavy pre-computation and caching rather than a live query per request.

---

## 3 · Signals

### 3.1 Demand

| Signal | What it captures | Why it matters |
|--------|---------------------|-----------------|
| Completed ride requests per area | The clearest, most reliable signal | Under-counts true demand, because it excludes riders who opened the app, saw no driver or a long wait, and gave up |
| **Unmatched searches / app-opens with no resulting request** | Latent demand — "wanted a ride, did not get one (or gave up before asking)" | Arguably the highest-value signal for *this specific feature*, because it is the leading indicator that supply should reposition toward, not a lagging one |
| Cancellations after a long wait | A demand signal disguised as a support problem | Cheap to fold in; correlates with under-supplied areas |

**Use both completed and unmatched signals, weighted, not just completed requests.** A design that only
counts completed rides is measuring where supply already *was* adequate, which is close to the opposite
of what a driver reading the map needs to know.

### 3.2 Supply

Read directly from the index [driver-location-matching.md §6](driver-location-matching.md) already
maintains — `ZRANGEBYSCORE` per cell for the fresh, available-driver count. **Do not build a second
supply-tracking system**; this file's only new supply-side work is aggregating that existing per-cell
count into the same time-windowed shape as the demand signal, so the two combine cleanly.

---

## 4 · Aggregation

### 4.1 Windowing

Tumbling windows (say, 60 s, non-overlapping) per cell, per signal type: count of demand events, snapshot
of available-driver count at window close. A tumbling window is the right default here — unlike the
matching design's need to react to every individual event, this is a periodic summary, and a tumbling
window is simpler to reason about and cheaper to compute than a sliding one when the consumer (§5) only
ever wants "the current summary," not a continuously recomputed trailing average.

### 4.2 Why H3, not S2, for the aggregation and display grid

[driver-location-matching.md §5.2](driver-location-matching.md) chose S2 for the hot-path index because
hash-friendly integer ids and hot-shard avoidance were what mattered. **Neither is the binding constraint
here.** What matters for a *heatmap a human looks at* is that neighbouring cells behave smoothly — a
hexagonal grid (H3) gives every neighbour the same distance and adjacency relationship, which avoids the
visual and numerical discontinuities a rectangular or S2-quad grid produces at cell boundaries when you
smooth or interpolate between them. **Say the contrast explicitly if asked**: this file and the previous
one solve adjacent problems and deliberately reach for different tools, because the property that
dominates the decision is different in each — hashability and hot-shard avoidance for the write-heavy
index, smooth adjacency for the human-facing display.

### 4.3 The score

```
raw_ratio(cell) = demand_events(cell, window) / max(available_drivers(cell, window), floor)
```

A `floor` (say, 1–2) avoids division blowing up in a cell with real demand and zero measured supply — a
cell with zero drivers is not "infinitely" hot, it is a data quality edge case, and the floor keeps the
score bounded and comparable across cells. The raw ratio then feeds the smoothing step in §7 before it is
ever displayed.

---

## 5 · The read path for the driver app

**Never compute a driver's map view from raw events on request** — that is the mistake the QPS number in
§2.4 is warning against. Instead:

```
[streaming aggregator] --writes--> [per-cell score cache, Redis or in-memory on a small fleet]
                                            │
                                            ▼
                               [tile builder: buckets cells into
                                map tiles at 1-2 zoom levels]
                                            │
                                            ▼
                         [CDN / edge cache, TTL matched to the
                          aggregation window, e.g. 30s]
                                            │
                                            ▼
                              driver app: GET /v1/heatmap/tiles/{z}/{x}/{y}
                                (polls on its own refresh cadence, or opens
                                 a low-frequency push channel for "layer updated")
```

- **Pre-aggregate into map tiles**, the same idea as a slippy-map tile server: one tile serves every
  driver looking at that part of the map, so the read cost is proportional to *tiles*, not to *drivers*.
- **Cache at the edge with a TTL matched to the aggregation window.** A 30 s aggregation window paired
  with a 30 s CDN TTL means the display is never more than one window stale, and the origin sees a request
  rate bounded by tile count and cache expiry, not by driver count — this is what actually resolves the
  10-20k/s naive read estimate from §2.4 down to something the origin barely notices.
- **A driver's own position determines which tiles they fetch**, not a per-driver query — the
  personalisation is entirely client-side (which tiles are on screen), so the server-side product is the
  same for every driver looking at the same patch of city.

---

## 6 · Staleness vs cost — the trade-off, made explicit

| Refresh cadence | Read cost | Staleness | Verdict |
|-------------------|-----------|------------|---------|
| Real-time (per-event push) | High — defeats the whole point of pre-aggregation | None | Wrong tool: a driver does not need sub-second demand data, and building for it wastes the design budget on a requirement nobody has |
| 5-10 s | Moderate | Low | Overkill for a feature whose consumer glances at a dashboard-mounted phone every so often |
| **30-60 s** | Low, cache-friendly | Low enough to still feel "current" | **The right default** — matches a driver's own repositioning decision timescale, which is minutes, not seconds |
| 5+ min | Very low | Noticeably stale, especially right after an event lets out | Only acceptable for a lower-priority secondary view (a "demand over the last hour" historical layer) |

**The general point to state:** pick the cadence from *how fast the consumer can act on the signal*, not
from how fast the signal *could* be produced. A driver cannot reposition in under a minute anyway, so
paying for sub-minute freshness buys nothing — and, per §7, can actively hurt.

---

## 7 · The feedback loop: showing the heatmap changes the thing it measures

This is the requirement that makes the problem interesting, and it is worth naming unprompted even if the
interviewer does not ask for it.

### 7.1 The mechanism

1. The map shows cell X as hot.
2. Drivers who see it reposition toward X — a rational, desired response.
3. Supply in X rises; the demand/supply ratio falls.
4. The *next* aggregation window shows X as no longer hot — but drivers who saw the *previous* window are
   still arriving, because there is a lag between seeing the signal and acting on it.
5. X can now be **oversupplied**, while the driver who reacted last is worse off than if the signal had
   never existed for them.

This is the same shape as the reconnect-storm and retry-storm failure modes elsewhere in this program
([realtime-chat-delivery-guarantees.md §5.4](realtime-chat-delivery-guarantees.md),
[rate-limiter.md](rate-limiter.md)) — a system reacting in bulk to a signal, with just enough lag that the
reaction overshoots and the signal itself was a lie by the time everyone acted on it. It is also a
concrete instance of a general observation worth citing: a widely publicised measure changes the
behaviour it measures (the folk formulation is Goodhart's Law) — naming that this is a known class of
problem, not a bug specific to this feature, is a good Staff-level move.

### 7.2 Mitigations, cheapest first

1. **Smoothing (EMA) plus hysteresis on the displayed tier**, not on the raw number — implemented in
   §9. This alone kills the highest-frequency flapping, where a cell hovers right at a tier boundary and
   would otherwise flip every window.
2. **Coarse buckets, not raw numbers.** Show "high / elevated / normal", not "2.3x". A driver chasing a
   precise number over-reacts to noise a bucketed signal absorbs for free, and a coarse signal is also
   simply less exploitable.
3. **Cap how many drivers effectively "see" a hot cell as directive** — if the product can rate-limit how
   aggressively the app pushes a hot-zone notification (versus a purely passive map layer a driver checks
   voluntarily), do that; a passive layer that a driver chooses to look at self-limits in a way a push
   notification to everyone nearby does not.
4. **Lead the signal instead of only reporting it**, if the investment is justified: a short-horizon
   forecast (demand expected in the next 10-15 minutes, not just demand right now) reduces the lag
   problem directly, because drivers arrive closer to when demand actually peaks rather than chasing a
   window that is already stale by the time they act. This is a real trade-off to name, not necessarily
   to build: a forecast model is a bigger investment than an aggregation pipeline, and the honest answer
   in a 45-minute round is "I would ship the reactive version with smoothing first, and only reach for a
   forecast once the reactive version's own logs show how much the lag actually costs."

---

## 8 · Storage

| Data | Store | Why |
|------|-------|-----|
| Current per-cell score (hot) | Redis or in-process cache on a small aggregator fleet | Sub-millisecond reads for the tile builder; ephemeral, rebuilds every window regardless |
| Rendered tiles | CDN / edge cache | The actual read path, per §5 |
| Windowed historical aggregates (hourly/daily rollups) | A columnar store fed by the same pipeline | Feeds demand forecasting and after-the-fact analysis — a batch/analytics concern, decoupled from the live path, same separation as the crawler's link graph being a bulk-read artifact rather than an OLTP table ([distributed-web-crawler.md §9](distributed-web-crawler.md)) |

Nothing here needs a bespoke time-series database at this scale (low tens of thousands of cells, minute-
scale windows) — a fact worth stating rather than assuming, the same "does this fit on something simple"
instinct [napkin-math.md §9](napkin-math.md) asks you to apply every time.

---

## 9 · Code the round may ask for

*"The displayed heat level flickers between two tiers every refresh when the real ratio hovers near a
boundary. Fix it."*

```python
class SurgeDisplay:
    """Smooths a raw per-cell demand/supply ratio into a stable displayed
    tier, so the driver-facing heatmap does not flicker every aggregation
    cycle -- the mechanism behind this file's feedback-loop mitigation (§7).

    Two techniques stacked. An exponential moving average damps noise in
    the raw ratio between updates. Hysteresis -- a wider band required to
    drop a tier than to enter it -- stops a ratio sitting right at a tier
    boundary from flapping the *displayed* tier on every aggregation cycle,
    which would otherwise send drivers a signal that changes faster than
    they can act on it.
    """

    # (entry_threshold, tier_name), ascending. Tier 0's threshold is unused.
    TIERS = [(0.0, "normal"), (1.3, "elevated"), (1.8, "high"), (2.5, "very_high")]
    HYSTERESIS = 0.15

    def __init__(self, alpha: float = 0.3) -> None:
        self.alpha = alpha
        self._ema: float | None = None
        self._tier_idx = 0

    def update(self, raw_ratio: float) -> str:
        """Feed one window's raw ratio; returns the (possibly unchanged) displayed tier."""
        self._ema = raw_ratio if self._ema is None else (
            self.alpha * raw_ratio + (1 - self.alpha) * self._ema)
        idx = self._tier_idx
        while idx + 1 < len(self.TIERS) and self._ema >= self.TIERS[idx + 1][0]:
            idx += 1
        while idx > 0 and self._ema < self.TIERS[idx][0] - self.HYSTERESIS:
            idx -= 1
        self._tier_idx = idx
        return self.TIERS[idx][1]
```

```python
import unittest


class TestSurgeDisplay(unittest.TestCase):
    def test_climbs_tiers_as_ratio_rises(self):
        d = SurgeDisplay(alpha=1.0)   # alpha=1 makes the EMA track the raw value exactly
        self.assertEqual(d.update(1.0), "normal")
        self.assertEqual(d.update(1.5), "elevated")
        self.assertEqual(d.update(2.0), "high")

    def test_hysteresis_prevents_flapping_near_a_boundary(self):
        d = SurgeDisplay(alpha=1.0)
        d.update(1.35)                                 # -> elevated
        self.assertEqual(d.update(1.25), "elevated")    # dips below 1.3, not below 1.15: holds
        self.assertEqual(d.update(1.35), "elevated")    # back up: no-op

    def test_a_genuine_drop_below_the_hysteresis_band_relaxes_the_tier(self):
        d = SurgeDisplay(alpha=1.0)
        d.update(1.35)
        self.assertEqual(d.update(1.10), "normal")      # 1.10 < 1.3 - 0.15

    def test_a_large_jump_moves_multiple_tiers_in_one_update(self):
        d = SurgeDisplay(alpha=1.0)
        self.assertEqual(d.update(2.6), "very_high")

    def test_ema_damps_a_single_noisy_spike(self):
        d = SurgeDisplay(alpha=0.3)
        d.update(1.0)
        # a one-window spike to 3.0 should not immediately read as very_high
        self.assertNotEqual(d.update(3.0), "very_high")


if __name__ == "__main__":
    unittest.main()
```

**What to say while writing it:** hysteresis alone, applied to the raw ratio, would not be enough — a
genuinely noisy signal can still cross a fixed band repeatedly. Stacking the EMA underneath it means
hysteresis only has to absorb boundary-hovering in the *smoothed* signal, which is a much smaller problem
than absorbing raw noise. Naming that the two techniques solve different halves of the flapping problem is
the detail that separates this from "I added a moving average" as a one-line answer.

---

## 10 · Failure modes

| Component | Failure | Detection | Mitigation | User sees |
|-----------|---------|-----------|------------|-----------|
| Streaming aggregator | Falls behind or crashes | Consumer lag metric | Serve last-known-good tiles with an "as of" timestamp; never blank the map | A slightly stale but present heatmap |
| Demand event source | Partial outage (one channel of demand events missing) | Per-source event-rate anomaly detection | Degrade gracefully to the remaining signal(s), flagged internally as lower-confidence | No visible change; internal confidence score drops |
| Supply index (shared with matching) | Down | Already covered in [driver-location-matching.md §13](driver-location-matching.md) | Same mitigation; this feature just reads a degraded input and should widen its own hysteresis band temporarily rather than trust a noisier signal at full sensitivity | Heatmap slower to update, not wrong |
| CDN / edge cache | Miss storm (cold cache after a deploy) | Origin request-rate spike | Origin still only serves tile-count-bounded traffic, not driver-count-bounded — this is exactly why pre-aggregation into tiles matters, the failure is bounded by design | Brief origin load increase, no user impact |
| One viral cell (stadium event) | A single cell's event rate spikes far above normal | Per-cell rate anomaly | Same hot-key mitigations as the supply index: this is a read-heavy hot key, not a write-heavy one, so simple caching absorbs it without a sharding change | No visible effect |

---

## 11 · Working design vs good design, for this problem

| Working | Good |
|---------|------|
| "Count ride requests per cell" | Weighted blend of completed requests *and* unmatched searches, because completed-only undercounts exactly the areas the feature exists to surface |
| "Use S2 cells, same as the matching system" | H3 for the display grid specifically, because smooth neighbour adjacency — not hashability — is what a human-facing heatmap needs |
| "Refresh the map every few seconds for freshness" | Cadence chosen from how fast a driver can act (minutes), not from how fast the pipeline could produce a number — and named as a deliberate cost/staleness trade-off |
| "Show the raw demand/supply ratio" | Smoothed with an EMA and displayed through a hysteresis band, because showing drivers a number that flickers makes their aggregate response worse, not better |
| "It's a real-time dashboard" | An explicit statement that showing the signal changes the signal, with a named mitigation, not just a pipeline diagram |
| "Cache it" | Pre-aggregated map tiles behind a CDN with TTL matched to the aggregation window, which is *why* the read side survives 300k drivers without ever touching the origin per-driver |

---

## Interview questions

**1. How would you design a feature that shows drivers where demand is highest?** **[Reported at Lyft]**
Aggregate a demand signal — completed requests plus unmatched searches, since completed-only undercounts
the areas most worth surfacing — and a supply signal read from the existing driver location index, both
windowed per area on a tens-of-seconds cadence. Serve it as pre-aggregated map tiles behind a CDN, because
the read side (hundreds of thousands of drivers checking a map) is the actual scaling problem, not the
aggregation. The interesting part is that showing the signal changes it: drivers react to a hot zone, and
a lagged, un-smoothed signal overshoots and flaps.

**2. Why would you use a different geospatial grid here than in the driver-matching design?**
Because a different property matters. The matching index needs hash-friendly integer cell ids and
hot-shard avoidance, which S2 gives cleanly. A heatmap a human looks at needs smooth behaviour between
neighbouring cells so the display does not show artificial discontinuities at cell boundaries, which is
what a hexagonal grid like H3 buys with its equidistant neighbours. Using the same tool for both would be
convenient, not correct.

**3. How fresh does this data need to be?**
Much less fresh than it looks like it should be. A driver reading a dashboard-mounted phone reacts on a
timescale of minutes, so a 30-60 second aggregation window is already faster than the driver can act on
it — spending engineering effort on a sub-second pipeline would buy freshness nobody can use, and would
make the feedback-loop problem in question 5 worse, not better.

**4. What is the read-side scaling problem here, and how do you solve it?**
Hundreds of thousands of drivers checking a map on their own refresh cadence, which is a much larger
number than the write-side aggregation rate. The fix is pre-aggregating into map tiles the way a slippy
map server does — one tile serves every driver looking at that patch of city — and caching those tiles at
the edge with a TTL matched to the aggregation window, so the origin's load is bounded by tile count and
cache expiry, not by driver count.

**5. What happens when the heatmap itself changes driver behaviour?**
Drivers reposition toward a shown hot zone, supply there rises, and by the time the next window reflects
that, more drivers who saw the *previous* window are still arriving — a lagged bulk reaction that
overshoots. I mitigate it by smoothing the underlying ratio with an exponential moving average, displaying
through a hysteresis band so the shown tier does not flap, and showing coarse buckets rather than a
precise number, which is both less noisy and less exploitable. A longer-horizon fix, if justified, is
forecasting demand instead of only reporting current demand.

**6. How do you prevent the displayed heat level from flickering?**
Two layers: an EMA damps noise in the raw ratio before it is ever compared to a tier boundary, and
hysteresis requires the smoothed value to clear a boundary by a margin to drop a tier, though it can climb
tiers immediately on a genuine rise. The two solve different halves of the problem — the EMA absorbs raw
noise, the hysteresis absorbs boundary-hovering in the already-smoothed signal — and neither alone is
enough.

**7. What would you leave out of the first version of this design?**
The pricing/fare-multiplier function itself — that is an economics model with its own validation process,
not an infrastructure decision, and scoping it out early keeps the round on the actual system-design
questions: signal quality, aggregation, the read path, and the feedback loop. I would also defer
forecasting and ship the reactive, smoothed version first, since it is a much smaller investment and its
own logs would tell you whether the lag problem is big enough to justify a forecast model.

**8. Why not just compute the heatmap on demand when a driver's app requests it?**
Because the read volume (hundreds of thousands of drivers, each refreshing every tens of seconds) is far
larger than the write volume (aggregation events), so computing per-request repeats the same aggregation
work an enormous number of times for an answer that barely changes between requests. Pre-computing on the
aggregator's own schedule and serving cached tiles turns a per-driver cost into a per-tile cost.

**9. How would you store the historical version of this data?**
Separately from the live path — hourly or daily rollups in a columnar store, fed by the same aggregation
pipeline, used for demand forecasting and after-the-fact analysis. The live path only ever needs the
current window's score, so coupling the two would make the hot path pay for a query pattern (long-range
historical analysis) it does not actually serve.

**10. What is the single most interesting design requirement in this problem?**
That the measurement changes the thing it measures. Most system-design prompts assume the system is a
passive observer; this one is a participant whose output causes the behaviour it reports on next, which
turns "how do I aggregate this efficiently" into "how do I aggregate this without creating an oscillation"
— a control-systems problem hiding inside what looks like a plain data-pipeline question.
