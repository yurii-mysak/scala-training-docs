# Purely Functional State

Purely functional state threads an immutable **state value** through computations, avoiding mutable vars yet enabling algorithms like random number generation, parsers, or finite‑state machines.

---

## 1 · State Monad

A `State[S, A]` wraps a function `S => (S, A)`. Running it transforms an input state and yields a result plus the next state.citeturn0search10turn0search0

```scala
case class State[S, A](run: S => (S, A)):
  def map[B](f: A => B): State[S, B] =
    State(s => {
      val (s1, a) = run(s); (s1, f(a))
    })
  def flatMap[B](f: A => State[S,B]): State[S,B] =
    State(s => {
      val (s1,a) = run(s); f(a).run(s1)
    })
```

### Example: RNG
```scala
val nextInt: State[Int, Int] = State(seed => {
  val newSeed = seed * 1103515245 + 12345
  (newSeed, newSeed >>> 16)
})
```

---

## 2 · Cats‑Effect `Ref` & `Deferred`

`Ref[F, A]` is an atomic mutable cell inside an effect; operations are pure and safe for concurrency.citeturn0search1turn0search11  
`Deferred[F, A]` acts like a one‑shot promise, useful for hand‑off between fibers.

```scala
for
  ref <- Ref.of[IO](0)
  _   <- ref.update(_ + 1)
  n   <- ref.get
yield n
```

---

## 3 · Software Transactional Memory (STM)

ZIO’s `STM` allows composable, lock‑free transactions. Reads & writes happen in *journals*; commit retries on conflict.citeturn0search6

```scala
for
  bal <- TRef.make(100)
  _   <- bal.update(_ - 10)
yield ()
```

---

## 4 · Practical Tips

| Need | Tool |
|------|------|
| Thread‑safe counter | `Ref[F, Int]` |
| One‑time latch | `Deferred[F, Unit]` |
| Complex shared map | `Ref[F, Map[K,V]]` |
| Multi‑var atomic update | `STM` (ZIO) |

---

## 5 · Takeaways

Purely functional state hides mutation behind *referentially‑transparent* APIs, gaining thread safety, testability, and determinism.

