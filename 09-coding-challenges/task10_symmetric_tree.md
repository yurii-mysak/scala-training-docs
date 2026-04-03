# Task 10: Symmetric Tree

## Problem Statement
Given the root of a binary tree, check whether it is a mirror of itself (symmetric around its center).

## Scala 3 Implementation

```scala
case class TreeNode(value: Int, left: TreeNode = null, right: TreeNode = null)

object SymmetricTree:
  def isSymmetric(root: TreeNode): Boolean =
    def isMirror(t1: TreeNode, t2: TreeNode): Boolean =
      if t1 == null && t2 == null then true
      else if t1 == null || t2 == null then false
      else (t1.value == t2.value) &&
           isMirror(t1.left, t2.right) &&
           isMirror(t1.right, t2.left)

    isMirror(root, root)

  @main def run(): Unit =
    val tree = TreeNode(1, TreeNode(2, TreeNode(3), TreeNode(4)), TreeNode(2, TreeNode(4), TreeNode(3)))
    println(s"Is Symmetric: ${isSymmetric(tree)}") // true
```

## Explanation & Traversal
1. **Approach**: Recursively compare left subtree of one with right subtree of the other.
2. **Traversal**:
   - Base cases: both null -> true; one null -> false.
   - Check node values and recurse swapped children.

## Time & Space Complexity
- **Time**: O(n)  
- **Space**: O(h) recursion stack, where h is tree height
