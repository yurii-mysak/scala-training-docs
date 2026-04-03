# Authentication Mechanisms

This area covers common authentication methods in web and messaging systems, including protocol-level auth, token-based schemes, OAuth, SSO, and framework-specific directives.

---

## 1. HTTP Basic Authentication

- **Definition**: Simple auth scheme transmitting credentials in `Authorization: Basic <base64>` header.
- **Workflow**:  
  1. Client sends `Authorization: Basic Base64(username:password)`.  
  2. Server decodes and validates against user store.
- **Analogy**: ID badge with photo and name printed in clear.
- **Scala Example (Akka HTTP)**:
  ```scala
  import akka.http.scaladsl.server.Directives._
  val route =
    authenticateBasic(realm = "secure", myUserPassAuthenticator) { userName =>
      complete(s"Hello, $userName")
    }
  ```
- **Reference**: https://www.httpwatch.com/httpgallery/authentication/

---

## 2. Digest Access Authentication

- **Definition**: Challenge–response scheme hashing credentials with server nonce to avoid plain-text.
- **Workflow**:  
  1. Server responds `401` with `WWW-Authenticate: Digest ... nonce=...`.  
  2. Client sends `Authorization: Digest username="...", response="hash", ...`.  
- **Benefit**: Prevents replay and plaintext credential exposure.
- **Learn more**: https://en.wikipedia.org/wiki/Digest_access_authentication

---

## 3. Token-Based Authentication

- **Definition**: Client obtains a token (often JWT) after login, sends it in `Authorization: Bearer <token>`.
- **Workflow**:  
  1. Client POSTs credentials → server issues token (signed JSON).  
  2. Client includes token in subsequent requests.  
  3. Server verifies signature, expiration, claims.
- **Analogy**: Event wristband granting access until it expires.
- **Key Concepts**: stateless, scalable, tokens carry claims.
- **Tutorial**: https://scotch.io/tutorials/the-ins-and-outs-of-token-based-authentication

---

## 4. OAuth 2.0

- **Definition**: Authorization framework for delegated access to resources.
- **Roles**:  
  - **Resource Owner**: user.  
  - **Client**: app requesting access.  
  - **Authorization Server**: issues tokens.  
  - **Resource Server**: serves protected resources.
- **Flows**:  
  - **Authorization Code**: secure server-to-server exchange.  
  - **Implicit**: browser-based clients.  
  - **Client Credentials**: machine-to-machine auth.  
- **Analogy**: Hotel desk issuing room keys (tokens) with limited scope and duration.
- **Learn more**: https://developer.okta.com/blog/2017/06/21/what-the-heck-is-oauth

---

## 5. Single Sign-On (SSO)

- **Definition**: Users authenticate once for multiple systems or applications.
- **Mechanisms**: SAML, OpenID Connect, OAuth-based.
- **Analogy**: Master key card granting access to an office building and all rooms.
- **Benefits**: improved UX, central identity management.

---

## 6. Framework-Specific Security

### 6.1 Play Framework Security

- **Security Module**: filters, action composition for auth/role checks.
- **Scala Example**:
  ```scala
  import play.api.mvc._
  object SecuredAction extends ActionBuilder[Request, AnyContent] {
    override def invokeBlock[A](req: Request[A], block: (Request[A]) => Future[Result]) = {
      req.session.get("user").map { user =>
        block(req)
      }.getOrElse(Future.successful(Results.Redirect("/login")))
    }
  }
  ```
- **Reference**: https://www.playframework.com/documentation/2.0.1/ScalaSecurity

### 6.2 http4s Authentication

- **AuthMiddleware**: compose HTTP routes with auth logic.
- **Basic Auth**:
  ```scala
  import org.http4s.server.middleware.{BasicAuth, Logger}
  val authUser: Credentials => IO[Option[User]] = creds => ...
  val authedRoutes = BasicAuth("realm", authUser)(protectedRoutes)
  ```
- **Bearer Token**: custom middleware verifying JWT.
- **Reference**: https://http4s.org/v0.19/auth/

### 6.3 Akka HTTP Security Directives

- **authenticateBasic** / **authenticateOAuth2**  
- **authorize**: conditionally allow based on user/role.
  ```scala
  path("admin") {
    authorize(user.isAdmin) {
      complete("Admin content")
    }
  }
  ```
- **Reference**: https://doc.akka.io/docs/akka-http/current/routing-dsl/directives/security-directives/index.html

---

## 7. Authorization for Actions (Annotation-Based)

- **Concept**: decorate controller methods with annotations to enforce permissions.
- **Example (Java/Spring)**:
  ```java
  @PreAuthorize("hasRole('ADMIN')")
  public ResponseEntity<?> deleteUser(...) { ... }
  ```
- **Pattern**: declarative, centralizes access control.
- **Learn more**: https://martinfowler.com/articles/web-security-basics.html#AuthorizeActions

---

## 8. Further Reading

- OWASP Top Ten – authentication & authz risks: https://owasp.org/www-project-top-ten/  
- Web Security Basics: Martin Fowler article above.  
