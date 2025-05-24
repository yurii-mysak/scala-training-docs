# Unit Testing Fundamentals

Unit testing focuses on verifying the behavior of the smallest testable parts of an application (often single functions or classes) in isolation.

---

## 1. What is Unit Testing

- **Definition**: Testing individual “units” of code (methods, classes) separately from the rest of the system.  
- **Purpose**: Ensure each unit works as intended, catch regressions early.  
- **Analogy**: A mechanic testing each piston of an engine independently before assembling the whole car.

---

## 2. Unit Tests vs. Integration Tests

| Aspect                     | Unit Test                          | Integration Test                     |
|----------------------------|------------------------------------|--------------------------------------|
| **Scope**                  | Single class/function              | Multiple modules/systems             |
| **Dependencies**           | Mocked or stubbed                  | Real databases, services             |
| **Speed**                  | Very fast (< 10ms)                 | Slower (100ms+), depends on I/O      |
| **Isolation**              | High (no external calls)           | Medium (cross-component interactions)|

---

## 3. What Makes a Good Unit Test

1. **Fast**: Should run in milliseconds.  
2. **Isolated**: No reliance on databases, file systems, network.  
3. **Deterministic**: Same inputs → same results always.  
4. **Readable & Maintainable**: Clear setup, exercise, verify, teardown phases (Arrange–Act–Assert).  
5. **Focused**: Tests one behavior or edge case per test.  
6. **Repeatable**: Can run in any order and on any environment.

---

## 4. Testable vs. Untestable Code

- **Testable**:  
  - Follows **dependency injection** (pass collaborators in constructors).  
  - Uses **pure functions** (no side effects).  
  - Encapsulates side effects behind interfaces.  

- **Untestable**:  
  - Has **static/global state** and hidden dependencies.  
  - Performs file, network, or time-based I/O directly in logic.  
  - Uses `Thread.sleep`, tight loops, or randomness without injection.

---

## 5. Scala Example (ScalaTest)

```scala
import org.scalatest.flatspec.AnyFlatSpec
import org.scalatest.matchers.should.Matchers

class Calculator {
  def add(a: Int, b: Int): Int = a + b
}

class CalculatorSpec extends AnyFlatSpec with Matchers {
  "Calculator.add" should "return sum of two integers" in {
    val calc = new Calculator()
    calc.add(2, 3) shouldEqual 5
  }
}
```

*Arrange–Act–Assert* structure:
1. **Arrange**: create `Calculator`.  
2. **Act**: call `add(2, 3)`.  
3. **Assert**: verify result equals `5`.  
