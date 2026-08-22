# React & TypeScript Refresher

> **Priority:** Optional
> **Est. time:** 60 min
> **Track:** Server + Web
> **HelloInterview:** none

*Conditional Web track — see the [section README](README.md) before investing time here; skip
if the recruiter hasn't confirmed Web scope.*

This is not an introduction to React. It assumes you already know what a component and a prop
are. It's a diff against React as it stood before hooks were the norm — what changed, and what
an interviewer or a code review will actually poke at.

---

## 1 · What actually changed

- **Function components are the default**, not an alternative style. Class components still
  render, but new code doesn't use them except for error boundaries (below).
- **Hooks replaced lifecycle methods, HOCs, and render props** as the primary composition
  mechanism. `componentDidMount`/`componentDidUpdate`/`componentWillUnmount` collapse into one
  `useEffect`. Cross-cutting behavior is a custom hook, not a wrapper component.
- **Concurrent rendering** (React 18) means React can start, pause, and abandon a render before
  committing it. Components are expected to be pure during render — side effects that used to
  "mostly work" in impure render code are now more likely to visibly misbehave.
- **The ecosystem is TypeScript-first.** Prop types via `PropTypes` are gone from new code;
  types are the interface.
- **Server Components** (conceptual, below) are a newer rendering model on top of all of this,
  relevant mainly if the stack is Next.js App Router or similar.

## 2 · `useState` and `useEffect`: the one that actually bites

`useState` needs no refresher — it's a slot plus a setter. `useEffect` is where the traps are,
because it looks like "run this when X changes" but its actual contract is narrower: **it
synchronizes a component with something outside React** (a subscription, the DOM, a network
request, a timer). If you're deriving a value from props or state, compute it during render
instead of syncing it via an effect — that's the single biggest source of unnecessary effects
in code written by someone coming from an older mental model.

**Trap 1 — stale closures.** An effect closes over the values visible at the time it ran, not
the current ones:

```tsx
function Counter() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      console.log(count); // always logs 0 — this closure was captured on mount
    }, 1000);
    return () => clearInterval(id);
  }, []); // empty deps: effect runs once, never sees a fresh `count`

  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

Fix: either include `count` in the dependency array (and accept the interval resubscribing on
every change), or use the functional updater form (`setCount(c => c + 1)`) inside the interval
so the effect never needs to read `count` at all. The `exhaustive-deps` ESLint rule exists to
catch exactly this class of bug — disabling it is usually a sign the bug is being hidden, not
fixed.

**Trap 2 — race conditions on fetch.** Effects that fetch data need cleanup, or a fast prop
change can let an old response overwrite a newer one:

```tsx
function UserProfile({ userId }: { userId: string }) {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`/api/users/${userId}`, { signal: controller.signal })
      .then((res) => res.json())
      .then(setUser)
      .catch((err) => {
        if (err.name !== 'AbortError') throw err;
      });
    return () => controller.abort();
  }, [userId]);

  return user ? <Profile user={user} /> : <Spinner />;
}
```

In practice, a data-fetching library (React Query / SWR) handles this cancellation and
de-duplication for you — see
[api-integration-patterns.md](api-integration-patterns.md). Writing it by hand is worth
understanding once, not repeating in every component.

**Trap 3 — object/array/function literals in the dependency array.** `{ id }`, `[a, b]`, and
inline arrow functions are new references every render, so a dep array containing one
re-triggers the effect every time regardless of whether the values actually changed. Memoize
the literal or narrow the dependency to the primitive values inside it.

## 3 · `useMemo` / `useCallback`: when they're premature

Both solve the same problem — referential equality across renders — for two different
purposes: `useMemo` avoids recomputing an expensive value, `useCallback` avoids creating a new
function identity that would otherwise defeat a downstream `React.memo` or re-trigger an effect
that depends on it.

```tsx
// Premature: this computation is trivial. useMemo here adds overhead and a dependency
// array to maintain, for no measurable benefit.
const label = useMemo(() => `${first} ${last}`, [first, last]);

// Justified: real cost, worth skipping on unrelated re-renders.
const sorted = useMemo(() => expensiveSort(items), [items]);

