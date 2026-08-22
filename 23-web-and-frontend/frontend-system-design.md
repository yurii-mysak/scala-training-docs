# Frontend System Design

> **Priority:** Recommended
> **Est. time:** 60 min
> **Track:** Server + Web
> **HelloInterview:** System Design in a Hurry → Common Patterns → Real-time Updates

*Conditional Web track — see the [section README](README.md) before investing time here; skip
if the recruiter hasn't confirmed Web scope.*

If the Web half of this role is in scope, this is the one file in the directory worth treating
as load-bearing: the design rounds are where a Server+Web candidate is actually differentiated,
and Lyft's design rounds already include real coding, code review, and library choices rather
than staying abstract — that holds whether a given round leans backend or frontend.

---

## 1 · A distinct discipline, not a smaller backend design round

Backend system design optimizes for scale you mostly don't let the user see: sharding,
replication lag, consistency windows. Frontend system design optimizes for constraints the user
experiences directly and immediately:

- **Perceived performance** matters as much as actual latency — a spinner that appears instantly
  reads better than a faster response that appears with no feedback in between.
- **Network unreliability is visible**, not hidden behind a retrying load balancer — the client
  has to decide what the user sees while a request is in flight, retried, or failed.
- **The runtime isn't yours.** A backend service runs on infrastructure you control; a browser
  tab runs on a device, network, and browser build you don't — the design has to degrade
  gracefully rather than assume a clean environment.
- **State consistency is watched in real time.** A backend can be eventually consistent for
  milliseconds without anyone noticing. A UI that shows stale or self-contradictory state for
  the same window is a visible bug.

The rubric follows from this: sensible component and state boundaries, an articulated rendering
and caching strategy, a plan for network failure — not throughput numbers.

## 2 · Component decomposition and state ownership

The organizing principle: **state lives at the lowest common ancestor of the components that
need it — no lower, and no higher.** "Lift state up" only as far as the nearest shared parent
actually requires; anything higher is unnecessary re-render surface and unnecessary coupling.

Not all state is the same kind, and treating it as if it were is the most common design mistake:

| Category | Lifecycle | Where it lives |
|---|---|---|
| Local UI state | Owned entirely by one component | `useState` in that component |
| Shared UI state | A few sibling/related components | Lifted to their common ancestor, or a small context |
| Server cache state | Has its own loading/stale/error lifecycle, originates outside the client | A cache library (React Query/SWR), never mixed into local state |
| URL state | Should be shareable, bookmarkable, back-button-safe | The URL itself (query params/route segments) |
| Global app state | Genuinely needed everywhere, changes rarely | A store, or context split narrowly enough to avoid over-rendering |

The container/presentational split from the pre-hooks era is largely obsolete — a custom hook
now extracts the "container" logic without forcing a matching shape onto the component tree.
Context is well-suited to low-frequency, broadly-needed values (auth identity, theme) and poorly
suited to anything else: every consumer re-renders on any change to the value it reads, so
high-frequency state (form input, live data) or server-derived state belongs in a dedicated
store or cache library instead, not Context used as a general state-management substitute.

## 3 · Rendering strategy: CSR vs SSR vs SSG vs ISR

| Strategy | HTML built | First paint | SEO | Ongoing cost | Fits |
|---|---|---|---|---|---|
| **CSR** | In the browser, after JS loads | Slower first paint, nothing to show until JS runs | Poor without extra work | No hydration step — render *is* the first render | Authenticated dashboards, internal tools |
| **SSR** | Per request, on the server | Fast — real content arrives with the HTML | Good | Hydration: re-run render client-side to attach handlers | Personalized pages that also need to be crawlable |
| **SSG** | At build time | Fastest — served as a static file, cacheable at the edge | Best | Hydration, same as SSR | Content identical for everyone, changes rarely |
| **ISR** | At build time, revalidated on a timer or on demand | Same as SSG between revalidations | Best | Same as SSR/SSG | Content that changes but not per request |

The trade is essentially TTFB and crawlability against infrastructure complexity and hydration
cost. An authenticated, per-user surface — a support console, an internal dashboard — usually
has nothing to make crawlable and no content shared across users, so CSR is frequently the
*correct* default there rather than a compromise; reaching for SSR because it's "more modern"
without a concrete TTFB or SEO reason is itself a design smell worth flagging out loud.

## 4 · Data fetching and caching

