# QUALITY-003 — Independent Protocol Reference Matrix (first test slice)

**Date:** 2026-11-23 (ISO).  
**Source baseline:** `main@11bdcbc8819c27df5b74172139615d699e08e1a8`.  
**Scope:** Linux-only network simulation. No Windows or macOS target.  
**Status:** **EVIDENCE IN PROGRESS**; this small reference-vector slice is not the full QUALITY-003 acceptance or an assertion of standards compliance.

## Method and provenance

This file fixes expected packet bytes and route decisions **before** running the code under test. The regression file `tests/test_protocol_reference_vectors.py` contains independent literal constants based on published wire formats. Expected values are not generated from `network_core` methods, and success is not inferred from serializer/parser roundtrips. For byte vectors, positive assertions compare the exact encoded bytes and negative assertions corrupt a field. Running tests on their own code is not proof of end-to-end packet delivery.

**Reference versions (official sources):**
- [RFC 894 — IP over Ethernet](https://www.rfc-editor.org/rfc/rfc894.html), 1984.
- [IEEE 802.1Q 802.1 VLAN tagging format](https://www.ieee802.org/1/files/public/docs2009/ba-cgunther-vlan-tagging-0309.pdf), IEEE 802.1 public technical material, 2009 (TPID/TCI layout; not a claim of complete 802.1Q compliance).
- [RFC 826 — ARP](https://www.rfc-editor.org/rfc/rfc826.html), 1982.
- [RFC 791 — IPv4](https://www.rfc-editor.org/rfc/rfc791.html), 1981.
- [RFC 1071 — Internet checksum](https://www.rfc-editor.org/rfc/rfc1071.html), 1988, numerical example in section 3.
- [RFC 1812 — IPv4 router requirements](https://www.rfc-editor.org/rfc/rfc1812.html), 1995, longest-match routing.
- [RFC 3021 — IPv4 /31 point-to-point](https://www.rfc-editor.org/rfc/rfc3021.html), 2000; boundary verification is in existing tests and remains to be independently extended.
- [RFC 792 — ICMP](https://www.rfc-editor.org/rfc/rfc792.html), 1981, Echo format.
- [RFC 2131 — DHCPv4](https://www.rfc-editor.org/rfc/rfc2131.html), 1997, BOOTP layout, magic cookie, options, and DORA.

## Precommitted independent outcomes

| QUALITY class | Reference vector / scenario | Required outcome in supported subset | Test method |
|---|---|---|---|
| **3A Ethernet** | Destination `02:...:0B`, source `02:...:0A`, EtherType `0x0800`, data `IP!` | Exact 14-byte Ethernet II header and 46-byte padded payload, total 60 without FCS; shorter byte frame rejected | `test_ethernet_rfc894_exact_ethertype_padding_and_negative_length` |
| **3B VLAN** | One C-tag: `0x8100 0x0025 0x0800`, i.e., VID 37, PCP=DEI=0 | Exact 18-byte tagged header, 42-byte padded payload; nonzero PCP rejected as outside supported subset | `test_vlan_8021q_exact_single_ctag_and_invalid_tag` |
| **3C ARP** | Ethernet/IPv4 ARP `htype=1, ptype=0x0800, hlen=6, plen=4, op=1`, explicit sender/target | Exact 28-byte request with zero target MAC, malformed hardware length rejected | `test_arp_rfc826_exact_request_and_invalid_hardware_length` |
| **3D Checksum** | RFC 1071 numerical example `00 01 F2 03 F4 F5 F6 F7` | Folded sum `DDF2`, complement `220D` | `test_rfc1071_independently_published_checksum_example` |
| **3D IPv4** | 32-byte IPv4 datagram carrying Echo; TTL 64, source `192.0.2.10`, destination `198.51.100.20` | Exact 20-byte header, checksum `8E8B`, forwarding decrements TTL; invalid header checksum rejected | `test_ipv4_rfc791_exact_20byte_header_and_ttl` |
| **3D Routing** | Router with `10.0.0.0/8` and `10.8.0.0/16`, no cables | Longest prefix wins for `10.8.10.20`, /8 for `10.9.2.1`, NO_ROUTE outside; X/Y changes cannot affect route; inactive narrow port falls back to /8; a routing match is not reachability | `test_rfc1812_longest_prefix_and_no_inferred_reachability` |
| **3E ICMP** | Echo type8/code0, ID 0x1234, seq1, `ping` | Exact request checksum `06FA`, reply type0 checksum `0EFA`, corrupted request rejected; reply-to-reply prohibited | `test_icmp_rfc792_exact_echo_and_checksum_corruption` |
| **3F DHCP** | DISCOVER XID `0x10203040`, explicit MAC | Exact 300-byte BOOTP/DHCP subset, magic cookie `63825363`, option 53 DISCOVER, END; OFFER's declared subset options and 3600s lease encoded correctly; malformed cookie rejected | `test_dhcp_rfc2131_exact_discover_bootp_cookie_options_and_corruption` |

## Observation and acceptability

The canonical verification command is:

```bash
python3 -m unittest discover -s tests -p 'test_protocol_reference_vectors.py' -v
```

This first slice is PASS **only when** these exact tests and the regular required `unit-tests` workflow succeed on the **same final PR HEAD**. Record HEAD/run in the PR. No success is claimed from this document alone. Code not covered here remains `NOT_VERIFIED` by this particular external matrix, even if older code-based tests pass.

**Still outside the demonstrated slice (QUALITY-003 remains open):** 3A learned/unlearned MAC forwarding, unknown-unicast and loop/STP boundaries; 3B VLAN end-to-end isolation and trunk/drop paths; 3C ARP cache and silent-peer paths; 3D multi-hop IPv4 with independent return-route and /31 boundary references; 3E router-generated ICMP errors and full Echo roundtrip; 3F DORA/leases/T1/T2/rebinding with an external state-machine oracle. Each requires independent expected traces and their own positive/negative tests; existing tests cannot be relabeled as independent simply because they are green.

**No changes authorized:** production protocol code, canonical schema, implicit network facts, real network commands, Windows/macOS support, or required CI gates. On a confirmed discrepancy, propose a separate minimal correction instead of changing expected values to match an implementation.


## QUALITY-003 second slice: independent forwarding, VLAN, and ARP state oracles

**Pre-registered on 2026-11-23 before executing the added tests.** The topology descriptions below explicitly determine expected forwarding behavior using the known rules of Ethernet MAC learning, 802.1Q access/trunk forwarding and RFC 826 ARP exchange. These expectations are declared before observing production `EthernetFabric` or `ArpSession` output, and must not be relaxed to match the engine. Their source references remain RFC 826 and IEEE 802.1Q, with standard transparent bridging MAC learning as captured by the product's explicitly limited forwarding contract in `docs/ETHERNET_FORWARDING.md`. The contract intentionally **rejects** switch loops rather than pretending to support STP.

### 3A: Three-host single-switch forwarding, predetermined trace

Declared links: host `a:eth0` — `la` — switch `sw:p1`; host `b:eth0` — `lb` — `sw:p2`; host `c:eth0` — `lc` — `sw:p3`. Fixed endpoint MACs: A=`02:00:00:00:00:0A`, B=`02:00:00:00:00:0B`, C=`02:00:00:00:00:0C`. Initially empty learning table.

1. `a -> B`: destination B unknown; expected physical links `la, lb, lc` (flood), endpoint arrivals `b,c`, learned `A:p1`.
2. `b -> A`: A known on `p1`; expected links `lb,la`, arrival `a`, `FORWARD_UNICAST`, learned `B:p2`.
3. `c -> B`: B known on `p2`; expected links `lc,lb`, arrival `b`, `FORWARD_UNICAST`, learned `C:p3`.
4. Same physical links but reversed document array order, different diagram coordinates: expected same endpoint *sets* and switch decision under a new session. No network paths can be created or removed by changing diagram geometry.

**Negative:** if link `lb` is disabled before any session traffic, there can be no arrival at `b`, even if its MAC is the destination. The engine must not infer another link from destination MAC.

### 3B: Two-switch VLAN isolation and prohibited trunk ingress

Explicit topology from `tests/test_vlan.py::two_switches`: `a--la--s1--lt--s2--lb--b` in VLAN 10, plus `c--lc--s1--lt--s2--ld--d` in VLAN 20. `s1:t`/`s2:t` are 802.1Q trunk ports; all host-facing ports are access ports with their specified VLAN. No VLAN routing exists.

- `a` broadcasts in VLAN 10: expected `la,lt,lb`, tagged flags `false,true,false`, only `b` arrives, switch MAC learning in VLAN 10.
- `c` broadcasts in VLAN 20: expected `lc,lt,ld`, tagged flags `false,true,false`, only `d` arrives, independent switch MAC learning in VLAN 20.
- With `s2:t` allowed **only VLAN 10**, `c` broadcasts: expected `lc,lt`, no `d` arrival, exactly one `TRUNK_NOT_ALLOWED` ingress drop for VLAN 20 at `s2:t` and no VLAN-20 learning at `s2`. VLAN 10 must still cross the trunk as above.

**Negative:** VLAN 20 being denied must never silently reroute it over VLAN 10 or manufacture a receiving port.

### 3C: RFC 826 ARP over those same VLANs

Hosts `a,b,c,d` have explicit IPv4s `192.0.2.10, .20, .30, .40/24` and distinct MACs ending `0A,0B,0C,0D`. Although the IPv4 prefix is shared, **physical VLAN isolation** defines separate broadcast domains.

1. `a` ARPs for `.40` (host `d`, VLAN 20): request travels only `la,lt,lb`, **NO_REPLY**, no `.40` cache entry. Common IP subnet cannot override VLAN isolation.
2. `a` ARPs for `.20` (host `b`, VLAN 10): request `la,lt,lb`, reply `lb,lt,la`, **RESOLVED** MAC B; only `.20 -> B` is cached.
3. Same query, unchanged simulation session: **CACHE_HIT** and zero request/reply transmissions.
4. No canonical project data changes from these simulations; a new session starts without the prior ARP cache.

These are **simulated outcomes**, not claims of real NIC acceptance or complete RFC 826 compliance. Remaining QUALITY-003 work: independent IPv4 multi-hop / ICMP error traces, DHCP DORA/T1/T2 state-machine cases, and broader negative conditions. No protocol engine, project schema, CI gate or Linux platform policy is changed by this reference-test slice.
