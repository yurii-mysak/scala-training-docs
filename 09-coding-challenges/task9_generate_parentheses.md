# Task 9: Generate Parentheses

## Problem Statement
Given `n` pairs of parentheses, generate all combinations of well-formed parentheses.

## Scala 3 Implementation

```scala
object GenerateParentheses:
  def generateParenthesis(n: Int): List[String] =
    def backtrack(open: Int, close: Int, path: StringBuilder, res: List[String]): List[String] =
      var results = res
      if path.length == 2*n then return path.toString :: results
      if open < n then
        path.append('(')
        results = backtrack(open+1, close, path, results)
        path.setLength(path.length-1)
      if close < open then
        path.append(')')
        results = backtrack(open, close+1, path, results)
        path.setLength(path.length-1)
      results

    backtrack(0, 0, new StringBuilder, Nil).reverse

  @main def run(): Unit =
    println(generateParenthesis(3)) // List("((()))","(()())","(())()","()(())","()()()")
```

## Explanation & Traversal
1. **Approach**: Backtracking with counts of open and close parentheses.
2. **Traversal**:
   - Add `'('` if `open < n`.
   - Add `')'` if `close < open`.
3. **Example** for `n=3`: generates 5 valid sequences.

## Time & Space Complexity
- **Time**: O(4^n / sqrt(n))  
- **Space**: O(n)
