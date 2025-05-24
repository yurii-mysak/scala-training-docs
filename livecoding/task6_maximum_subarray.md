# Task 6: Maximum Subarray

## Problem Statement
Given an integer array `nums`, find the contiguous subarray (containing at least one number) which has the largest sum and return its sum.

## Scala 3 Implementation

```scala
object MaximumSubarray:
  def maxSubArray(nums: Array[Int]): Int =
    var currentSum = nums(0)
    var maxSum = nums(0)
    for i <- 1 until nums.length do
      currentSum = math.max(nums(i), currentSum + nums(i))
      maxSum = math.max(maxSum, currentSum)
    maxSum

  @main def run(): Unit =
    val nums = Array(-2,1,-3,4,-1,2,1,-5,4)
    println(s"Max Subarray Sum: ${maxSubArray(nums)}") // 6
```

## Explanation & Traversal
1. **Approach (Kadane's Algorithm)**: Maintain a running sum and reset if it drops below the current element.
2. **Traversal**:
   - `currentSum` = max(`nums[i]`, `currentSum + nums[i]`)
   - `maxSum` = max(`maxSum`, `currentSum`)
3. **Example** for `[-2,1,-3,4,-1,2,1,-5,4]`:
   - currentSum progression: -2, 1, -2, 4, 3, 5, 6, 1, 5
   - maxSum progression: -2, 1, 1, 4, 4, 5, 6, 6, 6

## Time & Space Complexity
- **Time**: O(n)  
- **Space**: O(1)
