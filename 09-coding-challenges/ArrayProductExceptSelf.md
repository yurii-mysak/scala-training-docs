Given an integer array nums, return an array answer such that answer[i] is equal to the product of all the elements of nums except nums[i].

The product of any prefix or suffix of nums is guaranteed to fit in a 32-bit integer.

You must write an algorithm that runs in O(n) time and without using the division operation.

Example 1:

Input: nums = [1,2,3,4]
Output: [24,12,8,6]
Example 2:

Input: nums = [-1,1,0,-3,3]
Output: [0,0,9,0,0]

```scala 3
object Solution {
    def productExceptSelf(nums: Array[Int]): Array[Int] = {
        // nums.foldLeft(Array.fill(nums.length)(1), 0) {
        //     case ((acc, idx), num) => {
        //       (Array.tabulate(nums.length){ i => 
        //         if i != idx then acc(i) * num else acc(i)
        //       }, idx + 1)
        //     }
        // }._1
        val rightToLeftComputed = nums.dropRight(1).scanLeft(1)(_*_)
        val leftToRightComputed = nums.drop(1).scanRight(1)(_*_)
        rightToLeftComputed.zip(leftToRightComputed).map { case (i,j) => i * j }
    }
}
```