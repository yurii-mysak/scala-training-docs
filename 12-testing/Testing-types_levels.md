# Types & Levels of Software Testing

This area classifies testing by purpose (types) and scope (levels) to ensure comprehensive quality coverage.

---

## 1. Types of Software Tests

| Type                      | Purpose                                         | Example Tools/Frameworks            |
|---------------------------|-------------------------------------------------|-------------------------------------|
| **Functional Testing**    | Verify features work as specified               | Selenium, ScalaTest                 |
| **Regression Testing**    | Ensure new changes don’t break existing behavior| JUnit, Specs2                       |
| **Smoke Testing**         | Quick check of critical functionality           | Custom scripts                      |
| **Sanity Testing**        | Narrow subset of regression tests               | SBT test subsets                    |
| **Performance Testing**   | Measure responsiveness and stability            | JMeter, Gatling, ScalaMeter         |
| **Load Testing**          | Test under expected peak load                   | JMeter, Gatling                     |
| **Stress Testing**        | Test beyond limits to find breaking point       | Gatling, custom tools               |
| **Security Testing**      | Identify vulnerabilities and threats            | OWASP ZAP, Burp Suite               |
| **Usability Testing**     | Evaluate user experience and interface          | Manual exploration                  |
| **Compatibility Testing** | Ensure app works across environments            | BrowserStack, Sauce Labs            |
| **Acceptance Testing**    | Validate requirements/user stories              | Cucumber, Specs2 FeatureSpec        |
| **Alpha/Beta Testing**    | Early user feedback in controlled/public beta   | TestRail, LaunchDarkly              |

*For detailed list*:  
https://hackr.io/blog/types-of-software-testing  
https://en.wikipedia.org/wiki/Software_testing

---

## 2. Testing Levels

| Level             | Scope                                       | Purpose                               |
|-------------------|---------------------------------------------|---------------------------------------|
| **Unit Testing**  | Individual classes/functions                | Verify smallest code units            |
| **Integration Testing** | Combined modules or services              | Test interactions between components  |
| **System Testing**| Entire application end-to-end               | Validate full system behavior         |
| **Acceptance Testing** | Against user requirements/acceptance criteria | Confirm readiness for production |
| **Regression Testing** | Any level post-changes                     | Detect unintended side-effects        |

*Overview of levels*:  
http://softwaretestingfundamentals.com/software-testing-levels/  
https://en.wikipedia.org/wiki/Software_testing#Testing_levels
