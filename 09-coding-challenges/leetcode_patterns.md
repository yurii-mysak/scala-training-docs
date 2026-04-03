# LeetCode Patterns with Scala Implementations

This guide includes algorithmic patterns used in solving coding interview problems. Each section includes:

- Pattern name
- Common LeetCode problems
- Naive solution (if applicable)
- Optimized solution

---

## 🟩 Depth-First Search (DFS)

**Common Problems:**
- Number of Islands
- Clone Graph
- Max Area of Island
- Path Sum
- Flood Fill

### Naive Recursive DFS (Max Area of Island)
```scala
object MaxAreaOfIslandDFS {
  def maxAreaOfIsland(grid: Array[Array[Int]]): Int = {
    def dfs(r: Int, c: Int): Int = {
      if (r < 0 || c < 0 || r >= grid.length || c >= grid(0).length || grid(r)(c) == 0) return 0
      grid(r)(c) = 0
      1 + dfs(r+1, c) + dfs(r-1, c) + dfs(r, c+1) + dfs(r, c-1)
    }
    var maxArea = 0
    for (r <- grid.indices; c <- grid(0).indices) {
      maxArea = math.max(maxArea, dfs(r, c))
    }
    maxArea
  }
}
```

---

## 🟦 Breadth-First Search (BFS)

**Common Problems:**
- Number of Islands
- Word Ladder
- Rotten Oranges
- Shortest Path in Binary Matrix

### Naive DFS Alternative (Number of Islands)
```scala
object NumberOfIslandsDFS {
  def numIslands(grid: Array[Array[Char]]): Int = {
    def dfs(r: Int, c: Int): Unit = {
      if (r < 0 || c < 0 || r >= grid.length || c >= grid(0).length || grid(r)(c) == '0') return
      grid(r)(c) = '0'
      dfs(r+1, c); dfs(r-1, c); dfs(r, c+1); dfs(r, c-1)
    }
    var count = 0
    for (r <- grid.indices; c <- grid(0).indices) {
      if (grid(r)(c) == '1') {
        dfs(r, c)
        count += 1
      }
    }
    count
  }
}
```

### Optimized BFS (Number of Islands)
```scala
object NumberOfIslandsBFS {
  import scala.collection.mutable
  def numIslands(grid: Array[Array[Char]]): Int = {
    val directions = Array((1,0), (-1,0), (0,1), (0,-1))
    val queue = mutable.Queue[(Int, Int)]()
    var count = 0
    for (r <- grid.indices; c <- grid(0).indices) {
      if (grid(r)(c) == '1') {
        queue.enqueue((r, c))
        grid(r)(c) = '0'
        while (queue.nonEmpty) {
          val (x, y) = queue.dequeue()
          for ((dx, dy) <- directions) {
            val (nx, ny) = (x + dx, y + dy)
            if (nx >= 0 && ny >= 0 && nx < grid.length && ny < grid(0).length && grid(nx)(ny) == '1') {
              queue.enqueue((nx, ny))
              grid(nx)(ny) = '0'
            }
          }
        }
        count += 1
      }
    }
    count
  }
}
```

---

## 🟥 Dynamic Programming (DP)

**Common Problems:**
- Climbing Stairs
- Longest Increasing Subsequence
- Coin Change
- Edit Distance

### Optimized (Climb Stairs)
```scala
object ClimbStairs {
  def climbStairs(n: Int): Int = {
    if (n <= 2) return n
    var one = 2
    var two = 1
    for (_ <- 3 to n) {
      val temp = one
      one = one + two
      two = temp
    }
    one
  }
}
```

---

## 🟨 Sliding Window

**Common Problems:**
- Longest Substring Without Repeating Characters
- Permutation in String
- Minimum Window Substring

### Optimized
```scala
object LongestSubstring {
  def lengthOfLongestSubstring(s: String): Int = {
    import scala.collection.mutable
    val set = mutable.Set[Char]()
    var l = 0
    var maxLen = 0
    for (r <- s.indices) {
      while (set.contains(s(r))) {
        set -= s(l)
        l += 1
      }
      set += s(r)
      maxLen = math.max(maxLen, r - l + 1)
    }
    maxLen
  }
}
```

---

## 🟪 Union-Find

**Common Problems:**
- Number of Connected Components
- Redundant Connection
- Accounts Merge

### Optimized
```scala
object UnionFindExample {
  class UnionFind(n: Int) {
    val parent = (0 until n).toArray
    def find(x: Int): Int = {
      if (parent(x) != x) parent(x) = find(parent(x))
      parent(x)
    }
    def union(x: Int, y: Int): Unit = {
      val px = find(x)
      val py = find(y)
      if (px != py) parent(px) = py
    }
  }
}
```

---

## 🟧 Greedy

**Common Problems:**
- Jump Game
- Gas Station
- Partition Labels

### Optimized (Jump Game)
```scala
object JumpGame {
  def canJump(nums: Array[Int]): Boolean = {
    var reach = 0
    for (i <- nums.indices) {
      if (i > reach) return false
      reach = math.max(reach, i + nums(i))
    }
    true
  }
}
```

---

## 🟫 Backtracking

**Common Problems:**
- Subsets
- Permutations
- N-Queens

### Optimized (Subsets)
```scala
object Subsets {
  def subsets(nums: Array[Int]): List[List[Int]] = {
    val result = scala.collection.mutable.ListBuffer[List[Int]]()
    def backtrack(start: Int, path: List[Int]): Unit = {
      result += path
      for (i <- start until nums.length) {
        backtrack(i + 1, path :+ nums(i))
      }
    }
    backtrack(0, List())
    result.toList
  }
}
```

---

## 🟨 Two Pointers

**Common Problems:**
- 3Sum
- Valid Palindrome
- Container With Most Water

### Optimized (3Sum)
```scala
object ThreeSum {
  def threeSum(nums: Array[Int]): List[List[Int]] = {
    val sorted = nums.sorted
    val res = scala.collection.mutable.ListBuffer[List[Int]]()
    for (i <- sorted.indices if i == 0 || sorted(i) != sorted(i - 1)) {
      var l = i + 1
      var r = sorted.length - 1
      while (l < r) {
        val sum = sorted(i) + sorted(l) + sorted(r)
        if (sum == 0) {
          res += List(sorted(i), sorted(l), sorted(r))
          while (l < r && sorted(l) == sorted(l + 1)) l += 1
          while (l < r && sorted(r) == sorted(r - 1)) r -= 1
          l += 1; r -= 1
        } else if (sum < 0) l += 1
        else r -= 1
      }
    }
    res.toList
  }
}
```

---

## 🟦 Topological Sort

**Common Problems:**
- Course Schedule
- Alien Dictionary

### Optimized (Course Schedule)
```scala
object CourseSchedule {
  def canFinish(numCourses: Int, prerequisites: Array[Array[Int]]): Boolean = {
    val adj = Array.fill(numCourses)(List[Int]())
    val indegree = Array.fill(numCourses)(0)
    prerequisites.foreach { case Array(a, b) =>
      adj(b) ::= a
      indegree(a) += 1
    }
    val queue = scala.collection.mutable.Queue[Int]()
    for (i <- 0 until numCourses if indegree(i) == 0) queue.enqueue(i)
    var taken = 0
    while (queue.nonEmpty) {
      val course = queue.dequeue()
      taken += 1
      for (next <- adj(course)) {
        indegree(next) -= 1
        if (indegree(next) == 0) queue.enqueue(next)
      }
    }
    taken == numCourses
  }
}
```