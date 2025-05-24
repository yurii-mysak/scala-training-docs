# Task 16: Subsets

## Problem Statement
Given an integer array `nums` of unique elements, return all possible subsets (the power set).

## Scala 3 Implementation

```scala
object Subsets:
  def subsets(nums: Array[Int]): List[List[Int]] =
    val res = scala.collection.mutable.ListBuffer[List[Int]]()
    def backtrack(index: Int, path: List[Int]): Unit =
      if index == nums.length then
        res += path; return
      backtrack(index+1, path)
      backtrack(index+1, nums(index) :: path)
    backtrack(0, Nil)
    res.toList.map(_.reverse)

  @main def run(): Unit =
    println(subsets(Array(1,2,3))) // List(List(), List(1), List(2), List(1,2), List(3), ...)
```

## Explanation & Traversal
1. **Approach**: Backtracking to include/exclude each element.
2. **Traversal**:
   - At each index, recurse without and with the current number.

## Time & Space Complexity
- **Time**: O(2^n * n)  
- **Space**: O(n)
