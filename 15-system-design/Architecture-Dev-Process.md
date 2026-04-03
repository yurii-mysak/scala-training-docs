# Architecture & Development Process — Full Reference  

## 1 · Algorithms & Complexity  

| Concept | Explanation | Typical Ops | Big-O | Notes |
|---------|-------------|-------------|-------|-------|
| Array search (linear) | Scan each cell until found | `find` | **O(n)** | Fast on tiny datasets |
| Binary search | Halve sorted list each step | `find` | **O(log n)** | Needs random access |
| Linked list | Nodes with `data + next` | insert front | **O(1)** | Search is O(n) |
| Stack | LIFO (push/pop) | `push`, `pop` | **O(1)** | Call-stack sim |
| Queue | FIFO | `enqueue`, `dequeue` | **O(1)** | Often circular buffer |
| Hash table | `h(k) = k mod m` | lookup | **amort O(1)** | Collisions ⇒ chain |

> **Rule of thumb**: drop constants, analyse worst-case, but profile real workloads.

---

## 2 · Object-Oriented Design Glossary  

* **Abstraction** – expose “what”, hide “how”.  
* **Encapsulation** – keep state private; change through methods only.  
* **Inheritance** – *“is-a”* hierarchy; enables reuse.  
* **Aggregation / Composition** – *“has-a”* (lifetime bound for composition).  
* **Polymorphism** – same interface, multiple impls (overriding, type-classes).  
* **Cohesion** – how strongly related class responsibilities are (↑ good).  
* **Coupling** – degree modules depend on each other (↓ good).

### 2.1 SOLID (with micro-examples)

| Principle | One-liner | Mini Scala example |
|-----------|-----------|--------------------|
| **S**ingle Responsibility | One reason to change | `class InvoicePrinter` vs `InvoiceCalculator` |
| **O**pen/Closed | Open for ext, closed for mod | add new `PaymentType` via subtype |
| **L**iskov Substitution | Subclass honour contracts | don’t throw broader exceptions |
| **I**nterface Segregation | Small, focused traits | `Readable`, `Writable` not `FatIO` |
| **D**ependency Inversion | Depend on abstractions | `trait Logger` injected, not `println` |

### 2.2 Common Anti-patterns

* **God Object** – monolith class with 1000 LOC.  
* **Database-as-IPC** – services comm via shared tables.  
* **Poltergeist / Middle-Man** – meaningless pass-through class.  
* **Magical Numbers / Push-button** – config hard-coded constants.

---

## 3 · Refactoring Catalogue  

| Smell | Classic Fix | Intent |
|-------|-------------|--------|
| **Long method** | *Extract Method* | Clarify intent, enable reuse |
| **Switch stmt** | *Replace Conditional with Polymorphism* | Move logic to subclasses |
| **Temp field** | *Extract Class* | Remove partial lifecycle variables |
| **Parallel Inheritance** | *Move Method/Field* | Collapse duplicated hierarchies |
| **Speculative general.* | *Collapse Hierarchy* | Delete YAGNI abstractions |

Tools: IntelliJ *Structural Search & Replace*, `scalafix`, `scalafmt`.

---

## 4 · Estimation & Planning  

1. **Relative sizing** – Fibonacci story-points (1,2,3,5,8…).  
2. **Velocity** – avg points *Done* per sprint ⇒ date projection.  
3. **Decomposition** – split epic → stories → tasks.  
4. **Three-point (PERT)** – (Optimistic + 4·Most-likely + Pessimistic)/6.  
5. **Planning poker** – team consensus beats “HiPPO” (highest-paid opinion).

---

## 5 · Requirements Engineering  

* **Functional** – behaviour (*user can upload avatar*).  
* **Non-functional** – quality (*99.95 % uptime, <250 ms P95*).  
* **Business** – ROI (*reduce cart abandon by 5 %*).  

**Good requirement**: atomic, testable, traceable, prioritised, unambiguous.

Methods: stakeholder interview, gemba walk, brainstorming, prototypes, MoSCoW prioritisation.

---

## 6 · SDLC Models  

| Model | Pros | Cons |
|-------|------|------|
| Waterfall | Clear phases, docs | Rigid to change |
| V-Model | Test plan per phase | Same rigidity |
| Agile (Scrum) | Iterative, feedback loop | Discipline needed |
| Kanban | Continuous flow | Scope creep risk |

### Scrum quick cards
* **Roles**: PO, Dev Team, Scrum Master.  
* **Events**: Sprint Planning → Daily Scrum → Sprint Review → Retro.  
* **Artifacts**: Product Backlog, Sprint Backlog, Increment.  
* Chart: *Sprint Burndown* tracks work left vs time.

---

## 7 · Kanban Essentials  

Columns (`Backlog → Dev → Code Review → Test → Done`) + **WIP limits** reveal bottlenecks.  
Lead time = commit → production; Cumulative Flow Diagram shows ageing tasks.

---

## 8 · UML & Diagrams  

| Diagram | Purpose |
|---------|---------|
| Use-Case | capture actor interactions |
| Class | static structure |
| Sequence | message flow |
| Activity | business workflow |
| ERD | DB entities & relations |
| DFD | data movement |

Notation: `+` public, `-` private, `#` protected, `<<interface>>` stereotypes.

---

## 9 · Code Quality & Metrics  

* **Review flavours** – pair-programming, formal inspection, tool-gate.  
* **Automated metrics** – test coverage, cyclomatic complexity, afferent/efferent coupling, fan-out, code churn.  
* **Test pyramid** – many unit tests, fewer service/component, least E2E.  
* **CI/CD pipeline** – commit → build → test → static analysis → deploy.

---

### Quick-Reference diagram

![Layered Architecture](https://i.imgur.com/1psf7YY.png)

*Presentation ↔ Application ↔ Domain ↔ Infrastructure*.  
Each layer only calls the one below, promoting isolation & testability.

---
