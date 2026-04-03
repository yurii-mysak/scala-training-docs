We define a harmonious array as an array where the difference between its maximum value and its minimum value is exactly 1.

Given an integer array nums, return the length of its longest harmonious subsequence among all its possible subsequences.

Example 1:

Input: nums = [1,3,2,2,5,2,3,7]

Output: 5

Explanation:

The longest harmonious subsequence is [3,2,2,2,3].

Example 2:

Input: nums = [1,2,3,4]

Output: 2

Explanation:

The longest harmonious subsequences are [1,2], [2,3], and [3,4], all of which have a length of 2.

Example 3:

Input: nums = [1,1,1,1]

Output: 0

Explanation:

No harmonic subsequence exists.

```scala 3
object Solution {
  def findLHS(nums: Array[Int]): Int = {
    // is subsequence
    // find biggest subsequence where dif between min/max = 1
    // sort? hashtable?
    nums
      .sorted
      .distinct // at this stage have candidates
      .sliding(2, 1)
      .foldLeft(0)((acc, pair) => {
        if (pair.length == 2 && pair(1) - pair(0) == 1) {
          val count = nums.count(_ == pair(0)) + nums.count(_ == pair(1))
          if (count > acc) count else acc
        } else acc
      })
  }
}
```