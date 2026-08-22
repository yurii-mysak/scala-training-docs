# Distributed Web Crawler — full worked design

> **Priority:** Required
> **Est. time:** 75 min
> **Track:** Server
> **HelloInterview:** System Design in a Hurry → Common Patterns → Managing Long Running Tasks, Scaling Reads/Writes; Advanced → Data Structures for Big Data; Core Concepts → Sharding

Reported at Lyft twice, once with the framing *"design a malware software that copies the whole
Wikipedia"* and once as a web crawler with explicit sub-questions on **API design, data schema, HTML
parsing, and real-time considerations**. A follow-up on **recovering after a site was down for 24
hours** is part of the reported question set.

---

## 1 · Handling the framing

The "malware" version is the same problem with a hostile wrapper. Handle it in one sentence and move
on — do not moralise, and do not pretend you did not notice:

> "I will design a large-scale crawler. I am going to design it to be a well-behaved one — robots.txt,
> per-host rate limits, identifying User-Agent, conditional requests — because those constraints are
> what make the interesting engineering problems appear. An impolite crawler is not a harder system; it
> is the same system with the hardest constraint deleted, and it gets your IP range blocked within an
> hour, which is a correctness problem as much as an ethical one."

That framing is a positive signal: it shows judgement, and it converts politeness from a moral point
into an engineering constraint you then design against.

---

## 2 · Requirements and scoping

### 2.1 Scoping questions worth asking

| Question | Why it changes the design |
|----------|---------------------------|
| One site or the open web? | One site means one host: politeness dominates and there is no frontier prioritisation problem |
| Do we need JavaScript rendering? | Headless browsers are 10–50x the CPU and change the whole fetcher tier |
| Freshness target — one snapshot or continuous recrawl? | A one-shot copy is a batch job; continuous recrawl is a scheduling system |
| What do we do with the pages — archive, index, extract? | Decides the storage shape and whether the parse output matters |
| Politeness budget — how much load may we put on one host? | The main throughput constraint on a single-site crawl |
| Is the crawl restartable, and what is the RTO? | Decides frontier durability |

### 2.2 Requirements

| # | Requirement |
|---|-------------|
| F1 | Fetch pages starting from a seed set, following discovered links within scope |
| F2 | Never fetch the same URL twice unnecessarily; detect duplicate *content* as well as duplicate URLs |
| F3 | Respect robots.txt and per-host rate limits |
| F4 | Store raw content plus extracted metadata and the link graph |
| F5 | Recrawl changed pages on a policy; do not recrawl unchanged ones |
| F6 | Resume without loss or a large amount of re-fetching after a crash |

| # | Non-functional |
|---|----------------|
| N1 | Politeness is a hard constraint, not a best effort |
| N2 | At-least-once fetch, idempotent storage — a duplicate fetch is waste, not a correctness bug |
| N3 | Horizontally scalable by adding fetcher workers |
| N4 | Bounded memory: the seen-set cannot grow without a plan |

### 2.3 Napkin math — "the whole Wikipedia"

State the assumptions, then the numbers ([napkin-math.md](napkin-math.md)):

```
~7 × 10^6 English articles (assumption, stated)   ·   ~100 KB HTML each
raw:      7e6 × 100 KB   = 0.7 TB          gzip ~5x -> ~0.14 TB
at 100 pages/s:  7e6 / 100 / 3600  ≈ 19 hours
at 1000 pages/s: 7e6 / 1000 / 3600 ≈ 2 hours,  bandwidth 100 MB/s ≈ 0.8 Gbps
```

**The conclusion that reframes the problem:** the data is *small* — under a terabyte, which fits on one
disk. So the design is not about storage scale; it is about **politeness throughput**. At a courteous
1 request/second to one host, 7 M pages takes 81 days. Every interesting decision follows from that
tension, and naming it early is the strongest opening move available.

Mitigations to offer immediately: use the official database dumps if the goal is a copy (the correct
engineering answer, and worth saying); otherwise negotiate a crawl-delay, use conditional requests, and
parallelise across the many hostnames a large site actually serves.

---

## 3 · Architecture

