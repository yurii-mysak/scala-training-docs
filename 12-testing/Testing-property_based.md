# Property-Based Testing with ScalaCheck

Property-Based Testing (PBT) focuses on stating general properties about code behavior and verifying them against many automatically generated inputs.

---

## 1. Concepts

- **Property**: A logical assertion that should hold for all valid inputs.
- **Generator (Gen)**: Describes how to produce random test data.
- **Shrink**: When a test fails, ScalaCheck tries to reduce the input to the smallest failing case.
- **Observable**: The output or behavior under test.

Analogy: Instead of testing with selected examples, throwing hundreds of darts randomly at the target to ensure it never misses.

---

## 2. ScalaCheck Basics

### Defining Properties

```scala
import org.scalacheck.Properties
import org.scalacheck.Prop.forAll

object ListProperties extends Properties("List") {
  property("reverseTwice") = forAll { (l: List[Int]) =>
    l.reverse.reverse == l
  }
}
```

### Generators

- **Built-in**: `Gen.int`, `Gen.alphaStr`, `Gen.listOf(Gen.alphaNumChar)`.
- **Custom**: Combine existing generators to model complex data.

```scala
val genUser: Gen[User] =
  for {
    id   <- Gen.posNum[Int]
    name <- Gen.alphaStr.suchThat(_.nonEmpty)
    age  <- Gen.choose(18, 99)
  } yield User(id, name, age)
```

### Shrinking

When a property fails, ScalaCheck reduces (`shrinks`) the input to simplify the failing case, aiding debugging.

---

## 3. Integration with ScalaTest

ScalaCheck can integrate with ScalaTest for seamless testing:

```scala
import org.scalatest.propspec.AnyPropSpec
import org.scalatest.matchers.should.Matchers
import org.scalatestplus.scalacheck.ScalaCheckPropertyChecks

class MySpec extends AnyPropSpec with ScalaCheckPropertyChecks with Matchers {
  property("sum of two ints is commutative") {
    forAll { (a: Int, b: Int) =>
      a + b shouldEqual b + a
    }
  }
}
```

---

## 4. Best Practices

- **Specify clear properties** that capture essential behavior.
- **Limit domain size** if full domain is unbounded (e.g., strings length ≤ 100).
- **Label cases** using `Prop.label` for clarity.
- **Combine unit tests** with PBT for comprehensive coverage.
- **Run enough samples**: default 100, can adjust via `Test.Parameters.default.withMinSuccessfulTests(200)`.

---

## 5. Further Reading

- ScalaCheck User Guide: https://github.com/typelevel/scalacheck/blob/main/doc/UserGuide.md#concepts  
- Property-Based Testing General: https://scala.github.io/scala-check/  
