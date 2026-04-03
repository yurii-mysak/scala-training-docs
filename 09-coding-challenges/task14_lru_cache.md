# Task 14: LRU Cache

## Problem Statement
Design a data structure that follows the constraints of a Least Recently Used (LRU) cache. Implement the `LRUCache` class:
- `get(key)` – Get the value of the key if it exists, otherwise return -1.
- `put(key, value)` – Update the value of the key if exists, or add the key-value pair. If the cache reaches capacity, it should invalidate the least recently used item.

## Scala 3 Implementation

```scala
object LRUCache:
  import scala.collection.mutable
  class LRUCache(capacity: Int):
    private val cache = mutable.LinkedHashMap[Int, Int]()

    def get(key: Int): Int =
      if !cache.contains(key) then -1
      else
        val value = cache.remove(key).get
        cache.put(key, value)
        value

    def put(key: Int, value: Int): Unit =
      if cache.contains(key) then cache.remove(key)
      cache.put(key, value)
      if cache.size > capacity then
        cache.remove(cache.head._1)

  @main def run(): Unit =
    val lru = LRUCache(2)
    lru.put(1,1); lru.put(2,2)
    println(lru.get(1))    // returns 1
    lru.put(3,3)           // evicts key 2
    println(lru.get(2))    // returns -1
    lru.put(4,4)           // evicts key 1
    println(lru.get(1))    // returns -1
    println(lru.get(3))    // returns 3
    println(lru.get(4))    // returns 4
```

## Explanation & Traversal
1. **Approach**: Use `LinkedHashMap` to maintain insertion/access order.
2. **Traversal**:
   - On `get`, remove and reinsert to mark as recently used.
   - On `put`, remove existing, insert new, and remove oldest if over capacity.

## Time & Space Complexity
- **Time**: O(1) average per operation  
- **Space**: O(capacity)
