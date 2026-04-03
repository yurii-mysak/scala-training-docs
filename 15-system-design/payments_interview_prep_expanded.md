# Payments Interview Preparation Guide

This guide covers core Payments topics for interviews, explained in detail for non-experts:

1. **Card-Network Flows**
   - Authorization
   - Capture
   - Settlement

2. **Tokenization & PCI-DSS Basics**

3. **3-D Secure (3DS) & Fraud-Prevention Strategies**

---

## 1. Card-Network Flows

Payments over card networks happen in three main steps: authorization, capture, and settlement. Below is a detailed look.

### 1.1 Authorization
- **Definition**: Checking if funds are available and reserving (holding) that amount on the cardholder’s account. No money moves yet.
- **Why It Matters**: Prevents overspending; gives merchant confidence funds exist.
- **Detailed Flow**:
  ```mermaid
  sequenceDiagram
    participant Cardholder
    participant MerchantPOS as Merchant
    participant AcquirerBank as Acquirer
    participant CardNetwork as Network
    participant IssuingBank as Issuer

    Cardholder->>MerchantPOS: Swipe or enter card details
    MerchantPOS->>AcquirerBank: Authorization request (amount, card data)
    AcquirerBank->>CardNetwork: Routes request
    CardNetwork->>IssuingBank: Checks account & fraud signals
    IssuingBank-->>CardNetwork: Approve/Decline + hold funds
    CardNetwork-->>AcquirerBank: Relay response
    AcquirerBank-->>MerchantPOS: Relay response
    MerchantPOS-->>Cardholder: “Approved” or “Declined”
  ```
- **Key Data**: Transaction amount, card number (PAN), expiry, CVV, merchant ID.
- **Common Delays**: Network latency, bank fraud checks.
- **Example in Everyday Life**: When you’re at a gas pump, it authorizes $1 before you pump fuel, then updates to actual amount later.
- **Best Practices**:
  - **Minimize Payload**: Send only necessary fields to reduce latency.
  - **Timeout & Retry**: Retry small number of times if no response.
  - **EMV 3DS Data**: Include device/browser signals to reduce fraud declines.

### 1.2 Capture
- **Definition**: Converting the previously held funds into an actual charge.
- **Why It Matters**: Merchant only gets paid once capture completes.
- **Detailed Flow**:
  1. Merchant sends capture request referencing the original authorization code.
  2. Acquirer → Network → Issuer confirms capture.
  3. Issuer moves hold amount to settlement batch.
- **Timing**: Usually within 1–7 days after authorization.
- **Examples**:
  - **Hotels**: Authorize $200 at check-in, capture final bill at check-out.
  - **E-commerce**: Authorize at order, capture when item ships.
- **Edge Cases**:
  - **Partial Capture**: Capture less than authorized (specify amount).
  - **Voiding**: Cancel authorization if capture not needed.
- **Best Practices**:
  - **Capture Promptly**: Avoid expired holds.
  - **Accurate Amounts**: Ensure capture amount matches invoice.
  - **Handle Declines**: Notify customer if capture fails.

### 1.3 Settlement
- **Definition**: Batching captured transactions and transferring funds from issuing banks to the merchant’s bank.
- **Why It Matters**: Finalizes payment and moves money.
- **Detailed Flow**:
  ```mermaid
  sequenceDiagram
    participant MerchantPOS as Merchant
    participant AcquirerBank as Acquirer
    participant CardNetwork as Network
    participant IssuingBank as Issuer

    loop Daily Settlement Batch
      MerchantPOS->>AcquirerBank: Send settlement file (captured txns)
      AcquirerBank->>CardNetwork: Forward batch
      CardNetwork->>IssuingBank: Request fund transfers
      IssuingBank-->>CardNetwork: Approve fund transfers
      CardNetwork-->>AcquirerBank: Send funds
      AcquirerBank-->>MerchantPOS: Deposit funds
    end
  ```
- **Settlement Cycle**: Often daily; merchant cut-off times apply.
- **Reconciliation**: Match settlement totals with internal records.
- **Exceptions**: Chargebacks, reversals must be handled separately.
- **Best Practices**:
  - **Align with Cut-offs**: Know bank deadlines.
  - **Automate Reconciliation**: Use matching algorithms.
  - **Monitor Failures**: Alert on any settlement discrepancies.

