# Microbenchmarking with JMH

Java Microbenchmark Harness (JMH) is the de facto standard for writing reliable microbenchmarks on the JVM.

---

## 1. What is JMH

- **Definition**: A Java library and annotation processor to avoid JVM optimizations skewing benchmark results.
- **Why**: Prevents JIT, dead-code elimination, and inlining from invalidating benchmarks.
- **Analogy**: Calibrated test track for evaluating car acceleration, independent of external variables.

---

## 2. Setting Up JMH in Scala

Add JMH plugin and dependency in `build.sbt`:

```scala
enablePlugins(JmhPlugin)

libraryDependencies += "org.openjdk.jmh" % "jmh-core" % "1.36"
libraryDependencies += "org.openjdk.jmh" % "jmh-generator-annprocess" % "1.36"
```

---

## 3. Writing Benchmarks

Use JMH annotations:

```scala
import org.openjdk.jmh.annotations._

@State(Scope.Benchmark)
class MyBenchmark {

  var data: Array[Int] = _

  @Setup(Level.Trial)
  def setup(): Unit = {
    data = (1 to 1000000).toArray
  }

  @Benchmark
  @BenchmarkMode(Array(Mode.Throughput))
  @OutputTimeUnit(TimeUnit.MILLISECONDS)
  def sumStream(): Int = {
    data.foldLeft(0)(_ + _)
  }

  @Benchmark
  @BenchmarkMode(Array(Mode.AverageTime))
  @OutputTimeUnit(TimeUnit.NANOSECONDS)
  def sumIterator(): Int = {
    data.iterator.sum
  }
}
```

- `@State`: shared state across benchmark iterations.
- `@Benchmark`: marks methods to measure.
- `@Setup`: initialization before benchmarks.
- `@BenchmarkMode`: throughput, average time, sample time, single shot, etc.
- `@OutputTimeUnit`: time unit for results.

---

## 4. Running Benchmarks

```bash
sbt jmh:run -i 5 -wi 5 -f1 -t1
```
- `-i`: iteration count.
- `-wi`: warmup iterations.
- `-f`: forks.
- `-t`: threads.

Output includes operations per second or time per op.

---

## 5. Best Practices

- **Warmup**: ensure JIT compilation stabilizes.
- **Forking**: isolate benchmarks from build process.
- **Avoid Dead Code**: use results to prevent elimination.
- **State Scoping**: use `Thread` or `Benchmark` scopes appropriately.
- **Parameterization**: use `@Param` to run benchmarks for different inputs.

---

## Further Reading

- Microbenchmarking Scala with JMH: https://chariotsolutions.com/blog/post/microbenchmarking-scala-with-jmh/  
- JMH Official Documentation: https://openjdk.org/projects/code-tools/jmh/  
