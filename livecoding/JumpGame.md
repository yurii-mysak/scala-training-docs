You are given an integer array nums. You are initially positioned at the array's first index, and each element in the array represents your maximum jump length at that position.

Return true if you can reach the last index, or false otherwise.

Example 1:

Input: nums = [2,3,1,1,4]
Output: true
Explanation: Jump 1 step from index 0 to 1, then 3 steps to the last index.
Example 2:

Input: nums = [3,2,1,0,4]
Output: false
Explanation: You will always arrive at index 3 no matter what. Its maximum jump length is 0, which makes it impossible to reach the last index.

```scala 3
object Solution {
    def canJump(nums: Array[Int]): Boolean = {
      nums.indices.reverse.foldLeft(nums.length - 1) {
        case (last, idx) =>
          if (idx + nums(idx) >= last) idx else last
      } == 0

    //   !nums.init.scanLeft(1)((m, n) => n.max(m - 1)).contains(0)
    }
}
```

You are given a 0-indexed array of integers nums of length n. You are initially positioned at nums[0].

Each element nums[i] represents the maximum length of a forward jump from index i. In other words, if you are at nums[i], you can jump to any nums[i + j] where:

0 <= j <= nums[i] and
i + j < n
Return the minimum number of jumps to reach nums[n - 1]. The test cases are generated such that you can reach nums[n - 1].

Example 1:

Input: nums = [2,3,1,1,4]
Output: 2
Explanation: The minimum number of jumps to reach the last index is 2. Jump 1 step from index 0 to 1, then 3 steps to the last index.
Example 2:

Input: nums = [2,3,0,1,4]
Output: 2

```scala 3
import scala.util.control.Breaks._

object Solution {
    def jump(nums: Array[Int]): Int = {
        // if nums.length == 1 then 0
      // var dp = List(0)
      // breakable {
      //   for (i <- 0 until nums.length) {
      //     dp = dp :+ (0 until dp(i) + 1).map(j => {
      //       nums(j) + j
      //     }).max

      //     if dp(i+1) >= nums.length - 1 then break
      //   }
      // }
      // dp.length - 1
      if nums.length == 1 then 0
      else {
        var last = 0
        var next = 0
        var count = 1
        breakable {
          for (i <- 0 until nums.length) {
            val temp = next
            next = (last until next + 1).map(j => {
              nums(j) + j
            }).max
            if next >= nums.length - 1 then break
            count += 1
            last = temp
          }
        }
        count
      }
    }
}
```