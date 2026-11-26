# Repository-wide coding-agent instructions

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
remains separately gated. S1 coding waits for proven A3/A4/A5/A7 completion.

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
