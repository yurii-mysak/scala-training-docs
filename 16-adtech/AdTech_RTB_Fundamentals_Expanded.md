# AdTech & RTB Fundamentals

This guide provides clear, detailed explanations of key concepts in AdTech and Real-Time Bidding (RTB), suitable even for those new to advertising technology.

---

## 1. Kafka Streams Commit Semantics

**Overview:**  
Kafka Streams is a client library for building streaming applications on Apache Kafka. It continuously processes data in motion, such as ad events, and ensures accurate state management through commit semantics.

**Definitions:**  
- **Offset:** A unique identifier for each record in a Kafka partition.
- **Commit:** The act of writing the current offset back to Kafka, marking records as processed.

### Commit Modes

1. **At-Least-Once Processing**  
   - **Behavior:** Offsets are committed after the application processes a record.  
   - **Implication:** If the application crashes *after* processing but *before* committing, records may be reprocessed on restart, leading to duplicates.  
   - **Use Case:** Acceptable when occasional duplicates are tolerable or deduplication downstream is trivial.  
   - **Best Practices:**  
     - Apply idempotent operations (e.g., counters that ignore duplicates).  
     - Use a deduplication store (e.g., Redis) keyed by event ID.

2. **Exactly-Once Processing**  
   - **Behavior:** Uses Kafka Transactions to atomically write output records and commit offsets in a single transaction.  
   - **Implication:** Guarantees each input record influences downstream exactly once, even across failures.  
   - **Use Case:** Billing or financial pipelines where duplicates or losses are unacceptable.  
   - **Configuration Example:**  
     ```scala
     val props = new Properties()
     props.put(StreamsConfig.PROCESSING_GUARANTEE_CONFIG, StreamsConfig.EXACTLY_ONCE_V2)
     ```
   - **Best Practices:**  
     - Monitor transaction abort metrics in Kafka (e.g., `transaction.abort.rate`).  
     - Tune `transaction.timeout.ms` to balance latency and failure handling.

---

## 2. Real-Time Bidding (RTB) Flow

**Overview:**  
RTB is an automated auction process in digital advertising where ad impressions are bought and sold in milliseconds.

### Step-by-Step Flow

1. **Bid Request**  
   - **Definition:** A message sent from an ad exchange to potential bidders containing details about the ad opportunity (user demographics, context, minimum bid price).  
   - **Example Fields:** user ID, device type, page URL, floor price.

2. **Bidder Decision**  
   - **Definition:** The bidder's logic that decides whether to bid, and at what price, often using machine learning to predict user value (eCPM, or effective cost per mille).  
   - **Example:** A simple rule might bid $1.50 if the predicted eCPM > $1.50.

3. **Auction**  
   - **Definition:** The process where the ad exchange compares all bid responses and selects the winner based on price and other criteria.  
   - **Types:**  
     - **Second-Price Auction:** Winner pays the second-highest bid plus a small increment.  
     - **First-Price Auction:** Winner pays their bid amount.

4. **Bid Response**  
   - **Definition:** The bidder’s reply indicating bid price, ad creative URL, and tracking URLs.

5. **Win Notification**  
   - **Definition:** A confirmation message sent by the exchange to the winning bidder, allowing them to serve the ad.

6. **Impression Tracking**  
   - **Definition:** Recording that the ad was displayed to the user, for billing and analytics.

**Key Consideration:**  
- **Latency Budget:** The entire cycle from bid request to bid response must complete within a strict timeframe (typically ≤ 100ms).

---

## 3. High-Scale Messaging Patterns for Bidding Engines

**Overview:**  
At high scale, hundreds of thousands of bid requests per second require robust messaging and processing patterns.

### Core Patterns

- **Partitioning**  
  - **Definition:** Dividing a Kafka topic into multiple partitions so that different consumers can read in parallel.  
  - **Example Key:** Partitioning by user ID ensures the same user’s events always go to the same partition.

- **Consumer Groups**  
  - **Definition:** A set of consumers that coordinate to read from partitions without overlap.  
  - **Benefit:** Allows horizontal scaling by adding more consumer instances.

- **Backpressure and Flow Control**  
  - **Definition:** Mechanisms to prevent consumers from being overwhelmed by too much data.  
  - **Implementation:** Use Reactive Streams libraries (e.g., Akka Streams) which automatically signal upstream to slow down.

- **Transactional Processing**  
  - **Definition:** Bundling writes to multiple topics and offset commits into a single atomic transaction.  
  - **Use Case:** Ensures billing and analytics pipelines remain consistent.

---

## 4. In-Memory Caches & Data Locality

**Overview:**  
Caching critical data (e.g., user segments or model features) in memory (such as Redis) reduces lookup latency in the bidding decision loop.

