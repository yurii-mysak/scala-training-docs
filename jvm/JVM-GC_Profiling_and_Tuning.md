# GC Profiling & Tuning

## GC Implementations

- **Serial GC** (`-XX:+UseSerialGC`):  
  - Single-threaded, suitable for small heaps (<100MB).  
- **Parallel GC** (`-XX:+UseParallelGC`):  
  - Multi-threaded, throughput-oriented.  
- **CMS (Concurrent Mark-Sweep)** (`-XX:+UseConcMarkSweepGC`):  
  - Low-pause goal, concurrent marking phases.  
- **G1 (Garbage-First) GC** (`-XX:+UseG1GC`):  
  - Region-based, mixed collection of young and old regions.  
- **ZGC** (`-XX:+UseZGC`):  
  - Low-latency (<10ms pauses), concurrent relocation.  
- **Shenandoah** (`-XX:+UseShenandoahGC`):  
  - Low-pause (US-based), concurrent evacuation.

---

## Tuning GC

- **Pause Time Goal**:  
  - `-XX:MaxGCPauseMillis=<ms>` for G1, ZGC.  
- **Heap Occupancy Trigger**:  
  - `-XX:InitiatingHeapOccupancyPercent=<percent>` for G1.  
- **Survivor Ratio & Tenuring**:  
  - `-XX:SurvivorRatio=<ratio>`, `-XX:MaxTenuringThreshold=<n>`.  
- **Ergonomics**:  
  - JVM auto-tunes based on available CPU cores and memory.

## Memory Profiling Tools

- **jstat**: Monitor GC and heap statistics.  
  ```bash
  jstat -gc <pid> 1000
  ```  
- **jmap**: Heap dump generation.  
  ```bash
  jmap -dump:live,format=b,file=heap.hprof <pid>
  ```  
- **jconsole**: GUI for monitoring memory, threads, classes.  
- **VisualVM**: Plugin-based profiling (CPU, memory, GC).  
- **Java Flight Recorder (JFR)**: Low-overhead event recording.

## Performance Profiling with Java Agent

- **Java Agents**: Attach at startup (`-javaagent:path/agent.jar`) or dynamically with `VirtualMachine.attach()`.  
- **Common Tools**:  
  - **Async-Profiler**: CPU, allocation, lock profiling.  
  - **BTrace**: Dynamic tracing via bytecode instrumentation.  
  - **YourKit** / **JProfiler**: Commercial profilers with agents.  
- **Example**:  
  ```bash
  java -javaagent:async-profiler.jar=start,dir=./profile,events=cpu,file=profile.svg        -jar myapp.jar
  ```
- **Use Cases**: Identify hot methods, memory leaks, synchronization bottlenecks.

---

*Continue to the final area? (Ahead-of-Time vs Just-In-Time Compilation)*