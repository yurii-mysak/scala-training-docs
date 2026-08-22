# Accessibility & Quality

> **Priority:** Optional
> **Est. time:** 20 min
> **Track:** Server + Web
> **HelloInterview:** none

*Conditional Web track — see the [section README](README.md) before investing time here; skip
if the recruiter hasn't confirmed Web scope.* Kept deliberately brief — but not zero-probability:
a reported Lyft interview question was "How can you make your app more accessible?"

---

## 1 · Semantic HTML

Use the native element before reaching for ARIA. A real `<button>` gets keyboard operability,
focus, and role for free; a `<div onClick>` gets none of that until you rebuild it by hand.
Landmark elements (`<nav>`, `<main>`, `<header>`, `<footer>`) let assistive tech jump between page
regions instead of reading linearly through all of it. A correct heading hierarchy (`h1` →
`h2` → `h3`, no skipped levels) is how a screen reader user builds a mental outline of the page
before reading it in detail.

## 2 · ARIA basics

The first rule of ARIA: don't use it if a native HTML element or attribute already gives you the
semantics and behavior you need. ARIA never adds behavior — only announces semantics on top of
whatever behavior you build yourself.

Worth knowing cold: `aria-label` (accessible name when there's no visible text), `aria-live`
(announce a region's changes without moving focus there — directly relevant to a chat UI's new
messages or an "agent is typing" update), `aria-expanded` (disclosure state on a toggle),
`aria-hidden` (hide decorative content from the accessibility tree). A `role="button"` on a
`<div>` still needs a manually-wired `tabIndex`, an `onKeyDown` handler for Enter/Space, and
focus styling to actually behave like a button — the role alone announces the semantics, it
doesn't supply the behavior.

## 3 · Keyboard navigation

Every interactive element must be reachable and operable via keyboard alone — the fastest gut
check for a quietly-inaccessible custom control. Never remove the visible focus indicator
(`outline: none`) without a replacement; sighted keyboard users rely on it as much as anyone.
Tab order follows DOM order by default — avoid positive `tabIndex` values, which override it and
are almost always a bug once more than one element on the page uses one. Skip links ("skip to
main content") let a keyboard user bypass repeated navigation on every page load.

## 4 · Focus management in dynamic UIs

A modal or dialog traps focus while open (Tab doesn't escape to the page behind it) and returns
focus to the element that opened it on close — both easy to miss when a modal is built from a
plain `<div>` instead of the native `<dialog>` element or a library that already handles this.
Client-side route changes should move focus (typically to the new view's heading) or announce
the navigation, since the browser's own "focus follows navigation" behavior doesn't happen for
free in an SPA the way it does on a full page load. Async status changes — a toast, a "message
sent" confirmation, a typing indicator — belong in an `aria-live` region so they're announced
without requiring the user to be focused on that exact spot; the chat UI in
[frontend-system-design.md](frontend-system-design.md) needs exactly this for incoming messages.

---

## Interview questions

**[Reported at Lyft]** **"How can you make your app more accessible?"**
Answer it as a hierarchy, not a checklist: semantic HTML first, ARIA only where semantics still
fall short, full keyboard operability, then managed focus for anything dynamic (modals, live
regions), then automated tooling (axe-core, `eslint-plugin-jsx-a11y`) plus a manual
screen-reader pass to catch what automation can't. Anchor it in one concrete example rather than
a generic list — a chat message list needs `aria-live="polite"` so new messages are announced
without stealing focus from the composer.

**"What's the first rule of ARIA?"**
Don't use it if a native element already provides the semantics and behavior you need — reach
for ARIA to fill a genuine gap, not as a default layered onto custom-built controls.

**"How do you make a modal dialog accessible?"**
Trap focus inside it while open, return focus to the triggering element on close, give it an
accessible name (`aria-labelledby` pointing at its heading), and make sure Escape closes it. The
native `<dialog>` element or a maintained library handles most of this; hand-rolling it from a
`<div>` means reimplementing all of it correctly.

**"Why is `outline: none` on `:focus` a common accessibility bug?"**
It removes the only visual signal a keyboard user has for where they are on the page — not only
screen reader users, any sighted person navigating by keyboard. If the default outline doesn't
fit the design, replace it with a custom focus style; don't just delete it.

**"How would you announce a new chat message to a screen reader user without being disruptive?"**
An `aria-live="polite"` region around the message list. "Polite" queues the announcement until
the user's current activity — typing a reply — pauses, instead of interrupting it the way
`"assertive"` would.
