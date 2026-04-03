# Mock Testing Frameworks

This section introduces popular mock testing libraries in Scala and JVM ecosystems: ScalaMock, Mockito-Scala, EasyMock, JMock, and MUnit.

---

## 1. ScalaMock

A native Scala mocking framework providing compile-time type safety and rich DSL.

- **Integration**: ScalaTest, Specs2, MUnit  
- **Key Features**:  
  - Stubbing, Mocking, Verification  
  - Argument matchers, ordered and unordered expectations  
- **Example** (with ScalaTest):
  ```scala
  import org.scalamock.scalatest.MockFactory
  import org.scalatest.flatspec.AnyFlatSpec

  trait AuthService {
    def login(user: String, pass: String): Boolean
  }

  class AuthManager(authService: AuthService) {
    def authenticate(user: String, pass: String): String =
      if (authService.login(user, pass)) "Welcome" else "Denied"
  }

  class AuthManagerSpec extends AnyFlatSpec with MockFactory {
    "authenticate" should "welcome valid users" in {
      val mockService = mock[AuthService]
      (mockService.login _).expects("alice", "secret").returning(true)

      val manager = new AuthManager(mockService)
      assert(manager.authenticate("alice", "secret") == "Welcome")
    }
  }
  ```

*Guide*: https://scalamock.org/user-guide/integration/

---

## 2. Mockito-Scala

A Scala-friendly wrapper around Mockito offering concise syntax and Scala idioms.

- **Integration**: ScalaTest, Specs2, MUnit  
- **Key Features**:  
  - `when`/`verify` syntax  
  - Deep stubbing, argument captors  
  - Supports Scala features (Option, Futures)  
- **Example**:
  ```scala
  import org.mockito.MockitoSugar.*
  import org.scalatest.flatspec.AnyFlatSpec

  class PaymentService {
    def charge(amount: Double): Boolean = ???
  }

  class Checkout(paymentService: PaymentService) {
    def purchase(amount: Double): String =
      if (paymentService.charge(amount)) "Success" else "Failure"
  }

  class CheckoutSpec extends AnyFlatSpec {
    "purchase" should "succeed when charge returns true" in {
      val mockService = mock[PaymentService]
      when(mockService.charge(100.0)).thenReturn(true)

      val checkout = new Checkout(mockService)
      assert(checkout.purchase(100.0) == "Success")
      verify(mockService).charge(100.0)
    }
  }
  ```

*Repository*: https://github.com/mockito/mockito-scala

---

## 3. EasyMock

A dynamic mocking library for Java and Scala with expectation-style API.

- **Integration**: JUnit, TestNG, ScalaTest via adapters  
- **Key Features**:  
  - Record-replay model  
  - Strict and nice mocks  
- **Example** (ScalaTest):
  ```scala
  import org.easymock.EasyMock.*
  import org.scalatest.flatspec.AnyFlatSpec

  trait Repo {
    def save(data: String): Unit
  }

  class Service(repo: Repo) {
    def process(data: String): Unit = {
      repo.save(data.toUpperCase)
    }
  }

  class ServiceSpec extends AnyFlatSpec {
    "process" should "uppercase data before saving" in {
      val mockRepo = createMock(classOf[Repo])
      mockRepo.save("HELLO")
      replay(mockRepo)

      new Service(mockRepo).process("hello")

      verify(mockRepo)
    }
  }
  ```

*Guide*: http://easymock.org/user-guide.html#mocking

---

## 4. JMock

A Java-based mocking framework using expectation DSL.

- **Integration**: JUnit, ScalaTest via adapters  
- **Key Features**:  
  - Domain-specific language for expectations  
  - Integrates with Hamcrest for matchers  
- **Example**:
  ```scala
  import org.jmock.Mockery
  import org.jmock.Expectations
  import org.scalatest.flatspec.AnyFlatSpec

  class Calculator {
    def add(a: Int, b: Int): Int = a + b
  }

  class CalculatorSpec extends AnyFlatSpec {
    val context = new Mockery

    "add" should "sum numbers" in {
      val calc = context.mock(classOf[Calculator])
      context.checking(new Expectations {
        oneOf(calc).add(2, 3); will(returnValue(5))
      })

      assert(calc.add(2, 3) == 5)
    }
  }
  ```

*Reference*: https://jmock.org/

---

## 5. MUnit

A Scala testing library with minimal dependencies, supports mocks via integration.

- **Integration**: Cats Effect, ScalaTest, Mockito  
- **Key Features**:  
  - Light-weight, fast startup  
  - Rich assertion API, fixtures  
  - Tagless support  
- **Example**:
  ```scala
  import munit.FunSuite
  import org.mockito.MockitoSugar.*

  class Greeter(service: String => String) {
    def greet(name: String): String = service(name)
  }

  class GreeterSuite extends FunSuite {
    val mockService = mock[String => String]

    test("greet delegates to service") {
      when(mockService.apply("Bob")).thenReturn("Hello Bob")
      val greeter = new Greeter(mockService)
      assertEquals(greeter.greet("Bob"), "Hello Bob")
      verify(mockService).apply("Bob")
    }
  }
  ```

*Docs*: https://scalameta.org/munit/
