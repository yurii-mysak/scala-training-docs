Given a string s, reverse only all the vowels in the string and return it.

The vowels are 'a', 'e', 'i', 'o', and 'u', and they can appear in both lower and upper cases, more than once.

Example 1:

Input: s = "IceCreAm"

Output: "AceCreIm"

Explanation:

The vowels in s are ['I', 'e', 'e', 'A']. On reversing the vowels, s becomes "AceCreIm".

Example 2:

Input: s = "leetcode"

Output: "leotcede"

```scala 3
object Solution {
  def reverseVowels(s: String): String = {
    // val vowels = Array('a', 'A', 'e', 'E', 'i', 'I', 'o', 'O', 'u', 'U')
    // val stringAsArray = s.toCharArray
    // val vowelsInString = stringAsArray.filter(c => vowels.contains(c))
    // var vowelsInStringReversed = vowelsInString.reverse

    // stringAsArray.foldLeft(0) {
    //   case (idx, char) =>
    //     if (vowels.contains(char))
    //       stringAsArray(idx) = vowelsInStringReversed(0)
    //       vowelsInStringReversed = vowelsInStringReversed.takeRight(vowelsInStringReversed.length - 1)
    //     idx+1
    // }

    // stringAsArray.mkString
    val lst = List('a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U')
        var f = 0
        var r = s.length - 1
        var ns = s

        for (i <- 0 to s.length-1 ) {
            if (f < s.length-1 | r >= 0) {
                (s.charAt(f), s.charAt(r)) match {
                    case (a, b) if lst.contains(a) & lst.contains(b) => ns = ns.updated(f, s(r)).updated(r, s(f)); f+=1; r-=1;
                    case (_, b) if lst.contains(b) => f += 1
                    case (a, _) if lst.contains(a) => r -= 1
                    case _ => f += 1; r -= 1
                }
            }
        }
        ns
  }
}
```