You are given two strings word1 and word2. Merge the strings by adding letters in alternating order, starting with word1. If a string is longer than the other, append the additional letters onto the end of the merged string.

Return the merged string.
```scala 3
object Solution {
  def mergeAlternately(word1: String, word2: String): String = {
    word1.zipAll(word2, "", "").map(_.toString + _.toString).mkString("")
  }
//   def mergeAlternately(word1: String, word2: String): String = {
//         def recurMerge(word1: String, word2: String, res: String): String = {
//           if (word1.isEmpty || word2.isEmpty) res + word1 + word2
//           else recurMerge(word1.tail, word2.tail, res + word1.head + word2.head)
//         }
//         recurMerge(word1, word2, "")
//     }
}
```