# JVM, JRE & JDK

## Overview

- **JVM (Java Virtual Machine)**: Executes Java bytecode, providing platform independence.
- **JRE (Java Runtime Environment)**: Includes the JVM and the core libraries needed to run Java applications.
- **JDK (Java Development Kit)**: Bundles the JRE plus development tools like the compiler (`javac`) and debugger.

```ascii
+-----------------------------+
|   Java Application (.jar)   |
+-----------------------------+
|           JRE               |
| +-------------------------+ |
| |        JVM              | |
| +-------------------------+ |
| |   Core Libraries        | |
| +-------------------------+ |
+-----------------------------+
```

---

## JVM Purpose

- Abstracts away operating system and hardware specifics.
- Manages memory allocation, thread scheduling, and garbage collection.
- Enforces the Java security model via class verification and bytecode checks.

---

## JVM Components

1. **Class Loader Subsystem**: Loads `.class` files and handles namespace management.
2. **Runtime Data Areas**:
   - **Method Area**: Stores class structures and metadata.
   - **Heap**: Runtime allocation pool for objects.
   - **Java Stacks**: Holds stack frames for method invocations.
   - **PC Registers**: Tracks the JVM instruction address.
   - **Native Method Stacks**: Manages native (non-Java) calls.
3. **Execution Engine**:
   - **Interpreter**: Executes bytecode one instruction at a time.
   - **JIT Compiler**: Compiles hot code paths to native machine code.
4. **Native Interface & Method Registry**: Integrates native libraries (`JNI`).

---

# Tools

## `javac`

- **Purpose**: Compiles Java source (`.java`) to bytecode (`.class`).
- **Example**:
  ```bash
  javac HelloWorld.java
  ```

## `java`

- **Purpose**: Launches the JVM to run a compiled application.
- **Example**:
  ```bash
  java HelloWorld
  java -jar myapp.jar
  ```

## `jar`

- **Purpose**: Packages `.class` files and resources into a JAR (ZIP format).
- **Basic Usage**:
  ```bash
  jar cf myapp.jar *.class
  jar tf myapp.jar   # list contents
  jar xf myapp.jar   # extract
  ```

---

# Debugging with Local Dev Environment

- **IDEs (IntelliJ/Eclipse)**: Set breakpoints, inspect variables, and step through code interactively.
- **Hot Swap**: Modify method bodies during a debug session (supported by many IDEs).
- **Command-Line Flags**:
  ```bash
  java -agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=5005 -jar myapp.jar
  ```
  - Connect an IDE or debugger to port `5005`.
- **Best Practices**:
  - Write focused unit tests for critical paths.
  - Use logging frameworks (SLF4J, Log4j) for rich diagnostic output.
  - Profile CPU/memory early to identify bottlenecks.

---

*Continue to the next area? (Memory Model: Stack & Heap)*
