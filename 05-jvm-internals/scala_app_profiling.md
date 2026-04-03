# Profiling a Scala Application

When diagnosing performance issues in a Scala application, use a systematic approach:

1. **Define your goals** (CPU hotspots, memory leaks, GC pauses, thread contention).  
2. **Choose tools** (sampling vs. instrumentation, open‑source vs. commercial).  
3. **Collect data** in an environment close to production.  
4. **Analyze results** (flame graphs, allocation charts, JFR events).  
5. **Iterate**: apply changes, re‑profile, and compare.

---

## 1. Profiling Goals

- **CPU profiling**: Identify methods consuming the most CPU cycles.  
- **Memory profiling**: Detect heap usage and potential leaks.  
- **Allocation profiling**: Find code paths generating excessive garbage.  
- **GC analysis**: Measure pause times and frequency.  
- **Thread contention**: Spot lock and I/O bottlenecks.

---

## 2. Common Tools

| Category         | Tool                               | Pros                                     | Cons                                |
|------------------|------------------------------------|------------------------------------------|-------------------------------------|
| **JDK Built-in** | Java Flight Recorder (JFR) + JMC   | Very low overhead; rich event set         | GUI-based; learning curve           |
| **Sampling**     | async-profiler + FlameGraph        | Nanosecond resolution; minimal overhead  | Requires native build; CLI only     |
| **Open-source**  | VisualVM                           | Easy GUI; plugin ecosystem               | Coarse sampling; higher overhead    |
| **Commercial**   | JProfiler / YourKit                | Deep allocation stacks; thread analysis  | License costs                       |
| **Scala ecosystem** | sbt-jfr plugin                  | JFR via sbt; integrates with builds      | Only JFR events                     |
| **Metrics**      | Kamon + Prometheus                 | Real-time metrics; histograms            | Requires code instrumentation       |

---

## 3. CPU Profiling with async-profiler

```bash
# Clone & build
git clone https://github.com/jvm-profiling-tools/async-profiler.git
cd async-profiler && ./build.sh

# Attach to JVM (30s CPU profile)
PID=$(jps -l | grep your-app.jar | awk '{print $1}')
./async-profiler/tool/profiler.sh -e cpu -d 30 -f cpu.svg $PID

# Inspect
open cpu.svg  # or view in your browser
```

---

## 4. Memory & Allocation Profiling

### Java Flight Recorder (JFR)

```bash
java -XX:StartFlightRecording=duration=5m,filename=app.jfr,settings=profile      -jar your-app.jar
```

- Open `app.jfr` in **Java Mission Control (JMC)**  
- Analyze “Memory” for heap usage and “Allocation” for garbage hotspots.

### async-profiler allocations

```bash
./async-profiler/tool/profiler.sh -e alloc -d 30 -f alloc.svg $PID
```

---

## 5. Thread Contention & Locks

```bash
./async-profiler/tool/profiler.sh -e lock -d 30 -f locks.svg $PID
```

- Visualize which monitors or locks cause the most wait time.

---

## 6. sbt Integration

Add to `project/plugins.sbt`:

```scala
addSbtPlugin("com.typesafe.sbt" % "sbt-jfr" % "2.2.0")
```

Enable in `build.sbt`:

```scala
enablePlugins(SbtJfr)
```

Record via sbt:

```bash
sbt jfr:record  # defaults to 60s, outputs .jfr under target/jfr/
```

---

## 7. IntelliJ IDEA Integration

### Java Flight Recorder

1. **IntelliJ Ultimate** includes JFR support.  
2. Run your app in IDEA, then open **Help → Diagnostic Tools → Start Flight Recording**.  
3. Stop and view recordings directly in IDEA’s JFR viewer.

### async-profiler Plugin

1. Install **async-profiler** plugin from JetBrains Marketplace.  
2. Configure the path to your `profiler.sh` in **Settings → Tools → async-profiler**.  
3. Start/stop profiling from the **Run** toolbar or via context menu.

### VisualVM Integration

1. Download and launch VisualVM.  
2. In IDEA, enable **Tools → VisualVM Launcher** plugin.  
3. Use **Run → Attach VisualVM** to connect to your JVM process.

---

## 8. Best Practices

- **Warm up** the JVM before profiling for accurate JIT-optimized hotspots.  
- **Profile realistic workloads** or replay production traffic.  
- **Use sampling** for low overhead; instrument only when necessary.  
- **Document runs**: record timestamps, JVM flags, app version.  
- **Compare profiles** before/after changes to validate improvements.  
- **Automate** basic benchmarks in CI (e.g., via sbt-jmh or JetBrains Benchmark).

---

## 9. Quick Reference

```text
# CPU Flame Graph
profiler.sh -e cpu -d 30 -f cpu.svg $PID

# Allocations
profiler.sh -e alloc -d 30 -f alloc.svg $PID

# Locks
profiler.sh -e lock -d 30 -f locks.svg $PID

# JFR Recording
java -XX:StartFlightRecording=duration=2m,filename=rec.jfr,settings=profile -jar app.jar

# sbt JFR
sbt jfr:record
```
