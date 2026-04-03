# IP Addressing Fundamentals

## 1  IPv4 Address Structure  

An **IPv4 address** is a 32‑bit value divided into four 8‑bit *octets*, written in *dotted‑decimal* form (e.g., `192.168.10.25`).  
Each octet can range from **0–255** because 8 bits allow 2⁸ = 256 values.

```
+--------+--------+--------+--------+
| Octet1 | Octet2 | Octet3 | Octet4 |
+--------+--------+--------+--------+
   8 bits   8 bits   8 bits   8 bits   = 32 bits
```

> **Analogy:** Think of an IP address like a street address: the *network* part is the city, and the *host* part is the house number on that street.

---

## 2  Classful Network Addresses (Historic)

| Class | 1st Octet Range | Default Subnet Mask | # Networks | Max Hosts / Net | Typical Use |
|-------|-----------------|---------------------|------------|-----------------|-------------|
| **A** | 0 – 127         | 255.0.0.0 (/8)      | 128        | 16 777 214      | Very large orgs |
| **B** | 128 – 191       | 255.255.0.0 (/16)   | 16 384     | 65 534          | Medium‑large orgs |
| **C** | 192 – 223       | 255.255.255.0 (/24) | 2 097 152  | 254             | Small nets |
| **D** | 224 – 239       | *NA* (multicast)    | –          | –               | Multicast |
| **E** | 240 – 255       | *Reserved*          | –          | –               | Research |

> Modern networks use **CIDR** (Classless Inter‑Domain Routing) instead of rigid classes.

---

## 3  CIDR & Subnet Masks  

A subnet mask identifies which bits of the address denote the *network* and which denote the *host*.

* **Dotted‑decimal:** `255.255.255.0`  
* **CIDR prefix:** `/24` (the number of 1‑bits)

Example:

```
Address:  192.168.10.25   → 11000000.10101000.00001010.00011001
Mask /26: 255.255.255.192 → 11111111.11111111.11111111.11000000
---------------------------------------------------------------
Network:                  → 11000000.10101000.00001010.00000000
                           192.168.10.0/26
```

Splitting a /24 into /26 gives **4 subnets** (64 addresses each), improving broadcast containment.

---

## 4  Private vs. Public Ranges  

| RFC1918 Range | CIDR | Typical Size |
|---------------|------|--------------|
| 10.0.0.0 – 10.255.255.255 | /8  | 16.7 M |
| 172.16.0.0 – 172.31.255.255 | /12 | 1 M |
| 192.168.0.0 – 192.168.255.255 | /16 | 65 K |

Private addresses are **not routable on the public Internet** and usually hide behind **NAT**.

---

## 5  Default Gateway  

A *default gateway* is the router IP on your subnet that **forwards traffic destined to other networks**.  
Think: the post office that forwards mail outside your neighborhood.

Typical home setup:

```
PC (192.168.1.10/24)
      │
Switch/Wi‑Fi
      │
Router GW ‑‑> 192.168.1.1  ⇄  ISP Internet
```

---

## 6  IPv4 vs. IPv6 (Preview)

| Feature | **IPv4** | **IPv6** |
|---------|----------|----------|
| Address length | 32 bit | 128 bit |
| Format | Decimal (`192.0.2.1`) | Hex (`2001:0db8::1`) |
| Address space | ~4.3 B | 3.4×10³⁸ |
| Built‑in security | Optional IPSec | Mandatory IPSec support |
| Fragmentation | Routers & hosts | Hosts only (Path MTU) |
| NAT required | Common | Rare |

![IPv4 vs IPv6](https://upload.wikimedia.org/wikipedia/commons/0/07/IPv4_vs_IPv6.svg)

---

## 7  Quick Cheat‑Sheet

* **/30** → 255.255.255.252 → 4 IPs (2 usable) – point‑to‑point links  
* **/24** → 255.255.255.0   → 256 IPs (254 usable) – common LAN  
* **/16** → 255.255.0.0     → 65 536 IPs – large campus

**Binary shortcut:**  
* 128 = /1, 192 = /2, 224 = /3, 240 = /4, 248 = /5, 252 = /6, 254 = /7, 255 = /8.

---

### Further Reading  
* Tutorialspoint – “IPv4 Tutorial”  
* Microsoft *Networking Fundamentals* – Lesson 4  
* Cisco – IP Addressing docs
