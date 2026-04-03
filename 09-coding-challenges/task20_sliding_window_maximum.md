# Task 20: Sliding Window Maximum

## Problem Statement
Given an array `nums` and an integer `k`, return the maximum value of each subarray of length `k`.

## Scala 3 Implementation

```scala
object SlidingWindowMax:
  import scala.collection.mutable
  def maxSlidingWindow(nums: Array[Int], k: Int): Array[Int] =
    val deque = mutable.ArrayDeque[Int]()
    val result = scala.collection.mutable.ArrayBuffer[Int]()
    for i <- nums.indices do
      if deque.nonEmpty && deque.head < i - k + 1 then deque.removeHead()
      while deque.nonEmpty && nums(deque.last) < nums(i) do deque.removeLast()
      deque.append(i)
      if i >= k - 1 then result.append(nums(deque.head))
    result.toArray

  @main def run(): Unit =
    val nums = Array(1,3,-1,-3,5,3,6,7)
    val k = 3
    println(maxSlidingWindow(nums, k).mkString(", ")) // 3,3,5,5,6,7
```

## Explanation & Traversal
1. **Approach**: Double-ended queue (deque) to track candidate maximum indices.
2. **Traversal**:
   - Remove indices out of window.
   - Remove smaller values at deque tail.
   - Append current index and record head as max when window is full.

## Time & Space Complexity
- **Time**: O(n)  
- **Space**: O(k)