---

## 2. Tokenization & PCI-DSS Basics

Handling cardholder data securely reduces risk and compliance burden.

### 2.1 Tokenization
- **Definition**: Store only a surrogate value (token) instead of the real card number.
- **How It Works**:
  1. Cardholder enters PAN.
  2. Payment gateway sends PAN to secure vault.
  3. Vault returns a token (e.g., `tok_1A2B3C`).
  4. Merchant uses token for future transactions.
- **Benefits**:
  - Merchant never touches raw PAN.
  - Even if breached, tokens are useless outside system.
- **Types of Tokens**:
  - **Format-Preserving**: Looks like a card number (for legacy systems).
  - **Random**: No relation to PAN.
- **Example Flow**:
  ```mermaid
  sequenceDiagram
    participant Merchant
    participant Vault
    Merchant->>Vault: Send PAN for tokenization
    Vault-->>Merchant: Receive token
  ```
- **Best Practices**:
  - Always use PCI-compliant vaults.
  - Rotate tokens periodically if supported.
  - Limit token retrieval to authorized services.

### 2.2 PCI-DSS Basics
- **Definition**: Set of 12 standards ensuring secure handling of payment data.
- **High-Level Requirements**:
  1. **Secure Network**: Use firewalls; change default passwords.
  2. **Protect Data**: Encrypt PAN in transit & at rest.
  3. **Vulnerability Management**: Regularly patch systems; use anti-malware.
  4. **Access Control**: Unique IDs; least privilege.
  5. **Monitoring & Testing**: Log all access; quarterly scans.
  6. **Security Policy**: Document policies & train staff.
- **PCI Scope Reduction**:
  - **Tokenization** and **Hosted Payment Pages** shrink what systems are in scope.
- **Best Practices**:
  - Annual external penetration testing.
  - Continuous log monitoring for unusual access.
  - Employee phishing training.

---

## 3. 3-D Secure (3DS) & Fraud-Prevention Strategies

Adding layers of authentication and intelligence to reduce fraud.

### 3.1 3-D Secure (3DS)
- **Definition**: An extra authentication step via card issuer to confirm cardholder identity.
- **Version Differences**:
  - **3DS 1.0**: Redirect to bank page → poor mobile UX.
  - **3DS 2.x**: In-app/browser SDK collects device/browser data for risk checks, enabling “frictionless” flow when risk is low.
- **Detailed Flow**:
  ```mermaid
  sequenceDiagram
    participant MerchantWebsite as Merchant
    participant 3DSDirectory
    participant ACS as Issuer
    participant Cardholder

    MerchantWebsite->>3DSDirectory: Find ACS for card
    MerchantWebsite->>Cardholder: Trigger challenge (if needed)
    Cardholder->>ACS: Authenticate (SMS OTP or biometric)
    ACS-->>MerchantWebsite: Return authentication result
  ```
- **Data Elements**: Device fingerprint, transaction history, geo-IP.
- **Frictionless vs. Challenge**:
  - **Frictionless**: No user step if risk low.
  - **Challenge**: User enters OTP or biometric if risk high.
- **Best Practices**:
  - Provide clear messaging during challenge.
  - Collect rich signals (browser info, transaction context).
  - Monitor metrics: challenge rates, success rates.

### 3.2 Fraud-Prevention Strategies
- **Layered Approach**:
  1. **Rule-Based Filters**: E.g., block IPs from high-fraud countries.
  2. **Velocity Checks**: Limit number of transactions per card per hour/day.
  3. **Device Fingerprinting**: Identify repeat devices.
  4. **Behavioral Analytics**: Spot anomalies in spending patterns.
  5. **Machine Learning Scoring**: Combine signals for real-time risk score.
- **Sample Rule**:
  - Decline >\$5000 orders from new cards in <24h.
- **Best Practices**:
  - Balance user friction and security.
  - Regularly review & tune rules based on fraud trends.
  - Integrate feedback loops: flagged transactions feed model retraining.

---

*End of Expanded Guide*
