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
- Think of TLS/SSL like exchanging locked boxes with secret combination locks:

1. **Initial Contact (ClientHello/ServerHello)**
The client sends a random nonce (ClientRandom) and a list of supported cipher-suites (e.g. TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256).
The server picks one cipher-suite, sends its own random nonce (ServerRandom), and its certificate (containing its long-term public key).
  - Alice wants to send Bob a secret message
  - She sends Bob an empty box with several different types of locks she can use
  - Bob picks one lock type they both have and sends back his own empty box

2. **Certificate Exchange**
This also contains public key
  - Bob shows Alice his ID card (certificate) certified by a trusted authority
  - Alice verifies Bob's ID is genuine through the authority's signature

3. **Key Exchange**
Alice and Bob now derive a shared secret combination:
  - Alice generates a new secret combination for a lock
  - She locks a box containing this combination using Bob's public lock
  - Only Bob can unlock it with his private key
  - Now both have the same secret combination

4. **Secure Communication**
For current session, they use the shared secret combination to encrypt messages:
  - Alice and Bob can now use matching locks with their shared combination
  - Each message goes in a new box with the same combination
  - Even if someone intercepts the boxes, they can't open them
  - The combination is unique to this conversation and discarded afterwards

This is why MITM attacks fail: an interceptor can't pretend to be Bob without his ID and private key, and can't discover the secret combination protected by Bob's lock.

This is symmetric encryption: both parties use the same secret combination to lock and unlock messages.

Symmetric - large data volumes, fast encryption/decryption
Asymmetric - small data volumes, secure key exchange, slower
TLS uses both: asymmetric for handshake, symmetric for data transfer.

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
