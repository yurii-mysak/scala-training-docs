# Concurrency & Async Programming

Scala Futures, Cats Effect, and functional concurrency primitives.

## Beginner

| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 1 | Futures basics | [scala_akka_futures.md](scala_akka_futures.md) | Future creation, map/flatMap, ExecutionContext |

## Intermediate

| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 2 | Working with multiple futures | [multiple_futures.md](multiple_futures.md) | Sequence, traverse, parallel composition, error handling |
| 3 | Cats Effect concurrency | [CatsEffectConcurrency.md](CatsEffectConcurrency.md) | Fibers, Ref, Deferred, Semaphore, concurrent patterns |

## Advanced

| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 4 | Memoization with Cats Effect | [cats_effects_memoize.md](cats_effects_memoize.md) | Memoize, caching effects, concurrent memoization |

## Key Interview Questions by Level

**Beginner**: What is an ExecutionContext? How do Future and map/flatMap work? What happens with failed futures?

**Intermediate**: How do you combine multiple futures? What is the difference between Future.sequence and Future.traverse? How do fibers differ from threads?

**Advanced**: How does Ref provide thread-safe mutable state in a pure FP context? Explain the difference between Cats Effect IO and Scala Future.
