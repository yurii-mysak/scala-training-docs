# AdTech

Real-time bidding, OpenRTB protocol, and high-scale bidding engine architecture.

## Intermediate

| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 1 | OpenRTB protocol | [openrtb.md](openrtb.md) | Bid request/response format, protocol specification |
| 2 | RTB fundamentals | [AdTech_RTB_Fundamentals_Expanded.md](AdTech_RTB_Fundamentals_Expanded.md) | Auction mechanics, DSP/SSP/DMP, bid request flow, Kafka commit semantics |

## Advanced

| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 3 | High-scale bidding engine | [High-Scale-Bidding-Engine-Architecture-Expanded.md](High-Scale-Bidding-Engine-Architecture-Expanded.md) | Sub-100ms latency, millions QPS, pacing, budget management |

## Key Interview Questions by Level

**Intermediate**: What is RTB and how does the auction work? What are DSP, SSP, and DMP? Walk through a bid request lifecycle.

**Advanced**: How would you design a bidding engine that handles 1M+ QPS with sub-100ms latency? How do you implement budget pacing? What are the failure modes and how do you handle them?
