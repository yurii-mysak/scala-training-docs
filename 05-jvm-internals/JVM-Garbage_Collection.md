# Garbage Collection & Heap Tuning

## Garbage Collection Basics

- **Purpose**: Automate memory management by reclaiming objects that are no longer reachable, preventing memory leaks.
- **Generational Hypothesis**: Most objects die young; GC divides the heap into generations to optimize reclaiming.
- **GC Roots**: Starting points for reachability analysis (e.g., local variables, static fields, JNI references).

## Heap Memory Details

The heap is subdivided into:

1. **Young Generation**  
   - **Eden Space**: New objects are allocated here.  
   - **Survivor Spaces (S0 & S1)**: Objects that survive one GC cycle move here.  
2. **Old (Tenured) Generation**  
   - Stores long-lived objects promoted from the young generation.  
3. **Permanent Generation / Metaspace**  
   - Stores class metadata, interned strings (PermGen in Java 7 and earlier; Metaspace in Java 8+).

```ascii
Heap Layout:
+-----------------------------+
| Permanent Generation (Meta) |
+-----------------------------+
|       Old Generation        |
+-----------------------------+
| Survivor 1 | Survivor 2     |
+------------+----------------+
|           Eden              |
+-----------------------------+
```

### Tuning Heap Sizes

- `-Xms<size>`: Initial heap size.  
- `-Xmx<size>`: Maximum heap size.  
- `-XX:NewSize` / `-XX:MaxNewSize`: Young generation size.  
- `-XX:SurvivorRatio=<ratio>`: Ratio between Eden and Survivor spaces.  
- `-XX:MaxTenuringThreshold=<n>`: Number of GC cycles before promotion.

```bash
java -Xms512m -Xmx2g -XX:NewSize=256m -XX:MaxNewSize=512m      -XX:SurvivorRatio=8 -XX:MaxTenuringThreshold=15 -jar myapp.jar
```

## Garbage Collection Details

### 1. Mark-and-Sweep
1. **Mark**: Traverse object graph from GC Roots, mark reachable objects.  
2. **Sweep**: Reclaim unmarked (unreachable) objects.

### 2. Mark-and-Compact
- **Mark**: Same as above.  
- **Compact**: Move live objects towards one end to reduce fragmentation, update references.

### 3. Copying (used in Young Gen)
- Divide space into two semispaces.  
- **Copy** live objects from Eden & one Survivor to the other Survivor, then swap.

### Object Aging & Promotion
- Each GC cycle increments an object's age if it survives.  
- When age exceeds the tenuring threshold, it's promoted to the Old Generation.

---

*Continue to the next area? (Classloaders)*