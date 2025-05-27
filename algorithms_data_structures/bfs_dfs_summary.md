# BFS vs DFS: Summary

## 1. Purpose & Goals
- **BFS (Breadth-First Search)**: layer-by-layer traversal; finds the shortest path in unweighted graphs.
- **DFS (Depth-First Search)**: dive-then-backtrack; useful for existence checks, topological sort, and connectivity.

## 2. Mental Models
- **BFS**: imagine ripples expanding from a stone dropped in a pond; uses a queue.
- **DFS**: explore as far down a maze corridor as possible, then backtrack; uses a stack or recursion.

## 3. Key Steps

### BFS
1. **Initialize**  
   - `visited = Set(start)`  
   - `queue   = Queue(start)`  
   - (Optional) `parents = Map.empty[A, A]` for path reconstruction.
2. **Loop**  
   - Dequeue `node`.  
   - If `node == goal`, reconstruct path via `parents`.  
   - For each neighbor `nbr`:
     - If `nbr` not in `visited`:
       - Mark visited.
       - Enqueue `nbr`.
       - Record `parents(nbr) = node`.
3. **End** when queue is empty or goal is found.

### DFS
1. **Initialize**  
   - `visited = Set.empty[A]`
2. **Recursive approach**  
   ```scala
   def visit(node: A): Unit = {
     visited += node
     for (nbr <- neighbors(node) if !visited(nbr))
       visit(nbr)
   }
   visit(start)
   ```
3. **Iterative approach**  
   ```scala
   val stack = Stack(start)
   while (stack.nonEmpty) {
     val node = stack.pop()
     for (nbr <- neighbors(node) if !visited(nbr)) {
       visited += nbr
       stack.push(nbr)
     }
   }
   ```

## 4. Handling Cycles
- Always track `visited` to avoid infinite loops in graphs with cycles.
- Without `visited`, a cycle (e.g., A → B → C → A) would cause infinite repetition.

## 5. BFS vs DFS: Pros & Cons

| Aspect         | BFS                                     | DFS                                         |
|----------------|-----------------------------------------|---------------------------------------------|
| **Use-case**   | Shortest paths, level-order traversal   | Existence checks, topological sort, puzzles |
| **Memory**     | May store large frontiers on wide graphs| Lower memory on wide graphs; recursion depth can be a risk |
| **Guarantee**  | Finds shortest path (unweighted)        | No shortest-path guarantee                  |
| **Performance**| Better for shallow targets              | Can find deep targets faster                |

## 6. Choosing the Right Algorithm
- **Shortest path** in unweighted graph → **BFS**.  
- **Depth-based** properties or low memory needs on shallow graphs → **DFS**.  
- Consider **graph shape** (wide vs deep) and **resource constraints**.