```
 [seeds] ─▶ ┌─────────────┐  lease   ┌──────────┐  fetch   ┌─────────┐
            │  FRONTIER   │ ───────▶ │ FETCHER  │ ───────▶ │  web    │
            │ (priority + │ ◀─────── │  pool    │ ◀─────── └─────────┘
            │  politeness)│  new URLs└────┬─────┘
            └─────────────┘               │ raw bytes
                  ▲                       ▼
                  │                 ┌──────────┐      ┌──────────────┐
                  │                 │  PARSER  │ ───▶ │ blob store   │ raw HTML (S3/WARC)
                  │                 │ + extract│      └──────────────┘
                  │                 └────┬─────┘
                  │  discovered URLs     │ links, canonical, text
                  │                      ▼
            ┌─────┴──────┐        ┌──────────────┐    ┌──────────────┐
            │  DEDUP     │◀───────│  URL norm    │    │ metadata KV  │ url_hash -> state
            │ seen-set   │        └──────────────┘    │ link graph   │
            │ + content  │                            └──────────────┘
            │   hashes   │                                   │
            └────────────┘                            ┌──────┴───────┐
                                                      │  SCHEDULER   │ recrawl policy
                                                      └──────────────┘
```

Each stage is a separate service for one reason each: fetchers are **I/O-bound and want high
concurrency**; parsers are **CPU-bound, crash on hostile input, and must be isolated**; the frontier is
**stateful and must be durable**. Say that reasoning — "microservices because it is nice" is not an
answer; "these three have different resource profiles and different failure modes" is.

---

## 4 · The frontier

### 4.1 Why a single global queue fails

A naive priority queue hands ten consecutive `wikipedia.org` URLs to ten workers, which is a
denial-of-service on one host and an idle crawler everywhere else. Politeness is per host; parallelism
is per worker; a single queue cannot express both.

### 4.2 The two-level (Mercator-style) design

```
front queues  F1..Fk   : priority classes. A URL is enqueued into Fi by priority.
back queues   B1..Bn   : exactly one HOST per back queue. n ≈ 3x worker count.
host -> back queue map : which queue serves which host
heap of (next_fetch_time, back_queue_id)
```

- A worker pops the earliest-due back queue from the heap; because a back queue holds exactly one host,
  **politeness is enforced structurally** rather than by a lock.
- When a back queue empties, it pulls from a front queue (biased to high priority) and re-binds to the
  new host.
- **Front queues give priority; back queues give politeness.** Explaining that separation of concerns in
  one sentence is worth several minutes of diagram.

### 4.3 Distributing it

**Partition the frontier by `hash(registrable_domain) % N`.** One shard owns a host, so:

- Per-host rate limiting is a local decision — **no distributed locks, no coordination on the hot path**.
- Robots.txt and DNS caches are naturally warm per shard.
- Rebalancing on scale-out moves hosts, not URLs; use consistent hashing so it moves 1/N of them.
  See [Partitioning & Rebalancing](../06-databases-and-distributed-data/Partitioning_Rebalancing.md).

Hash on the **registrable domain** (eTLD+1), not the full hostname, otherwise `a.example.com` and
`b.example.com` land on different shards and each thinks it owns the politeness budget for what is
usually one origin server.

### 4.4 Durability

| Option | Pros | Cons |
|--------|------|------|
| In-memory only | Fastest | Crash loses the frontier — unacceptable for a multi-day crawl |
| Kafka/SQS as the queue | Durable, replayable, backpressure for free | Priority and per-host scheduling are awkward in a log; ordering is per-partition |
| **DB-backed with lease** (`urls` table: `state`, `owner`, `lease_until`, `next_fetch_at`) | Priority, politeness, and restart all fall out of a single index. Crashed worker's lease simply expires | Needs an index scan; must avoid lock contention |
| Hybrid | Kafka for discovered-URL ingest, DB for scheduling state | Two systems, but each does what it is good at |

**The lease pattern is the answer to "what happens if a fetcher dies mid-page":** the URL's lease
expires, it becomes claimable again, and another worker refetches it. At-least-once, and safe because
storage is keyed by URL hash and therefore idempotent.

---

## 5 · Politeness and rate limiting

| Control | Mechanism | Notes |
|---------|-----------|-------|
| robots.txt | Fetch once per host, cache with TTL (24 h), honour `Disallow`, `Crawl-delay`, `Sitemap` | Treat a fetch failure as "allow with a conservative delay" or "deny", but pick one and say why |
| Per-host delay | Token bucket / next-allowed-time per host | Default 1 rps; adapt from observed latency |
| Adaptive rate | `delay = max(configured, k × observed_latency)` | A slow server is a server you are hurting |
| Backoff on errors | Double the delay on 5xx, honour `Retry-After` on 429 | Never retry-hammer |
| Concurrency cap | 1–2 in-flight requests per host | Delay alone does not bound concurrency |
| **Per-IP, not only per-host** | Resolve and group hosts by IP | Thousands of virtual hosts can share one server; per-host limits then multiply into a DoS. This is the detail that separates people who have run a crawler from people who have read about one |
| DNS | Cache with a floor TTL, use an async resolver | DNS is a classic hidden bottleneck; the default resolver is synchronous and blocking |
| Identity | Descriptive `User-Agent` with a contact URL | Makes you blockable — deliberately |

