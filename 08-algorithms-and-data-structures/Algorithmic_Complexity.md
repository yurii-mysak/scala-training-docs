# Algorithmic Complexity

Understanding algorithmic complexity is crucial for writing efficient code and making informed design decisions. This file covers:

- Big O Notation  
- Complexities for common algorithms  
- NP Complexity  

---

## Big O Notation

**Definition:**  
Big O describes an upper bound on an algorithm’s running time (or space) as input size *n* grows → captures worst-case growth rate.

> **Analogy:**  
> Think of driving:  
> - A short trip (O(1)) always takes the same time—like driving around the block.  
> - A route through city traffic (O(n)) takes longer the more lights you hit.  
> - A hiker (O(2ⁿ)) slows down exponentially with each extra mile of uphill terrain!

### Common Complexity Classes

| Class                      | Growth Rate                          | Example                   |
|----------------------------|--------------------------------------|---------------------------|
| O(1) (Constant)            | Doesn’t change with *n*              | `arr(0)`, hash lookup     |
| O(log n) (Logarithmic)     | Grows very slowly                   | Binary search             |
| O(n) (Linear)              | Grows proportionally to *n*         | Single loop               |
| O(n log n) (Linearithmic)  | Slightly superlinear                 | Merge sort, Quick sort    |
| O(n²) (Quadratic)          | Grows with square of *n*             | Bubble sort, Selection sort |
| O(2ⁿ) (Exponential)        | Doubles with each additional element | Recursive Fibonacci       |
| O(n!) (Factorial)          | Grows factorially                    | Permutation generation    |

```scala
// O(n) example: linear scan
def contains[A](seq: Seq[A], v: A): Boolean =
  seq.exists(_ == v)
```

#### Growth Curve (Mermaid Diagram)
```mermaid
flowchart LR
    A[O(1)] --> B[O(log n)] --> C[O(n)] --> D[O(n log n)] --> E[O(n²)] --> F[O(2ⁿ)] --> G[O(n!)]
```

---

## Complexities for Specific Algorithms

| Algorithm            | Time Complexity      | Space Complexity    |
|----------------------|----------------------|---------------------|
| Linear Search        | O(n)                 | O(1)                |
| Binary Search        | O(log n)             | O(1)                |
| Bubble Sort          | O(n²)                | O(1)                |
| Selection Sort       | O(n²)                | O(1)                |
| Merge Sort           | O(n log n)           | O(n)                |
| Quick Sort (avg.)    | O(n log n)           | O(log n) (stack)    |
| HashMap operations   | O(1) average, O(n) worst | O(n)            |
| DFS/BFS on graph     | O(V + E)             | O(V)                |

> **Tip:** Always consider both average-case and worst-case. For hash tables, collisions can degrade performance to O(n).

---

## NP Complexity

- **P:** Problems solvable in polynomial time (O(nᵏ)).  
- **NP:** Decision problems where a “yes” answer can be *verified* in polynomial time.  
- **NP-Complete:** Hardest problems in NP—if you find a poly-time solution, P = NP!  
- **NP-Hard:** At least as hard as NP-Complete; may not be in NP (e.g., optimization versions).

> **Example:**  
> - **Travelling Salesman (TSP)**—finding the shortest route is NP-Hard.  
> - **Subset Sum**—deciding if a subset sums to a target is NP-Complete.

---

*Next up: Fundamental Data Structures (e.g., ArrayList vs LinkedList, HashMap vs TreeMap, Queue vs Stack, collision resolution).*  
*Send “continue” when you’re ready!*  
