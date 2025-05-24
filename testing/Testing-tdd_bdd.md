# TDD, BDD & Best Practices

This section covers Test-Driven Development (TDD), Behavior-Driven Development (BDD), and general best practices for unit testing.

---

## 1. Test-Driven Development (TDD)

- **Definition**: A software development process where tests are written before code implementation.  
- **Cycle**:  
  1. **Red**: Write a failing test.  
  2. **Green**: Write minimal code to pass the test.  
  3. **Refactor**: Clean up code and tests while preserving functionality.  
- **Benefits**: Ensures test coverage, guides design, catches regressions early.  
- **Analogy**: Writing a checklist for a task before performing it.  
- **Resources**: https://en.wikipedia.org/wiki/Test-driven_development

### Scala Example (ScalaTest)

```scala
// Red: Test for a Stack
import org.scalatest.flatspec.AnyFlatSpec
import org.scalatest.matchers.should.Matchers

class StackSpec extends AnyFlatSpec with Matchers {
  "A Stack" should "pop values in last-in-first-out order" in {
    val stack = new scala.collection.mutable.Stack[Int]
    stack.push(1)
    stack.push(2)
    stack.pop() shouldEqual 2
  }
}
```

---

## 2. Behavior-Driven Development (BDD)

- **Definition**: An extension of TDD emphasizing behavior and business outcomes, often using natural language.  
- **Syntax**: Given–When–Then format for scenarios.  
- **Benefits**: Improves collaboration between technical and non-technical stakeholders.  
- **Analogy**: Writing user stories and scenarios as acceptance criteria.  
- **Resources**: https://en.wikipedia.org/wiki/Behavior-driven_development

### Scala Example (Specs2)

```scala
import org.specs2.mutable.Specification

class CalculatorSpec extends Specification {
  "Calculator" should {
    "add two numbers" in {
      Given("a Calculator")
      val calc = new Calculator()
      When("adding 2 and 3")
      val result = calc.add(2, 3)
      Then("the result should be 5")
      result mustEqual 5
    }
  }
}
```

---

## 3. Unit Testing Best Practices

- **Arrange–Act–Assert**: Structure tests clearly into setup, execution, and verification.  
- **One Assertion per Test**: Focus on a single behavior to simplify failures.  
- **Descriptive Test Names**: Use clear, expressive names for test methods and specs.  
- **Avoid Flaky Tests**: Eliminate time, randomness, and external dependencies.  
- **Use Setup Hooks**: `beforeEach` / `beforeAll` to initialize common test fixtures.  
- **Mock External Dependencies**: Isolate units under test using mocks/stubs.  
- **Continuous Integration**: Run tests on every commit.  
- **Code Coverage**: Measure but don’t over-focus; high-quality tests matter more.

*Additional Reading*:  
- Unit Testing Best Practices:  
  - https://brightsec.com/blog/unit-testing-best-practices/  
  - https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-best-practices  