### Concepts

- **Data Locality**  
  - **Definition:** Ensuring data and compute are co-located to minimize network latency.  
  - **Implementation:**  
    - Align Kafka and Redis partitions on the same cluster nodes.  
    - Use client libraries that support connection pooling and pipelining.

- **Cache Warm-Up**  
  - **Definition:** Pre-loading frequently accessed data into cache on service start.  
  - **Benefit:** Avoids cold-start latency spikes.

- **Cache Miss Handling**  
  - **Definition:** Logic to fetch data from the primary store (e.g., database) when absent from cache.  
  - **Best Practice:** Perform cache fills asynchronously so bidding threads aren’t blocked.

---

## 5. Key Metrics in RTB

| Metric         | Definition                                         | Why It Matters                                         |
|----------------|----------------------------------------------------|--------------------------------------------------------|
| **CPM**        | Cost Per Mille – cost per 1,000 impressions.       | Standardized way to compare ad costs.                  |
| **Fill Rate**  | Percentage of requests that result in a bid above the floor price. | Measures coverage of eligible ad opportunities.        |
| **Bid-Win Ratio** | Ratio of won auctions to bid attempts.           | Indicates competitiveness and bidding efficiency.      |
| **Latency**    | Round-trip time from bid request to bid response.  | Critical to meet exchange deadlines (≤ 100ms).         |

---

*Diagram: RTB Flow*

```
Bid Request → [Bidding Pool] → Decision Engine → Auction → Bid Response
        ↓                                          ↑
   Impression Tracking ← Win Notification ← [Ad Exchange]
```

## 6. AdTech Ecosystem Roles

**Overview:**  
The RTB process involves multiple participants:

- **DSP (Demand-Side Platform):** Places bids on behalf of advertisers.
- **SSP (Supply-Side Platform):** Manages publisher inventory, sending bid requests to DSPs.
- **Ad Exchange:** The marketplace that matches bid requests (from SSPs) with bid responses (from DSPs).
- **Ad Network:** Typically aggregates inventory across publishers and can act as an SSP.

**Best Practice:** Understand each role’s integration points and APIs.

---

## 7. OpenRTB Protocol Overview

**Definition:**  
OpenRTB is a standardized JSON-based protocol for bid requests and responses.

**Key Fields:**
- `id`: Unique auction identifier
- `imp`: Array of impressions (ad slots)
- `site` / `app`: Contextual metadata
- `user`: User identifiers, segments
- `device`: Device characteristics

**Example Request Snippet:**
```json
{
  "id":"12345",
  "imp":[{"id":"1","banner":{"w":300,"h":250},"bidfloor":0.5}],
  "site":{"domain":"example.com","page":"https://example.com"},
  "device":{"ua":"...", "ip":"..."}
}
```

---

## 8. Bidding Strategies

- **Bid Shading:** In first-price auctions, automatically reduce the bid to the minimum needed to win, improving cost efficiency.
- **Dynamic Floor Pricing:** Adjust floor prices based on time of day, user segment, or inventory performance.
- **Frequency Capping:** Limit how often the same user sees an ad to avoid fatigue.

---

## 9. Monitoring & Observability

**Key Components:**
- **Metrics Collection:** Track request rates, latencies, error rates with Prometheus.
- **Dashboards:** Visualize SLIs/SLOs in Grafana (e.g., p95 latency ≤ 80ms).
- **Logging:** Centralize logs (bid requests, responses, cache misses) in ELK stack.
- **Alerting:** Configure alerts on high error rates or latency spikes.

---

## 10. Security & Privacy

- **GDPR/CCPA Compliance:** Ensure user consent; strip personally identifiable information (PII) when required.
- **Tokenization:** Use encrypted tokens for user identifiers.
- **Fraud Detection:** Monitor for invalid bid requests, bot traffic, and creative spoofing.

---

## 11. Machine Learning Lifecycle in RTB

- **Feature Store:** Central repository (e.g., Feast) for real-time features like user recency scores.
- **Model Training Pipeline:** Batch processes for historical data, stored in data warehouse.
- **Online Inference:** Low-latency feature retrieval and scoring in the bidding loop.
- **Model Monitoring:** Track drift and performance; schedule retraining.

---

## 12. Glossary of Key Terms

| Term               | Definition                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **eCPM**           | Effective Cost per Thousand Impressions: estimated revenue per 1,000 views. |
| **Floor Price**    | Minimum bid price required to participate in auction.                       |
| **Header Bidding** | Parallel bidding across multiple SSPs before calling the ad server.         |
| **Waterfall**      | Sequential bidding across SSPs based on priority and price.                 |
| **Impression**     | Display of an ad to a user.                                                 |

*End of Expanded Guide*