Code in §11.2 implements the per-host scheduler.

---

## 6 · Deduplication

Three distinct problems that candidates routinely conflate. Name all three.

### 6.1 URL normalisation (before anything else)

| Rule | Example |
|------|---------|
| Lowercase scheme and host | `HTTP://Example.COM` → `http://example.com` |
| Strip default port | `https://x.com:443/` → `https://x.com/` |
| Drop the fragment | `/p#section` → `/p` |
| Empty path → `/` | `http://x.com` → `http://x.com/` |
| Resolve dot segments and relative links | `../c/d` against `/a/b/page` → `/a/c/d` |
| Sort query parameters | `?b=2&a=1` ≡ `?a=1&b=2` |
| Drop tracking parameters | `utm_*`, `gclid`, `fbclid`, `ref` |
| Percent-encoding normalisation | Uppercase hex, decode unreserved characters |
| Optionally strip trailing slash, `index.html` | Risky: sometimes semantically different. Make it configurable |

Honest caveat to voice: normalisation is heuristic. Over-normalising merges distinct pages; under-
normalising wastes fetches. Prefer under-normalising and catch the rest with content hashing.

### 6.2 URL-seen set — bloom filter math

Ten billion URLs cannot live in a hash set. A bloom filter at 1% false positives costs **~10 bits per
element** (see [napkin-math.md §6.4](napkin-math.md)):

| URLs | 1% FP | 0.1% FP |
|------|-------|---------|
| 1 B | 1.2 GB | 1.8 GB |
| 10 B | 12 GB | 18 GB |

**The direction of the error matters and you must say it:** a bloom filter false positive means "we
think we have seen this URL when we have not", so we **skip a page**. A false negative is impossible, so
we never refetch something already crawled because of the filter. Losing 1% of pages is acceptable for
a broad crawl and *not* acceptable for "copy this specific site completely" — in which case use an exact
set, sharded by URL hash, in RocksDB or Cassandra, or a bloom filter as a *front filter* backed by an
exact lookup only on a hit.

That two-tier design — bloom filter to avoid 99% of lookups, exact store to confirm — is the answer
that gets both memory and correctness.

### 6.3 Content deduplication

| Level | Method | Catches |
|-------|--------|---------|
| Exact | SHA-256 of the normalised body | Mirrors, aliases, session-id URLs serving identical bytes |
| Near-duplicate | SimHash (64-bit) or MinHash; duplicates are within Hamming distance ~3 | Print versions, boilerplate-only differences, paginated reprints |
| Structural | Hash of the DOM shape | Template pages with different content — do **not** dedupe these |

Practical points: hash the *extracted text*, not the raw HTML, or a rotating ad slot makes every page
unique. Store the content hash in the page metadata so an unchanged recrawl is detected in one
comparison — this feeds the recrawl policy directly (§8).

Near-duplicate detection at scale needs a lookup structure, not pairwise comparison: bucket SimHashes by
several bit-slices (LSH) so candidates are found in O(1). Mention it; do not implement it live.

---

## 7 · HTML parsing and extraction

The reported question asked about HTML parsing explicitly, so do not wave at it.

| Concern | Handling |
|---------|----------|
| Library choice | Python stdlib `html.parser` is dependency-free and tolerant; `lxml` is 10–50x faster and is what you would actually run. **Say the trade-off — library choice is explicitly part of this round** |
| Malformed HTML | Never assume well-formed. Use a tolerant parser; never regex over HTML |
| Character encoding | HTTP `Content-Type` → `<meta charset>` → BOM → detection heuristic, in that order. Getting this wrong silently corrupts a whole language's worth of pages |
| Link extraction | `<a href>`, plus `<link rel=canonical>`, `<area>`, sitemap entries. Resolve against `<base href>` if present, else the response URL (after redirects, not the request URL) |
| `rel=nofollow`, `<meta name=robots>` | Honour `noindex`/`nofollow` |
| Content extraction | Boilerplate removal (readability-style heuristics) if you are storing text; keep the raw bytes regardless |
| Size caps | Cap response size (e.g. 10 MB) and parse depth. **Decompression bombs** are real: a 1 KB gzip can expand to gigabytes — cap the decompressed size, not just the transferred size |
| Content type | Fetch `HEAD` or check `Content-Type` before parsing; do not run an HTML parser over a 2 GB video |
| Redirects | Cap the chain (5), detect loops, record the final URL, and dedupe on the *final* URL |
| **SSRF guard** | Refuse URLs resolving to private/link-local ranges (`10/8`, `127/8`, `169.254/16`, `::1`). A crawler is a request forger by construction — the single most important security control in this design |
| Isolation | Run parsers in a separate pool with strict memory and CPU limits. A parser that OOMs must not take the fetcher with it |

