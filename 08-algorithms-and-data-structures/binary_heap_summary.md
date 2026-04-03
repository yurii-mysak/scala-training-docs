# Binary Heap Summary

## 1. Definition and Properties
A **binary heap** is a **complete binary tree** that satisfies the **heap property**:
- **Min-Heap**: The key at each node is **no greater** than the keys of its children. The smallest element is at the root.
- **Max-Heap**: The key at each node is **no less** than the keys of its children. The largest element is at the root.
- **Complete Binary Tree**: All levels are fully filled except possibly the last, which is filled from left to right without gaps.

## 2. Array Representation
Binary heaps are typically stored in an array to avoid explicit pointers:
- **Indexing formulas** for a node at index `i` (0-based):
  - **Left child**: `2*i + 1`
  - **Right child**: `2*i + 2`
  - **Parent**: `⌊(i - 1) / 2⌋`
- **Advantages**:
  - Space-efficient: no extra pointers.
  - Cache-friendly: contiguous memory layout.

## 3. Core Operations & Time Complexities
| Operation             | Description                                                     | Time Complexity |
|-----------------------|-----------------------------------------------------------------|-----------------|
| `peek()`              | Return the root element (min or max)                            | O(1)            |
| `insert(key)`         | Add a new key and restore heap via **heapify up**               | O(log n)        |
| `extractRoot()`       | Remove the root, move last element to root, then **heapify down** | O(log n)      |
| `buildHeap(array)`    | Convert an arbitrary array into a heap using bottom-up approach | O(n)            |
| `remove(index)`       | Remove element at given index (decrease-key + extract)         | O(log n)        |
| `replaceRoot(x)`      | Pop the root and insert `x` in one operation                    | O(log n)        |

## 4. Heapify Operations
### 4.1 Heapify Up (Sift-Up)
- **When**: After **inserting** a new key at the end of the heap.
- **How**:
  1. Place the new key at the next available leaf position.
  2. While the new key violates the heap property with its parent:
     - **Min-Heap**: if `newKey < parentKey`, swap them.
     - **Max-Heap**: if `newKey > parentKey`, swap them.
  3. Continue until the heap property is restored or the root is reached.

### 4.2 Heapify Down (Sift-Down)
- **When**: After **removing** the root (extracting min or max).
- **How**:
  1. Move the last leaf element to the root position to maintain completeness.
  2. While this element violates the heap property with its children:
     - Select the child with the extreme value (smallest for min‑heap, largest for max‑heap).
     - Swap the element with that child.
  3. Continue until the heap property is restored or a leaf is reached.

## 5. Why Move the Last Element to the Root?
1. **Maintain Complete Shape**: Removing the root leaves a gap at the top. The only way to fill it without breaking completeness is to move the last leaf up.
2. **Restore Order**: That leaf may violate the heap property at the root, so we apply **heapify down** to re‑establish the heap.

## 6. Use Cases
- **Priority Queue**: Insert with priority, extract the highest/lowest priority element.
- **Heapsort**: Build a max-heap and repeatedly extract the maximum to sort in-place in O(n log n).
- **Graph Algorithms**: Efficiently select the next vertex in Dijkstra’s shortest-path or Prim’s MST.
- **Order Statistics**: Find the k largest (or smallest) elements in O(n + k log n).

## 7. Examples

### 7.1 Min-Heap Example
```
      1
     /     3   5
   /   4   8
```
- **Array**: `[1, 3, 5, 4, 8]`

### 7.2 Max-Heap Example
```
      9
     /     7   6
   /   2   5
```
- **Array**: `[9, 7, 6, 2, 5]`

## 8. Build-Heap in O(n)
Using a **bottom-up** approach:
```scala
for (i <- (n / 2 - 1) to 0 by -1) {
  heapifyDown(i)
}
```
Although each `heapifyDown` can cost O(log n), most calls touch small subtrees, leading to overall O(n) time.

## 9. Variations and Considerations
- **d-ary Heaps**: Generalize to `d` children per node. Trade‑offs between tree height and per-level cost.
- **Stability**: Standard binary heaps are not stable.
- **Decrease/Increase Key**: Needed for algorithms like Dijkstra; must support adjusting an existing key.
- **Alternative Heaps**: Pairing heap, Fibonacci heap for different amortized bounds on decrease‑key and meld operations.

---

*This summary covers essential concepts to understand, implement, and apply binary heaps efficiently.*