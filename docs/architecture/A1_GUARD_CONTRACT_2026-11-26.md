# A1 – Architecture guard, contracts and required-check installation

**Date:** 2026-11-26  
**Active plan:** [A0–A10 remediation roadmap](../REMEDIATION_PLAN_2026-11-26.md)  
**Status:** **IN_PROGRESS / NOT ACCEPTED** until the `architecture-guard` check is actually marked **Required** in the active main ruleset and a failing check demonstrably blocks merge.  
**Baseline:** `main@fcf81716285ef3a4d927d3ac05556b5c2fb6f7f5`, [A0 report](A0_FORENSIC_BASELINE_2026-11-26.md) and A0 Git-blob manifest.  
**Scope:** G1–G7, C03–C05. No network simulator, UI, persistence schema or protocol code was intentionally changed.

## G1. Monotonic budgets

`architecture/baseline.json` declares exactly the physical source-line counts and current responsibility counters:

| File | Accepted physical lines | Rule |
|---|---:|---|
| `web/app.js` | 2,977 | Must match checked-in budget and never increase versus PR base |
| `network_core/import_plan.py` | 966 | Same |
| `network_core/icmp_investigation.py` | 843 | Same |
| `app.js` direct `.addEventListener(` occurrences | 96 | Must not increase versus base |
| `app.js` DOM-related lexical references | 104 | Must not increase versus base |

These are *regression tripwires*, not objective quality or runtime-correctness scores. A legitimate removal must reduce the accepted budget in the **same PR**. The guard compares PR policy against the actual existing policy on the base commit (`git show BASE_SHA:architecture/baseline.json`) and rejects budget increases. The initial installation may use the verified A0 predecessor commit without an existing policy; later missing-base-policy situations are fatal. A future architecture exception needs a **separate explicit authorized design decision**, not a self-edited larger budget.

## G2. Structural and ownership boundaries

`tools/architecture_guard.py` verifies current source rather than trusting the historical A0 file list:

- Every first-party ES module is registered in the authoritative frontend contract, imported from the entrypoint, free of cycles, and contains only declared ES imports/exports.
- Presentation modules cannot import project storage. Session controllers cannot depend on project storage, presentation or DOM utility. The app composition root cannot be imported downstream. **Module layer is derived from its actual file path**, not trusted from the editable JSON owner's label; a forged owner therefore cannot launder a forbidden dependency.
- Existing top-level `app.js` function and state-binding inventories are frozen; adding a copied presenter/controller function or new state binding fails. The counters forbid increasing direct event registration and DOM references in `app.js`.
- Python source is parsed using **Python AST**, checking the single final project validator and single ICMP EchoExchange implementation and preventing import-stage dependencies on HTTP.
- Native JS syntax remains verified by the existing `npm run check` and real Chromium functional tests.

**Limitations:** Static JavaScript imports/exports and top-level declaration checks are conservative **lexical scans**, not a complete JS AST, dataflow analysis or proof that a variable was not copied into an inner closure. Proper code review, real Chromium and behavior tests remain mandatory. This A1 is designed to catch repeated architectural degradation, not to claim that any future change is formally proven correct.

## G3. Module contracts

`frontend_contracts` in `architecture/baseline.json` registers all 18 current JavaScript modules with an owner, exact relative imports and their public exports. New modules and tests must be added to the inventory. Removing a module, test, public API or owner is rejected when compared with the base policy; new module dependencies are checked against the layer matrix. Later A3/A4 refactors must preserve compatibility and document changes in the same PR. The A0 inventory and `tests/test_web_import_graph.py` remain retained and independently testable.

## G4. Independent CI status and branch rules

`.github/workflows/architecture_guard.yml` executes a separate job named **`architecture-guard`** on every push and pull request, without path filters or conditional skips:

1. Run `tests/test_architecture_guard.py`, including deliberate invalid fixtures.
2. Run `tools/architecture_guard.py --base-ref BASE_SHA` on PRs (or without a base on branch pushes).
3. Fail on any contract or policy discrepancy; publish a compact architecture report in the Actions job summary even if validation fails.

**Defense in depth already active in this PR:** the existing `unit-tests` workflow (already Required by main ruleset) now executes the same `tools/architecture_guard.py` with the exact PR-base ratchet, and `tests/test_ci_integrity.py` checks that this step is not detached. This gives a **required functional gate** against architectural regression even before the separately named check is configured Required. It does **not** satisfy the explicit A1 acceptance criterion for independently required status.

**Crucial remaining deployment task:** GitHub repository administrator must add the exact `architecture-guard` context from the GitHub Actions installation alongside `unit-tests` in the active main branch ruleset: [main ruleset ID 27419615](https://github.com/Northsw-spec/YadiLab/rules/27419615). Preserve strict required checks and protected linear history. After adding, confirm the API returns both contexts with the correct app integration ID, and verify that the status is genuinely required (missing or failing check causes merge to be blocked). **A green workflow alone is not a required status. Do not mark A1 DONE without this evidence.**

## G5. Named source ownership

`.github/CODEOWNERS` assigns policy, frontend, importer, ICMP and workflow paths to the actual repository owner `@Northsw-spec`. The branch ruleset currently requires **zero** reviews; CODEOWNERS is ownership documentation, not a proof of independent human approval. Do not enable a review gate that would permanently deadlock a sole-author repository. Any increased budget, destructive module change or relaxed guard still requires a separate explicit project-owner decision and compatible protected workflow.

## G6. Behavioral parity

The existing `unit-tests` job still tests Python, JavaScript, real Chromium, X11 PRIMARY, ELK and durable Save/Open. A1 itself changes no runtime code. Later refactors must retain the exact positive and negative fixture oracles, actual HTTP/API behavior, SHAs, stale-guards and session lifecycle; architecture checks do not replace behavioral checks.

## G7. Ongoing report and anti-regression policy

The guard writes machine-readable `architecture-report.json` to the job workspace and publishes the report as a GitHub Actions step summary. Each accepted PR must record line budgets, module count, dependency count, ownership and negative tests. Re-check the state of the required ruleset after each batch of five merged PRs or a major feature batch. A missing workflow, test file, registered module or protected source path causes failure. A rule requiring the job to run prevents a deleted workflow from silently satisfying branch protection.

## Test matrix

`tests/test_architecture_guard.py` has **17** independent synthetic demonstrations for: valid baseline, removed ICMP session file, import cycle, orphan, presentation→storage dependency, forged source owner and owner-label laundering attempt, duplicated ping presenter, copied session state, fraudulent raised budget even with matching source change, deleted regression test, removed guard script, removed module contract, weakened public exports, duplicate backend validator, legitimate decreased code budget, and removed required test from policy.

**A1 completion evidence required:**

- [ ] Required GitHub Actions `architecture-guard` is green on the **final PR HEAD**.
- [ ] Existing `unit-tests` is green on the **same exact final PR HEAD**.
- [ ] GitHub API confirms the active main ruleset requires both contexts.
- [ ] Deliberate invalid change is demonstrated to fail the new job; verify required-check merge blocking without modifying protected main.
- [ ] PR is mergeable and squash-merged with no unauthorized bypass.
- [ ] Main status verified and A0–A10 roadmap updated to A1 DONE / next A2.

**Failure policy:** If ruleset editing is unavailable, retain an honest `BLOCKED_REQUIRED_RULESET_UPDATE` status. A1 implementation may be merged as partial infrastructure after successful functional CI; that does **not** authorize A2, A3 or A4 or certify A1 complete.