// Justified: identity stability matters because Row is memoized.
const handleSelect = useCallback((id: string) => setSelectedId(id), []);
const MemoRow = React.memo(Row);
```

Rule of thumb: reach for these when you can point at a real cost (a measured re-render, an
expensive computation, a memoized child that needs stable props) — not by default on every
value and callback in a component. Memoizing something cheap doesn't make it free; it trades a
render-time cost for a comparison-time cost and a maintenance burden (the dependency array).
This is also the thing React's compiler tooling is aimed at automating away — worth knowing the
direction of travel even without hands-on experience with it.

## 4 · `useRef`

`useRef` returns a mutable box that survives across renders without causing one when it
changes. Two uses: holding a reference to a DOM node, and holding any other mutable value a
component needs to remember but never render (a previous prop value, a timer id, a "did this
effect already run" guard).

```tsx
function TextInput() {
  const inputRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    inputRef.current?.focus();
  }, []);
  return <input ref={inputRef} />;
}
```

`forwardRef` plus `useImperativeHandle` expose a narrow imperative API from a child component
(`focus()`, `scrollIntoView()`) without leaking the underlying DOM node itself — reach for it
rarely; prop-driven rendering handles the vast majority of cases.

## 5 · `useReducer`

Worth reaching for once a component has several related pieces of state that transition
together, rather than a pile of independent `useState` calls that all need updating in sync.
The shape will look familiar:

```ts
type State = { status: 'idle' | 'sending' | 'sent' | 'error'; draft: string };
type Action =
  | { type: 'EDIT'; text: string }
  | { type: 'SEND' }
  | { type: 'ACK' }
  | { type: 'FAIL'; error: string };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'EDIT':
      return { ...state, draft: action.text };
    case 'SEND':
      return { ...state, status: 'sending' };
    case 'ACK':
      return { ...state, status: 'sent', draft: '' };
    case 'FAIL':
      return { ...state, status: 'error' };
  }
}
```

This is the same discipline as a command-to-event reducer in an event-sourced aggregate:
explicit transitions instead of ad hoc mutation, one place that owns "what does this action do
to this state." Same mental model, different runtime.

## 6 · Custom hooks

A custom hook is just a function whose name starts with `use` that calls other hooks — the
mechanism for extracting reusable stateful logic, replacing what higher-order components and
render props did before. The Rules of Hooks (call unconditionally, only from the top level of a
component or another hook) apply to it exactly as they do to built-ins.

```ts
function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(id);
  }, [value, delayMs]);
  return debounced;
}
```

## 7 · Suspense and error boundaries

Two different failure/pending modes, meant to compose:

```tsx
<ErrorBoundary fallback={<ErrorPanel />}>
  <Suspense fallback={<Spinner />}>
    <ConversationThread conversationId={id} />
  </Suspense>
</ErrorBoundary>
```

- **Suspense** catches a component "not ready yet" (lazy-loaded code via `React.lazy`, or a
  framework's data-fetching integration) and shows a fallback until it resolves.
- **Error boundaries** catch a thrown render error and show a fallback instead of unmounting
  the whole tree. There is still no hook equivalent — this is the one place a class component
  (or the widely-used `react-error-boundary` package) remains the pragmatic default.
- The nearest boundary of each kind up the tree catches; place them at the granularity where a
  failed or loading subtree shouldn't take the rest of the page down with it.

## 8 · Concurrent rendering implications

React 18 introduced a concurrent renderer: rendering can be interrupted, so a component's
render function needs to be safe to call more than once for one committed update. Practical
consequences:

- **Automatic batching**: state updates inside promises, timeouts, and native event handlers
  are now batched into a single re-render, not just updates inside React's own event handlers
  (the React 17 behavior).
- **`useTransition` / `startTransition`** mark an update as low-priority so React can keep the
  UI responsive to more urgent input (typing) while the marked update renders in the
  background.
- **`useDeferredValue`** is the read-side equivalent — defer using a value for a lower-priority
  part of the tree without marking a whole state update as a transition.

```tsx
function SearchBox() {
  const [query, setQuery] = useState('');
  const deferredQuery = useDeferredValue(query);

  return (
    <>
      <input value={query} onChange={(e) => setQuery(e.target.value)} />
      <ResultList query={deferredQuery} />
    </>
  );
}
```

- **Strict Mode double-invokes** component render, and mounts/unmounts/remounts effects, in
  development only. This is deliberate — it surfaces effects and render logic that aren't
  actually idempotent, which concurrent rendering depends on. A component that breaks under
  Strict Mode had a latent bug; Strict Mode didn't introduce one.

## 9 · Server Components (conceptual)

Worth understanding the shape of, not worth over-investing in unless the stack is confirmed to
use it. React Server Components render on the server and ship **zero JavaScript** for that
component to the client — not just pre-rendered HTML plus a hydration script, which is what
traditional SSR does. A Server Component can read from a database or an internal service
directly in its render function; it never re-renders in the browser. Client Components (marked
`"use client"`) are the interactive boundary — state, effects, and event handlers only exist on
that side of it. The practical framework this shows up in is Next.js App Router. Calibration:
know what problem this solves (less client JS, data fetching colocated with the component that
needs it, no client-server waterfall for server-only data) and how it differs from SSR — that's
enough to not be caught flat-footed if it comes up.

## 10 · TypeScript in React

**Props and children.** `children` is typed as `React.ReactNode` (or the `PropsWithChildren`
helper); prefer an explicit `type`/`interface` over inferring props from usage.

```tsx
type ButtonProps = {
  variant?: 'primary' | 'secondary';
  onClick: () => void;
  children: React.ReactNode;
};

