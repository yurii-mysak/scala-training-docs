# Task 4: Merge Two Sorted Lists

## Problem Statement
You are given the heads of two sorted linked lists `l1` and `l2`. Merge the two lists in a one sorted list. The list should be made by splicing together the nodes of the first two lists. Return the head of the merged linked list.

## Scala 3 Implementation

```scala
case class ListNode(var value: Int, var next: ListNode = null)

object MergeTwoSortedLists:
  def mergeTwoLists(l1: ListNode, l2: ListNode): ListNode =
    // Dummy head to simplify edge cases
    val dummy = ListNode(0)
    var tail = dummy
    var p1 = l1
    var p2 = l2

    while p1 != null && p2 != null do
      if p1.value <= p2.value then
        tail.next = p1
        p1 = p1.next
      else
        tail.next = p2
        p2 = p2.next
      tail = tail.next

    // Append remaining nodes
    tail.next = if p1 != null then p1 else p2

    dummy.next

  @main def run(): Unit =
    // Example: l1 = [1,2,4], l2 = [1,3,4]
    val list1 = List(1,2,4).map(ListNode(_))
    val list2 = List(1,3,4).map(ListNode(_))
    for i <- 0 until list1.length-1 do list1(i).next = list1(i+1)
    for i <- 0 until list2.length-1 do list2(i).next = list2(i+1)
    val mergedHead = mergeTwoLists(list1.head, list2.head)
    // Print merged list
    print("Merged List: ")
    var cur = mergedHead
    while cur != null do
      print(s"${cur.value} ")
      cur = cur.next
    println()
```

## Explanation & Traversal
1. **Approach**: Use a dummy head and two pointers `p1` and `p2` to iterate both lists.
2. **Steps**:
   - Create a dummy node to start the merged list.
   - Compare `p1.value` and `p2.value`: attach the smaller node to `tail.next`.
   - Advance the pointer (`p1` or `p2`) and move `tail`.
   - After the loop, attach any remaining nodes from `p1` or `p2`.
   - Return `dummy.next`, skipping the dummy node.

### Traversal Example
For `l1 = 1→2→4` and `l2 = 1→3→4`:
- Compare 1 and 1 → choose l1's 1 → merged: `1`
- Compare 2 and 1 → choose l2's 1 → merged: `1→1`
- Compare 2 and 3 → choose 2 → merged: `1→1→2`
- Compare 4 and 3 → choose 3 → merged: `1→1→2→3`
- Compare 4 and 4 → choose 4 (from l1) → merged: `1→1→2→3→4`
- Remaining: l2 has 4 → attach → merged: `1→1→2→3→4→4`

## Time & Space Complexity
- **Time**: O(n + m), where n and m are the lengths of the two lists.  
- **Space**: O(1), in-place merging.
