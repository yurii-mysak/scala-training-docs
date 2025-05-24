Given an integer array nums, return true if there exists a triple of indices (i, j, k) such that i < j < k and nums[i] < nums[j] < nums[k]. If no such indices exists, return false.

Example 1:

Input: nums = [1,2,3,4,5]
Output: true
Explanation: Any triplet where i < j < k is valid.
Example 2:

Input: nums = [5,4,3,2,1]
Output: false
Explanation: No triplet exists.
Example 3:

Input: nums = [2,1,5,0,4,6]
Output: true
Explanation: The triplet (3, 4, 5) is valid because nums[3] == 0 < nums[4] == 4 < nums[5] == 6.

```scala 3
object Solution {
    def increasingTriplet(nums: Array[Int]): Boolean = {
        if (nums.length < 3) false
        else
        //   var result = false
        //   nums.foldLeft(Int.MaxValue, Int.MaxValue, Int.MaxValue) {
        //     case ((first, second, third), num) =>
        //       if (num <= first) (num, second, third)
        //       else if (num <= second) (first, num, third)
        //       else 
        //         result = true
        //         (first, second, num)
        //   }

        //   result
            // var first: Int = Int.MaxValue
            // var second: Int = Int.MaxValue
            // var isFind: Boolean = false

            // nums.foreach(num => {
            //     if (!isFind) {
            //         first = Math.min(num, first)
            //         second = if(num > first) Math.min(num, second) else second
            //         isFind = num > second
            //     }
            // })
            // isFind

            // bad speed, good memory:
            // val maxSuffix = nums.scanRight(0)(math.max)
            // val minPrefix = nums.scanLeft(Int.MaxValue)(math.min)
            // (1 until nums.length).exists { i =>
            // minPrefix(i) < nums(i) && nums(i) < maxSuffix(i + 1)
            }
    }
}
```