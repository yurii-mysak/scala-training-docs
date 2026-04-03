A phrase is a palindrome if, after converting all uppercase letters into lowercase letters and removing all non-alphanumeric characters, it reads the same forward and backward. Alphanumeric characters include letters and numbers.

Given a string s, return true if it is a palindrome, or false otherwise.

Example 1:

Input: s = "A man, a plan, a canal: Panama"
Output: true
Explanation: "amanaplanacanalpanama" is a palindrome.
Example 2:

Input: s = "race a car"
Output: false
Explanation: "raceacar" is not a palindrome.
Example 3:

Input: s = " "
Output: true
Explanation: s is an empty string "" after removing non-alphanumeric characters.
Since an empty string reads the same forward and backward, it is a palindrome.

```scala 3
object Solution {
    def isPalindrome(s: String): Boolean = {
    // val lowerS = s.toLowerCase()
    // val alphaNumericS = lowerS.replaceAll("[\\W]|_", "");
    // val reverseAlphaNumericS = alphaNumericS.reverse
    // alphaNumericS == reverseAlphaNumericS
    val filtered = s.filter(_.isLetterOrDigit)
    filtered.reverse equalsIgnoreCase filtered
    // convert all to lower
    // remove whitespace, commas (non-alphanumeric)
    // reverse
    // compare
  }
}
```