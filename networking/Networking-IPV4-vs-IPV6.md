# IPv4 vs. IPv6 & Transition Mechanisms

---

## 1  Why IPv6?

| Metric | **IPv4** | **IPv6** |
|--------|----------|----------|
| Address length | 32 bits | 128 bits |
| Total addresses | ~4.29 billion | 3.4 × 10³⁸ |
| Notation | Dotted‑decimal `192.0.2.1` | Hex, colon‑separated `2001:db8::1` |
| Header size | 20–60 bytes | Fixed 40 bytes |
| Fragmentation | Routers & hosts | Hosts only (Path MTU) |
| Built‑in security | Optional IPsec | IPsec mandatory (implementation) |
| Broadcast | Yes | Replaced by multicast & anycast |
| NAT required? | Common | Rare (end‑to‑end) |

Source: PhoenixNAP “IPv4 vs IPv6 – What’s the Difference?” (2025) citeturn0search0

> **Analogy:** IPv4 is an old ZIP code system that ran out of numbers; IPv6 is a new scheme that assigns every grain of sand its own address.

---

## 2  IPv6 Address Anatomy

```
2001:0db8:85a3:0000:0000:8a2e:0370:7334
|--| |--| |--| |--| |--| |--| |--| |--|
 16 bits × 8 = 128 bits
```

* **Zero compression** – replace consecutive 0 sections with `::` (`2001:db8::8a2e:370:7334`).  
* **Leading zeros** omitted per hextet.

### Address Types

| Type | Prefix | Example | Scope |
|------|--------|---------|-------|
| **Global Unicast** | `2000::/3` | 2001:db8::1 | Internet‑routable |
| **Link‑Local** | `fe80::/10` | fe80::1ff:fe23:4567:890a | Same LAN segment |
| **Multicast** | `ff00::/8` | ff02::1 | One‑to‑many |
| **Unique‑Local** | `fc00::/7` | fd12:3456::/48 | Private (RFC 4193) |
| **Anycast** | n/a | 2001:4860:4860::8888 | Nearest instance |

---

## 3  Header Comparison

```text
IPv4 Header (min 20 B)        IPv6 Header (40 B fixed)
+----+-----+------+-----+     +---+---+---+---+
|Ver|IHL |TOS|Len | ... |     |Ver|TC |FlowLbl |
+----+-----+------+-----+     +---+---+---+---+
```

IPv6 removes/relocates:

* **Header checksum** – redundant (handled by L4).  
* **Options** → moved to **extension headers** (chainable).  
* Simplifies router processing → faster hardware pipelines.

---

## 4  Transition Techniques

Because we can’t flip a switch overnight, networks use **dual‑stack** and **tunnels**.

| Category | Mechanism | Idea | Scenario |
|----------|-----------|------|----------|
| **Dual‑Stack** | Native v4 + v6 on every node | Preferred where both supported | Modern ISPs |
| **Tunneling** | 6to4 (`2002::/16`), ISATAP, GRE, Teredo | Encapsulate IPv6 inside IPv4 | v6‑islands across v4 infra |
| **Translation** | NAT64/DNS64, 464XLAT | IPv6‑only client ↔ IPv4 server via gateway | Mobile carriers, IoT |
| **Proxy** | Application‑layer (HTTP, SMTP) | v6 client to proxy, proxy to v4 | CDN edges |

![Transition map](https://upload.wikimedia.org/wikipedia/commons/7/7b/IPv6_transition_mechanisms.svg)

### NAT64 Flow

```
IPv6 Client → DNS64 → Synth AAAA from A
        ↓
     NAT64 (IPv6 ↔ IPv4 translation, protocol‑64)
        ↓
   Legacy IPv4‑only Server
```

> **Tip:** Android uses **464XLAT** (CLAT + PLAT) so legacy IPv4 apps still work on IPv6‑only mobile networks.

---

## 5  Address Planning Best Practices

1. **Use /64 per LAN** – SLAAC relies on 64‑bit interface IDs.  
2. Reserve **/48 per site**; subnet into /56 or /60 for departments.  
3. Leverage **Unique‑Local (ULA)** for internal‑only traffic.  
4. Document **RIR allocation** & reverse‑DNS zones early.  
5. Train ops teams: **ICMPv6** is *not optional* (Path MTU, NDP).

---

## 6  Troubleshooting Cheat‑Sheet

```bash
# Show IPv6 addresses
ip -6 addr

# Default gateways (routers)
ip -6 route show default

# Ping link‑local (need %iface)
ping6 fe80::1%eth0

# Trace IPv6 path
traceroute6 ipv6.google.com

# Test NAT64 reachability (well‑known prefix)
ping6 64:ff9b::8.8.8.8
```

---

### Further Reading

* PhoenixNAP – “IPv4 vs IPv6” guide  
* RFC 4291 – IPv6 Addressing Architecture  
* RFC 6146 – NAT64  
* “IPv6 Essentials” (O’Reilly) – 4th ed.
