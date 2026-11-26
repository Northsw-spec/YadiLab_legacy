# Repository-wide agent instructions

All coding agents, including Codex, MUST follow [AGENTS.md](../AGENTS.md) and
[Codex execution policy](../docs/CODEX_EXECUTION_POLICY.md). The only active
roadmap is [A0–A10](../docs/REMEDIATION_PLAN_2026-11-26.md); historical P0–P7
is CLOSED. This file is an entrypoint to existing rules, not a separate plan.

**Deliver source/test/architecture improvement before narration.** No passive
GitHub Actions polling, repeated waiting calls or wasteful duplicate full
test runs. Use targeted checks before the appropriate Required CI gate.
Do not promise background execution. One active PR; no concurrent independent
branch PR. When only external CI is pending, record exact PR/HEAD/checks and
end the active agent run rather than spending credits waiting.

**Never bypass safety to save time:** full Required status on exact HEAD,
unchanged expected main, allowed squash merge, no unresolved blocking reviews,
no dropped tests, no invented network data or protocol semantics. Docs-only
scope is proven by fail-closed git diff; runtime/test/workflow changes always
receive the full required test matrix.
