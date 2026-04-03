# Security Threats & Vulnerabilities

This area covers prevalent security risks in web and messaging systems, including the OWASP Top Ten and man-in-the-middle attacks.

---

## 1. OWASP Top Ten Security Risks

The OWASP Top Ten is a standardized awareness document listing the most critical web application security risks:

| Risk ID | Name                                    | Description                                                      |
|---------|-----------------------------------------|------------------------------------------------------------------|
| A01     | Broken Access Control                   | Unauthorized access to functionality or data                     |
| A02     | Cryptographic Failures                  | Insecure encryption or hashing leading to data exposure         |
| A03     | Injection                               | SQL, NoSQL, OS, and LDAP injections enabling data manipulation   |
| A04     | Insecure Design                         | Flaws in business or security design principles                  |
| A05     | Security Misconfiguration               | Incorrect configurations, default settings, verbose errors       |
| A06     | Vulnerable and Outdated Components      | Using libraries with known vulnerabilities                       |
| A07     | Identification and Authentication Failures | Broken authentication, session management                    |
| A08     | Software and Data Integrity Failures    | Code and infrastructure compromised (e.g., CI/CD tampering)      |
| A09     | Security Logging and Monitoring Failures | Insufficient logging and monitoring for detecting breaches     |
| A10     | Server-Side Request Forgery (SSRF)      | Server-side HTTP requests initiated by attackers                |

*For details and remedial guidance, see:*  
https://owasp.org/www-project-top-ten/

---

## 2. Man‑in‑the‑Middle (MITM) Attack

A MITM attacker intercepts and potentially alters communication between two parties.

- **Attack Process**:
  1. Attacker positions between client and server (e.g., via network spoofing).
  2. Intercepts initial handshake (e.g., SSL/TLS).
  3. Relays messages, possibly modifying them in transit.
- **Impacts**: Credential theft, data tampering, session hijacking.
- **Mitigations**:
  - Enforce TLS with strict certificate validation.
  - Use HSTS and certificate pinning.
  - Employ mutual TLS where feasible.
- **Analogy**: A spy intercepting and rewriting letters sent between two correspondents.

---

## 3. Other Common Threats (Brief)

- **Cross-Site Scripting (XSS)**: Injecting malicious scripts into web pages.
- **SQL Injection**: Executing unauthorized SQL commands.
- **Cross-Site Request Forgery (CSRF)**: Unauthorized commands transmitted from a user the site trusts.
- **Remote Code Execution (RCE)**: Execution of arbitrary code on a target system.

---

## 4. Further Reading

- OWASP Top Ten Project: https://owasp.org/www-project-top-ten/  
- OWASP Cheat Sheets: https://cheatsheetseries.owasp.org/  
