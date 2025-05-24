# Ahead-of-Time vs Just-in-Time Compilation

## Just-in-Time (JIT) Compilation

- **Process**:
  1. **Interpretation**: JVM interpreter executes bytecode instruction-by-instruction.
  2. **Profiling**: JVM identifies “hot” methods or loops (frequently executed).
  3. **Compilation**: Hot code is compiled to native machine code by the JIT compiler.
     - **C1 (Client) Compiler**: Optimized for quick compilation with modest optimizations.
     - **C2 (Server) Compiler**: Performs deeper optimizations for long-running applications.
  4. **Execution**: Native code is executed directly, improving performance.

- **Advantages**:
  - Adapts to runtime behavior and data, enabling dynamic optimizations.
  - Uses feedback from execution (e.g., inlining, branch prediction) for HotSpot optimizations.

- **Disadvantages**:
  - Warm-up time: performance improves gradually as code is profiled and compiled.
  - Runtime resource usage for compilation.

- **Configuration Flags**:
  ```bash
  -XX:+UseJVMCICompiler      # Use Graal as JIT compiler
  -XX:CompileThreshold=10000 # Number of invocations before compiling a method
  ```

---

## Ahead-of-Time (AOT) Compilation

- **Process**:
  1. **Native Image Generation**: Bytecode and dependencies are compiled into a standalone native binary.
  2. **Linking**: Native code and required libraries are linked into a single executable.

- **Tools**:
  - **GraalVM Native Image**: Produces small, self-contained executables.
    ```bash
    native-image --no-fallback -jar myapp.jar
    ```

- **Advantages**:
  - Fast startup time and low memory overhead (no JVM startup).
  - Simplified deployment: single binary without separate JRE.
- **Disadvantages**:
  - Limited dynamic features (reflection, dynamic class loading) require configuration.
  - Native-image build time can be lengthy.
  - Potentially larger binary size depending on include/exclude settings.

---

## Comparison

| Aspect            | JIT Compilation                  | AOT Compilation                    |
|-------------------|----------------------------------|------------------------------------|
| Startup Time      | Slower (JVM boot + warm-up)      | Fast (native binary)               |
| Peak Performance  | High (runtime optimizations)     | Moderate (static optimizations)    |
| Memory Footprint  | Larger (JVM + compiled code)     | Smaller (single binary)            |
| Dynamic Features  | Full (reflection, class loading) | Limited (requires config)          |
| Deployment        | Requires JRE/JDK installation    | Standalone executable              |

---

## Analogy

- **JIT**: Like a chef learning your favorite dishes over time and cooking them faster each visit.
- **AOT**: Like a meal kit pre-packed with ingredients and instructions — ready to heat and serve immediately.

---

*All sections complete!*