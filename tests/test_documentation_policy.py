"""Guard the governing documentation against stale roadmaps and broken local links.

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
    def test_closed_pedagogy_program_preserves_contract_without_active_phase(self):
        self.assertTrue(PLAN.is_file())
        body = PLAN.read_text(encoding="utf-8")
        for label in EXACT_HEADINGS:
            self.assertIn(label, body)
        for phase in range(8):
            self.assertIn(f"**P{phase} –", body)
        # P0–P7 was formally closed by explicit user decision on 2026-11-26.
        # Preserve the educational contract, but reject regression to an
        # automatically active roadmap or implicit next phase.
        self.assertIn("P0–P7 **CLOSED (2026-11-26)**", body)
        self.assertIn("**Nästa etapp: INGEN BESLUTAD.**", body)
        self.assertNotIn("enda aktiva utvecklingsplanen", body.lower())
        for path in (ROOT / "AGENTS.md", ROOT / "README.md",
                     ROOT / "docs" / "MASTERPROMPT.md"):
            with self.subTest(path=str(path.relative_to(ROOT))):
                text = path.read_text(encoding="utf-8")
                self.assertIn("2026-11-26", text)
                self.assertIn("automatiskt", text.lower())
                self.assertNotIn("enda aktiva utvecklingsplanen", text.lower())

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

    def test_independent_icmp_reply_ttl_is_not_labeled_shared(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("TTL per riktning", html)
        for token in ("ping-reply-ttl", "probe-reply-ttl",
                      "Echo Request TTL", "simulerat 64"):
            self.assertIn(token, html)

    def test_active_packet_views_label_simulation_as_simulation(self):
        # Static checks of precise user-facing claims. These do not certify
        # external live networks; Chromium exercises the rendered UI separately.
        app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        presenters = (ROOT / "web" / "features" / "diagnostics" /
                      "presenters.js").read_text(encoding="utf-8")
        icmp_panel = (ROOT / "web" / "features" / "diagnostics" /
                      "icmp-investigation-panel.js").read_text(encoding="utf-8")
        for source, forbidden in (
            (app, ("fysisk(a) överföring(ar)", "Faktiska överföringar:",
                   "Verkligt observerade kablar:", "riktig DHCPACK", "verklig DHCPACK")),
            (html, ("riktiga kodade DHCP-meddelanden", "VERKLIG DHCPREQUEST",
                    "Skicka riktigt DHCPREQUEST", "Mät faktisk kabel-/länkstatus",
                    "Verkligt ICMP Echo", "verkligt simulerade")),
            (presenters, ("fysisk(a) överföring(ar)",
                          "Ingen faktisk paketöverföring",
                          "ingen faktisk datagramöverföring")),
            (icmp_panel, ("Skicka sedan verklig ICMP", "faktisk tur-och-retur Echo Reply")),
        ):
            for phrase in forbidden:
                with self.subTest(label=phrase):
                    self.assertNotIn(phrase, source)
        self.assertIn("Simulerade kabelöverföringar:", app)
        self.assertIn("simulerade kabelöverföringar", presenters)
        self.assertIn("ej levererade felpaket redovisas separat", presenters)
        self.assertNotIn("ICMP-fel visas endast när", presenters)
        self.assertIn("simulerat DHCPACK", html)
        self.assertIn("Simulerat ICMP Echo över ARP", html)
        self.assertIn("simulerat ICMP Echo", icmp_panel)

    def test_dhcp_icmp_contracts_do_not_deny_present_capabilities(self):
        from network_core.dhcp import DhcpSession
        from network_core.dhcp_registry import DhcpLabSession
        from network_core.icmp_ping import EchoExchange
        from network_core.icmp_errors import ICMPError

        self.assertTrue(callable(DhcpSession.renew))
        self.assertTrue(callable(DhcpLabSession.renew))
        self.assertTrue(callable(EchoExchange.ping))
        self.assertTrue(callable(ICMPError.parse))
        dhcp = (ROOT / "docs" / "DHCP_DORA.md").read_text(encoding="utf-8")
        self.assertNotIn("eller RFC-förnyelsemekanism finns", dhcp)
        self.assertIn("T1- och T2-förnyelse", dhcp)
        self.assertIn("/api/dhcp/session/renew", dhcp)
        self.assertIn("Ingen realtidsbaserad nedräkning, automatisk", dhcp)
        self.assertIn("ny ACK-bekräftad simulerad BOUND-lease", dhcp)
        self.assertNotIn("verkligt T1-/T2-DHCPREQUEST", dhcp)
        source = (ROOT / "network_core" / "icmp_ping.py").read_text(encoding="utf-8")
        codec = (ROOT / "network_core" / "ipv4_packet.py").read_text(encoding="utf-8")
        trace = (ROOT / "network_core" / "ipv4.py").read_text(encoding="utf-8")
        self.assertNotIn("No synthetic RTT, ICMP Time Exceeded, or default route", source)
        self.assertIn("explicit default routes", source)
        self.assertIn("ICMP Time Exceeded (11/0)", source)
        self.assertIn("ICMPv4 Echo and the bounded ICMP router-error", codec)
        self.assertIn("router-error *candidates* only", trace)

    def test_saved_vlan_and_arp_docs_match_real_native_session_behavior(self):
        from network_core.arp import ArpSession
        from test_vlan_persistence import persisted_topology

        # Independent end-to-end confirmation: an explicitly configured VLAN
        # takes effect even without a vlan_ports argument. The target on VLAN
        # 10 is resolved; a host on VLAN 20 is not silently reached.
        session = ArpSession(persisted_topology())
        result = session.resolve("a", "eth0", "192.0.2.20")
        self.assertEqual(result["status"], "RESOLVED")
        self.assertEqual(result["requestTransmissions"][1]["vlanId"], 10)
        self.assertEqual(session.resolve("a", "eth0", "192.0.2.40")["status"],
                         "NO_REPLY")

        arp = (ROOT / "docs" / "ARP.md").read_text(encoding="utf-8")
        vlan = (ROOT / "docs" / "VLAN.md").read_text(encoding="utf-8")
        self.assertNotIn("ingen beständig ARP-session eller interaktiv flerpaketssimulering", arp)
        self.assertIn("Interaktiv flerpaketssimulering finns", arp)
        self.assertIn("/api/simulation/start", arp)
        self.assertNotIn("Omitting `vlan_ports` retains legacy unsegmented ARP.", vlan)
        self.assertIn("ArpSession(project)` is VLAN-aware", vlan)
        self.assertIn("only when the project also contains no persisted", vlan)
        self.assertIn("not packet captures from physical cables", vlan)

    def test_router_icmp_sent_and_session_capacity_claims_match_native_behavior(self):
        from network_core.icmp_ping import EchoExchange
        from test_icmp_echo import routed_reply_lab

        # A router-generated Type 11 packet was transmitted and received, so
        # icmpSent cannot truthfully mean "only Echo was sent".
        ping = EchoExchange(routed_reply_lab()).ping(
            "a", "eth0", "203.0.113.20", 1, 12, 44)
        self.assertEqual(ping["status"], "REQUEST_FAILED")
        self.assertEqual(ping["icmpError"]["type"], 11)
        self.assertEqual(ping["icmpError"]["status"], "RECEIVED")
        self.assertTrue(ping["icmpError"]["trace"]["icmpSent"])
        self.assertTrue(ping["request"]["icmpSent"])  # Echo request was sent before TTL expired.

        ipv4 = (ROOT / "docs" / "IPV4_FORWARDING.md").read_text(encoding="utf-8")
        session = (ROOT / "docs" / "SIMULATION_SESSION.md").read_text(
            encoding="utf-8")
        self.assertNotIn("`icmpSent` is true only if a protocol-1 ICMP Echo-containing", ipv4)
        self.assertIn("Echo **or one of the supported router-error messages**", ipv4)
        self.assertIn("It does **not** mean a response was received", ipv4)
        self.assertIn("**Stop** releases a session's slot", session)
        self.assertIn("**Reset** clears the operation count", session)
        self.assertIn("A simulated Ethernet send", session)
        self.assertNotIn("Stop or Reset is required to free capacity", session)

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
