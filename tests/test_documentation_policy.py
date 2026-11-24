"""Guard the active documentation against stale roadmaps and broken local links.

This test checks document structure and navigability, not the truth of every
technical claim. Actual behavior remains subject to code and real test results.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs" / "PEDAGOGICAL_TROUBLESHOOTING_PLAN.md"
RETIRED = (
    "QUALITY_IMPROVEMENT_PLAN.md",
    "QUALITY_IMPROVEMENT_HISTORY.md",
    "ELK_IMPLEMENTATION_PLAN.md",
    "IMPLEMENTATION_STATUS.md",
    "QUALITY_003_VERIFICATION_REPORT.md",
    "QUALITY_004_4A_ARCHITECTURE_AUDIT.md",
    "QUALITY_005_FRONTEND_STALE_ORACLES.md",
    "QUALITY_005_HTTP_SESSION_RACE_ORACLES.md",
    "QUALITY_005_STORAGE_FAILURE_ORACLES.md",
    "SOURCE_INTEGRITY_AUDIT_2026-11-24.md",
    "SVG_CAMERA_NAVIGATION_RESEARCH.md",
    "SVG_PERFORMANCE_2026-11-22.md",
    "ARCHITECTURE.md",
    "PROTOCOL_REFERENCE_MATRIX.md",
)
EXACT_HEADINGS = (
    "Om [observerat]:",
    "Då [vad det faktiskt betyder]:",
    "Möjliga orsaker [inte fastställda/hypoteser]:",
    "Vad detta inte bevisar:",
    "Nästa diagnostiska steg:",
    "Förväntat resultat och tolkning:",
    "Åtgärd [först efter fastställd orsak]:",
    "Verifiering [fungerar det nu?]:",
    "Beviskälla och begränsningar:",
)


class DocumentationPolicyTests(unittest.TestCase):
    def test_single_authoritative_pedagogy_plan_is_present(self):
        self.assertTrue(PLAN.is_file())
        body = PLAN.read_text(encoding="utf-8")
        for label in EXACT_HEADINGS:
            self.assertIn(label, body)
        for phase in range(8):
            self.assertIn(f"**P{phase} –", body)
        self.assertIn("enda aktiva utvecklingsplanen", body.lower())

    def test_retired_markdown_is_absent_and_never_referenced(self):
        markdown_files = list(ROOT.rglob("*.md"))
        self.assertGreater(len(markdown_files), 10)
        for filename in RETIRED:
            self.assertFalse((ROOT / "docs" / filename).exists(), filename)
        for path in markdown_files:
            body = path.read_text(encoding="utf-8")
            for filename in RETIRED:
                with self.subTest(path=str(path.relative_to(ROOT)), old=filename):
                    self.assertNotIn(filename, body)

    def test_source_code_has_no_broken_links_to_retired_documents(self):
        # Deliberately exclude this policy test: its RETIRED tuple is the ban list.
        # Vendor assets are external third-party material, not our own docs.
        source_suffixes = {".py", ".js", ".mjs", ".html", ".css", ".yml", ".yaml", ".json"}
        for path in ROOT.rglob("*"):
            if not path.is_file() or path == Path(__file__).resolve():
                continue
            if "vendor" in path.relative_to(ROOT).parts or path.suffix not in source_suffixes:
                continue
            body = path.read_text(encoding="utf-8")
            for filename in RETIRED:
                with self.subTest(path=str(path.relative_to(ROOT)), old=filename):
                    self.assertNotIn("docs/" + filename, body)

    def test_module_docs_do_not_deny_present_simulation_capabilities(self):
        from network_core.model import EVIDENCE_SCHEMA_VERSION
        from network_core.simulation import SimulationSession
        from network_core.icmp_ping import EchoExchange

        self.assertEqual(EVIDENCE_SCHEMA_VERSION, "1.4")
        self.assertTrue(callable(SimulationSession.run))
        self.assertTrue(callable(EchoExchange.ping))
        ethernet = (ROOT / "docs" / "ETHERNET_FORWARDING.md").read_text("utf-8")
        self.assertIn("[SIMULATION_SESSION.md](SIMULATION_SESSION.md)", ethernet)
        self.assertIn("[IPV4_FORWARDING.md](IPV4_FORWARDING.md)", ethernet)

    def test_relative_markdown_links_point_to_real_files(self):
        # This is a deliberately narrow repository-file check, not a general
        # Markdown, HTTP, GitHub anchor or external-link validator.
        for path in ROOT.rglob("*.md"):
            body = path.read_text(encoding="utf-8")
            for candidate in re.findall(r"\]\(([^)\n]+)\)", body):
                address = candidate.strip().split(" ", 1)[0].strip("<>")
                if address.startswith(("#", "https://", "http://", "mailto:")):
                    continue
                target = unquote(address.split("#", 1)[0])
                if not target:
                    continue
                resolved = (path.parent / target).resolve()
                with self.subTest(path=str(path.relative_to(ROOT)), link=address):
                    self.assertTrue(resolved.is_relative_to(ROOT))
                    self.assertTrue(resolved.is_file(), str(resolved))


if __name__ == "__main__":
    unittest.main()
