# Mocking & Stubbing Techniques

Mocking and stubbing are fundamental to isolating units under test by replacing real dependencies with controlled test doubles.

---

## 1. Definitions

- **Stub**: A minimal implementation of an interface that returns fixed responses for method calls.  
  - **Purpose**: Provide indirect input to the unit under test.  
  - **Analogy**: A test ATM that always dispenses \$100 for any request.

- **Mock**: A test double that both provides stubbed behavior and records interactions (method calls, parameters) for later verification.  
  - **Purpose**: Assert that certain interactions happened (or didn’t).  
  - **Analogy**: A spy device in the ATM that logs every button press and transaction.

*For an in-depth comparison, see Martin Fowler’s article*:  
https://martinfowler.com/articles/mocksArentStubs.html

---

## 2. When to Use

| Scenario                        | Use Stub                     | Use Mock                                |
|---------------------------------|------------------------------|-----------------------------------------|
| Need to supply simple data      | Yes                          | Rarely                                  |
| Verify method calls or order    | No                           | Yes                                     |
| Complex behavior orchestration   | Stub behavior chaining       | Mock expectations and verifications     |
| Isolation of side-effect dependencies | Stubbing external calls   | Verifying interactions with side-effect systems (e.g., message brokers) |

---

## 3. ScalaMock Example (Mock)

```scala
import org.scalamock.scalatest.MockFactory
import org.scalatest.flatspec.AnyFlatSpec

trait UserService {
  def findUser(id: Int): Option[String]
}

class UserManager(userService: UserService) {
  def greet(id: Int): String =
    userService.findUser(id).map(name => s"Hello, $name").getOrElse("User not found")
}

class UserManagerSpec extends AnyFlatSpec with MockFactory {
  "UserManager.greet" should "return greeting when user exists" in {
    val mockService = mock[UserService]
    (mockService.findUser _).expects(42).returning(Some("Alice"))

    val manager = new UserManager(mockService)
    assert(manager.greet(42) == "Hello, Alice")
  }
}
```

---

## 4. Mockito-Scala Example (Stub)

```scala
import org.mockito.MockitoSugar.*
import org.scalatest.flatspec.AnyFlatSpec

class Calculator {
  def add(a: Int, b: Int): Int = a + b
}

class CalculatorSpec extends AnyFlatSpec {
  "Calculator.add" should "sum correctly" in {
    val calc = mock[Calculator]
    when(calc.add(1, 2)).thenReturn(99)  // stub behavior

    assert(calc.add(1, 2) == 99)
  }
}
```

---

## 5. Further Reading

- Martin Fowler: Mocks vs Stubs: https://martinfowler.com/articles/mocksArentStubs.html  
- ScalaMock Guide: https://scalamock.org/user-guide/integration/  
- Mockito-Scala: https://github.com/mockito/mockito-scala  
