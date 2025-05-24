# Task 8: Letter Combinations of a Phone Number

## Problem Statement
Given a string containing digits from 2-9 inclusive, return all possible letter combinations that the number could represent (phone keypad mapping).

## Scala 3 Implementation

```scala
object LetterCombinations:
  private val mapping = Map(
    '2' -> "abc", '3' -> "def", '4' -> "ghi",
    '5' -> "jkl", '6' -> "mno", '7' -> "pqrs",
    '8' -> "tuv", '9' -> "wxyz"
  )

  def letterCombinations(digits: String): List[String] =
    if digits.isEmpty then return Nil
    def backtrack(index: Int, path: StringBuilder, res: List[String]): List[String] =
      if index == digits.length then return path.toString :: res
      for ch <- mapping(digits(index)) do
        path.append(ch)
        backtrack(index+1, path, res)
        path.setLength(path.length - 1)
      res

    backtrack(0, new StringBuilder, Nil).reverse

  @main def run(): Unit =
    println(letterCombinations("23")) // List("ad", "ae", "af", "bd", "be", "bf", ...)
```

## Explanation & Traversal
1. **Approach**: Backtracking to build combinations recursively.
2. **Traversal**:
   - For each digit, iterate over its mapped letters.
   - Append letter, recurse for next digit, then backtrack.
3. **Example** `"23"`:
   - Paths: "ad","ae","af","bd","be","bf","cd","ce","cf"

## Time & Space Complexity
- **Time**: O(4^n * n) where n = number of digits  
- **Space**: O(n) recursion depth
