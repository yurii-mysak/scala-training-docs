# Task 5: Best Time to Buy and Sell Stock

## Problem Statement
You are given an array `prices` where `prices[i]` is the price of a given stock on day `i`.  
Return the maximum profit you can achieve by choosing a single day to buy one stock and choosing a different day in the future to sell that stock.

## Scala 3 Implementation

```scala
object BestTimeToBuySell:
  def maxProfit(prices: Array[Int]): Int =
    var minPrice = Int.MaxValue
    var maxProfit = 0
    for price <- prices do
      if price < minPrice then
        minPrice = price
      else if price - minPrice > maxProfit then
        maxProfit = price - minPrice
    maxProfit

  @main def run(): Unit =
    val prices = Array(7,1,5,3,6,4)
    println(s"Max Profit: ${maxProfit(prices)}") // 5
```

## Explanation & Traversal
1. **Approach**: Track the minimum price seen so far and the maximum profit.
2. **Traversal**:
   - Initialize `minPrice` to ∞ and `maxProfit` to 0.
   - For each `price`:
     - Update `minPrice` if `price` is lower.
     - Else, compute profit `price - minPrice` and update `maxProfit`.
3. **Example** for `[7,1,5,3,6,4]`:
   - Day 0: price=7, minPrice=7
   - Day 1: price=1, minPrice=1
   - Day 2: price=5, profit=4, maxProfit=4
   - Day 3: price=3, profit=2, maxProfit=4
   - Day 4: price=6, profit=5, maxProfit=5
   - Day 5: price=4, profit=3, maxProfit=5

## Time & Space Complexity
- **Time**: O(n)  
- **Space**: O(1)
