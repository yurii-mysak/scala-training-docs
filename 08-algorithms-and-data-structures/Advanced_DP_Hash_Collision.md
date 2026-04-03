# Advanced Dynamic Programming & Hash Table Collision Resolution

This file covers:
- Advanced Dynamic Programming patterns  
- Hash Table Collision Resolution techniques  

---

## Advanced Dynamic Programming

DP extends beyond simple linear problems to complex domains:

### 1. 0/1 Knapsack

- **Problem:** Maximize value under weight limit.
- **Approach:** 2D DP table `dp[i][w]` = max value using first `i` items with weight ≤ `w`.
- **Complexity:** O(nW) time & space.

```scala
case class Item(weight: Int, value: Int)
def knapsack(items: Seq[Item], W: Int): Int =
  val n = items.length
  val dp = Array.ofDim[Int](n + 1, W + 1)
  for i <- 1 to n do
    for w <- 0 to W do
      dp(i)(w) = dp(i - 1)(w)
      if items(i - 1).weight <= w then
        dp(i)(w) = dp(i)(w) max (items(i - 1).value + dp(i - 1)(w - items(i - 1).weight))
  dp(n)(W)
```

### 2. Longest Common Subsequence (LCS)

- **Problem:** Find longest subsequence present in both strings.
- **Approach:** 2D table `dp[i][j]` = LCS length of `A[0..i-1]` and `B[0..j-1]`.
- **Complexity:** O(nm) time & space.

```scala
def lcs(a: String, b: String): Int =
  val dp = Array.ofDim[Int](a.length + 1, b.length + 1)
  for i <- 1 to a.length do
    for j <- 1 to b.length do
      dp(i)(j) =
        if a(i - 1) == b(j - 1) then dp(i - 1)(j - 1) + 1
        else dp(i - 1)(j) max dp(i)(j - 1)
  dp(a.length)(b.length)
```

### 3. Matrix Chain Multiplication

- **Problem:** Parenthesize matrix product to minimize scalar multiplications.
- **Approach:** DP on chain splits: `dp[i][j]` = min cost for matrices `i..j`.
- **Complexity:** O(n³) time, O(n²) space.

```scala
def matrixChain(dims: Array[Int]): Int =
  val n = dims.length - 1
  val dp = Array.fill(n, n)(0)
  for length <- 2 to n do
    for i <- 0 until n - length + 1 do
      val j = i + length - 1
      dp(i)(j) = Int.MaxValue
      for k <- i until j do
        val cost = dp(i)(k) + dp(k + 1)(j) + dims(i) * dims(k + 1) * dims(j + 1)
        dp(i)(j) = dp(i)(j) min cost
  dp(0)(n - 1)
```

---

## Hash Table Collision Resolution

When multiple keys map to same bucket, collisions occur. Common strategies:

### 1. Separate Chaining

- **Structure:** Each bucket holds a linked list (or other container) of entries.
- **Pros:** Simple, load factor >1 tolerated.
- **Cons:** Extra memory for lists; worst-case O(n) per bucket.

```scala
// conceptual chaining with ListBuffer
val table = Array.fill[ListBuffer[(K, V)]](capacity)(ListBuffer.empty)
def put(k: K, v: V): Unit =
  val idx = hash(k) % table.length
  table(idx).find(_._1 == k) match
    case Some((_, _)) => // update
    case None => table(idx) += ((k, v))
```

### 2. Open Addressing

Stores all entries in array; probes for empty slot.

#### a) Linear Probing

- **Probe:** `(hash + i) % capacity`
- **Pros:** Cache-friendly.
- **Cons:** Clustering (primary).

#### b) Quadratic Probing

- **Probe:** `(hash + c1*i + c2*i*i) % capacity`
- **Reduces** primary clustering.

#### c) Double Hashing

- **Probe:** `(hash1 + i * hash2) % capacity`
- **Best** distribution, needs good secondary hash.

> **Load Factor (α):** `size / capacity`—as α ↑, collision resolution cost ↑.  
> **Resize** when α > threshold (e.g., 0.7).

---

*Next up: Dijkstra’s Algorithm.*  
*Send “continue” when you’re ready!*  
