"""Policy wiring tests; not proof of actual agents' credit usage."""
from __future__ import annotations

from pathlib import Path
import re
import unittest
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "docs" / "CODEX_EXECUTION_POLICY.md"
DEPENDENTS = (
    "AGENTS.md", "README.md", "docs/MASTERPROMPT.md",
    "docs/REMEDIATION_PLAN_2026-11-26.md",
    "docs/IMPORT_SOURCE_CONTRACT.md", ".github/pull_request_template.md",
    ".github/copilot-instructions.md",
    "docs/PEDAGOGICAL_TROUBLESHOOTING_PLAN.md",
    "docs/architecture/A0_FORENSIC_BASELINE_2026-11-26.md",
    "docs/architecture/A1_GUARD_CONTRACT_2026-11-26.md",
    "docs/architecture/A2_HTTP_DISCONNECT_2026-11-26.md",
    "docs/architecture/A3_WORKSPACE_PANELS_2026-11-26.md",
    "docs/architecture/A3_WORKSPACE_REVISIONS_2026-11-26.md",
)


class CodexGovernanceTests(unittest.TestCase):
    def test_shared_policy_is_referenced_by_all_steering_dependencies(self):
        policy = POLICY.read_text(encoding="utf-8").lower()
        for phrase in ("ingen passiv väntan", "fail-closed docs-only",
                       "required", "squash", "en aktiv pr",
                       "github actions", "codex-credits"):
            self.assertIn(phrase, policy)
        for relative in DEPENDENTS:
            with self.subTest(document=relative):
                doc = (ROOT / relative).read_text(encoding="utf-8")
                self.assertIn("CODEX_EXECUTION_POLICY.md", doc)

    def test_documentation_only_lane_still_rejects_broken_local_markdown_links(self):
        # The full documentation-policy suite contains network tests; this
        # lightweight link oracle MUST run on the docs-only quick lane.
        for path in ROOT.rglob("*.md"):
            body = path.read_text(encoding="utf-8")
            for address in re.findall(r"\]\(([^)\n]+)\)", body):
                address = address.strip().split(" ", 1)[0].strip("<>")
                if address.startswith(("#", "http://", "https://", "mailto:")):
                    continue
                target = unquote(address.split("#", 1)[0].split("?", 1)[0])
                if not target:
                    continue
                resolved = (path.parent / target).resolve()
                with self.subTest(file=str(path.relative_to(ROOT)), link=address):
                    self.assertTrue(resolved.is_relative_to(ROOT))
                    self.assertTrue(resolved.is_file(), str(resolved))

    def test_single_active_roadmap_and_closed_legacy_queue(self):
        plan = (ROOT / "docs/REMEDIATION_PLAN_2026-11-26.md").read_text("utf-8")
        import_doc = (ROOT / "docs/IMPORT_SOURCE_CONTRACT.md").read_text("utf-8")
        pr = (ROOT / ".github/pull_request_template.md").read_text("utf-8")
        self.assertIn("A0–A10", plan)
        self.assertIn("REMEDIATION_PLAN_2026-11-26.md", import_doc)
        self.assertNotIn(
            "enda aktiva utvecklingsplanen** är [PEDAGOGICAL_TROUBLESHOOTING_PLAN.md]",
            import_doc)
        self.assertIn("P0–P7", import_doc)
        self.assertNotIn("ska införas i A1", pr)

    def test_ci_keeps_required_statuses_and_bounded_docs_lane(self):
        ci = (ROOT / ".github/workflows/ci.yml").read_text("utf-8")
        guard = (ROOT / ".github/workflows/architecture_guard.yml").read_text("utf-8")
        concurrency = "cancel-in-progress: " + "$" + "{{ github.event_name == 'pull_request' }}"
        for body in (ci, guard):
            self.assertIn("    branches:\n      - main\n  pull_request:", body)
            self.assertIn(concurrency, body)
            self.assertNotIn("continue-on-error: true", body)
        self.assertIn("python3 tools/ci_change_scope.py", ci)
        self.assertIn("if: steps.scope.outputs.docs_only == 'true'", ci)
        self.assertIn("test_codex_governance.py", ci)
        self.assertIn("Required architecture anti-regression backup gate", ci)
        self.assertIn("\n  architecture-guard:\n", guard)

    def test_policy_rejects_active_wait_and_unsafe_merge(self):
        source = POLICY.read_text("utf-8")
        self.assertIn("Auto-merge", source)
        self.assertIn("Ingen pollingloop", source)
        self.assertIn("A8/A9", source)
        self.assertIn("unit-tests", source)
        self.assertIn("architecture-guard", source)


if __name__ == "__main__":
    unittest.main()
