# Classloaders in the JVM

## Overview

The JVM uses a delegation model of class loading. Each classloader delegates loading requests to its parent before attempting to load classes itself.

```ascii
Bootstrap
   |
Extension (Platform)
   |
System (Application)
   |
Custom ClassLoader
```

---

## Bootstrap ClassLoader

- **Loads**: Core Java classes from the `<JAVA_HOME>/jre/lib/rt.jar` (or modules in Java 9+).
- **Type**: Native, typically implemented in C/C++.
- **Role**: Foundation of the delegation chain; has no parent.

---

## Extension (Platform) ClassLoader

- **Loads**: Classes from `<JAVA_HOME>/jre/lib/ext` or the `java.ext.dirs` system property.
- **Parent**: Bootstrap.
- **Usage**: Additional platform libraries beyond the core.

---

## System (Application) ClassLoader

- **Loads**: Classes from the application classpath (`-classpath` or `CLASSPATH` env).
- **Parent**: Extension ClassLoader.
- **Common Name**: “AppClassLoader”.

---

## Custom ClassLoader

- **Extends**: `java.lang.ClassLoader`.
- **Overrides**: `findClass()` to define custom loading logic.
- **Use Cases**:
  - Loading plugins/modules at runtime.
  - Sandbox security environments.
  - Hot-reloading components.
- **Example**:

  ```java
  public class MyClassLoader extends ClassLoader {
      public MyClassLoader(ClassLoader parent) {
          super(parent);
      }
      @Override
      protected Class<?> findClass(String name) throws ClassNotFoundException {
          byte[] bytes = loadClassBytes(name);
          return defineClass(name, bytes, 0, bytes.length);
      }
      private byte[] loadClassBytes(String className) {
          // Read `.class` file bytes from custom source.
      }
  }
  ```

---

## Analogy

- Think of classloaders as a chain of departments in a company. A request for a document (class) is passed up the chain (delegation) until a department that owns it returns the document.

---

*Continue to the next area? (GC Profiling & Tuning)*