---

## 8 · Scheduling and recrawl policy

For a one-shot copy this section is trivial. For a continuous crawl it is the heart of the system.

**Priority score:**

```
score = importance × staleness_urgency × host_budget_factor
  importance        : PageRank-ish, inbound-link count, depth from seed, or a manual tier
  staleness_urgency : time_since_last_crawl / expected_change_interval
  host_budget       : demote when a host's queue is already saturated
```

**Adaptive recrawl.** Model each page's change rate; a Poisson process with rate λ estimated from
observed change history is the standard treatment. Practical version:

- Page changed since last crawl → halve the interval (bounded below, e.g. 1 hour).
- Page unchanged → increase by 1.5x (bounded above, e.g. 30 days).
- Seed the interval from page type: a news index changes hourly, an archived article annually.

**Conditional GET is the highest-leverage optimisation in the whole design.** Store `ETag` and
`Last-Modified`; send `If-None-Match` / `If-Modified-Since`. A `304 Not Modified` costs ~300 bytes
instead of 100 KB. On a mature crawl where most pages are unchanged this cuts bandwidth by well over an
order of magnitude and lets you recrawl far more often within the same politeness budget. Also read
**sitemaps** (`<lastmod>`) — the site is telling you what changed for free.

---

## 9 · Storage and schema

The reported question asked for the data schema, so write it.

| Data | Store | Key | Why |
|------|-------|-----|-----|
| Raw HTML | S3 / blob store, WARC files | `content_hash` (content-addressed) | Immutable, dedupes identical bodies for free, cheap, no hot-key problem |
| Page metadata | DynamoDB / Cassandra | `PK = url_hash` | Point lookups by URL, high write rate, no ad-hoc queries needed |
| Frontier / schedule | Postgres or DynamoDB | `PK = host_shard`, `SK = next_fetch_at#url_hash` | Range scan for "what is due next" per shard |
| Link graph | Columnar/blob (Parquet) or a graph store | `(from_url_hash, to_url_hash)` | Written once, read in bulk by batch jobs — not an OLTP pattern |
| Seen-set | Bloom filter in memory + RocksDB/Cassandra | `url_hash` | See §6.2 |
| Search index | Elasticsearch, fed by CDC | | Eventually consistent, and say so |

```
pages (PK = url_hash)
  url                 text        # canonical, normalised
  registrable_domain  text
  status              enum(NEW, IN_FLIGHT, FETCHED, ERROR, BLOCKED_BY_ROBOTS, GONE)
  http_status         int
  content_hash        bytes(32)   # SHA-256 of extracted text; unchanged => skip reprocessing
  content_location    text        # s3://bucket/<content_hash>
  etag, last_modified text        # for conditional GET
  first_seen_at, last_fetched_at, next_fetch_at  timestamp
  fetch_interval_s    int         # adaptive, see §8
  error_count         int
  depth               int
  discovered_from     text        # url_hash of a referrer, for debugging and importance
```

**Key choices to defend:** `url_hash` (not the URL) as the partition key gives fixed-size keys and a
uniform distribution — a URL as a key range-partitions terribly because millions of URLs share a prefix.
`content_hash` as the blob key makes storage naturally deduplicated and writes idempotent: rewriting the
same content is a no-op. Both are worth one sentence each.

---

## 10 · Failure, restart, and the 24-hour site outage

### 10.1 General failure handling

