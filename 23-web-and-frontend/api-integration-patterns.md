# API Integration Patterns

> **Priority:** Optional
> **Est. time:** 40 min
> **Track:** Server + Web
> **HelloInterview:** System Design in a Hurry → Core Concepts → API Design

*Conditional Web track — see the [section README](README.md) before investing time here; skip
if the recruiter hasn't confirmed Web scope.*

---

## 1 · REST vs GraphQL vs gRPC-web from the client's perspective

| | Fetching shape | Caching | Reachable from a browser | Tooling cost |
|---|---|---|---|---|
| **REST** | Fixed endpoint shapes — over-fetching (extra fields) or under-fetching (follow-up requests) is common | HTTP caching works for free on `GET` (cache headers, CDN-friendly) | Directly | Low — `fetch` and a URL |
| **GraphQL** | Client specifies exactly the fields it needs, one round trip across domains | Mostly not HTTP-cacheable (single `POST` endpoint) — needs a normalized client cache (Apollo, urql) keyed by query + variables or entity id | Directly | Higher — schema codegen, cache normalization |
| **gRPC-web** | Strongly-typed contract via Protobuf, efficient binary wire format, streaming support | Not HTTP-cache-shaped | **No** — browsers can't speak the HTTP/2-trailers form gRPC needs | Codegen from `.proto`, plus a translating proxy |

The gRPC-web row is the one worth understanding even without hands-on use: a browser can't reach
a gRPC service directly, so the call goes browser → a translating proxy → the real gRPC service.
Envoy — general-purpose knowledge, not a claim about any specific deployment — ships a gRPC-Web
filter for exactly this, which is the shape you'd expect if a browser client needed to talk to a
Protobuf-defined service sitting behind an Envoy mesh: the proxy terminates gRPC-web from the
browser and speaks real gRPC on the other side.

## 2 · Pagination and infinite scroll

**Offset-based** (`?page=3&pageSize=20`) is simple but wrong once the underlying list mutates
between requests — an insert before the current offset shifts every later page, producing
skipped or duplicated items on the next fetch.

**Cursor-based** (`?after=<opaque_cursor>`) encodes a stable position, usually derived from a
sort key (the last item's id or timestamp), and is immune to inserts before it. It's the
standard choice for anything that changes while the user is scrolling — a support queue, a chat
history, a feed.

Client-side pattern: an "infinite query" keyed by the base request, storing an ordered list of
fetched pages, requesting the next one on a scroll-proximity trigger (an intersection observer)
or an explicit "load more," appending to the same cache entry rather than re-fetching from the
start. Combine with virtualization ([web-performance.md](web-performance.md)) once the
accumulated list is long — pagination controls how much is *fetched*, virtualization controls
how much is *rendered*; a long-scrolling screen needs both, solving different halves of the same
problem.

## 3 · Retries and idempotency on the client

Retry what's actually retryable — network failure, timeout, `5xx` — and not what isn't: a `4xx`
means the request was rejected for a reason a retry won't fix, with `429` plus `Retry-After` as
the one conditional exception. Back off exponentially with jitter; retrying instantly, in
lockstep with every other client, against a backend that's already struggling makes the outage
worse.

A retried mutation is only safe if it's idempotent. `GET`/`PUT`/`DELETE` are idempotent by HTTP's
own contract; `POST` generally isn't — a retried "create" can double-create unless the client
attaches an idempotency key (a client-generated UUID sent with the request) that the server uses
to recognize and collapse a duplicate. Generating and attaching that key is the client's half of
the job; see [Idempotency & Deduplication](../15-system-design/idempotency-and-deduplication.md)
for the server-side half — how it's stored, deduplicated, and what guarantee it actually buys.
This is the same territory as Lyft's reported design-round topic of idempotency keys and request
deduplication, just viewed from where the key originates. Where a data-fetching/cache library is
already in use, check what it does by default before hand-rolling a retry loop — it usually
already encodes the safe-to-retry distinction.

## 4 · Error and loading state modelling

The naive shape — three independent booleans, `isLoading` / `isError` / `data` — allows
impossible combinations the type system doesn't rule out (loading and error both `true`, or
`data` present alongside `isError`), which every consumer then has to defensively guard against
anyway. The fix is a discriminated union with a single `status` field, so only one state is
representable at a time and the compiler narrows automatically at each branch — worked through
in full, with the actual type, in
[react-typescript-refresher.md § 10](react-typescript-refresher.md#10--typescript-in-react).
Model it once as a generic `FetchState<T>` rather than re-deriving three booleans per component;
a cache library's own status field (React Query's `status`/`fetchStatus` pair, for instance) is
the same idea already built in.

