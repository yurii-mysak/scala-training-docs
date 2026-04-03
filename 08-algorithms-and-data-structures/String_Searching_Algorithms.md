# String Searching Algorithms

This file covers:
- Knuth–Morris–Pratt (KMP) Algorithm
- Rabin–Karp Substring Search

---

## Knuth–Morris–Pratt (KMP) Algorithm

**Definition:**  
Efficient pattern search using a precomputed “failure” (prefix) table to skip redundant comparisons.

### Key Concepts

1. **Prefix Function (π):**  
   - For each position *i* in pattern *P*, π[i] = length of longest proper prefix of P[0..i] which is also a suffix of P[0..i].
2. **Search Phase:**  
   - Use π to shift pattern by skipping already matched prefixes.

> **Analogy:**  
> Searching a book index and using known structure to skip chapters that can’t match.

### Building Prefix Table

```scala
def buildPrefix(pattern: String): Array[Int] =
  val n = pattern.length
  val pi = Array.fill(n)(0)
  var k = 0
  for i <- 1 until n do
    while k > 0 && pattern(k) != pattern(i) do
      k = pi(k - 1)
    if pattern(k) == pattern(i) then k += 1
    pi(i) = k
  pi
```

### Search Implementation

```scala
def kmpSearch(text: String, pattern: String): List[Int] =
  val pi = buildPrefix(pattern)
  var q = 0
  val results = scala.collection.mutable.ListBuffer.empty[Int]

  for i <- text.indices do
    while q > 0 && pattern(q) != text(i) do
      q = pi(q - 1)
    if pattern(q) == text(i) then q += 1
    if q == pattern.length then
      results += (i - pattern.length + 1)
      q = pi(q - 1)
  results.toList
```

**Complexity:**  
- **Time:** O(n + m) where n = text length, m = pattern length  
- **Space:** O(m)

---

## Rabin–Karp Substring Search

**Definition:**  
Uses rolling hash to compare pattern and text substrings; reduces average comparisons.

### Key Concepts

1. **Rolling Hash:**  
   - Compute hash for current window, update by removing leading char and adding trailing char.
2. **Hash Comparison:**  
   - On hash match, verify by direct string comparison.

> **Analogy:**  
> Rolling fingerprint scanner: compare hashed prints quickly, verify visually if fingerprint matches.

### Implementation

```scala
def rabinKarp(text: String, pattern: String, prime: Int = 101): List[Int] =
  val n = text.length; val m = pattern.length
  val results = scala.collection.mutable.ListBuffer.empty[Int]
  val base = 256

  // Precompute highest-order multiplier
  var h = 1
  for _ <- 1 until m do h = (h * base) % prime

  // Initial hashes
  var pHash = 0; var tHash = 0
  for i <- 0 until m do
    pHash = (base * pHash + pattern(i).toInt) % prime
    tHash = (base * tHash + text(i).toInt) % prime

  // Slide window
  for i <- 0 to n - m do
    if pHash == tHash && text.substring(i, i + m) == pattern then
      results += i
    if i < n - m then
      tHash = (base * (tHash - text(i).toInt * h) + text(i + m).toInt) % prime
      if tHash < 0 then tHash += prime

  results.toList
```

**Complexity:**  
- **Average Time:** O(n + m)  
- **Worst Case:** O(nm) (due to hash collisions)  
- **Space:** O(1)

---

*Next up: Advanced Dynamic Programming & Hash Table Collision Resolution.*  
*Send “continue” when you’re ready!*  