| Failure | Handling |
|---------|----------|
| Fetcher crashes mid-page | Lease expires; URL becomes claimable; refetch. At-least-once |
| Parser crashes on hostile input | Isolated pool; mark the URL `ERROR`, increment `error_count`, DLQ after N attempts |
| Poison URL (always OOMs the parser) | Error budget per URL, then `GONE`; sample the DLQ for a human |
| Frontier shard lost | Rebuild from the `pages` table: everything with `next_fetch_at < now` and status not `IN_FLIGHT` |
| Seen-set (bloom filter) lost | Rebuild from `pages` by scanning `url_hash`; until then, extra refetches — waste, not corruption |
| Whole crawl restarted | The crawl's state *is* the `pages` table. Nothing else needs to survive |
| Duplicate fetch after retry | Harmless: content-addressed writes are idempotent |

**The principle to state:** at-least-once everywhere, idempotent storage, and no exactly-once
machinery. A crawler is the textbook case where paying for exactly-once buys nothing, because a
duplicate fetch costs bandwidth and no correctness. Cross-reference
[idempotency-and-deduplication.md](idempotency-and-deduplication.md).

### 10.2 The 24-hour site outage follow-up

*"A site you crawl was down for 24 hours. What happens, and how do you recover?"* This tests whether
your error handling loses work and whether your recovery is a thundering herd.

**During the outage — the wrong behaviours to name and reject:**

- Marking URLs `ERROR` and dropping them — silently loses a day of the frontier.
- Retrying at the normal rate for 24 hours — a pointless 86,400 requests against a dead host, and you
  are indistinguishable from an attacker when it comes back.

**During the outage — the design:**

1. **Per-host circuit breaker.** After N consecutive connection failures or 5xx, open the breaker for
   that host. The host's back queue is **parked, not drained** — its URLs stay in the frontier with
   `next_fetch_at` pushed out.
2. **Exponential backoff with a cap**, with jitter: 1 min, 2, 4, … capped at ~1 hour, so a 24-hour
   outage costs ~30 probe requests instead of 86,400.
3. **Cheap probes.** Half-open state sends a single request (ideally `HEAD` on a known-stable URL) and
   closes the breaker only after a couple of consecutive successes.
4. **Distinguish "down" from "blocking us".** 5xx and connection refused mean down; a sudden wall of
   403/429 means we are being rate-limited or banned, and the correct response is to slow down
   permanently, not to retry harder.
5. **Do not let one host's failure consume workers.** Parked hosts must not sit in the ready heap;
   otherwise fetchers spin on a dead host while other hosts starve. This is a bulkhead
   ([third-party-failure-modes.md](third-party-failure-modes.md)).

**On recovery — the catch-up plan:**

1. **What did we miss?** Nothing is lost: the frontier still holds the parked URLs, and everything else
   is discoverable by scanning `pages` for `next_fetch_at < now AND registrable_domain = host`. The
   backlog is `outage_duration / mean_fetch_interval` URLs.
2. **Ramp, do not flood.** A just-recovered server is the worst possible time to send a day's backlog.
   Ramp the per-host rate over minutes (10% of normal, doubling on sustained success), and keep the
   breaker half-open until latency returns to its pre-outage baseline. Watch **latency**, not just
   status codes — a recovering server returns 200s slowly before it returns them fast.
3. **Reprioritise the backlog.** Do not process it FIFO. Sort by importance × staleness so the front
   page and hub pages come back first; a deep archive page can wait another day. Cap the catch-up
   budget at a fraction (say 25%) of the host's steady-state rate so ongoing crawling is not starved.
4. **Do the catch-up cheaply.** Conditional GETs mean most of the backlog returns `304` — the backlog is
   far cheaper than the original crawl.
5. **Bound the pain.** If the backlog exceeds what can be caught up within one recrawl interval, drop
   the oldest low-priority entries deliberately and log the decision. Silently accumulating an
   unbounded backlog is how the *next* incident starts.
6. **Instrument it.** Alert on "host breaker open > 1 h", track backlog depth per host, and treat
   time-to-drain as an SLI.

The general lesson to say out loud: **park work, do not drop it; back off exponentially, resume with a
ramp, and prioritise the backlog rather than replaying it.** That answer generalises to every dependency
outage, which is why it is a good question.

---

## 11 · Code the round may ask for

### 11.1 URL canonicalisation

```python
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode, urljoin

TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term",
                   "utm_content", "gclid", "fbclid", "ref"}
DEFAULT_PORTS = {"http": "80", "https": "443"}


def canonicalize(url: str, base: str | None = None) -> str:
    """Normalise a URL so that equivalent URLs hash to the same key."""
    if base:
        url = urljoin(base, url)
    parts = urlsplit(url)
    scheme = parts.scheme.lower()
    host = parts.hostname or ""
    port = parts.port
    if port is not None and str(port) != DEFAULT_PORTS.get(scheme, ""):
        host = f"{host}:{port}"
    path = parts.path or "/"
    query = urlencode(sorted(
        (k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k.lower() not in TRACKING_PARAMS
    ))
    return urlunsplit((scheme, host, path, query, ""))     # fragment dropped
```

