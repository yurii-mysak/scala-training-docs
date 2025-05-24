# Task 12: Number of Islands

## Problem Statement
Given a 2D grid of `'1's (land) and '0's (water), return the number of islands. An island is surrounded by water and is formed by connecting adjacent lands horizontally or vertically.

## Scala 3 Implementation

```scala
object NumberOfIslands:
  def numIslands(grid: Array[CharArray]): Int =
    var count = 0
    for i <- grid.indices; j <- grid(i).indices do
      if grid(i)(j) == '1' then
        count += 1
        dfs(grid, i, j)
    count

  private def dfs(grid: Array[CharArray], i: Int, j: Int): Unit =
    if i < 0 || j < 0 || i >= grid.length || j >= grid(i).length || grid(i)(j) != '1' then return
    grid(i)(j) = '0'
    dfs(grid, i+1, j); dfs(grid, i-1, j)
    dfs(grid, i, j+1); dfs(grid, i, j-1)

  @main def run(): Unit =
    val grid = Array("11110".toCharArray, "11010".toCharArray, "11000".toCharArray, "00000".toCharArray)
    println(s"Islands: ${numIslands(grid)}") // 1
```

## Explanation & Traversal
1. **Approach**: DFS flood fill to sink visited land.
2. **Traversal**:
   - Iterate all cells; when finding '1', increment count and flood-fill to mark connected land.

## Time & Space Complexity
- **Time**: O(m * n)  
- **Space**: O(m * n) recursion stack
