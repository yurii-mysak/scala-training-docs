# Task 13: Course Schedule (Topological Sort)

## Problem Statement
There are `numCourses` labeled from `0` to `numCourses-1`. You are given an array `prerequisites` where `prerequisites[i] = [ai, bi]` indicates that you must take course `bi` first if you want to take course `ai`.  
Return `true` if you can finish all courses, otherwise `false`.

## Scala 3 Implementation

```scala
object CourseSchedule:
  def canFinish(numCourses: Int, prerequisites: Array[Array[Int]]): Boolean =
    import scala.collection.mutable
    val adj = Array.fill(numCourses)(List[Int]())
    val indegree = Array.fill(numCourses)(0)
    for Array(course, pre) <- prerequisites do
      adj(pre) = course :: adj(pre)
      indegree(course) += 1
    val queue = mutable.Queue[Int]()
    for i <- 0 until numCourses do if indegree(i) == 0 then queue.enqueue(i)
    var count = 0
    while queue.nonEmpty do
      val node = queue.dequeue(); count += 1
      for nei <- adj(node) do
        indegree(nei) -= 1
        if indegree(nei) == 0 then queue.enqueue(nei)
    count == numCourses

  @main def run(): Unit =
    println(canFinish(2, Array(Array(1,0)))) // true
    println(canFinish(2, Array(Array(1,0), Array(0,1)))) // false
```

## Explanation & Traversal
1. **Approach**: Kahn's algorithm for topological sort.
2. **Traversal**:
   - Build adjacency list and indegree array.
   - Enqueue courses with indegree 0.
   - Dequeue, visit neighbors, decrement indegree, enqueue when it drops to 0.
   - Check if all nodes processed.

## Time & Space Complexity
- **Time**: O(V + E)  
- **Space**: O(V + E)