`urljoin` already resolves dot segments, so `../c/d.html` against `http://e.com/a/b/page.html` becomes
`http://e.com/a/c/d.html` without hand-rolled path logic. Reaching for the standard library instead of
writing a path normaliser is the readable choice, and readability is graded.

```python
import unittest

class TestCanonicalize(unittest.TestCase):
    def test_case_port_fragment_and_tracking(self):
        self.assertEqual(
            canonicalize("HTTPS://En.Wikipedia.ORG:443/wiki/Main_Page?utm_source=x#toc"),
            "https://en.wikipedia.org/wiki/Main_Page")

    def test_query_order_is_stable(self):
        self.assertEqual(canonicalize("http://e.com/p?b=2&a=1"),
                         canonicalize("http://e.com/p?a=1&b=2"))

    def test_relative_resolution(self):
        self.assertEqual(canonicalize("../c/d.html", base="http://e.com/a/b/page.html"),
                         "http://e.com/a/c/d.html")

    def test_nondefault_port_kept(self):
        self.assertEqual(canonicalize("http://e.com:8080/x"), "http://e.com:8080/x")
```

### 11.2 Per-host politeness scheduler

```python
import heapq
from collections import deque
from dataclasses import dataclass, field


@dataclass(order=True)
class _HostSlot:
    ready_at: float
    host: str = field(compare=False)


class PolitenessScheduler:
    """One worker owns a host, so per-host rate limiting needs no lock.

    Hosts become due at `ready_at`; a heap gives the next due host in
    O(log H). Delay per host is adaptive: it grows on errors and on slow
    responses and decays back toward the configured floor.
    """

    def __init__(self, default_delay: float = 1.0, max_delay: float = 60.0) -> None:
        self.default_delay = default_delay
        self.max_delay = max_delay
        self._queues: dict[str, deque[str]] = {}
        self._delay: dict[str, float] = {}
        self._heap: list[_HostSlot] = []
        self._queued: set[str] = set()

    def add(self, host: str, url: str, now: float) -> None:
        q = self._queues.setdefault(host, deque())
        q.append(url)
        if host not in self._queued:
            self._queued.add(host)
            heapq.heappush(self._heap, _HostSlot(now, host))

    def next_url(self, now: float) -> tuple[str, str] | None:
        """Return (host, url) if a host is due, else None (caller sleeps)."""
        if not self._heap or self._heap[0].ready_at > now:
            return None
        slot = heapq.heappop(self._heap)
        self._queued.discard(slot.host)
        q = self._queues.get(slot.host)
        if not q:
            return None
        url = q.popleft()
        if q:                                     # re-arm for the next fetch
            self._queued.add(slot.host)
            heapq.heappush(
                self._heap,
                _HostSlot(now + self._delay.get(slot.host, self.default_delay), slot.host))
        return (slot.host, url)

    def observe(self, host: str, ok: bool, latency: float, now: float) -> None:
        """Back off on failure, and never poll faster than the host answers."""
        cur = self._delay.get(host, self.default_delay)
        if ok:
            target = max(self.default_delay, latency * 2)
            self._delay[host] = max(
                self.default_delay, min(cur * 0.9 + target * 0.1, self.max_delay))
        else:
            self._delay[host] = min(max(cur * 2, self.default_delay), self.max_delay)

    def park(self, host: str, until: float) -> None:
        """Host is down: keep its URLs, retry after the backoff window."""
        if host in self._queued:
            self._heap = [s for s in self._heap if s.host != host]
            heapq.heapify(self._heap)
        self._queued.add(host)
        heapq.heappush(self._heap, _HostSlot(until, host))
```

```python
class TestPolitenessScheduler(unittest.TestCase):
    def test_respects_delay_between_fetches(self):
        s = PolitenessScheduler(default_delay=1.0)
        s.add("a.com", "http://a.com/1", now=0)
        s.add("a.com", "http://a.com/2", now=0)
        self.assertEqual(s.next_url(now=0), ("a.com", "http://a.com/1"))
        self.assertIsNone(s.next_url(now=0.5))
        self.assertEqual(s.next_url(now=1.0), ("a.com", "http://a.com/2"))

    def test_park_defers_without_losing_urls(self):
        s = PolitenessScheduler()
        s.add("a.com", "http://a.com/1", now=0)
        s.park("a.com", until=3600)
        self.assertIsNone(s.next_url(now=10))
        self.assertEqual(s.next_url(now=3600), ("a.com", "http://a.com/1"))
```

