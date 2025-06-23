Given two strings s and t, return true if s is a subsequence of t, or false otherwise.

A subsequence of a string is a new string that is formed from the original string by deleting some (can be none) of the characters without disturbing the relative positions of the remaining characters. (i.e., "ace" is a subsequence of "abcde" while "aec" is not).

Example 1:

Input: s = "abc", t = "ahbgdc"
Output: true
Example 2:

Input: s = "axc", t = "ahbgdc"
Output: false

```scala 3
object Solution {
  def isSubsequence(s: String, t: String): Boolean = {
    // val filtered = t.toSeq.filter(s.toSeq.contains).mkString("")
    if (s.length > t.length) false
    else
      (0 until s.length).foldLeft(0)({ (lastIdxReached, idx) =>
        if (lastIdxReached >= 0)
          t.indexOf(s(idx).toString, lastIdxReached + lastIdxReached.sign)
        else -1
      }) != -1
  }
}
```