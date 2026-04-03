# Task 11: Binary Tree Level Order Traversal

## Problem Statement
Given the root of a binary tree, return the level order traversal of its nodes' values (i.e., from left to right, level by level).

## Scala 3 Implementation

```scala
case class TreeNode(value: Int, left: TreeNode = null, right: TreeNode = null)

object LevelOrderTraversal:
  def levelOrder(root: TreeNode): List[List[Int]] =
    import scala.collection.mutable.Queue
    if root == null then return Nil
    val result = scala.collection.mutable.ListBuffer[List[Int]]()
    val queue = Queue[TreeNode]()
    queue.enqueue(root)
    while queue.nonEmpty do
      val levelSize = queue.size
      val level = scala.collection.mutable.ListBuffer[Int]()
      for _ <- 0 until levelSize do
        val node = queue.dequeue()
        level += node.value
        if node.left != null then queue.enqueue(node.left)
        if node.right != null then queue.enqueue(node.right)
      result += level.toList
    result.toList

  @main def run(): Unit =
    val tree = TreeNode(3, TreeNode(9), TreeNode(20, TreeNode(15), TreeNode(7)))
    println(levelOrder(tree)) // List(List(3), List(9, 20), List(15, 7))
```

## Explanation & Traversal
1. **Approach**: BFS using a queue to process level by level.
2. **Traversal**:
   - Enqueue root, then loop: for each level, dequeue nodes, record values, enqueue children.

## Time & Space Complexity
- **Time**: O(n)  
- **Space**: O(n)
