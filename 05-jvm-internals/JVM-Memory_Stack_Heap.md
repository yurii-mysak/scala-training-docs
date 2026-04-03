# Memory Model: Stack & Heap

## Overview

The JVM memory model is divided into two primary regions:

- **Stack**:  
  - Stores method call frames, local primitive variables, and references to objects.  
  - Organized as LIFO (last-in, first-out).  
  - Fast allocation and deallocation.

- **Heap**:  
  - Stores all Java objects (`new`) and arrays.  
  - Shared among all threads.  
  - Managed by Garbage Collector (GC).

```ascii
+----------------------+    <-- Heap (objects)
|  Object A            |
+----------------------+
|  Object B            |
+----------------------+

+----------------------+    <-- Stack for Thread-1
| MethodC frame        |
| - localVar3          |
| - localRefX ---------+--> (ref to Object B on heap)
+----------------------+
| MethodB frame        |
| - localVar2          |
| - localRefY ---------+--> (ref to Object A on heap)
+----------------------+
| MethodA frame        |
| - localVar1          |
+----------------------+
```

---

## Primitive vs Reference Types

- **Primitive Types** (`byte`, `short`, `int`, `long`, `float`, `double`, `char`, `boolean`):  
  - Stored **directly** on the stack (if local) or inside the object on the heap (if field).  
  - Hold actual values.

- **Reference Types** (all subclasses of `Object`):  
  - Variable holds a **reference** (pointer) on the stack (for locals) or within another object.  
  - The actual object data resides on the heap.

### Example

```java
void example() {
    int x = 10;             // primitive: value 10 on stack
    String s = new String("Hi"); // reference s on stack, object on heap
}
```

---

## Passing: By Value vs By Reference

Java uses **pass-by-value**:

- **Primitives**: copy of the actual value is passed.
- **References**: copy of the reference (pointer) is passed, **not** the object itself.

```java
public void mutate(int a, MyObject obj) {
    a = 5;                // only local copy changes
    obj.value = 5;        // changes the heap object that both refer to
}

int x = 3;
MyObject mo = new MyObject(3);
mutate(x, mo);
// x remains 3, mo.value is now 5
```

---

## Stack Frames

Each method invocation creates a **stack frame** containing:

1. **Local Variables Array**  
2. **Operand Stack** (used by bytecode instructions)  
3. **Frame Data** (return address, method metadata pointer)

- **Allocation**: On method entry  
- **Deallocation**: On method exit  

```ascii
Stack Frame Structure:
+---------------------------+
| Operand Stack             |
+---------------------------+
| Local Variables           |
+---------------------------+
| Reference to Constant Pool|
+---------------------------+
| Return Address            |
+---------------------------+
```

---

## Analogy

- **Stack**: A stack of plates — you always add/remove from the top.  
- **Heap**: A large warehouse — objects can live anywhere, and GC cleans up unused items periodically.

---

*Continue to the next area? (Garbage Collection Basics & Details)*
