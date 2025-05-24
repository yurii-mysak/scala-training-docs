You have a long flowerbed in which some of the plots are planted, and some are not. However, flowers cannot be planted in adjacent plots.

Given an integer array flowerbed containing 0's and 1's, where 0 means empty and 1 means not empty, and an integer n, return true if n new flowers can be planted in the flowerbed without violating the no-adjacent-flowers rule and false otherwise.

Example 1:

Input: flowerbed = [1,0,0,0,1], n = 1
Output: true
Example 2:

Input: flowerbed = [1,0,0,0,1], n = 2
Output: false

```scala 3
import scala.annotation.tailrec

object Solution {
  // def canPlaceFlowers(flowerbed: Array[Int], n: Int): Boolean = {
  // flowerbed.foldLeft((0, n)) {
  // case ((idx, leftToPlant), value) if flowerbed.length == 1 && value == 0 && leftToPlant == 1 => flowerbed(0) = 1; (idx + 1, leftToPlant - 1)
  // case ((idx, leftToPlant), value) if leftToPlant == 0 || value == 1 => (idx + 1, leftToPlant)
  // case ((idx, leftToPlant), value) if value == 0 && leftToPlant > 0 && idx == 0 && flowerbed(idx + 1) == 1 =>
  //     (idx + 1, leftToPlant)
  // case ((idx, leftToPlant), value) if value == 0 && leftToPlant > 0 && idx == 0 && flowerbed(idx + 1) == 0 =>
  //     flowerbed(idx) = 1
  //     (idx + 1, leftToPlant - 1)
  // case ((idx, leftToPlant), value) if value == 0 && leftToPlant > 0 && idx == flowerbed.length - 1 && flowerbed(idx - 1) == 1 =>
  //     (idx + 1, leftToPlant)
  // case ((idx, leftToPlant), value) if value == 0 && leftToPlant > 0 && idx == flowerbed.length - 1 && flowerbed(idx - 1) == 0 =>
  //     flowerbed(idx) = 1
  //     (idx + 1, leftToPlant - 1)
  // case ((idx, leftToPlant), value) if value == 0 && leftToPlant > 0 && flowerbed(idx - 1) == 0 && flowerbed(idx + 1) == 1 =>
  //     (idx + 1, leftToPlant)
  // case ((idx, leftToPlant), value) if value == 0 && leftToPlant > 0 && flowerbed(idx - 1) == 1 && flowerbed(idx + 1) == 0 =>
  //     (idx + 1, leftToPlant)
  // case ((idx, leftToPlant), value) if value == 0 && leftToPlant > 0 && flowerbed(idx - 1) == 0 && flowerbed(idx + 1) == 0 =>
  //     flowerbed(idx) = 1
  //     (idx + 1, leftToPlant - 1)
  // case default => (default._1._1 + 1, default._1._2)
  // }._2 == 0

  // sol2
  // lazy val fb2 = (0 +: flowerbed :+ 0)
  // var leftFlowers = n
  // (1 until fb2.size - 1) foreach { i =>
  // if (fb2.slice(i - 1, i + 2).forall(_ == 0)) {
  //     fb2(i) = 1; leftFlowers = leftFlowers - 1
  // }
  // }
  // leftFlowers <= 0

  @tailrec
  final def placeFlowersRecurse(flowerbed: List[Int], n: Int): Boolean =
    if (n == 0)
      true
    else
      flowerbed match {
        case Nil => false
        case 0 :: Nil => n == 1
        case 1 :: 0 :: xs => {
          placeFlowersRecurse(xs, n)
        }
        case 0 :: 0 :: xs => {
          placeFlowersRecurse(1 :: 0 :: xs, n - 1)
        }
        case h :: xs => {
          placeFlowersRecurse(xs, n)
        }
      }

  def canPlaceFlowers(flowerbed: Array[Int], n: Int): Boolean =
    placeFlowersRecurse(flowerbed.toList, n)

  //   }
}
```