`park()` is exactly the §10.2 mechanism: the 24-hour outage becomes one method call and the URLs are
never lost. Being able to point at that is worth more than any amount of prose about resilience.

### 11.3 Bloom filter sizing (say it, do not implement it)

```python
import math

def bloom_bits(n: int, p: float) -> tuple[int, int]:
    """Return (bits, hash_count) for n items at false-positive rate p."""
    m = math.ceil(-n * math.log(p) / (math.log(2) ** 2))
    k = max(1, round(m / n * math.log(2)))
    return m, k
# bloom_bits(10_000_000_000, 0.01) -> ~9.6 bits/element, 7 hashes, ~12 GB
```

---

## 12 · API design

The reported variant asked for it explicitly.

```
POST /v1/crawls
  { "seeds": ["https://en.wikipedia.org/wiki/Main_Page"],
    "scope": { "allow_domains": ["en.wikipedia.org"], "max_depth": 6 },
    "politeness": { "max_rps_per_host": 1.0, "respect_robots": true },
    "budget": { "max_pages": 7000000, "max_bytes": 1000000000000 },
    "recrawl": { "mode": "adaptive", "min_interval_s": 3600 } }
  -> 202 { "crawl_id": "...", "state": "RUNNING" }

GET    /v1/crawls/{id}          -> counters: discovered, fetched, errors, bytes, eta
PATCH  /v1/crawls/{id}          -> { "state": "PAUSED" }   # pause/resume/cancel
POST   /v1/crawls/{id}/seeds    -> add seeds to a running crawl
GET    /v1/pages?url=...        -> page metadata + a signed URL for the stored content
GET    /v1/crawls/{id}/errors?after=<cursor>  -> paginated error sample for debugging
GET    /v1/hosts/{host}         -> current delay, breaker state, queue depth  (ops surface)
```

Points to make: crawl submission is **asynchronous** because the job runs for days (202 + a resource to
poll, not a blocking call); every list endpoint is **cursor-paginated**; `POST /crawls` takes an
idempotency key so a retried submission does not start two crawls; and the per-host ops endpoint exists
because "why is this host slow" is the question you will be asked in production every week.

---

## 13 · Real-time considerations

Also asked in the reported version.

- **Streaming discovery.** Discovered URLs go onto Kafka rather than a synchronous call, decoupling
  fetch rate from frontier write rate and giving replay for free.
  See [Kafka Fundamentals](../07-messaging-and-streaming/Messaging-kafka_fundamentals.md).
- **A priority lane.** A separate high-priority frontier partition for breaking content (sitemap
  `lastmod` changes, RSS/Atom, push protocols like WebSub) so fresh pages skip the normal queue.
- **Near-real-time indexing.** Parser output → Kafka → indexer → Elasticsearch, so a fetched page is
  searchable in seconds. State the consistency: search is eventually consistent with the crawl.
- **Change detection as a stream.** Content-hash comparison at parse time emits `page.changed` events;
  downstream consumers (index, alerting, diff storage) subscribe. Recrawl-interval adjustment becomes a
  consumer of that stream rather than a batch job.
- **Backpressure.** If the parser tier falls behind, the fetchers must slow down, not buffer. Lag on the
  raw-content topic is the control signal. See
  [Akka Streams & Backpressure](../03-akka-ecosystem/akka_streaming_and_backpressure_detailed_guide.md)
  for the mechanics.

---

## 14 · Working design vs good design, for this problem

| Working | Good |
|---------|------|
| "A queue of URLs and a pool of workers" | Two-level frontier: front queues for priority, back queues for politeness, sharded by registrable domain so politeness needs no locks |
| "We check a set so we do not refetch" | Bloom filter in front, exact store behind, with the false-positive direction and its cost stated |
| "We respect robots.txt" | Plus per-IP grouping, adaptive delay from observed latency, and a breaker that parks a host instead of hammering it |
| "Store pages in S3" | Content-addressed by `content_hash`, so identical bodies dedupe and writes are idempotent; metadata keyed by `url_hash` for uniform distribution |
| "Recrawl periodically" | Adaptive interval from observed change rate, driven by conditional GETs so most recrawls cost 300 bytes |
| "Retry on failure" | Park and back off exponentially; on recovery, ramp the rate and prioritise the backlog, with a capped catch-up budget |
| "It scales horizontally" | 7 M pages is 0.7 TB — the constraint is politeness throughput, not storage, and here is what follows from that |

