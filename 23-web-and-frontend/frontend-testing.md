# Frontend Testing

> **Priority:** Optional
> **Est. time:** 30 min
> **Track:** Server + Web
> **HelloInterview:** none

*Conditional Web track — see the [section README](README.md) before investing time here; skip
if the recruiter hasn't confirmed Web scope.*

For the general testing taxonomy (unit/integration/system, mocks vs stubs) this file specializes
for the frontend, see [12 — Testing](../12-testing/README.md), in particular
[Types & Levels](../12-testing/Testing-types_levels.md) and
[Mocks & Stubs](../12-testing/Testing-mocks_stubs.md).

---

## 1 · Testing Library philosophy

The governing principle: the more a test resembles how the software is actually used, the more
confidence it gives you. Concretely, that means querying the rendered output the way a user (or
assistive technology) would, not reaching into component internals.

Query priority, roughly, from most to least preferred:

`getByRole` → `getByLabelText` → `getByPlaceholderText` / `getByText` → `getByDisplayValue` →
… → `getByTestId` (last resort).

This ordering isn't arbitrary — it doubles as an accessibility check. If an element can't be
found by role or label, a screen reader user probably can't identify it either; reaching for
`getByTestId` immediately skips that signal. See
[accessibility-and-quality.md](accessibility-and-quality.md) for the ARIA/semantics side of the
same idea.

Prefer `userEvent` over raw `fireEvent`: `userEvent` simulates the full realistic sequence of
browser events (focus, keydown, input, keyup) that a raw `fireEvent.change` skips straight past —
which means it catches bugs that only surface from realistic event ordering (a handler that reads
focus state, for instance).

## 2 · What to test, and what not to

**Test:** user-visible behavior, business logic, edge and error states — anything that would
actually break the user's task if it regressed.

**Don't test:** third-party library internals (trust the library, or you're re-testing their
test suite), trivial prop pass-through, or the exact DOM structure of everything via snapshot.
Blanket snapshot testing is a particular trap — a snapshot diff on every unrelated markup change
trains reviewers to click "update" without reading it, which defeats the point of the test.
Snapshots earn their place where the exact shape *is* the point (a generated report, a serialized
config), not as a default assertion strategy for UI.

## 3 · Mocking network at the boundary

Mock at the network layer — intercepting the actual `fetch`/`XHR` call (Mock Service Worker is
the standard tool for this) — rather than mocking the data-fetching module or hook itself
(`jest.mock('./api')`).

The difference matters: mocking at the network boundary means the real request-building,
response-parsing, and error-handling code under test still runs, so a bug in how the app
constructs a URL or handles a malformed response actually gets caught. Mocking the hook/module
skips all of that and only proves the component renders correctly given whatever shape was
hard-coded into the mock — a weaker test, and one more coupled to the current implementation. A
useful side benefit: the same MSW handlers can run in local dev, not just in tests.

## 4 · Component vs integration vs end-to-end

| Level | Scope | Network | Typical tool |
|---|---|---|---|
| Component | One component in isolation, rendered into jsdom | Mocked | Testing Library + Jest/Vitest |
| Integration | Several components together — real routing, real state wiring | Mocked at the boundary (MSW) | Testing Library + Jest/Vitest |
| End-to-end | Real browser, real (or staging) backend, the whole app | Real | Cypress / Playwright |

This is the general pyramid from
[Types & Levels](../12-testing/Testing-types_levels.md) applied to where those boundaries
actually fall in a frontend codebase — "integration" here means several components wired
together with a mocked network, not several backend services.

## 5 · Cypress (on the CV) vs Playwright today

**Cypress** runs inside the browser, in the same run loop as the app under test (via an injected
iframe) — a real strength for developer experience: a time-travel debugger, live reload, direct
DOM access from the test itself. The trade-off is architectural: historically confined to one
tab/origin per test, and to Chromium-family, Firefox, and Electron. Commands are a chainable,
auto-retrying queue (`cy.get(...).click()`), not plain `async`/`await`.

**Playwright** drives the browser out-of-process (over CDP for Chromium, the browser's own remote
protocol for Firefox/WebKit), so a single test can span multiple tabs, multiple origins, and
multiple browser engines — including real WebKit, i.e. actual Safari behavior. Every action
auto-waits on actionability (visible, stable, enabled) without a separate assertion, and the API
is plain `async`/`await` rather than a command queue.

For a new project started today, Playwright has become the more common default industry-wide —
broader engine coverage, native multi-tab/multi-origin support, and a stronger built-in
parallelization story. That's general industry framing, not a claim about any specific team's
stack. What transfers from Cypress experience either way is the concepts, not the exact API:
network interception/stubbing, auto-retrying assertions instead of manual waits, page-object-style
organization. The syntax differs (`cy.intercept` vs `page.route`); the mental model doesn't need
to be rebuilt from scratch.

---

## Interview questions

**"Why does Testing Library push you toward `getByRole` instead of a test ID?"**
Because it queries the output the way a real user or assistive technology would, which both
gives more confidence the test reflects real usage and doubles as an accessibility check — if an
element isn't reachable by role or label, that's a signal independent of the test itself.

**"Where do you mock the network in a component test, and why not mock the fetching hook
directly?"**
At the network boundary (intercepting `fetch`/`XHR`, typically with MSW), so the real
request-building and response-handling code under test still executes. Mocking the hook or
module instead only proves the component renders correctly given a hard-coded shape — it skips
the code that's actually most likely to have a bug.

**"What's the practical difference between a component test and an integration test in a
frontend codebase?"**
A component test isolates one component with everything around it mocked; an integration test
wires several components together with real routing and real internal state, mocking only the
network boundary — the question each answers is different: "does this unit work" vs "do these
units work together."

**"What would make you choose Playwright over Cypress for a new project today?"**
Needing real cross-browser coverage (actual WebKit, not just Chromium/Firefox), multi-tab or
multi-origin scenarios in one test, or a stronger built-in parallelization story — all areas
where Playwright's out-of-process architecture is a structural advantage over Cypress's
in-browser one.

**"You have a test that fails intermittently in CI but passes locally — how do you approach
it?"**
Suspect timing before suspecting the assertion: an unawaited async update, a network mock that
resolves faster locally than the real dependency does in CI, or an animation/transition the test
didn't wait out. Reproduce with the CI environment's actual timing characteristics rather than
adding a blind retry or a longer sleep, which hides the race instead of fixing it.

**"Should you snapshot-test a component? When does it help versus just create noise?"**
It helps when the exact output shape is the point of the test — a serializer, a generated
report. It creates noise as a default UI-testing strategy, because a snapshot diff fires on any
markup change, relevant or not, which trains reviewers to approve the diff without reading it —
the opposite of what the test was meant to catch.
