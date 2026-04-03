You are given an array prices where prices[i] is the price of a given stock on the ith day.

You want to maximize your profit by choosing a single day to buy one stock and choosing a different day in the future to sell that stock.

Return the maximum profit you can achieve from this transaction. If you cannot achieve any profit, return 0.

Example 1:

Input: prices = [7,1,5,3,6,4]
Output: 5
Explanation: Buy on day 2 (price = 1) and sell on day 5 (price = 6), profit = 6-1 = 5.
Note that buying on day 2 and selling on day 1 is not allowed because you must buy before you sell.
Example 2:

Input: prices = [7,6,4,3,1]
Output: 0
Explanation: In this case, no transactions are done and the max profit = 0.

```scala 3
object Solution {
    def maxProfit(prices: Array[Int]): Int = {

    // prices.foldLeft((Int.MaxValue, 0)) {
    //   case ((minPrice, maxProfit), price) =>
    //     (minPrice min price, maxProfit max (price - minPrice))
    // }._2
    var maxProfit = 0
    var minPrice = Int.MaxValue

    prices.foldLeft(maxProfit) {
      case (idx, price) =>
        if (price < minPrice)
          minPrice = price
        else if (price - minPrice > maxProfit)
          maxProfit = price - minPrice
        maxProfit
    }
  }
}
```
II

You are given an integer array prices where prices[i] is the price of a given stock on the ith day.

On each day, you may decide to buy and/or sell the stock. You can only hold at most one share of the stock at any time. However, you can buy it then immediately sell it on the same day.

Find and return the maximum profit you can achieve.

```scala 3
object Solution {
    def maxProfit(prices: Array[Int]): Int = {
        if (prices.length <= 1) 0
        else
            prices.sliding(2).map(p => (p(1) - p(0)) max 0).sum
    }
}
```