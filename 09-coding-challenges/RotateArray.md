Given an integer array nums, rotate the array to the right by k steps, where k is non-negative.

Example 1:

Input: nums = [1,2,3,4,5,6,7], k = 3
Output: [5,6,7,1,2,3,4]
Explanation:
rotate 1 steps to the right: [7,1,2,3,4,5,6]
rotate 2 steps to the right: [6,7,1,2,3,4,5]
rotate 3 steps to the right: [5,6,7,1,2,3,4]

```scala 3
object Solution {
  def rotate(nums: Array[Int], k: Int): Unit = {
    val num_size = nums.length
    val normalizedShift = k % num_size
    val new_nums = nums.takeRight(normalizedShift).concat(nums.take(num_size-normalizedShift))
    for (i <- 0 until num_size)
      nums(i) = new_nums(i)
  }
}
```