The recurring failure mode is the **waterfall**: component A fetches, then renders component B,
which only then starts its own fetch — two sequential round trips where one would do. Fixes:
fetch in parallel at a shared ancestor and pass data down, prefetch on a signal that precedes
navigation (link hover, route-transition start), or colocate the fetch with the component that
needs it if using a model (Server Components) where that hop is server-to-server and therefore
cheap.

A client cache library (React Query, SWR) earns its place over hand-rolled `useEffect` fetching
for three reasons: **stale-while-revalidate** by default (show cached data immediately, refetch
in the background instead of blocking on a spinner every time), **request de-duplication**
(two components requesting the same key inside one render pass collapse to one network call),
and a consistent **invalidation** story on mutation (a write invalidates the cache keys it
affects, rather than every consumer manually refetching).

## 5 · Optimistic updates and rollback

Pattern: apply the update to local/cache state immediately, send the mutation, reconcile on the
real response. On error, roll back to the pre-update snapshot (cache libraries retain this for
you) and surface the failure rather than silently reverting.

The sharp edge is **creates**: the client doesn't have the server-assigned id yet when it
optimistically renders the new item. Assign a temporary client-side id, keep the item keyed by
that id in any list, and swap it for the server-assigned id when the response lands — without
ever reusing a temp id for a different entity once that swap happens.

Optimistic updates aren't free of judgment calls: skip them where "it looked like it worked and
then reversed" is worse than a brief spinner — an irreversible action or anything payment-shaped
is a case where the honest wait beats the confident-looking rollback.

## 6 · Real-time updates in the browser

| Mechanism | Direction | Reconnect | Infra friction | Fits |
|---|---|---|---|---|
| **Polling** | Client-pull | Trivial — it's just another request | Works through anything | Low-frequency updates where simplicity beats latency |
| **SSE** | Server push, one-way | Browser auto-reconnects (`EventSource`), resumable via `Last-Event-ID` | HTTP-based, proxy/LB-friendly | Server-to-client streams: notifications, live logs, token-by-token AI output |
| **WebSocket** | Full duplex | Manual — reconnect/backoff/resubscribe is your code | Needs the whole path (load balancer, service mesh, proxy) to support the upgrade | Bidirectional and latency-sensitive: chat, presence, collaborative editing |

This is the browser-side half of the decision only. For the delivery-guarantee side — ack
semantics, ordering, at-least-once vs exactly-once, backpressure — see
[Real-Time Chat Delivery Guarantees](../15-system-design/realtime-chat-delivery-guarantees.md).
The two halves are meant to be read together: that file covers what the server promises, this
section covers what the client does with what actually arrives.

---

## 7 · Worked example: a customer-support chat UI

This isn't an arbitrary choice of example. A multi-agent customer-support platform is the
literal product domain closest to this role — whatever the backend agent-routing architecture
looks like underneath, something has to render the conversation for the human on the other end
of it.

**Requirements.** Functional: a live conversation transcript, sending messages with visible
delivery status, typing indicators, a conversation queue with paginated history, attachments.
Non-functional: feels immediate despite an unreliable mobile network on the rider/driver side,
recovers from a dropped connection without losing or duplicating messages, stays smooth on long
conversation histories.

**Component decomposition:**

```
SupportConsole
├── ConversationList         (queue, virtualized)
└── ConversationPane
    ├── ConnectionStatusBanner
    ├── MessageThread        (virtualized)
    │   ├── MessageBubble
    │   └── TypingIndicator
    └── Composer
```

**State ownership:**

| State | Owner | Category |
|---|---|---|
| Message history pages | Cache entry keyed by `conversationId` + page | Server cache |
| Live incoming messages | Same cache entry, appended by the socket handler | Server cache |
| Composer draft text | `Composer`, local | Local UI |
| "other side is typing" | `ConversationPane`, driven by socket events, locally TTL-expired | Shared UI, ephemeral |
| Selected conversation id | The route (`/conversations/:id`) | URL state |
| Connection status | A small store read by the banner and by `Composer` (to disable send while offline) | Shared UI |

**Rendering strategy: CSR**, as a considered choice, not a default. This is an authenticated
surface with nothing to index and no content shared across users — SSR would buy latency this
screen has no personalization-vs-crawlability trade to spend it on.

**Data fetching:** the conversation list and the active conversation's first page of history
fetch in parallel at the `SupportConsole` level, not serially. Older history loads on scroll-up
via cursor-based pagination (see [api-integration-patterns.md](api-integration-patterns.md)).
The socket for the active conversation opens once; both the initial page and live updates land
in the same cache entry so the thread never has two sources of truth for the same messages.

