# Task 1: Two Sum

## Problem Statement
Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`.  
Assume that each input would have exactly one solution, and you may not use the same element twice. You can return the answer in any order.

## Scala 3 Implementation

```scala
object TwoSum:
  def twoSum(nums: Array[Int], target: Int): Array[Int] =
    // Implementation here
    ???

  @main def run(): Unit =
    val nums = Array(2, 7, 11, 15)
    val target = 9
    val result = twoSum(nums, target)
    println(s"Indices: ${result.mkString(", ")}")
```

## Explanation & Traversal
1. **Approach**: Use a HashMap to store complement and index.
2. **Traversal**:
   - Iterate through the array with index `i`.
   - For each element `num = nums(i)`, check if `target - num` exists in the map.
   - If yes, return indices.
   - Otherwise, add `num` -> `i` to the map.

## Time & Space Complexity
- **Time**: O(n)
- **Space**: O(n)

```scala
// Example traversal for [2,7,11,15], target=9:
// i=0, num=2, complement=7, not in map -> map = {2 -> 0}
// i=1, num=7, complement=2, found in map -> return [0, 1]
```
