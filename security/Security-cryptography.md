# Cryptography Fundamentals

This area covers core concepts in cryptography relevant to messaging and web applications: Encryption, Hashing, and Authentication Codes.

---

## 1. Encryption Basics

**Encryption** transforms readable data (**plaintext**) into an unreadable form (**ciphertext**), ensuring confidentiality.

- **Symmetric Encryption**  
  - **Definition**: Uses a single shared secret key for both encryption and decryption.  
  - **Examples**: AES, DES, 3DES.  
  - **Analogy**: A locked box with one key given to both sender and receiver.  
  - **Workflow**:  
    1. Sender encrypts data with key.  
    2. Receiver decrypts data with the same key.  

- **Asymmetric Encryption**  
  - **Definition**: Uses a pair of keys — a **public** key to encrypt and a **private** key to decrypt.  
  - **Examples**: RSA, ECC.  
  - **Analogy**: A mailbox — anyone can drop letters (encrypt with public slot), only the owner with the private key can open and read them.  
  - **Workflow**:  
    1. Sender fetches receiver’s public key, encrypts message.  
    2. Receiver uses private key to decrypt.

*For deeper differences, see*:  
https://www.ssl2buy.com/wiki/symmetric-vs-asymmetric-encryption-what-are-differences

---

## 2. Encryption vs Hashing

| Aspect            | Encryption                          | Hashing                         |
|-------------------|-------------------------------------|---------------------------------|
| Reversibility     | Reversible (with key)               | Irreversible (one-way)          |
| Purpose           | Confidentiality                     | Integrity, fingerprinting       |
| Output size       | Similar to input                    | Fixed-size (e.g., 256 bits)     |
| Use cases         | Secure messaging, file encryption   | Password storage, checksums     |

- **Hashing** computes a fixed-length digest from input data; designed to be impossible to invert.  
- **Analogy**:  
  - Encryption: Sealed envelope you can open.  
  - Hashing: Ink stamp leaving a fingerprint — you can compare but not reconstruct the document.

*Learn more*:  
https://www.ssl2buy.com/wiki/difference-between-hashing-and-encryption

---

## 3. HMAC Authentication

**HMAC (Hash-based Message Authentication Code)** combines a cryptographic hash function with a secret key to ensure both integrity and authenticity.

- **Algorithm**: `HMAC = Hash(key ⊕ opad ∥ Hash(key ⊕ ipad ∥ message))`
- **Examples**: HMAC-SHA256, HMAC-SHA1.
- **Use case**: Verifying that messages weren’t altered and originated from a holder of the shared key.
- **Analogy**: Wax seal stamped with a secret emblem — break or forge it, and validation fails.

*Reference*:  
https://www.wolfe.id.au/2012/10/20/what-is-hmac-authentication-and-why-is-it-useful/

---

## 4. Password Encoding

Instead of raw hashing, **password encoding** uses adaptive functions with salt to protect against brute-force:

- **Bcrypt**: uses cost factor to slow down hashing.
- **Workflow**:  
  1. Generate a random *salt*.  
  2. Combine *salt* with plaintext password.  
  3. Compute Bcrypt hash.  
  4. Store hash and salt.  
  5. On login, repeat and compare.  
- **Analogy**: Pepper and salt in cooking — even if someone gets the recipe, replicating the taste is computationally expensive.

**Scala Example (pseudocode)**:

```scala
import org.mindrot.jbcrypt.BCrypt

// Encode
val salt = BCrypt.gensalt(12)            // cost factor = 12
val hashed = BCrypt.hashpw(password, salt)

// Verify
val ok = BCrypt.checkpw(inputPassword, hashed)
```

*Further reading*:  
https://www.baeldung.com/spring-security-registration-password-encoding-bcrypt
