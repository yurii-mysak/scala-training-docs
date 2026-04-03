# Task 18: Serialize and Deserialize Binary Tree

## Problem Statement
Design an algorithm to serialize and deserialize a binary tree.  
Serialization converts a tree to a string, and deserialization converts the string back to the original tree structure.

## Scala 3 Implementation

```scala
case class TreeNode(value: Int, left: TreeNode = null, right: TreeNode = null)

object Codec:
  def serialize(root: TreeNode): String =
    def dfs(node: TreeNode, sb: StringBuilder): Unit =
      if node == null then sb.append("null,")
      else
        sb.append(node.value).append(",")
        dfs(node.left, sb); dfs(node.right, sb)
    val sb = new StringBuilder()
    dfs(root, sb)
    sb.toString

  def deserialize(data: String): TreeNode =
    val nodes = scala.collection.mutable.Queue(data.split(","): _*)
    def dfs(): TreeNode =
      if nodes.isEmpty then null
      else
        val v = nodes.dequeue()
        if v == "null" then null
        else
          val node = TreeNode(v.toInt)
          node.left = dfs(); node.right = dfs()
          node
    dfs()

  @main def run(): Unit =
    val tree = TreeNode(1, TreeNode(2), TreeNode(3, TreeNode(4), TreeNode(5)))
    val data = serialize(tree)
    println(data)
    val restored = deserialize(data)
    println(serialize(restored))
```

## Explanation & Traversal
1. **Approach**: Pre-order traversal with sentinel `"null"` markers.
2. **Traversal**:
   - **Serialize**: DFS, append value or `"null"`.
   - **Deserialize**: Queue tokens, recursively build nodes.

## Time & Space Complexity
- **Time**: O(n)  
- **Space**: O(n)
