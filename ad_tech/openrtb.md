# Interview Preparation: IAB OpenRTB & AdTech Metrics

## 1. Introduction to IAB OpenRTB
The Interactive Advertising Bureau (IAB) Open Real-Time Bidding (OpenRTB) specification standardizes the protocol for real-time auctions in programmatic advertising. It defines JSON schemas for **BidRequest** and **BidResponse** messages exchanged between supply-side platforms (SSPs) and demand-side platforms (DSPs).

- **Latest Version**: OpenRTB 2.6 (or later); always check https://iabtechlab.com/standards/openrtb/ for updates.
- **Purpose**: Ensures interoperability, reduces integration friction, and accelerates auction performance.

## 2. Key JSON Schemas
### 2.1 Bid Request (`BidRequest`)
```json
{
  "id": "1234567890",
  "imp": [{
    "id": "1",
    "banner": { "w": 300, "h": 250 },
    "bidfloor": 0.5
  }],
  "site": { "id": "homepage", "domain": "example.com" },
  "device": { "ua": "Mozilla/5.0", "ip": "192.168.0.1" },
  "user": { "id": "A1B2C3" }
}
```
- **`id`**: Unique auction identifier.
- **`imp`**: Array of impressions (one per ad slot).
- **`bidfloor`**: Minimum bid price (in CPM).
- **`site` / `app`**: Context of the impression.
- **`device`** / **`user`**: Sender information for targeting.

### 2.2 Bid Response (`BidResponse`)
```json
{
  "id": "1234567890",
  "seatbid": [{
    "bid": [{
      "id": "1",
      "impid": "1",
      "price": 1.25,
      "adm": "<creative_markup>",
      "crid": "creative123"
    }]
  }],
  "cur": "USD"
}
```
- **`impid`**: Impression ID being bid on.
- **`price`**: Bid price in CPM.
- **`adm`**: Ad markup (HTML/JS).
- **`crid`**: Creative ID for tracking.

## 3. AdTech Metrics Explained
| Metric   | Definition                                                                 | Example                                                      |
|----------|-----------------------------------------------------------------------------|--------------------------------------------------------------|
| **CTR**  | Click-Through Rate: clicks ÷ impressions.                                    | 100 clicks / 10,000 impressions = **1%**                    |
| **CPM**  | Cost Per Mille: cost per 1,000 impressions.                                  | $5 CPM means $5 for every 1,000 impressions                 |
| **Win Rate** | Percentage of auctions won: bids won ÷ bids submitted.                   | 50 wins / 200 bids = **25%**                                 |

### Translating Metrics to Code
- **Low CTR** → Check creative performance; implement A/B testing.
- **High CPM** → Prioritize high-value impressions; adjust bid logic.
- **Low Win Rate** → Tune bid calculations; reduce underbidding.

## 4. Code Optimization Strategies
### 4.1 Caching Bid Logic
- **Why?**: Recomputing targeting and bid calculations for every auction is expensive.
- **How?**: 
  - Precompute static data (e.g., user segments) and store in in-memory cache (Redis).
  - Example (Java/Scala pseudocode):
    ```scala
    val userSegments = cache.getOrElseUpdate(userId, fetchSegmentsFromDB(userId))
    val bid = baseBid * segmentMultiplier(userSegments)
    ```
- **Best Practice**: Set appropriate TTLs; handle cache misses with fallback logic.

### 4.2 Reducing Serialization Overhead
- **Why?**: Converting between objects and JSON (jackson, circe) on every request adds latency.
- **How?**:
  - Use schema-aware serializers (e.g., Jackson after codegen).
  - Reuse `ObjectMapper` / codec instances.
  - Example (Java):
    ```java
    private static final ObjectMapper MAPPER = new ObjectMapper();
    ...
    String json = MAPPER.writeValueAsString(bidRequest);
    ```
- **Best Practice**: Warm-up serializers; use binary formats (e.g., Protocol Buffers) if supported.

## 5. Best Practices Summary
1. **Schema Validation**: Enforce JSON schema validation at ingress to catch malformed requests early.
2. **Monitoring & Metrics**: Track request/response latency, error rates, and bid metrics in real time.
3. **Graceful Degradation**: Implement fallback bidding logic when external systems (e.g., cache, DB) are unavailable.
4. **Threading & IO**: Use non-blocking IO and thread pools sized to hardware to avoid bottlenecks.
5. **Documentation & Versioning**: Pin OpenRTB version in client config; document extension fields clearly.

---

> _Diagram: Bid Flow Overview_
```
+---------+        HTTP JSON          +-------+        JSON        +-------+
| Exchange| -----------------------> |  DSP  | -------------------> |  Ad   |
|        (BidRequest)               | Logic |       (BidResponse)  | Server|
+---------+                        +-------+                      +-------+
```