**Optimistic send:**

1. Send clears the composer immediately; the message is inserted into the cache with a temp id
   and `status: 'sending'`.
2. The message is dispatched over the socket.
3. On ack, the temp id is swapped for the server id and status moves to `'sent'`.
4. On failure or timeout, status moves to `'failed'` with a retry affordance — the message stays
   visible rather than quietly vanishing.

**Real-time transport: WebSocket over SSE**, because the connection needs to carry traffic in
both directions — typing indicators and read receipts flow client-to-server too. SSE is
one-way; using it here would mean a second channel for that half, which is more moving parts
than one bidirectional connection with a message-type field.

**Reconnect and gap recovery:** when the socket drops, `ConnectionStatusBanner` reflects it
immediately — hiding connection state from the user is itself a bug in this design. On
reconnect, the client doesn't trust the socket to have delivered everything that happened while
it was down: it re-fetches the latest history page via REST from the last known message id and
merges, de-duplicating by message id so a message that arrives via both the backfill and a late
socket delivery renders once. That merge is the client-side half of
[Idempotency & Deduplication](../15-system-design/idempotency-and-deduplication.md) — the
backend may already guarantee at-least-once delivery, but "at least once" is a promise about
delivery, not about what's safe to render twice.

**Streaming agent responses:** a specialist agent's reply that streams token-by-token renders
as one message in a `'streaming'` status, appended to as tokens arrive, flipping to `'sent'` on
the terminal event — the same status-machine shape as the optimistic-send flow above, not a
second mechanism invented to handle it.

**List performance:** on long-running conversations, `MessageThread` virtualizes rather than
leaning on memoization alone — they solve different problems; see
[web-performance.md](web-performance.md) for which one actually helps here.

One Lyft interviewer explained a design-round rejection this way:

> "Having a full working design is not the same as having a good design. Answering all
> questions the interviewer has does not mean that you gave satisfactory answers."

The bar for this worked example isn't "does every box in the diagram have an arrow into it" —
it's whether the state-ownership and failure-recovery choices above are defensible under
follow-up questions, not just present.

---

## Interview questions

**[Reported at Lyft]** **"Design a scalable real-time chat system with delivery guarantees" —
if the interviewer narrows that to just the client side, what do you cover?**
Transport choice and why (WebSocket for bidirectional, SSE for one-way push, polling as a
fallback), rendering and reconciling optimistic sends against server acks, and gap recovery on
reconnect — fetching a backfill page and de-duplicating by message id rather than trusting the
socket alone to have delivered everything.

**"How do you decide between SSR and CSR for a given screen?"**
Start from what's actually being traded: does this screen need to be crawlable, and does it
share content across users (favors SSR/SSG), or is it authenticated and per-user with nothing
to index (favors CSR)? Reaching for SSR without a concrete TTFB or SEO reason just adds
hydration cost and infrastructure for no benefit.

**"Where should state live in a chat UI — component state, context, or a data-fetching cache?"**
Depends what the state *is*, not where it's used: message history is server cache state and
belongs in a cache library with its own loading/stale lifecycle; the composer draft is local;
which conversation is open is URL state so it survives a refresh and is shareable; connection
status is shared UI state a few components need to react to.

**"How would you implement optimistic message sending, and what happens when the server rejects
it?"**
Insert the message locally with a temp id and a `'sending'` status on submit, dispatch the
mutation, then reconcile: swap the temp id for the server id on success, or flip the status to
`'failed'` with a retry affordance on rejection — the message stays visible either way rather
than disappearing.

**"WebSocket vs SSE vs polling for a support chat UI — which would you pick and why?"**
WebSocket, because the UI needs to send typing indicators and read receipts back to the server,
not just receive messages — SSE's one-way model would need a second channel for that half.
Polling would work but adds latency that's visible to a rider or driver mid-conversation.

**"How do you avoid a request waterfall when a screen needs the conversation, the customer
profile, and the agent's saved macros all at once?"**
Fetch all three in parallel from a shared ancestor rather than letting a child component start
its fetch only after its parent's finishes — or prefetch on the signal that precedes navigation
into that screen, so the round trips overlap instead of chaining.

**"What happens in your UI when the WebSocket drops for thirty seconds and then reconnects?"**
The connection-status banner shows the disconnected state immediately rather than hiding it. On
reconnect, the client fetches a backfill page from the last known message id over REST and
merges it into the cache, de-duplicating by message id — because the socket reconnecting doesn't
guarantee nothing was missed while it was down.
