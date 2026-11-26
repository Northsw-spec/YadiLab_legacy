# A1 – Architecture guard, contracts and required-check installation

**Date:** 2026-11-26  
**Active plan:** [A0–A10 remediation roadmap](../REMEDIATION_PLAN_2026-11-26.md)  
**Status:** **DONE / ACCEPTED (2026-11-26).** [PR #170](https://github.com/Northsw-spec/YadiLab/pull/170) is merged; [PR #173](https://github.com/Northsw-spec/YadiLab/pull/173) independently demonstrated that a failing Required `architecture-guard` blocks merge although `unit-tests` succeeds. No probe was merged.  
**Baseline:** `main@fcf81716285ef3a4d927d3ac05556b5c2fb6f7f5`, [A0 report](A0_FORENSIC_BASELINE_2026-11-26.md) and A0 Git-blob manifest.  
**Scope:** G1–G7, C03–C05.

**Operativ styrning vid fortsatt Codex-arbete:** [CODEX_EXECUTION_POLICY.md](../CODEX_EXECUTION_POLICY.md). Avbryt äldre PR-run vid ny commit, men hoppa aldrig över separat Required `architecture-guard`. Modul-/testantal i historisk A1-rapport är ursprungliga värden; aktuell CI inventerar manifestet. No network simulator, UI, persistence schema or protocol code was intentionally changed.

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

`.github/workflows/architecture_guard.yml` executes a separate job named **`architecture-guard`** on every pull request and push to protected `main` (not also a duplicate push on each PR branch), without PR path filters or conditional skips:

1. Run `tests/test_architecture_guard.py`, including deliberate invalid fixtures.
2. Run `tools/architecture_guard.py --base-ref BASE_SHA` on PRs (or without a base on branch pushes).
3. Fail on any contract or policy discrepancy; publish a compact architecture report in the Actions job summary even if validation fails.

**Defense in depth retained:** the existing `unit-tests` workflow executes the same `tools/architecture_guard.py` with the exact PR-base ratchet, and `tests/test_ci_integrity.py` checks it remains attached. The **separate** `architecture-guard` is also Required, so both controls independently protect the branch.

**Actual Required status independently confirmed:** active [main ruleset ID 27419615](https://github.com/Northsw-spec/YadiLab/rules/27419615) lists both `unit-tests` and `architecture-guard` as **Required** from GitHub Actions integration ID `15368`, with strict status checks enabled. [PR #173](https://github.com/Northsw-spec/YadiLab/pull/173) deliberately added `exit 17` **only** to the independent workflow after normal validation. On exact HEAD `90e5ab61e23ee8a824c42f48f253d33e28cd76ce`, both `unit-tests` succeeded (push [45854012171](https://github.com/Northsw-spec/YadiLab/actions/runs/45854012171), PR [45854035243](https://github.com/Northsw-spec/YadiLab/actions/runs/45854035243)), while both independent architecture checks failed (push [45854011534](https://github.com/Northsw-spec/YadiLab/actions/runs/45854011534), PR [45854035286](https://github.com/Northsw-spec/YadiLab/actions/runs/45854035286)). GitHub API explicitly reported `mergeable_state=blocked`; #173 was **closed without merge**. This proves that the independently Required guard, not just the duplicate backup gate, is enforced.

## G5. Named source ownership

`.github/CODEOWNERS` assigns policy, frontend, importer, ICMP and workflow paths to the actual repository owner `@Northsw-spec`. The branch ruleset currently requires **zero** reviews; CODEOWNERS is ownership documentation, not a proof of independent human approval. Do not enable a review gate that would permanently deadlock a sole-author repository. Any increased budget, destructive module change or relaxed guard still requires a separate explicit project-owner decision and compatible protected workflow.

## G6. Behavioral parity

The `unit-tests` Required job retains full Python, JavaScript, real Chromium, X11 PRIMARY, ELK and durable Save/Open acceptance for all non-documentation changes. For a strictly verified Markdown-only diff, it runs bounded governance and supply-chain checks instead; `architecture-guard` and the architecture backup gate always run. Missing/unknown scope is fail-closed to full acceptance. A1 itself changed no runtime code. Later refactors must retain the exact positive and negative fixture oracles, actual HTTP/API behavior, SHAs, stale-guards and session lifecycle; architecture checks do not replace behavioral checks.

## G7. Ongoing report and anti-regression policy

The guard writes machine-readable `architecture-report.json` to the job workspace and publishes the report as a GitHub Actions step summary. Each accepted PR must record line budgets, module count, dependency count, ownership and negative tests. Re-check the state of the required ruleset after each batch of five merged PRs or a major feature batch. A missing workflow, test file, registered module or protected source path causes failure. A rule requiring the job to run prevents a deleted workflow from silently satisfying branch protection.

## Test matrix

`tests/test_architecture_guard.py` has **17** independent synthetic demonstrations for: valid baseline, removed ICMP session file, import cycle, orphan, presentation→storage dependency, forged source owner and owner-label laundering attempt, duplicated ping presenter, copied session state, fraudulent raised budget even with matching source change, deleted regression test, removed guard script, removed module contract, weakened public exports, duplicate backend validator, legitimate decreased code budget, and removed required test from policy.

**A1 acceptance ledger (all verified at 2026-11-26):**

- [x] Required GitHub Actions `architecture-guard` passed on merged [PR #170](https://github.com/Northsw-spec/YadiLab/pull/170)'s exact final HEAD.
- [x] Existing `unit-tests` passed on the exact same PR #170 HEAD.
- [x] GitHub API confirmed both Required checks (integration `15368`, strict).
- [x] Real negative probes: [#172](https://github.com/Northsw-spec/YadiLab/pull/172) (budget raise fails both checks); [#173](https://github.com/Northsw-spec/YadiLab/pull/173) (separate architecture fails while `unit-tests` succeeds, GitHub merge blocked). Neither merged.
- [x] Implementation PR #170 squash-merged; main protected with no bypass.
- [x] Main verified and A0–A10 roadmap updated in A1 acceptance closeout PR; A2 NEXT.

**Ongoing failure policy:** If a future repository change removes either Required check or modifies its integration, do not regard the guard as effective: mark A1 regression **BLOCKED** and restore the ruleset before dependent work. Static guards and passing workflow runs do not themselves prove semantic correctness; retain real browser/network/save tests for all subsequent PRs.
