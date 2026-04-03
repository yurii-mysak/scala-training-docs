# Load Testing Tools

Load testing evaluates system performance under expected and peak loads. This section covers JMeter, Gatling, and ScalaMeter.

---

## 1. Apache JMeter

- **Type**: Desktop application for load testing and performance measurement.
- **Use Cases**: HTTP, JDBC, JMS, FTP, and more.
- **Key Features**:
  - Thread groups to simulate users.
  - Samplers and listeners for detailed metrics.
  - Assertions and timers for realistic scenarios.
- **Scala Integration**: Use JMeter DSLs or call from sbt via plugins.

### Example: HTTP Load Test

```jmx
<!-- JMeter Test Plan snippet (JMX XML) -->
<ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup">
  <stringProp name="ThreadGroup.num_threads">50</stringProp>
  <stringProp name="ThreadGroup.ramp_time">10</stringProp>
  <elementProp name="HTTP Request Defaults" elementType="ConfigTestElement">
    <stringProp name="HTTPSampler.domain">example.com</stringProp>
  </elementProp>
  <hashTree>
    <HTTPSamplerProxy guiclass="HttpTestSampleGui">
      <stringProp name="HTTPSampler.path">/api/v1/orders</stringProp>
      <stringProp name="HTTPSampler.method">GET</stringProp>
    </HTTPSamplerProxy>
  </hashTree>
</ThreadGroup>
```

*Getting Started*: https://jmeter.apache.org/usermanual/get-started.html

---

## 2. Gatling

A high-performance load testing tool built on Akka and Netty.

- **Language**: Scala DSL for scenarios.
- **Key Features**:
  - Code-as-test with fluent Scala API.
  - Real-time metrics and HTML reports.
  - Supports HTTP, WebSocket, JMS.
- **Analogous to**: Writing regression tests with load scenarios.

### Example: Basic Gatling Simulation

```scala
import io.gatling.core.Predef._
import io.gatling.http.Predef._
import scala.concurrent.duration._

class BasicSimulation extends Simulation {

  val httpProtocol = http.baseUrl("http://example.com")
  val scn = scenario("BasicLoad")
    .exec(http("GET Orders").get("/api/v1/orders"))
    .pause(1.second)

  setUp(
    scn.inject(
      atOnceUsers(10),
      rampUsers(100) during (30.seconds)
    )
  ).protocols(httpProtocol)
}
```

*Documentation*: https://gatling.io/docs/current/

---

## 3. ScalaMeter

A Scala-specific performance testing framework.

- **Integration**: sbt plugin and library.
- **Key Features**:
  - Microbenchmarking and throughput measurement.
  - Regression testing of performance.
  - Support for parametrized tests.
- **Analogy**: Unit testing for performance metrics.

### Example: ScalaMeter Benchmark

```scala
import org.scalameter.api._

object CollectionBenchmark extends Bench.LocalTime {

  val sizes = Gen.range("size")(10000, 50000, 10000)

  performance of "List" in {
    measure method "map" in {
      using(sizes) in { size =>
        List.range(0, size).map(_ + 1)
      }
    }
  }
}
```

*Guide*: http://scalameter.github.io/home/gettingstarted/0.7/index.html

---

## 4. Choosing a Tool

- **JMeter**: broad protocol support, non-coders, GUI-driven.  
- **Gatling**: code-as-test, real-time monitoring, Scala-based.  
- **ScalaMeter**: focused on Scala code performance, regression tests.  

---

## Further Reading

- JMeter User Manual: https://jmeter.apache.org/usermanual/get-started.html  
- Gatling Docs: https://gatling.io/docs/current/  
- ScalaMeter Guide: http://scalameter.github.io/gettingstarted/0.7/  
