# JVM Internals

Memory model, garbage collection, class loading, compilation, and performance tuning.

## Beginner

| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 1 | JVM overview & tooling | [JVM-JVM_and_Tooling.md](JVM-JVM_and_Tooling.md) | JVM architecture, jps, jstack, jmap, jconsole |
| 2 | Memory: stack & heap | [JVM-Memory_Stack_Heap.md](JVM-Memory_Stack_Heap.md) | Stack frames, heap generations, PermGen/Metaspace |

## Intermediate

| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 3 | Classloaders | [JVM-Classloaders.md](JVM-Classloaders.md) | Bootstrap/extension/app classloaders, delegation model |
| 4 | Garbage collection | [JVM-Garbage_Collection.md](JVM-Garbage_Collection.md) | GC algorithms (Serial, Parallel, CMS, G1, ZGC), generations |
| 5 | AOT vs JIT compilation | [JVM-AOT_vs_JIT.md](JVM-AOT_vs_JIT.md) | C1/C2 compilers, GraalVM native-image, warm-up |

## Advanced

| # | Topic | File | Interview Focus |
|---|-------|------|-----------------|
| 6 | Performance tuning | [JVM-PerformanceTuning.md](JVM-PerformanceTuning.md) | JVM flags, heap sizing, thread tuning |
| 7 | GC profiling & tuning | [JVM-GC_Profiling_and_Tuning.md](JVM-GC_Profiling_and_Tuning.md) | GC logs analysis, pause time optimization |
| 8 | Scala app profiling | [scala_app_profiling.md](scala_app_profiling.md) | Flame graphs, async-profiler, memory leak detection |

## Key Interview Questions by Level

**Beginner**: What are stack and heap? What lives where? What is the difference between young and old generation?

**Intermediate**: How does G1 GC work? What is the classloader delegation model? How does JIT compilation optimize code at runtime?

**Advanced**: How would you diagnose a memory leak in a Scala application? What JVM flags would you tune for a low-latency application? When would you use GraalVM native-image?
