Given an array nums of size n, return the majority element.

The majority element is the element that appears more than ⌊n / 2⌋ times. You may assume that the majority element always exists in the array.

Example 1:

Input: nums = [3,2,3]
Output: 3
Example 2:

Input: nums = [2,2,1,1,1,2,2]
Output: 2

```scala 3
object Solution {
    def majorityElement(nums: Array[Int]): Int = {
        // val sorted = nums.sortInPlace
        // sorted(nums.length / 2)
        nums.foldLeft((nums(0), 0))((acc, x) => acc match {
            case (_, 0) => (x, 1)
            case (y, c) => if(x == y) (y, c + 1) else (y, c - 1)
        })._1
    }
}
```