function Button({ variant = 'primary', onClick, children }: ButtonProps) {
  return (
    <button className={variant} onClick={onClick}>
      {children}
    </button>
  );
}
```

**Generics in components.** A component can be generic over the data it renders, which keeps a
list/table component reusable without falling back to `any`:

```tsx
type ListProps<T> = {
  items: T[];
  renderItem: (item: T) => React.ReactNode;
  keyOf: (item: T) => string;
};

function List<T>({ items, renderItem, keyOf }: ListProps<T>) {
  return (
    <ul>
      {items.map((item) => (
        <li key={keyOf(item)}>{renderItem(item)}</li>
      ))}
    </ul>
  );
}
```

**Discriminated unions for state.** The alternative to three independent booleans
(`isLoading`, `isError`, `data`) that can represent impossible combinations:

```tsx
type FetchState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: string };

function render(state: FetchState<User>) {
  switch (state.status) {
    case 'idle':
      return null;
    case 'loading':
      return <Spinner />;
    case 'success':
      return <Profile user={state.data} />; // data is narrowed here, no cast needed
    case 'error':
      return <ErrorPanel message={state.error} />;
  }
}
```

See [api-integration-patterns.md](api-integration-patterns.md) for this pattern applied to a
real data-fetching hook.

**Avoiding `any`.** At trust boundaries (API responses, `JSON.parse`, third-party callbacks),
type as `unknown` and narrow explicitly rather than asserting a shape you haven't checked. The
`satisfies` operator validates a literal against a type without widening it the way an explicit
type annotation would:

```ts
const config = {
  retries: 3,
  backoffMs: 200,
} satisfies RetryConfig;
```

---

## Interview questions

**"What's the difference between `useMemo` and `useCallback`, and when would you reach for
neither?"**
`useMemo` caches a computed value; `useCallback` caches a function identity — `useCallback(fn,
deps)` is equivalent to `useMemo(() => fn, deps)`. Reach for neither when the computation is
cheap and nothing downstream depends on referential stability; premature memoization adds a
dependency array to maintain for no measured benefit.

**"Walk me through a `useEffect` dependency-array bug you'd expect to see, and how you'd fix
it."**
A timer or subscription set up in an effect with `[]` deps that reads a piece of state — the
closure captures that state's value at mount and never sees updates. Fix by using the
functional updater form so the callback doesn't need to read the stale variable, or by
including the value in the deps and accepting the resubscription cost.

**"Why would you choose `useReducer` over several `useState` calls?"**
When pieces of state change together as a unit and the transitions have real logic — it makes
illegal intermediate states harder to reach and puts all the transition logic in one place
instead of scattered across event handlers.

**"What problem does Suspense solve, versus an error boundary — and how do they compose?"**
Suspense handles "not ready yet" (lazy code, async data) with a fallback; error boundaries
handle "this threw" with a fallback. They nest, and the nearest boundary of each kind up the
tree catches — so you place them at the granularity where a failure or a pending state
shouldn't take out more of the page than necessary.

**"What is a stale closure, concretely?"**
A function created inside a render or effect that captured a variable's value at creation time,
then keeps referencing that captured value even after the component re-renders with a new one —
because closures capture bindings, not live state, and an effect with a dependency array only
re-creates its closure when that array changes.

**"How would you type a component that's generic over a list of items, each rendered by a
caller-supplied function?"**
A generic type parameter on the props (`ListProps<T>`), with `items: T[]` and a `renderItem:
(item: T) => ReactNode` prop — TypeScript infers `T` from the `items` array at the call site, so
callers get full type-checking on `renderItem` without the component ever needing to know the
concrete type.

**"What's the actual difference between a Server Component and a component rendered via
traditional SSR?"**
Traditional SSR renders HTML on the server but still ships the component's JavaScript to the
client for hydration. A Server Component never ships to the client at all — it renders once on
the server and its output is streamed in; only components explicitly marked as Client
Components carry interactivity and JS to the browser.

**"Why does React 18 double-invoke effects in development under Strict Mode, and what does
that reveal about a bug it surfaces?"**
To simulate an effect being mounted, torn down, and remounted, which is what concurrent
rendering can legitimately do to a component. If double-invocation breaks something, the effect
wasn't actually safe to run more than once — commonly a subscription or fetch without proper
cleanup — and that was a latent bug independent of Strict Mode.
