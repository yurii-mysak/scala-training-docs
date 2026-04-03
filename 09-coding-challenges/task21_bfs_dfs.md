# Task 21: BFS and DFS Graph Traversal

## Problem Statement
Given a graph represented by an adjacency list, implement Breadth-First Search (BFS) and Depth-First Search (DFS) traversals.

## Scala 3 Implementation

### BFS

```scala
object GraphBFS:
  def bfs(start: Int, graph: Map[Int, List[Int]]): List[Int] =
    import scala.collection.mutable
    val visited = mutable.Set[Int]()
    val queue = mutable.Queue[Int]()
    val traversal = mutable.ListBuffer[Int]()

    visited += start
    queue.enqueue(start)

    while queue.nonEmpty do
      val node = queue.dequeue()
      traversal += node
      for neighbor <- graph.getOrElse(node, Nil) do
        if !visited.contains(neighbor) then
          visited += neighbor
          queue.enqueue(neighbor)

    traversal.toList

  @main def runBFS(): Unit =
    val graph = Map(1 -> List(2,3), 2 -> List(4), 3 -> List(5), 4 -> Nil, 5 -> Nil)
    println(s"BFS: ${bfs(1, graph).mkString(", ")}") // Output: 1, 2, 3, 4, 5
```

### DFS

```scala
object GraphDFS:
  def dfs(start: Int, graph: Map[Int, List[Int]]): List[Int] =
    import scala.collection.mutable
    val visited = mutable.Set[Int]()
    val traversal = mutable.ListBuffer[Int]()

    def visit(node: Int): Unit =
      if !visited.contains(node) then
        visited += node
        traversal += node
        for neighbor <- graph.getOrElse(node, Nil) do
          visit(neighbor)

    visit(start)
    traversal.toList

  @main def runDFS(): Unit =
    val graph = Map(1 -> List(2,3), 2 -> List(4), 3 -> List(5), 4 -> Nil, 5 -> Nil)
    println(s"DFS: ${dfs(1, graph).mkString(", ")}") // Output: 1, 2, 4, 3, 5
```

## Explanation & Traversal
1. **BFS**: Explores neighbors level by level using a queue, ensuring shortest path in unweighted graphs.
2. **DFS**: Explores as far as possible along each branch before backtracking, using recursion (or an explicit stack).
3. **Example Graph**:  
   ```
     1
    /    2   3
   |   |
   4   5
   ```
   - BFS Order: `1 → 2 → 3 → 4 → 5`  
   - DFS Order: `1 → 2 → 4 → 3 → 5`

## Time & Space Complexity
- **Time**: O(V + E), where V = number of vertices and E = number of edges  
- **Space**: O(V + E) for storing visited set and queue/recursion stack
