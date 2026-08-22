# Web & Frontend – Conditional Track

> **Priority:** Recommended
> **Est. time:** 5 min
> **Track:** Server + Web
> **HelloInterview:** none

This entire directory is conditional. Read this page before opening anything else in it.

---

## 1 · Why this track exists, and why it might not matter

The recruiter described the role as **"Server або Server + Web"** — Server, or Server plus Web.
The job posting itself lists the frontend half as a nice-to-have, not a core requirement:

> "Full-stack versatility: while the role is server-focused, the ability to own frontend
> development when needed and deliver features end-to-end is a strong plus."

Read that plainly. The loop is **Server by default**; Web is an upside, not a floor. Three
things follow directly:

1. **This track is only worth time if the recruiter confirms the Web half is actually in
   scope.** Until that happens, everything in this directory is speculative prep for a variant
   of the loop that may not occur.
2. **Confirming it is one of the questions to ask** — put "is this Server-only or Server + Web,
   and will the design rounds touch frontend?" on the list for the recruiter screen or the
   hiring-manager call. Don't guess it from the job title alone.
3. **The server track always comes first.** Nothing in this directory outranks the Required
   material in the rest of this repo. If time is short, this directory loses.

## 2 · Section index

| File | Priority | Est. time | Description |
|---|---|---|---|
| [react-typescript-refresher.md](react-typescript-refresher.md) | Optional | 60 min | Hooks in depth, concurrent rendering, Server Components, and TypeScript patterns — the delta since your last hands-on React work. |
| [frontend-system-design.md](frontend-system-design.md) | Recommended | 60 min | Frontend system design as its own interview discipline, worked through a customer-support chat UI. |
| [web-performance.md](web-performance.md) | Optional | 40 min | Core Web Vitals, bundle splitting, critical rendering path, and measuring in the field instead of in a lab. |
| [api-integration-patterns.md](api-integration-patterns.md) | Optional | 40 min | REST vs GraphQL vs gRPC-web from the client, pagination, retries, auth refresh, cancellation. |
| [frontend-testing.md](frontend-testing.md) | Optional | 30 min | Testing Library philosophy, network mocking at the boundary, Cypress vs Playwright. |
| [accessibility-and-quality.md](accessibility-and-quality.md) | Optional | 20 min | Semantic HTML, ARIA, keyboard and focus handling — brief, but a reported Lyft question lives here. |

Two files in this directory are marked **Recommended** rather than **Optional**: this README
(so the gate in the next section actually gets read before the rest), and
`frontend-system-design.md` — because if Web is in scope, the design rounds are where a
Server+Web candidate is actually differentiated, not in hooks trivia. Everything else is
depth to reach for only if there's time left over.

## 3 · Reading order and gate

Only start this section after **both** of the following are true:

- The Required material in the server-focused sections of this repo is in reasonable shape.
- The recruiter or hiring manager has confirmed — or you've made a deliberate bet — that this
  specific loop includes frontend scope.

If both hold, read in this order: `react-typescript-refresher.md` to knock the rust off, then
`frontend-system-design.md` as the main event, then whichever of the remaining four files is
weakest for you.

---

## Interview questions

**"The posting says the role is 'Server or Server + Web.' How do you read that going in?"**
As Server-first with Web as a differentiator, not two tracks to prep equally. I'd confirm scope
with the recruiter early rather than assume either way, and say so directly if asked — guessing
wrong in either direction wastes interview time on both sides.

**"Are you comfortable picking up frontend work if the team needs it?"**
Yes, with a caveat: my hands-on React work is a few years old and predates the hooks-first
idioms that are now standard, so I've deliberately refreshed that rather than assuming it
transferred unchanged. I'd rather say that directly than overclaim current fluency.

**"Tell me about a time you worked outside your primary specialty to ship something end to
end."**
This is a CARL-shaped behavioural question, not a technical one. The honest answer draws on a
real project where backend ownership required picking up the client side (or vice versa) to
unblock delivery, told with a concrete result — not a general claim of versatility.

**"Given 13 years mostly on the JVM/backend side, why should we trust your frontend opinions?"**
I wouldn't claim frontend depth I don't have. What transfers is the engineering judgment
underneath it — state ownership is a distributed-systems problem in miniature, cache
invalidation is cache invalidation — and I've shipped React and Angular in production, plus
Node/TypeScript day to day. The specifics needed a refresh; the instincts didn't start at zero.

**"If a design round turns out to be more frontend-heavy than you expected, what do you do?"**
Say so, then reason from first principles out loud: component boundaries, where state lives,
what's client- vs server-rendered and why. Lyft's own stated bar for these rounds is that a
fully worked design and a good design aren't the same thing — the reasoning trail matters more
than encyclopedic API recall.
