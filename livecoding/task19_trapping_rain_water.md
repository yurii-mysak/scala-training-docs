# Task 19: Trapping Rain Water

## Problem Statement
Given `n` non-negative integers representing an elevation map where the width of each bar is 1, compute how much water it can trap after raining.

## Scala 3 Implementation

```scala
object TrappingRainWater:
  def trap(height: Array[Int]): Int =
    var left = 0; var right = height.length - 1
    var leftMax = 0; var rightMax = 0; var water = 0
    while left < right do
      if height(left) < height(right) then
        if height(left) >= leftMax then leftMax = height(left)
        else water += leftMax - height(left)
        left += 1
      else
        if height(right) >= rightMax then rightMax = height(right)
        else water += rightMax - height(right)
        right -= 1
    water

  @main def run(): Unit =
    println(trap(Array(0,1,0,2,1,0,1,3,2,1,2,1))) // 6
```

## Explanation & Traversal
1. **Approach**: Two-pointer technique tracking left/right max.
2. **Traversal**:
   - Move pointers inward from both ends.
   - Accumulate trapped water based on min(leftMax, rightMax) minus height.

## Time & Space Complexity
- **Time**: O(n)  
- **Space**: O(1)
