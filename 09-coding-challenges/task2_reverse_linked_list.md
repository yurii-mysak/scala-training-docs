# Task 2: Reverse Linked List

## Problem Statement
Given a singly linked list, reverse the list and return the head of the reversed list.

## Scala 3 Implementation

```scala
case class ListNode(var value: Int, var next: ListNode = null)

object ReverseLinkedList:
  def reverseList(head: ListNode): ListNode =
    var prev: ListNode = null
    var current = head
    while current != null do
      val nextTemp = current.next
      current.next = prev
      prev = current
      current = nextTemp
    prev

  @main def run(): Unit =
    // Example: 1 -> 2 -> 3 -> 4 -> 5
    val nodes = List(1,2,3,4,5).map(ListNode(_))
    for i <- 0 until nodes.length-1 do nodes(i).next = nodes(i+1)
    val reversedHead = reverseList(nodes.head)
    // Print reversed list
    print("Reversed List: ")
    var cur = reversedHead
    while cur != null do
      print(s"${cur.value} ")
      cur = cur.next
    println()
```

## Explanation & Traversal
1. **Approach**: Iteratively reverse pointers using three variables:
   - `prev` to track the previous node.
   - `current` for the node being processed.
   - `nextTemp` to temporarily store the next node.
2. **Steps**:
   - Initialize `prev` to `null` and `current` to `head`.
   - Loop until `current` is `null`:
     - Store `nextTemp = current.next`.
     - Set `current.next = prev` to reverse the link.
     - Move `prev = current` and `current = nextTemp`.
   - Return `prev` as the new head.

### Traversal Example
For list 1 → 2 → 3:
- **Iteration 1**: prev=null, current=1  
  nextTemp=2, 1.next=null, prev=1, current=2  
- **Iteration 2**: prev=1, current=2  
  nextTemp=3, 2.next=1, prev=2, current=3  
- **Iteration 3**: prev=2, current=3  
  nextTemp=null, 3.next=2, prev=3, current=null  

Result: 3 → 2 → 1

## Time & Space Complexity
- **Time**: O(n), where n is the number of nodes.  
- **Space**: O(1), in-place reversal.