---

## Interview questions

**1. Design a system that copies the whole of Wikipedia.** **[Reported at Lyft]**
Frontier of URLs partitioned by registrable domain, a fetcher pool, an isolated parser tier, and
content-addressed storage. The key observation is that 7 million pages at ~100 KB is under a terabyte —
storage is trivial — so the binding constraint is politeness: at one request per second, that crawl
takes 81 days. Everything interesting follows from that, and the honest first answer is to use the
published database dumps if the goal is a copy rather than a crawl.

**2. How do you avoid crawling the same page twice?** **[Reported at Lyft]**
Three layers: URL canonicalisation so equivalent URLs hash identically, a seen-set with a bloom filter
in front of an exact store, and content hashing to catch different URLs serving identical bytes. I say
the direction of the bloom filter's error explicitly: a false positive means skipping a page, which is
acceptable for a broad crawl but not for "copy this site completely", where the exact store behind the
filter is what preserves correctness.

**3. How do you enforce politeness across a distributed fleet?**
Structurally, by partitioning the frontier on registrable domain so exactly one shard owns a host —
then the per-host rate limit is a local decision with no distributed locking. Within a shard, one back
queue per host plus a heap of next-fetch times. I also group by resolved IP, because thousands of
virtual hosts can share one server and per-host limits would multiply into a denial of service.

**4. A site you crawl was down for 24 hours. What happens and how do you recover?** **[Reported at Lyft]**
A per-host circuit breaker opens after repeated failures and the host's queue is parked, not drained,
so no URLs are lost, and exponential backoff with a cap turns 86,400 pointless requests into about
thirty probes. On recovery I ramp the rate rather than flooding a just-restarted server, watch latency
rather than only status codes, prioritise the backlog by importance and staleness instead of FIFO, and
cap the catch-up at a fraction of steady-state so ongoing crawling is not starved. Most of the backlog
returns 304 anyway because of conditional GETs.

**5. What is your data schema?** **[Reported at Lyft]**
A `pages` table keyed by `url_hash` holding status, HTTP status, content hash, blob location, ETag and
Last-Modified, next-fetch time, adaptive interval, and error count; raw bodies in blob storage keyed by
`content_hash`; and the link graph written separately as a bulk-read dataset. `url_hash` rather than the
URL as the partition key because URLs share long prefixes and would partition terribly; `content_hash`
as the blob key because it makes storage deduplicated and writes idempotent.

**6. How do you parse HTML robustly?** **[Reported at Lyft]**
With a tolerant parser and never with regular expressions: `html.parser` if I must stay dependency-free,
`lxml` in production for the 10–50x speed. The details that actually bite are encoding resolution order,
resolving links against `<base href>` and the post-redirect URL, capping decompressed size against
compression bombs, and refusing URLs that resolve to private IP ranges — a crawler is a request forger
by construction, so SSRF is the security control that matters most.

**7. How do you decide when to recrawl a page?**
Adaptively: halve the interval when a page changed, extend it by half when it did not, bounded at both
ends and seeded by page type. The efficiency comes from conditional GETs — storing ETag and
Last-Modified means an unchanged page costs about 300 bytes instead of 100 KB, which lets me recrawl an
order of magnitude more often within the same politeness budget.

**8. What happens if a fetcher dies mid-page?**
Its lease on the URL expires and another worker claims it. The whole system is at-least-once with
idempotent, content-addressed storage, so a duplicate fetch costs bandwidth and nothing else. That is
the case where paying for exactly-once machinery buys literally nothing, and saying so is more useful
than building it.

**9. How would you make this near-real-time?**
Discovered URLs onto a log rather than a synchronous write, a separate high-priority frontier lane fed
by sitemaps, RSS, and push notifications, and a parse-to-index pipeline so a fetched page is searchable
in seconds. Change detection at parse time emits events that downstream consumers — the index, the
recrawl scheduler, alerting — subscribe to, and consumer lag on the raw-content topic is the
backpressure signal that slows the fetchers.

**10. How do you keep one slow or hostile host from consuming the whole fleet?**
Parked hosts leave the ready heap entirely, so workers never spin on a dead host; per-host concurrency
is capped independently of the delay; and response-size and time limits bound what one page can cost.
That is a bulkhead: the blast radius of one bad host is that host's own queue.