## 5 · Auth token handling and refresh

Standard shape: a short-lived access token on every request, plus a longer-lived refresh token
that exchanges for a new access token when the old one expires.

**Storage trade-off:** `localStorage` is readable by any script running on the page, so it's
directly exposed if an XSS vulnerability exists anywhere on the origin. An in-memory variable
avoids that but doesn't survive a reload. An `httpOnly` cookie is unreachable from JavaScript
entirely, which closes the XSS-read vector, but opens a CSRF surface that needs its own defense
(`SameSite`, a CSRF token). None of these is free — see
[Authentication Mechanisms](../11-security/Security-authentication.md) for the underlying
trade-offs in more depth.

**Silent refresh:** a request/response interceptor catches a `401`, attempts a refresh, and
retries the original request transparently, invisible to the calling code.

**The race to actually watch for:** two requests hit `401` at nearly the same moment, and each
independently tries to start a refresh. Fix with a single-flight pattern — the first `401`
starts the refresh and stores the in-flight promise; any `401` arriving while it's pending awaits
that same promise instead of firing a second refresh call.

On refresh failure (the refresh token itself is expired or revoked), the only correct move is to
fail the session — clear local state, redirect to login — rather than retry indefinitely.

## 6 · Request cancellation

`AbortController` is the primitive: create one per request, pass its `signal` to `fetch`, call
`.abort()` to cancel. Cancel a stale request when it's no longer wanted — on unmount, on a
dependency change that means any response is now for the wrong input (search-as-you-type firing
a request per keystroke), or on navigating away from the screen that requested it.

This is what prevents the classic race condition where a slow response to an old request arrives
*after* a fast response to a newer one and overwrites it on screen — cancelling the stale
request, or at minimum ignoring a response that's no longer for the current input, is required
either way. Cache libraries (React Query, SWR) wire this up automatically on query-key change,
which is another reason to prefer them over hand-rolled fetching once cancellation correctness
actually matters.

---

## Interview questions

**"Why would a browser client need a gRPC-web proxy instead of talking gRPC directly?"**
Browsers can't produce the HTTP/2 trailers-based frames real gRPC relies on. A gRPC-web proxy —
an Envoy gRPC-Web filter is the common shape — terminates a browser-friendly protocol on one side
and speaks real gRPC to the backend service on the other.

**"How do you make a retried `POST` request safe against double submission?"**
Generate an idempotency key client-side (a UUID) and send it with the mutation; the server
recognizes a retried request carrying the same key and returns the original result instead of
creating a second record. The client's only job is generating and consistently attaching that
key across retries of the *same* logical request.

**"Cursor vs offset pagination — which would you choose for a live-updating feed, and why?"**
Cursor-based — it encodes a stable position derived from a sort key, so an insert ahead of the
cursor doesn't shift it. Offset-based pagination breaks silently on a live feed: an insert before
the current offset shifts every subsequent page, producing skipped or duplicated items.

**"How do you prevent a race condition when a user types quickly in a search box that fires a
request per keystroke?"**
Cancel the in-flight request (or ignore its response) whenever a new keystroke supersedes it —
via `AbortController` tied to the input's dependency, or automatically through a cache library
keyed on the query string. Without it, a slow response to an earlier keystroke can arrive after a
faster response to a later one and overwrite the correct result on screen.

**"Where would you store an auth token in a browser app, and what are the trade-offs?"**
`localStorage` is simple but readable by any script, so it's directly exposed to XSS.
`httpOnly` cookies close that read vector but introduce a CSRF surface that needs `SameSite`
and/or a CSRF token. In-memory storage avoids both but doesn't survive a page reload. There's no
option without a trade-off; the choice depends on which risk the rest of the app's defenses
already cover.

**"Two tabs both get a 401 at the same time — how do you avoid firing two refresh-token
requests?"**
Single-flight the refresh: the first `401` starts the refresh call and stores the in-flight
promise somewhere shared (a module-level variable, or a lock in a shared worker); any `401`
arriving while that promise is pending awaits it instead of starting a second refresh.

**"Model the loading/error/success state for a data-fetching hook in TypeScript. Why not three
separate booleans?"**
A discriminated union on a single `status` field (`'idle' | 'loading' | 'success' | 'error'`,
each variant carrying only the fields valid for that state) instead of `isLoading`/`isError`/
`data` as independent booleans — the union makes invalid combinations (loading *and* error both
true) unrepresentable, rather than merely unlikely.
