# Web Performance

> **Priority:** Optional
> **Est. time:** 40 min
> **Track:** Server + Web
> **HelloInterview:** none

*Conditional Web track — see the [section README](README.md) before investing time here; skip
if the recruiter hasn't confirmed Web scope.*

---

## 1 · Core Web Vitals and what actually moves them

| Metric | Measures | Primary levers |
|---|---|---|
| **LCP** (Largest Contentful Paint) | Time until the largest visible element renders | Server response time (TTFB), render-blocking CSS/JS, load time of the LCP resource itself (image/font), client-rendering delay before content exists at all |
| **INP** (Interaction to Next Paint) | Full latency of a user interaction — input delay + processing + next paint — sampled across the whole session | Long tasks blocking the main thread, heavy event handlers, excessive re-renders per interaction |
| **CLS** (Cumulative Layout Shift) | Unexpected visual movement after initial render | Images/embeds without reserved dimensions, web fonts causing reflow, content injected above existing content |

INP replaced FID as the responsiveness Core Web Vital — FID only measured the delay before the
*first* interaction started processing; INP measures the full cost of any interaction,
throughout the page's life, which is a much harder number to fake with a light homepage and a
heavy app underneath it.

## 2 · Bundle splitting and lazy loading

- **Route-based splitting** is the default unit: each route's code loads only when navigated to
  (`React.lazy` + dynamic `import()` behind a `Suspense` boundary at the route level).
- **Separate the vendor/framework chunk from app code** so it caches independently across
  deploys — the framework doesn't change every release; app code does, and shouldn't invalidate
  the framework's cache entry every time it does.
- **Tree-shaking requires ESM and side-effect-free modules** (`"sideEffects": false` in
  `package.json`) to actually eliminate dead code. A CommonJS dependency, or a module with an
  import-time side effect, silently defeats it — the bundler can't prove it's safe to drop.
- **Analyze before guessing.** A bundle analyzer shows what's actually shipping and how big each
  piece is; "the bundle feels big" isn't a diagnosis, and the biggest chunk is often one
  unexpectedly large dependency rather than "too much app code."

## 3 · Critical rendering path

HTML parses into the DOM; CSS parses into the CSSOM; the two combine into a render tree; the
render tree produces layout (geometry) and then paint (pixels), which the browser composites
onto the screen.

- A `<script>` tag blocks HTML parsing until it's fetched and executed, by default.
- CSS blocks rendering entirely — the browser won't paint until it knows the styles, to avoid a
  flash of unstyled content.
- Interventions: `defer` (executes after parsing, in document order) or `async` (executes
  whenever it arrives, no order guarantee) instead of a blocking synchronous script;
  `<link rel="preload">` for a resource the browser wouldn't discover early enough on its own
  (a font only referenced from CSS, a hero image only referenced from JS); `<link
  rel="preconnect">` to pay a cross-origin connection's DNS/TLS cost before it's actually needed.

## 4 · Image and font strategy

**Images:** `srcset`/`sizes` so the browser requests a resolution appropriate to the viewport
and device pixel ratio instead of shipping a desktop-resolution image to a phone; modern formats
(AVIF/WebP) with a fallback; `loading="lazy"` on offscreen images so they don't compete with
above-the-fold content for bandwidth; explicit `width`/`height` (or `aspect-ratio`) so layout
space is reserved before the image loads — a direct CLS fix, not only a load-time one.

**Fonts:** `font-display: swap` (or `optional`) so text stays visible while a web font loads
instead of invisible (FOIT); subsetting to the character set actually used; preloading the
font(s) needed above the fold; variable fonts to avoid shipping a separate file per weight.

## 5 · Memoisation vs virtualisation for long lists

These solve different problems, and one is not a substitute for the other. Memoization
(`React.memo`, `useMemo`) reduces the cost of *re-rendering* a row that's already mounted — it
does nothing about the cost of having ten thousand DOM nodes mounted simultaneously.
Virtualization (windowing: render only the rows in or near the viewport, recycling DOM nodes as
the user scrolls) addresses that mounted-node cost directly.

Rule of thumb: memoize first for a list of dozens of items; virtualize once you're in the
hundreds or thousands, or as soon as the problem is visibly scroll performance rather than
update performance. The chat thread in the
[frontend-system-design.md](frontend-system-design.md) worked example virtualizes for exactly
this reason — a long-running support conversation is squarely the "thousands of rows" case.

## 6 · Measuring with real user monitoring, not lab tools

Lab tools (Lighthouse, WebPageTest, a local DevTools trace) run one synthetic scenario on one
simulated device and network — useful for catching regressions in CI, not for knowing what real
users actually experience.

RUM captures metrics from real page loads in the field: the `web-vitals` JS library (or the
browser's own Performance/Reporting APIs) reports LCP/INP/CLS per real visit to an analytics
endpoint; Chrome UX Report (CrUX) is a public, origin-level RUM dataset built from real Chrome
traffic.

Field and lab numbers diverge for real reasons, not measurement noise: device and network
diversity, cache state (a lab run is typically cold; most real visits aren't), and genuine
interaction patterns a synthetic script doesn't reproduce. Core Web Vitals are defined and
scored as field metrics — the 75th percentile across real visits — for exactly this reason: a
green Lighthouse score next to a red field report means the lab scenario doesn't represent real
usage, and the field number is the one that's real. Where possible, correlate RUM with a
business metric (conversion, task completion, session length by LCP bucket) — a performance
number that can't be tied to an outcome is hard to prioritize against feature work.

---

## Interview questions

**"What's the difference between LCP and INP, and what usually causes each to be bad?"**
LCP is about how long until the largest visible element paints — usually a slow server response,
render-blocking resources, or a slow-loading hero image/font. INP is about how sluggish the page
feels to interact with throughout the session — usually long tasks on the main thread or heavy
work inside event handlers.

**"How would you reduce the initial bundle size of a large React app without a rewrite?"**
Route-based code splitting first — most of the app doesn't need to load before first paint.
Then check the bundle analyzer for one or two oversized dependencies before assuming the problem
is diffuse app code; a single badly-chosen library is a common single cause.

**"Why prefer field data (RUM) over a Lighthouse score when judging real performance?"**
Lighthouse is one run on one simulated device and network; it can be green while real users on
real devices and real networks have a materially worse experience. Core Web Vitals are scored as
field percentiles specifically because lab conditions don't represent the distribution of real
visits.

**"When does virtualizing a list beat memoizing its rows?"**
Once the list is long enough that the cost is having thousands of DOM nodes mounted at all, not
the cost of re-rendering rows that change. Memoization doesn't reduce node count; virtualization
does, by only mounting what's near the viewport.

**"What causes cumulative layout shift, and how do you prevent it for images?"**
Content occupying space that wasn't reserved for it before it loaded — most commonly an image or
embed with no explicit dimensions, so the browser doesn't know its size until it arrives and
everything below it jumps. Reserve the space up front with explicit `width`/`height` or
`aspect-ratio`.

**"Walk through the critical rendering path and where you'd intervene to speed up first paint."**
HTML to DOM, CSS to CSSOM, the two merge into a render tree, then layout and paint. Both a
blocking `<script>` in the head and any blocking CSS delay that pipeline — interventions are
`defer`/`async` on scripts that don't need to run before parsing completes, and `preload` for
resources the browser wouldn't otherwise discover early enough (a CSS-only font, a JS-only hero
image).
