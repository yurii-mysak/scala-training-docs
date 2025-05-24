# Recursion & Dynamic Programming

This file covers fundamental recursion concepts and dynamic programming techniques.

---

## Recursion

**Definition:**  
A technique where a function calls itself to solve smaller instances of the same problem. Requires:
- **Base case:** Stops recursion.  
- **Recursive case:** Breaks problem into subproblems.

> **Analogy:**  
> Like Russian nesting dolls—each doll opens to reveal a smaller one until the smallest is reached.

### Example: Factorial

```scala
def factorial(n: Int): Int =
  if n <= 1 then 1
  else n * factorial(n - 1)
```

<details>
<summary>Call Tree (Mermaid)</summary>

```mermaid
graph TD
  A[factorial(4)] --> B[factorial(3)]
  B --> C[factorial(2)]
  C --> D[factorial(1)]
  D --> E[1]
```
</details>

---

## Dynamic Programming

**Definition:**  
Optimization over naive recursion by storing (memoizing) results of overlapping subproblems.

### 1. Top-Down (Memoization)

```scala
import scala.collection.mutable

def fibMemo(n: Int): Int =
  val cache = mutable.Map.empty[Int, Int]
  def go(k: Int): Int =
    if k <= 1 then k
    else cache.getOrElseUpdate(k, go(k - 1) + go(k - 2))
  go(n)
```

### 2. Bottom-Up (Tabulation)

```scala
def fibTab(n: Int): Int =
  if n <= 1 then n
  else
    val dp = Array.fill(n + 1)(0)
    dp(1) = 1
    for i <- 2 to n do dp(i) = dp(i - 1) + dp(i - 2)
    dp(n)
```

<details>
<summary>DP Table Diagram (Mermaid)</summary>

```mermaid
flowchart LR
  subgraph Table
    A[dp(0)=0] --> B[dp(1)=1] --> C[dp(2)=1] --> D[dp(3)=2] --> E[dp(4)=3]
  end
```
</details>

---

## Common DP Patterns

- **0/1 Knapsack:** Optimize selection within weight limit using 2D DP table.  
- **Longest Common Subsequence:** Build matrix of subsequence lengths.  
- **Matrix Chain Multiplication:** Evaluate optimal multiplication order.

---

*Next up: Trees & Graphs (Types, Tries, Binary Heaps, Traversals, Graph Search).*  
*Send “continue” when you’re ready!*  
