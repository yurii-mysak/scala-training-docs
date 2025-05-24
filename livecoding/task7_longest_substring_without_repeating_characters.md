# Task 7: Longest Substring Without Repeating Characters

## Problem Statement
Given a string `s`, find the length of the longest substring without repeating characters.

## Scala 3 Implementation

```scala
object LongestUniqueSubstring:
  def lengthOfLongestSubstring(s: String): Int =
    import scala.collection.mutable
    val seen = mutable.Map[Char, Int]()
    var start = 0
    var maxLen = 0
    for (i, ch) <- s.zipWithIndex do
      if seen.contains(ch) && seen(ch) >= start then
        start = seen(ch) + 1
      seen(ch) = i
      maxLen = math.max(maxLen, i - start + 1)
    maxLen

  @main def run(): Unit =
    val s = "abcabcbb"
    println(s"Longest length: ${lengthOfLongestSubstring(s)}") // 3
```

## Explanation & Traversal
1. **Approach**: Sliding window with a map of last seen indices.
2. **Traversal**:
   - When a repeated char at index `i` is within the current window, move `start` right past its last index.
   - Update `maxLen` = `i - start + 1`.
3. **Example** `"abcabcbb"`:
   - Window sizes: a(1), ab(2), abc(3), bca(3), cab(3), abc(3), cb(2), b(1)

## Time & Space Complexity
- **Time**: O(n)  
- **Space**: O(min(n, charset_size))
