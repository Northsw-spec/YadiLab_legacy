"""Hidden routed-ping fault training using actual Echo/IPv4/ARP/L2 proofs."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from network_core.icmp_investigation import (
    IcmpInvestigation, IcmpInvestigationRegistry, KINDS, _candidates,
)
from network_core.icmp_ping import EchoExchange
from network_core.model import ProjectValidationError
from network_core.server import LabHTTPServer
from network_core.storage import ProjectStore
from network_core.troubleshooting import compare_fault
from test_icmp_echo import routed_reply_lab


def scenario(kind):
    return IcmpInvestigation(
        routed_reply_lab(), "a", "eth0", "203.0.113.20", 5, _test_kind=kind)


def measure_routed_fault(case, kind):
    # Fixed selections for the first proven candidate of each fixture category.
    if kind == "IPV4_PREFIX_MISMATCH":
        case.probe("route", {"nodeId": "r", "destinationIpv4": "192.0.2.10"})
        return case.probe("port", {"nodeId": "r", "portId": "wan"})
    route = case.probe("route", {"nodeId": "a", "destinationIpv4": "203.0.113.20"})
    if kind == "CABLE_DOWN":
        return case.probe("link", {"linkId": "la"})
    if kind in ("PORT_SHUTDOWN", "VLAN_MISMATCH"):
        return case.probe("port" if kind == "PORT_SHUTDOWN" else "vlan",
                          {"nodeId": "sw-left", "portId": "a"})
    if kind == "IPV4_HOST_ADDRESS_MISMATCH":
        return case.probe("port", {"nodeId": "b", "portId": "eth0"})
    return route


class IcmpInvestigationTests(unittest.TestCase):
    def test_return_route_diagnosis_requires_evidence_in_the_failed_direction(self):
        project = routed_reply_lab()
        # Select a deterministic return-side fault from the reversed node order.
        project["nodes"].reverse()
        case = IcmpInvestigation(project, "a", "eth0", "203.0.113.20", 5,
                                 _test_kind="STATIC_ROUTE_MISSING")
        ping = case.probe("ping", {})["observation"]
        self.assertEqual((ping["requestStatus"], ping["replyStatus"]),
                         ("DELIVERED", "NO_ROUTE"))
        case.probe("address", {})
        case.probe("route", {"nodeId": "a", "destinationIpv4": "203.0.113.20"})
        case.probe("route", {"nodeId": "r", "destinationIpv4": "192.0.2.10"})
        self.assertFalse(case.state()["canDiagnose"])
        with self.assertRaisesRegex(ProjectValidationError, "relevant"):
            case.diagnose("STATIC_ROUTE_MISSING")
        self.assertEqual(case.state()["diagnosisAttempts"], 0)
        with self.assertRaisesRegex(ProjectValidationError, "correct diagnosis"):
            case.repair()
        reverse = case.probe("route", {"nodeId": "b", "destinationIpv4": "192.0.2.10"})
        self.assertEqual(reverse["observation"]["status"], "NO_ROUTE")
        self.assertTrue(reverse["canDiagnose"])
        self.assertTrue(case.diagnose("STATIC_ROUTE_MISSING")["correct"])
        self.assertTrue(case.repair()["replyMatched"])

    def test_each_hidden_cause_proven_by_failure_and_restored_echo(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                case = scenario(kind)
                before = deepcopy(case.project)
                state = case.state()
                self.assertNotIn(kind, json.dumps(state))
                self.assertNotIn("fault", json.dumps(state))
                self.assertEqual(state["dhcpAddressOrigin"], "UNKNOWN")
                self.assertEqual(state["dhcpCheck"], "NOT_VERIFIED")
                self.assertFalse(state["canDiagnose"])
                source = case.probe("address", {})["observation"]
                self.assertEqual(source["documentedIpv4"], "192.0.2.10/24")
                self.assertEqual(source["origin"], "UNKNOWN")
                self.assertEqual(source["dhcpStatus"], "NOT_VERIFIED")
                ping = case.probe("ping", {})["observation"]
                self.assertNotEqual(ping["status"], "REPLIED")
                self.assertFalse(ping["replyMatched"])
                self.assertEqual(ping["source"], "SIMULATED")
                self.assertTrue(ping["requestStatus"])
                route = case.probe(
                    "route", {"nodeId": "a", "destinationIpv4": "203.0.113.20"}
                )["observation"]
                self.assertIn(route["status"], ("MATCH", "NO_ROUTE"))
                self.assertEqual(route["source"], "SIMULATED_CONFIG")
                link = case.probe("link", {"linkId": "la"})["observation"]
                self.assertTrue(link["documentedEnabled"])
                self.assertIn(link["observedEnabled"], (True, False))
                port = case.probe("port", {"nodeId": "sw-left", "portId": "a"})["observation"]
                self.assertTrue(port["documentedEnabled"])
                self.assertIsNone(port["documentedIpv4"])
                self.assertIsNone(port["observedIpv4"])
                self.assertEqual(port["source"], "SIMULATED_CONFIG")
                vlan = case.probe("vlan", {"nodeId": "sw-left", "portId": "a"})["observation"]
                self.assertEqual(vlan["documentedVlan"], {"mode": "access", "vlan": 10})
                self.assertEqual(vlan["source"], "SIMULATED_CONFIG")
                measure_routed_fault(case, kind)
                self.assertTrue(case.state()["canDiagnose"])
                wrong = next(x for x in KINDS if x != kind)
                rejected = case.diagnose(wrong)
                self.assertFalse(rejected["correct"])
                self.assertNotIn(kind, json.dumps(rejected))
                with self.assertRaisesRegex(ProjectValidationError, "correct diagnosis"):
                    case.repair()
                approved = case.diagnose(kind)
                self.assertTrue(approved["correct"])
                restored = case.repair()
                self.assertEqual(restored["status"], "RECOVERED")
                self.assertNotEqual(restored["failedEchoStatus"], "REPLIED")
                self.assertEqual(restored["restoredEchoStatus"], "REPLIED")
                self.assertTrue(restored["replyMatched"])
                self.assertEqual(restored["faultCategory"], kind)
                self.assertEqual(restored["repair"]["scope"], "PREVIEW_ONLY")
                self.assertEqual(case.project, before)
                self.assertEqual(case.state()["dhcpCheck"], "NOT_VERIFIED")
                with self.assertRaisesRegex(ProjectValidationError, "already repaired"):
                    case.probe("ping", {})
                with self.assertRaisesRegex(ProjectValidationError, "already repaired"):
                    case.repair()

    def test_report_requires_verified_recovery_for_all_seven_causes(self):
        expected = {
            "CABLE_DOWN": ("Kabel", "ARP"),
            "PORT_SHUTDOWN": ("Switchport", "ARP"),
            "VLAN_MISMATCH": ("Access-VLAN", "ARP"),
            "STATIC_ROUTE_MISSING": ("Statisk route", "NO_ROUTE"),
            "IPV4_PREFIX_MISMATCH": ("IPv4-prefix", "NO_ROUTE"),
            "STATIC_NEXT_HOP_UNREACHABLE": ("Next-hop", "ARP"),
            "IPV4_HOST_ADDRESS_MISMATCH": ("IPv4-adress", "ARP"),
        }
        self.assertEqual(set(expected), set(KINDS))
        for kind, (cause, evidence) in expected.items():
            with self.subTest(kind=kind):
                project = routed_reply_lab()
                original = json.dumps(project, sort_keys=True)
                case = IcmpInvestigation(project, "a", "eth0", "203.0.113.20", 5,
                                         _test_kind=kind)
                self.assertNotIn("report", case.state())
                case.probe("ping", {})
                measure_routed_fault(case, kind)
                self.assertFalse(case.diagnose(next(k for k in KINDS if k != kind))["correct"])
                self.assertNotIn("report", case.state())
                self.assertTrue(case.diagnose(kind)["correct"])
                self.assertNotIn("report", case.state())
                result = case.repair()
                report = result["report"]
                self.assertEqual(result["status"], "RECOVERED")
                self.assertEqual(set(report), {"symptom", "rootCause", "evidence",
                                               "action", "verification"})
                self.assertIn(cause, report["rootCause"])
                self.assertIn(evidence, report["evidence"])
                self.assertIn("Echo", report["symptom"])
                point = case._fault.get("linkId", case._fault.get("routeId",
                        case._fault.get("portId")))
                self.assertIn(point, report["rootCause"])
                self.assertIn(point, report["action"])
                self.assertIn("REPLIED", report["verification"])
                self.assertIn("matchande Echo Reply", report["verification"])
                self.assertEqual(result["repair"]["scope"], "PREVIEW_ONLY")
                self.assertEqual(json.dumps(project, sort_keys=True), original)

    def test_failed_recovery_has_no_report_or_positive_conclusion(self):
        case = scenario("CABLE_DOWN")
        case.probe("ping", {})
        case.probe("route", {"nodeId": "a", "destinationIpv4": "203.0.113.20"})
        case.probe("link", {"linkId": "la"})
        case.diagnose("CABLE_DOWN")
        real_ping = EchoExchange.ping
        calls = 0

        def fail_restoration(exchange, *args):
            nonlocal calls
            calls += 1
            result = real_ping(exchange, *args)
            if calls == 2:
                return {**result, "status": "REQUEST_FAILED", "replyMatched": False}
            return result

        with patch.object(EchoExchange, "ping", fail_restoration):
            result = case.repair()
        self.assertEqual(result["status"], "NOT_VERIFIED")
        self.assertIsNone(result["report"])
        self.assertIsNone(result["faultCategory"])
        self.assertIsNone(result["repair"])
        self.assertFalse(case.state()["repaired"])

    def test_hidden_switch_port_shutdown_measured_and_recovered(self):
        case = scenario("PORT_SHUTDOWN")
        fault = case._fault
        self.assertEqual(fault["type"], "PORT_DISABLED")
        measured = case.probe("port", {
            "nodeId": fault["nodeId"], "portId": fault["portId"],
        })["observation"]
        self.assertEqual(measured["source"], "SIMULATED_CONFIG")
        self.assertTrue(measured["documentedEnabled"])
        self.assertFalse(measured["observedEnabled"])
        self.assertNotIn("PORT_SHUTDOWN", json.dumps(case.state()))
        self.assertNotEqual(case.probe("ping", {})["observation"]["status"], "REPLIED")
        case.probe("route", {"nodeId": "a", "destinationIpv4": "203.0.113.20"})
        self.assertTrue(case.state()["canDiagnose"])
        self.assertTrue(case.diagnose("PORT_SHUTDOWN")["correct"])
        restored = case.repair()
        self.assertEqual(restored["status"], "RECOVERED")
        self.assertEqual(restored["repair"]["action"], "RE_ENABLE_PORT")
        self.assertEqual(restored["repair"]["scope"], "PREVIEW_ONLY")
        self.assertTrue(restored["replyMatched"])

    def test_hidden_ipv4_prefix_fault_uses_documented_peer_and_real_echo(self):
        case = scenario("IPV4_PREFIX_MISMATCH")
        fault = case._fault
        self.assertEqual(fault["type"], "IPV4_PREFIX_CHANGED")
        self.assertEqual(fault["nodeId"], "r")
        self.assertIn(fault["portId"], ("wan", "lan"))
        observed = case.probe("port", {
            "nodeId": fault["nodeId"], "portId": fault["portId"],
        })["observation"]
        self.assertEqual(observed["source"], "SIMULATED_CONFIG")
        self.assertTrue(observed["documentedEnabled"])
        self.assertEqual(observed["documentedIpv4"].split("/")[0],
                         observed["observedIpv4"].split("/")[0])
        self.assertNotEqual(observed["documentedIpv4"], observed["observedIpv4"])
        self.assertNotIn("IPV4_PREFIX_MISMATCH", json.dumps(case.state()))
        original = deepcopy(case.project)
        failed = case.probe("ping", {})["observation"]
        self.assertNotEqual(failed["status"], "REPLIED")
        self.assertFalse(failed["replyMatched"])
        case.probe("route", {"nodeId": "r", "destinationIpv4": "203.0.113.20"})
        self.assertFalse(case.state()["canDiagnose"])
        case.probe("route", {"nodeId": "r", "destinationIpv4": "192.0.2.10"})
        self.assertTrue(case.state()["canDiagnose"])
        self.assertFalse(case.diagnose("STATIC_ROUTE_MISSING")["correct"])
        self.assertTrue(case.diagnose("IPV4_PREFIX_MISMATCH")["correct"])
        recovery = case.repair()
        self.assertEqual(recovery["status"], "RECOVERED")
        self.assertEqual(recovery["repair"]["action"], "RESTORE_IPV4")
        self.assertEqual(recovery["repair"]["expectedIpv4"],
                         observed["documentedIpv4"])
        self.assertEqual(recovery["repair"]["scope"], "PREVIEW_ONLY")
        self.assertTrue(recovery["replyMatched"])
        self.assertEqual(case.project, original)

    def test_hidden_host_address_fault_has_arp_failure_and_exact_recovery(self):
        original = routed_reply_lab()
        before = json.dumps(original, sort_keys=True)
        case = scenario("IPV4_HOST_ADDRESS_MISMATCH")
        self.assertNotIn("IPV4_HOST_ADDRESS_MISMATCH", json.dumps(case.state()))
        self.assertNotIn("newIpv4", json.dumps(case.state()))
        self.assertEqual(case._fault["nodeId"], "b")
        self.assertEqual(case._fault["portId"], "eth0")
        port = case.probe("port", {"nodeId": "b", "portId": "eth0"})["observation"]
        documented, observed = port["documentedIpv4"], port["observedIpv4"]
        self.assertNotEqual(documented.split("/")[0], observed.split("/")[0])
        self.assertEqual(documented.split("/")[1], observed.split("/")[1])
        ping = case.probe("ping", {})["observation"]
        self.assertEqual(ping["requestStatus"], "ARP_FAILED")
        self.assertFalse(ping["replyMatched"])
        self.assertTrue(any(step["arpStatus"] == "NO_REPLY"
                            and step["nextHopIpv4"] == "203.0.113.20"
                            for step in ping["requestSteps"]))
        self.assertEqual(case.probe("route", {"nodeId": "a",
            "destinationIpv4": "203.0.113.20"})["observation"]["status"], "MATCH")
        self.assertFalse(case.diagnose("IPV4_PREFIX_MISMATCH")["correct"])
        self.assertTrue(case.diagnose("IPV4_HOST_ADDRESS_MISMATCH")["correct"])
        repaired = case.repair()
        self.assertEqual(repaired["status"], "RECOVERED")
        self.assertEqual(repaired["repair"]["expectedIpv4"], documented)
        self.assertEqual(json.dumps(original, sort_keys=True), before)
        self.assertEqual(case.project, original)

    def test_host_address_fault_rejects_invalid_occupied_and_unproven_addresses(self):
        project = routed_reply_lab()
        fault = {"type": "IPV4_HOST_ADDRESS_CHANGED", "nodeId": "b",
                 "portId": "eth0", "newIpv4": "203.0.113.21"}
        for address in ("203.0.113.1", "203.0.113.0", "203.0.113.255",
                        "192.0.2.21", "203.0.113.20", "203.0.113.021", "bad"):
            with self.subTest(address=address), self.assertRaises(ProjectValidationError):
                compare_fault(project, "a", "eth0", "203.0.113.20", 5,
                              101, 1, {**fault, "newIpv4": address})
        with self.assertRaises(ProjectValidationError):
            compare_fault(project, "a", "eth0", "203.0.113.20", 5,
                          101, 1, {**fault, "newPrefix": 25})
        unavailable = deepcopy(project)
        next(n for n in unavailable["nodes"] if n["id"] == "b")["ports"][0]["ipv4"] = "203.0.113.20/31"
        with self.assertRaises(ProjectValidationError):
            IcmpInvestigation(unavailable, "a", "eth0", "203.0.113.20", 5,
                              _test_kind="IPV4_HOST_ADDRESS_MISMATCH")

    def test_hidden_static_next_hop_must_fail_arp_and_recover_exact_route(self):
        case = scenario("STATIC_NEXT_HOP_UNREACHABLE")
        before = deepcopy(case.project)
        fault = case._fault
        self.assertEqual(fault["type"], "STATIC_NEXT_HOP_CHANGED")
        self.assertIn((fault["nodeId"], fault["routeId"]),
                      {("a", "via-router"), ("b", "return-to-a")})
        destination = ("203.0.113.20" if fault["nodeId"] == "a"
                       else "192.0.2.10")
        route = case.probe("route", {
            "nodeId": fault["nodeId"], "destinationIpv4": destination,
        })["observation"]
        self.assertEqual(route["status"], "MATCH")
        selected = route["selectedRoute"]
        self.assertEqual(selected["routeId"], fault["routeId"])
        documented = next(r for r in route["documentedStaticRoutes"]
                          if r["id"] == fault["routeId"])
        self.assertNotEqual(selected["nextHop"], documented["nextHop"])
        self.assertEqual(selected["nextHop"], fault["newNextHop"])
        self.assertEqual(selected["destination"], documented["destination"])
        self.assertNotIn("STATIC_NEXT_HOP_UNREACHABLE", json.dumps(case.state()))
        ping = case.probe("ping", {})["observation"]
        self.assertNotEqual(ping["status"], "REPLIED")
        self.assertFalse(ping["replyMatched"])
        self.assertIn("ARP_FAILED", (ping["requestStatus"], ping["replyStatus"]))
        steps = ping["requestSteps"] + ping["replySteps"]
        self.assertTrue(any(step["arpStatus"] == "NO_REPLY" for step in steps))
        case.probe("address", {})
        self.assertTrue(case.state()["canDiagnose"])
        self.assertFalse(case.diagnose("STATIC_ROUTE_MISSING")["correct"])
        self.assertTrue(case.diagnose("STATIC_NEXT_HOP_UNREACHABLE")["correct"])
        result = case.repair()
        self.assertEqual(result["status"], "RECOVERED")
        self.assertEqual(result["restoredEchoStatus"], "REPLIED")
        self.assertTrue(result["replyMatched"])
        self.assertEqual(result["repair"]["action"], "RESTORE_NEXT_HOP")
        self.assertEqual(result["repair"]["expectedNextHop"], documented["nextHop"])
        self.assertEqual(result["repair"]["scope"], "PREVIEW_ONLY")
        self.assertEqual(case.project, before)

    def test_next_hop_candidates_reject_unused_routes_and_configured_peers(self):
        project = routed_reply_lab()
        next(n for n in project["nodes"] if n["id"] == "r")["staticRoutes"] = [{
            "id": "unrelated", "destination": "198.51.100.0/24",
            "nextHop": "192.0.2.10", "outPort": "wan",
        }]
        baseline = EchoExchange(project).ping(
            "a", "eth0", "203.0.113.20", 5, 101, 1)
        self.assertEqual(baseline["status"], "REPLIED")
        candidates = [fault for kind, fault in _candidates(project, baseline)
                      if kind == "STATIC_NEXT_HOP_UNREACHABLE"]
        self.assertTrue(candidates)
        self.assertFalse(any(f["nodeId"] == "r" for f in candidates))
        allocated = {port["ipv4"].split("/")[0]
                     for node in project["nodes"] for port in node["ports"]
                     if port["ipv4"] is not None}
        for fault in candidates:
            self.assertNotIn(fault["newNextHop"], allocated)
            original = next(route for node in project["nodes"]
                            if node["id"] == fault["nodeId"]
                            for route in node["staticRoutes"]
                            if route["id"] == fault["routeId"])
            self.assertNotEqual(fault["newNextHop"], original["nextHop"])

    def test_cable_diagnosis_requires_measurement_of_the_affected_link(self):
        case = scenario("CABLE_DOWN")
        case.probe("ping", {})
        case.probe("route", {"nodeId": "a", "destinationIpv4": "203.0.113.20"})
        unrelated = case.probe("link", {"linkId": "lb"})
        self.assertTrue(unrelated["observation"]["observedEnabled"])
        self.assertFalse(unrelated["canDiagnose"])
        with self.assertRaisesRegex(ProjectValidationError, "relevant"):
            case.diagnose("CABLE_DOWN")
        measured = case.probe("link", {"linkId": "la"})
        self.assertFalse(measured["observation"]["observedEnabled"])
        self.assertTrue(measured["canDiagnose"])
        self.assertTrue(case.diagnose("CABLE_DOWN")["correct"])

    def test_invalid_inputs_no_probe_recorded_or_canonical_mutation(self):
        case = scenario("CABLE_DOWN")
        original = case.state()
        original_project = deepcopy(case.project)
        bad = [
            ("ping", {"extra": 1}),
            ("address", {"portId": "eth0"}),
            ("route", {}),
            ("route", {"nodeId": "missing", "destinationIpv4": "203.0.113.20"}),
            ("route", {"nodeId": "a", "destinationIpv4": "8.8.8.8"}),
            ("route", {"nodeId": "sw-left", "destinationIpv4": "203.0.113.20"}),
            ("route", {"nodeId": "a", "destinationIpv4": "203.0.113.20", "extra": 1}),
            ("link", {"linkId": "wrong"}),
            ("link", {"linkId": True}),
            ("port", {"nodeId": "missing", "portId": "a"}),
            ("port", {"nodeId": "sw-left"}),
            ("port", {"nodeId": True, "portId": "a"}),
            ("port", {"nodeId": "sw-left", "portId": "missing"}),
            ("port", {"nodeId": "sw-left", "portId": "a", "extra": 1}),
            ("port", {"nodeId": "r", "portId": "missing"}),
            ("port", {"nodeId": "r", "portId": None}),
            ("vlan", {"nodeId": "a", "portId": "eth0"}),
            ("vlan", {"nodeId": "sw-left", "portId": "missing"}),
            ("vlan", {"nodeId": "sw-left"}),
            ("bad", {}),
            (True, {}),
        ]
        for kind, target in bad:
            with self.subTest(kind=kind, target=target), self.assertRaises(ProjectValidationError):
                case.probe(kind, target)
            self.assertEqual(case.state(), original)
            self.assertEqual(case.project, original_project)
        with self.assertRaisesRegex(ProjectValidationError, "real failed ping"):
            case.diagnose("CABLE_DOWN")
        with self.assertRaisesRegex(ProjectValidationError, "correct diagnosis"):
            case.repair()

    def test_failed_baseline_not_admitted_and_no_fake_connected_reachability(self):
        project = routed_reply_lab()
        next(n for n in project["nodes"] if n["id"] == "b")["staticRoutes"].clear()
        with self.assertRaisesRegex(ProjectValidationError, "initial Echo"):
            IcmpInvestigation(project, "a", "eth0", "203.0.113.20", 5)
        for ttl in (1, 0, 256, True, "5"):
            with self.subTest(ttl=ttl), self.assertRaises(ProjectValidationError):
                IcmpInvestigation(routed_reply_lab(), "a", "eth0", "203.0.113.20", ttl)
        with self.assertRaises(ProjectValidationError):
            IcmpInvestigation(routed_reply_lab(), "a", "eth0", "not-ip", 5)

    def test_no_eligible_fault_refuses_exercise(self):
        p = routed_reply_lab()
        p["links"] = [x for x in p["links"] if x["id"] == "la"]
        with self.assertRaises(ProjectValidationError):
            IcmpInvestigation(p, "a", "eth0", "203.0.113.20", 5)

    def test_no_cause_leak_and_guess_limit(self):
        case = scenario("STATIC_ROUTE_MISSING")
        for name, target in (
            ("ping", {}), ("address", {}),
            ("route", {"nodeId": "a", "destinationIpv4": "203.0.113.20"}),
        ):
            case.probe(name, target)
        for attempt in range(1, 4):
            result = case.diagnose("CABLE_DOWN")
            self.assertFalse(result["correct"])
            self.assertTrue(result["canDiagnose"])  # Existing evidence remains.
            self.assertEqual(result["canSubmitDiagnosis"], attempt < 3)
            self.assertEqual(result["maxDiagnosisAttempts"], 3)
            self.assertNotIn("STATIC_ROUTE_MISSING", json.dumps(result))
        with self.assertRaisesRegex(ProjectValidationError, "maximum guesses"):
            case.diagnose("STATIC_ROUTE_MISSING")

    def test_third_correct_guess_unlocks_repair_but_no_later_guess(self):
        case = scenario("STATIC_ROUTE_MISSING")
        case.probe("ping", {})
        case.probe("route", {"nodeId": "b", "destinationIpv4": "192.0.2.10"})
        case.probe("port", {"nodeId": "b", "portId": "eth0"})
        self.assertTrue(case.state()["canSubmitDiagnosis"])
        for _ in range(2):
            self.assertFalse(case.diagnose("CABLE_DOWN")["correct"])
        accepted = case.diagnose("STATIC_ROUTE_MISSING")
        self.assertTrue(accepted["correct"])
        self.assertTrue(accepted["repairAvailable"])
        self.assertFalse(accepted["canSubmitDiagnosis"])
        self.assertEqual(accepted["diagnosisAttempts"], 3)
        with self.assertRaisesRegex(ProjectValidationError, "already recorded"):
            case.diagnose("CABLE_DOWN")
        restored = case.repair()
        self.assertEqual(restored["status"], "RECOVERED")
        self.assertTrue(restored["replyMatched"])

    def test_numeric_equivalent_json_projects_fail_exact_session_snapshot(self):
        from network_core.simulation import _signature

        project = routed_reply_lab()
        changed = deepcopy(project)
        self.assertIs(type(project["nodes"][0]["x"]), int)
        changed["nodes"][0]["x"] = float(project["nodes"][0]["x"])
        # Python dict equality masks the JSON type change (0 == 0.0).
        self.assertEqual(changed, project)
        self.assertNotEqual(_signature(changed), _signature(project))

        registry = IcmpInvestigationRegistry()
        with patch("network_core.icmp_investigation.secrets.randbelow", return_value=0):
            started = registry.start(project, "a", "eth0", "203.0.113.20", 5)
        session_id = started["sessionId"]
        for operation in (
                lambda: registry.probe(session_id, changed, "address", {}),
                lambda: registry.diagnose(session_id, changed, "CABLE_DOWN"),
                lambda: registry.repair(session_id, changed)):
            with self.assertRaisesRegex(ProjectValidationError, "project changed"):
                operation()
        self.assertEqual(registry._get(session_id).state()["observations"], 0)
        original = registry.probe(session_id, project, "address", {})
        self.assertEqual(original["observation"]["source"], "DOCUMENTED")
        self.assertEqual(original["observations"], 1)
        self.assertEqual(registry.stop(session_id), {"status": "STOPPED"})

    def test_project_bound_opaque_multi_session_and_restart_semantics(self):
        p = routed_reply_lab()
        registry = IcmpInvestigationRegistry()
        with patch("network_core.icmp_investigation.secrets.randbelow", return_value=0):
            first = registry.start(p, "a", "eth0", "203.0.113.20", 5)
            second = registry.start(p, "a", "eth0", "203.0.113.20", 5)
        self.assertNotEqual(first["sessionId"], second["sessionId"])
        self.assertNotIn("fault", json.dumps(first))
        self.assertNotIn("fault", json.dumps(second))
        changed = deepcopy(p)
        changed["links"][0]["enabled"] = False
        with self.assertRaisesRegex(ProjectValidationError, "project changed"):
            registry.probe(first["sessionId"], changed, "ping", {})
        with self.assertRaisesRegex(ProjectValidationError, "project changed"):
            registry.diagnose(first["sessionId"], changed, "CABLE_DOWN")
        with self.assertRaisesRegex(ProjectValidationError, "project changed"):
            registry.repair(first["sessionId"], changed)
        self.assertEqual(registry.probe(first["sessionId"], p, "address", {})
                         ["observation"]["dhcpStatus"], "NOT_VERIFIED")
        self.assertEqual(registry.probe(second["sessionId"], p, "ping", {})
                         ["observation"]["replyMatched"], False)
        self.assertEqual(registry.stop(first["sessionId"]), {"status": "STOPPED"})
        with self.assertRaisesRegex(ProjectValidationError, "unknown or expired"):
            registry.probe(first["sessionId"], p, "ping", {})


class IcmpInvestigationHttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = ProjectStore(self.root)
        self.server = LabHTTPServer(("127.0.0.1", 0), self.store)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.temp.cleanup()

    def post(self, route, body):
        request = Request(self.url + "/api/icmp/investigation/" + route,
                          data=json.dumps(body).encode(),
                          headers={"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=10) as response:
                return response.status, json.loads(response.read())
        except HTTPError as error:
            return error.code, json.loads(error.read())

    def test_http_numeric_equivalent_stale_project_returns_422_without_writes(self):
        p = routed_reply_lab()
        saved = self.store.save("snapshot", p)
        path = self.root / "snapshot.yadilab"
        before = path.read_bytes()
        with patch("network_core.icmp_investigation.secrets.randbelow", return_value=0):
            status, opened = self.post("start", {
                "project": p, "sourceNode": "a", "sourcePort": "eth0",
                "destinationIpv4": "203.0.113.20", "ttl": 5,
            })
        self.assertEqual(status, 200)
        sid = opened["sessionId"]
        changed = deepcopy(p)
        changed["nodes"][0]["x"] = float(p["nodes"][0]["x"])
        self.assertEqual(changed, p)
        calls = (
            ("probe", {"sessionId": sid, "project": changed,
                       "probe": "address", "target": {}}),
            ("diagnose", {"sessionId": sid, "project": changed,
                          "diagnosis": "CABLE_DOWN"}),
            ("repair", {"sessionId": sid, "project": changed}),
        )
        for route, body in calls:
            with self.subTest(route=route):
                code, response = self.post(route, body)
                self.assertEqual(code, 422)
                self.assertEqual(response["error"], "INVALID_PROJECT")
                self.assertIn("project changed", response["message"])
                self.assertEqual(path.read_bytes(), before)
                self.assertEqual(self.store.read("snapshot")["sha256"], saved["sha256"])
        self.assertEqual(self.server.icmp_investigations._get(sid).state()["observations"], 0)
        code, response = self.post("probe", {
            "sessionId": sid, "project": p, "probe": "address", "target": {},
        })
        self.assertEqual(code, 200)
        self.assertEqual(response["observations"], 1)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual([entry["filename"] for entry in self.store.list()], ["snapshot"])

    def test_real_http_observations_repair_and_byte_identical_project(self):
        p = routed_reply_lab()
        self.store.save("original", p)
        path = self.root / "original.yadilab"
        raw = path.read_bytes()
        with patch("network_core.icmp_investigation.secrets.randbelow", return_value=0):
            status, opened = self.post("start", {
                "project": p, "sourceNode": "a", "sourcePort": "eth0",
                "destinationIpv4": "203.0.113.20", "ttl": 5,
            })
        self.assertEqual(status, 200)
        self.assertNotIn("fault", json.dumps(opened))
        sid = opened["sessionId"]
        base = {"sessionId": sid, "project": p}
        def call(route, **fields):
            return self.post(route, {**base, **fields})
        status, address = call("probe", probe="address", target={})
        self.assertEqual(status, 200)
        self.assertEqual(address["observation"]["dhcpStatus"], "NOT_VERIFIED")
        self.assertEqual(call("probe", probe="ping", target={})[1]
                         ["observation"]["replyMatched"], False)
        status, routing = call("probe", probe="route", target={
            "nodeId": "a", "destinationIpv4": "203.0.113.20",
        })
        self.assertEqual(status, 200)
        self.assertEqual(routing["observation"]["documentedStaticRoutes"],
                         p["nodes"][0]["staticRoutes"])
        self.assertEqual(routing["observation"]["selectedRoute"]["nextHop"],
                         "192.0.2.1")
        status, port_status = call("probe", probe="port", target={
            "nodeId": "sw-left", "portId": "a",
        })
        self.assertEqual(status, 200)
        self.assertTrue(port_status["observation"]["documentedEnabled"])
        self.assertEqual(port_status["observation"]["source"], "SIMULATED_CONFIG")
        status, router_ipv4 = call("probe", probe="port", target={
            "nodeId": "r", "portId": "lan",
        })
        self.assertEqual(status, 200)
        self.assertEqual(router_ipv4["observation"]["documentedIpv4"],
                         "203.0.113.1/24")
        self.assertEqual(router_ipv4["observation"]["source"], "SIMULATED_CONFIG")
        self.assertFalse(router_ipv4["canDiagnose"])
        status, blocked = call("diagnose", diagnosis="CABLE_DOWN")
        self.assertEqual(status, 422)
        self.assertNotIn("CABLE_DOWN", json.dumps(blocked))
        self.assertEqual(call("repair")[0], 422)
        status, measured = call("probe", probe="link", target={"linkId": "la"})
        self.assertEqual(status, 200)
        self.assertTrue(measured["canDiagnose"])
        self.assertEqual(measured["diagnosisAttempts"], 0)
        self.assertEqual(call("diagnose", diagnosis="STATIC_ROUTE_MISSING")[1]["correct"],
                         False)
        status, confirmed = call("diagnose", diagnosis="CABLE_DOWN")
        self.assertEqual(status, 200)
        self.assertTrue(confirmed["correct"])
        status, restored = call("repair")
        self.assertEqual(status, 200)
        self.assertEqual(restored["status"], "RECOVERED")
        self.assertEqual(restored["restoredEchoStatus"], "REPLIED")
        self.assertTrue(restored["replyMatched"])
        self.assertEqual(restored["faultCategory"], "CABLE_DOWN")
        self.assertEqual(path.read_bytes(), raw)
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),
                         hashlib.sha256(raw).hexdigest())
        self.assertEqual(self.store.read("original")["project"], p)

    def test_http_exact_shapes_invalid_project_and_server_restart(self):
        p = routed_reply_lab()
        status, started = self.post("start", {
            "project": p, "sourceNode": "a", "sourcePort": "eth0",
            "destinationIpv4": "203.0.113.20", "ttl": 5,
        })
        self.assertEqual(status, 200)
        sid = started["sessionId"]
        base = {"sessionId": sid, "project": p, "probe": "address", "target": {}}
        changed = deepcopy(p)
        changed["links"][0]["enabled"] = False
        tests = [
            ("start", {"project": p, "sourceNode": "a", "sourcePort": "eth0",
                       "destinationIpv4": "203.0.113.20", "ttl": 5, "extra": 1}),
            ("start", {"project": p, "sourceNode": "a", "sourcePort": "eth0",
                       "destinationIpv4": "203.0.113.20", "ttl": True}),
            ("probe", {**base, "extra": 1}),
            ("probe", {**base, "probe": "unsupported"}),
            ("probe", {**base, "project": changed}),
            ("probe", {**base, "sessionId": "not-a-session"}),
            ("diagnose", {"sessionId": sid, "project": p, "diagnosis": None}),
            ("repair", {"sessionId": sid, "project": p, "extra": True}),
        ]
        for route, payload in tests:
            with self.subTest(route=route):
                code, error = self.post(route, payload)
                self.assertEqual(code, 422)
                self.assertEqual(error["error"], "INVALID_PROJECT")
        self.assertEqual(self.server.icmp_investigations._get(sid).state()["observations"], 0)
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.server = LabHTTPServer(("127.0.0.1", 0), ProjectStore(self.root))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        code, error = self.post("probe", base)
        self.assertEqual(code, 422)
        self.assertIn("unknown or expired", error["message"])
