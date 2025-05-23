# Akka Actors Core Patterns

Consolidates our actor‑system conversations from 2024‑12 through 2025‑05.

---

## 1. Creating actors

```scala
class Greeter extends Actor:
  def receive: Receive = { case name: String => sender() ! s"Hi $name" }

val system = ActorSystem("demo")
val greeter = system.actorOf(Props[Greeter], "greeter")
greeter ! "Scala"
```

### 1.1 Functional style (Akka Typed)
```scala
object Counter:
  sealed trait Cmd; case object Inc extends Cmd; case object Get extends Cmd
  def apply(n:Int): Behavior[Cmd] = Behaviors.receive { (ctx, msg) => … }
```

---

## 2. Send / Receive / Reply
* `!` (tell) – fire‑and‑forget.  
* `?` (ask) – returns `Future`.  
* Access `sender()` inside `receive` to reply.

---

## 3. `become` / `unbecome`
```scala
context.become(connected)
def connected: Receive = { case Disconnect => context.unbecome() }
```
Switches actor behaviour; stack if `become(_, discardOld=false)`.

---

## 4. Dead letters
Messages to terminated or non‑existing actors end in `/deadLetters`.  
We hooked a listener to debug mis‑routed messages (chat 2025‑02‑20).

---

## 5. Pipe pattern
```scala
import akka.pattern.pipe
futureResult.pipeTo(recipient)
```
Avoids blocking `ask` inside actor.

---

## 6. Mailboxes
Use `BoundedMailbox` to back‑pressure slow actors:
```hocon
my-mailbox {
  mailbox-type = "akka.dispatch.BoundedDequeBasedMailbox"
  capacity     = 1000
}
```
Attach via `Props.withMailbox("my-mailbox")`.

---

## 7. Routing
```scala
val router = system.actorOf(RoundRobinPool(5).props(Props[Worker]))
```
Automatic supervision & balancing.

---

## 8. Dispatchers
Assign blocking actors to dedicated pool:
```scala
Props[IoActor].withDispatcher("blocking-dispatcher")
```
Defined in `application.conf`.

---

## 9. Ask pattern pitfalls
* Needs implicit timeout:
  ```scala
  implicit val to: Timeout = 2.seconds
  ```
* Actor may block on `Await.result` leading to dead‑letter when timed out.

---

## 10. Stash
```scala
class DBActor extends Actor with Stash:
  def receive = loading
  def loading: Receive = {
    case Ready(data) => unstashAll(); context.become(active(data))
    case _           => stash()
  }
```
Queues messages until state ready.

---

## 11. Testing with TestKit
```scala
class GreeterSpec extends TestKit(ActorSystem("test"))
    with AnyWordSpecLike with BeforeAndAfterAll:
  "Greeter" should {
    "reply with greeting" in {
      val greeter = system.actorOf(Props[Greeter])
      greeter ! "Bob"
      expectMsg("Hi Bob")
    }
  }
```
`TestProbe` acts as controllable actor.

---

