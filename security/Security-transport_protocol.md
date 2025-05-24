# Transport & Protocol Security

This area covers securing data **in transit**: SSL/TLS fundamentals, preventing man‑in‑the‑middle attacks, and client certificate authentication.

---

## 1. TLS & SSL Overview

**SSL (Secure Sockets Layer)** and **TLS (Transport Layer Security)** provide encrypted communication channels over unreliable networks.

- **TLS Handshake**:
  1. **ClientHello**: client sends supported protocol versions, cipher suites, and a random nonce.
  2. **ServerHello**: server selects protocol version and cipher suite, sends its certificate and random nonce.
  3. **Certificate Validation**: client verifies server’s certificate against trusted CAs.
  4. **Key Exchange**: client and server derive a **shared secret** (using RSA, Diffie–Hellman, or ECDHE).
  5. **Finished**: both parties send encrypted messages to confirm handshake integrity.

**Analogy**:  
- Exchanging locked boxes with secret combination locks that change per session.

*Learn more*: https://blog.barracuda.com/2015/07/09/ssl-and-tls-explained/

---

## 2. Man‑in‑the‑Middle (MITM) Attacks

A MITM attacker intercepts communication, potentially eavesdropping or altering messages.

- **Attack Vector**: attacker positions between client and server (e.g., rogue Wi‑Fi).
- **Prevention**:
  - **Certificate Pinning**: client trusts only known server certificates.
  - **Strict Certificate Validation**: reject self‑signed or expired certs.
  - **HSTS**: force HTTPS connections.
- **Detection**: mismatched certificates, unexpected CA chains.

**Analogy**:  
- Tampering with postal mail by substituting a fake mailbox en route.

---

## 3. Client Certificate Authentication

Mutual TLS (mTLS) extends TLS so both parties authenticate via certificates.

- **Workflow**:
  1. Server sends its certificate.
  2. Client verifies server certificate.
  3. Server requests client certificate.
  4. Client sends its certificate; server verifies against CA/truststore.
- **Use cases**: high‑security APIs, IoT device authentication.

**Configuration (Apache HTTP Server example)**:
```apache
SSLVerifyClient require
SSLVerifyDepth 2
SSLCACertificateFile /etc/ssl/certs/ca.pem
```

**Scala (http4s)**:
```scala
import org.http4s.server.blaze.BlazeServerBuilder
import javax.net.ssl.{SSLContext, KeyManagerFactory, TrustManagerFactory}

val sslContext: SSLContext = // initialize with client & server keystores
BlazeServerBuilder[IO]
  .withSslContext(sslContext)
  .bindHttp(443, "0.0.0.0")
  .withHttpApp(app)
  .resource
```

*Learn more*: http://www.jscape.com/blog/client-certificate-authentication

---

## 4. Best Practices

- Always use TLS ≥1.2; prefer TLS 1.3 for simplified handshake and forward secrecy.
- Rotate certificates regularly and revoke compromised certificates via CRLs/OCSP.
- Disable legacy protocols (SSLv2, SSLv3, TLS 1.0/1.1).
- Enforce strong cipher suites (e.g., ECDHE, AES-GCM).

---

## Further Reading

- SSL/TLS Explained: https://blog.barracuda.com/2015/07/09/ssl-and-tls-explained/  
- MITM Attack Overview: https://owasp.org/www-community/attacks/Man-in-the-middle  
- Client Certificate Auth: http://www.jscape.com/blog/client-certificate-authentication  
