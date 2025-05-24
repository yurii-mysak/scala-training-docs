# Task 3: Valid Parentheses

## Problem Statement
Given a string `s` containing just the characters `'('`, `')'`, `'{'`, `'}'`, `'['` and `']'`, determine if the input string is valid.

An input string is valid if:
- Open brackets are closed by the same type of brackets.
- Open brackets are closed in the correct order.
- Every closing bracket has a corresponding opening bracket of the same type.

## Scala 3 Implementation

```scala
object ValidParentheses:
  def isValid(s: String): Boolean =
    import scala.collection.mutable
    val stack = mutable.Stack[Char]()
    for ch <- s do
      ch match
        case '(' | '[' | '{' =>
          stack.push(ch)
        case ')' | ']' | '}' =>
          if stack.isEmpty then return false
          val top = stack.pop()
          if !((ch == ')' && top == '(') ||
               (ch == ']' && top == '[') ||
               (ch == '}' && top == '{')) then
            return false
        case _ => // ignore other characters if any
    stack.isEmpty

  @main def run(): Unit =
    val examples = List("()", "()[]{}", "(]", "([)]", "{[]}")
    examples.foreach { s =>
      println(s"Input: $$s -> Valid: $${isValid(s)}")
    }
```

## Explanation & Traversal
1. **Approach**: Use a stack to track opening brackets.
2. **Traversal**:
   - Iterate over each character `ch` in the string.
   - If `ch` is an opening bracket, push it onto the stack.
   - If `ch` is a closing bracket, check:
     - If the stack is empty, it's invalid (no matching opening).
     - Pop the top and verify it matches the type.
3. **Final Check**: After iteration, if the stack is empty, all brackets matched correctly.

### Traversal Example
For input `"([{}])"`:
- Read `'('`: push `(` → stack: `[(]`
- Read `'['`: push `[` → stack: `[(, []`
- Read `'{'`: push `{` → stack: `[(, [, {]`
- Read `'}'`: pop `{` → matches → stack: `[(, []`
- Read `']'`: pop `[` → matches → stack: `[(]`
- Read `')'`: pop `(` → matches → stack: `[]`
- End: stack empty → valid.

## Time & Space Complexity
- **Time**: O(n), where n is the length of the string.  
- **Space**: O(n), in the worst case of all opening brackets.
