For two strings s and t, we say "t divides s" if and only if s = t + t + t + ... + t + t (i.e., t is concatenated with itself one or more times).

Given two strings str1 and str2, return the largest string x such that x divides both str1 and str2.

Example 1:

Input: str1 = "ABCABC", str2 = "ABC"
Output: "ABC"
Example 2:

Input: str1 = "ABABAB", str2 = "ABAB"
Output: "AB"
Example 3:

Input: str1 = "LEET", str2 = "CODE"
Output: ""

```scala 3
import scala.annotation.tailrec

object Solution {
  def gcdOfStrings(str1: String, str2: String): String = {
    // if (str1 == "" || str2 == "")
    //   return ""

    // def isComposedOfSubstring(str: String, substring: String): Boolean = {
    //   val subLength = substring.length
    //   str.length % subLength == 0 && str.sliding(subLength, subLength).forall(_ == substring)
    // }

    // var basisStr = ""
    // var smallerStr = ""

    // @tailrec
    // def getDenominator(substr: String): String = {
    //   if (substr.isEmpty)
    //     return ""

    //   if (isComposedOfSubstring(basisStr, substr) && isComposedOfSubstring(smallerStr, substr))
    //     return substr

    //   getDenominator(substr.dropRight(1))
    // }

    // if (str1.length > str2.length) {
    //   basisStr = str1
    //   smallerStr = str2
    // } else {
    //   basisStr = str2
    //   smallerStr = str1
    // }

    // getDenominator(smallerStr)

    @tailrec
    def gcd(a: Int,b: Int): Int = {
      if(b == 0) a else gcd(b, a % b)
    }

    if (str1 ++ str2 == str2 ++ str1)
      return str1.substring(0, gcd(str1.length, str2.length))
    else return "";
  }
}

```