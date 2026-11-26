# Repository-wide coding-agent instructions

**LATEST MANDATORY ENGINE DECISION:** [ADR-0002](../docs/architecture/ADR_0002_FRESH_ENGINE_2026-11-26.md) supersedes selective migration of old network engine internals. Build a clean independent in-process DES engine, no imports from old EthernetFabric, ArpSession, IPv4Trace or DhcpSession. Preserve only independently tested external product and data contracts; retire legacy only after verified single cutover. No artificial full-S0/A3/A4/A5/A7 prerequisites for isolated S1-POC0. Retirement receipts allow replacing noncritical modules without weakening Required CI.


**NON-NEGOTIABLE SCOPE – 2026-11-26:** [PT-FULL-001](../docs/FULL_PACKET_TRACER_PARITY_CONTRACT.md) is the mandatory complete Cisco Packet Tracer parity contract. YadiLab MUST implement every documented and verified PT protocol, device, device CLI/GUI function, module, physical/logical workspace, realtime/simulation/PDU, all IoT/OT, Activity Wizard/auto-scoring/scripting, multiuser, ExApps/API, import/export/project formats and ALL other PT capabilities on Linux, then outperform PT in objectively validated correctness, precision, capabilities and pedagogy. **Only exclusions:** Windows/macOS, and additional accessibility/keyboard-only parity goals. NO other permanent gaps; OPEN/BLOCKED means no full-parity release. Preserve existing tests. The current implementation is PARTIAL. The sole A0–A10+S0–S12 roadmap must implement every PT-F01–F29 subfeature before S12; do not use phase labels to silently de-scope. This does not authorize VMs, IOS emulation or unsandboxed scripts.


**ADR-0001 (2026-11-26):** [Selective core rewrite](../docs/architecture/ADR_0001_CORE_REPLACEMENT_2026-11-26.md) supersedes any requirement to preserve the old synchronous execution methods. Retain product/persistence/UI/tests, replace event-incompatible forwarding and protocol clocks. Test-only S1 feasibility POCs allowed after S0+A1; one active production motor.


All coding agents, including Codex, MUST follow [AGENTS.md](../AGENTS.md),
[the single A0–A10 + S0–S12 masterplan](../docs/REMEDIATION_PLAN_2026-11-26.md),
[MASTERPROMPT](../docs/MASTERPROMPT.md),
[CODEX_EXECUTION_POLICY.md](../docs/CODEX_EXECUTION_POLICY.md),
[protocol coverage](../docs/PROTOCOL_COVERAGE_MATRIX.md) and
[the deterministic engine contract](../docs/architecture/DETERMINISTIC_ENGINE_CONTRACT.md).
Historical P0–P7 is CLOSED and not a parallel queue.

New explicit user decision 2026-11-26: build a complete, accurate, Linux-only,
deterministic in-process simulator that can measurably exceed Cisco Packet
Tracer's breadth, correctness and pedagogy. NO VM, IOS emulation, containers,
host-network scanners or FRRouting/ns-3/GNS3 runtime engines. Existing L2/ARP/
IPv4/ICMP/DHCP is limited but real; planned OSPF/BGP/STP/IPv6/TCP is NOT
implemented yet. A9 expansion is authorized within S0–S12. A8 human study
remains separately gated. S1 test-only POC may begin after S0+A1; production cutover still requires go/no-go and relevant A3/A4/A5/A7 contracts.

One authoritative project validator and one simulation engine. Per-protocol
RFC/IEEE/IEC version, deterministic time/state, independent positive,
negative and contradictory test oracles, explicit device/port/link facts.
Never fake protocol operation, packets, CLI, RFC compliance or user learning.

Deliver useful code/tests/architecture before narration. One active PR,
targeted preflight before full Required CI, no passive Actions polling or
credit-wasting repeated test suites. Preserve import provenance, explicit
Save/Open/SHA, session stale guards, architecture ratchet and Linux-only
support. Required unit-tests and architecture-guard SUCCESS on exact final
HEAD, all applicable extra checks, safe squash, never bypass main rules.
