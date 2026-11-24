"""The guided ICMP case validates a specific intervention and direction."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from network_core.icmp_investigation import IcmpInvestigation, _lesson_echo
from network_core.icmp_ping import EchoExchange
from network_core.model import ProjectValidationError
from network_core.troubleshooting import compare_fault
import test_icmp_investigation
from test_icmp_echo import routed_reply_lab


FIXTURE = Path(__file__).resolve().parents[1] / "web/fixtures/icmp-echo-lesson.json"
ARGS = ("a", "eth0", "203.0.113.20", 5)
REVERSE = {"nodeId": "b", "destinationIpv4": "192.0.2.10"}
PORT = {"nodeId": "b", "portId": "eth0"}
FAULT = {"type": "STATIC_ROUTE_REMOVED", "nodeId": "b", "routeId": "return-to-a"}


def project():
    return json.loads(FIXTURE.read_bytes())


def start():
    return IcmpInvestigation(project(), *ARGS, lesson="echo-reply")


def ready_case():
    case = start()
    case.probe("ping", {})
    case.probe("route", REVERSE)
    case.probe("port", PORT)
    return case


class GuidedIcmpLessonTests(unittest.TestCase):
    def test_fixture_matches_proven_routed_reply_lab(self):
        fixture = project()
        reference = routed_reply_lab()
        reference["name"] = fixture["name"]
        self.assertEqual(fixture, reference)
        baseline = EchoExchange(fixture).ping(*ARGS, 20, 1)
        self.assertEqual(baseline["status"], "REPLIED")
        self.assertEqual(baseline["request"]["receiver"], {"node": "b", "port": "eth0"})
        self.assertEqual(baseline["reply"]["receiver"], {"node": "a", "port": "eth0"})
        self.assertTrue(baseline["replyMatched"])

    def test_restarts_choose_the_exact_intervention_without_randomness(self):
        with patch("network_core.icmp_investigation.secrets.randbelow",
                   side_effect=AssertionError("lesson must not choose randomly")):
            for _ in range(3):
                case = start()
                self.assertEqual(case._fault, FAULT)
                expected = deepcopy(case.project)
                next(node for node in expected["nodes"] if node["id"] == "b")["staticRoutes"].clear()
                self.assertEqual(case._faulted, expected)
                self.assertEqual(case.project, project())
                ping = case.probe("ping", {})["observation"]
                self.assertEqual(ping["requestStatus"], "DELIVERED")
                self.assertEqual(ping["requestReceiver"], {"node": "b", "port": "eth0"})
                self.assertEqual((ping["status"], ping["replyStatus"]), ("REPLY_FAILED", "NO_ROUTE"))
                self.assertEqual(ping["replySteps"], [])
                self.assertFalse(ping["replyMatched"])

    def test_modified_missing_or_invalid_fixture_rejected(self):
        for field in ("name", "links", "nodes"):
            with self.subTest(field=field):
                modified = project()
                if field == "name":
                    modified[field] = "Changed"
                else:
                    modified[field].pop()
                with self.assertRaises(ProjectValidationError):
                    IcmpInvestigation(modified, *ARGS, lesson="echo-reply")
        with patch("network_core.icmp_investigation._LESSON_FIXTURE") as fixture:
            fixture.read_bytes.side_effect = FileNotFoundError
            with self.assertRaisesRegex(ProjectValidationError, "fixture unavailable"):
                start()
        with patch("network_core.icmp_investigation._LESSON_FIXTURE") as fixture:
            fixture.read_bytes.return_value = b'{"nodes":[],"nodes":[]}'
            with self.assertRaisesRegex(ProjectValidationError, "fixture unavailable"):
                start()
        for args in (("b", "eth0", "192.0.2.10", 5), ("a", "eth0", "203.0.113.1", 5)):
            with self.assertRaisesRegex(ProjectValidationError, "invalid lesson or endpoints"):
                IcmpInvestigation(project(), *args, lesson="echo-reply")

    def test_forward_route_arp_and_ttl_failures_are_not_the_lesson(self):
        forward = compare_fault(project(), *ARGS, 20, 1, {
            "type": "STATIC_ROUTE_REMOVED", "nodeId": "a", "routeId": "via-router",
        })["faulted"]
        self.assertEqual(forward["status"], "REQUEST_FAILED")
        self.assertIsNone(forward["reply"])
        self.assertFalse(_lesson_echo(forward, matched=False))

        arp = compare_fault(project(), *ARGS, 20, 2, {
            "type": "STATIC_NEXT_HOP_CHANGED", "nodeId": "b", "routeId": "return-to-a",
            "newNextHop": "203.0.113.254",
        })["faulted"]
        ttl = EchoExchange(project()).ping(*ARGS, 20, 3, reply_ttl=1)
        for result, expected in ((arp, "ARP_FAILED"), (ttl, "TTL_EXPIRED")):
            with self.subTest(expected=expected):
                self.assertEqual(result["request"]["status"], "DELIVERED")
                self.assertEqual(result["reply"]["status"], expected)
                self.assertFalse(_lesson_echo(result, matched=False))

    def test_repair_reports_only_independently_verified_recovery(self):
        case = ready_case()
        self.assertTrue(case.diagnose("STATIC_ROUTE_MISSING")["correct"])
        alternative = compare_fault(project(), *ARGS, 20, 4, {
            "type": "STATIC_ROUTE_REMOVED", "nodeId": "a", "routeId": "via-router",
        })
        with patch.object(case, "_compare_lesson", return_value=alternative):
            failure = case.repair()
        self.assertEqual(failure["status"], "NOT_VERIFIED")
        self.assertFalse(failure["replyMatched"])
        for key in ("faultCategory", "repair", "report"):
            self.assertIsNone(failure[key])
        self.assertNotIn("verification", failure)
        recovered = case.repair()
        self.assertEqual(recovered["restoredEchoStatus"], "REPLIED")
        self.assertTrue(recovered["replyMatched"])
        self.assertEqual(recovered["repair"]["expectedRoute"], {
            "id": "return-to-a", "destination": "192.0.2.0/24",
            "nextHop": "203.0.113.1", "outPort": "eth0",
        })
        self.assertEqual(recovered["verification"]["replyReceiver"], {"node": "a", "port": "eth0"})

    def test_direction_port_and_no_spoilers_over_http(self):
        http = test_icmp_investigation.IcmpInvestigationHttpTests()
        http.setUp()
        self.addCleanup(http.tearDown)
        fixture = project()
        saved = http.store.save("lesson", fixture)
        path = http.root / "lesson.yadilab"
        original = path.read_bytes()
        query = dict(project=fixture, sourceNode=ARGS[0], sourcePort=ARGS[1],
                     destinationIpv4=ARGS[2], ttl=ARGS[3], lesson="echo-reply")

        for bad in ({"lesson": None}, {"lesson": "unknown"}, {"fault": FAULT}, {"project": None}):
            self.assertEqual(http.post("start", {**query, **bad})[0], 422)

        def no_answer(payload):
            encoded = json.dumps(payload)
            for value in ("return-to-a", "STATIC_ROUTE_MISSING", "RESTORE_STATIC_ROUTE"):
                self.assertNotIn(value, encoded)

        code, opening = http.post("start", query)
        self.assertEqual(code, 200)
        self.assertEqual(opening["openingObservation"], {
            "requestStatus": "DELIVERED", "requestReceiver": {"node": "b", "port": "eth0"},
            "replyMatched": False, "source": "SIMULATED",
        })
        self.assertFalse(opening["canDiagnose"])
        self.assertNotIn("NO_ROUTE", json.dumps(opening))
        no_answer(opening)
        fields = dict(sessionId=opening["sessionId"], project=fixture)

        def call(operation, status=200, **body):
            code, result = http.post(operation, {**fields, **body})
            self.assertEqual(code, status, result)
            return result

        for op, body in (("diagnose", {"diagnosis": "STATIC_ROUTE_MISSING"}), ("repair", {})):
            no_answer(call(op, 422, **body))
        changed = deepcopy(fixture)
        changed["name"] += "!"
        no_answer(call("probe", 422, project=changed, probe="ping", target={}))
        no_answer(call("probe", probe="ping", target={}))
        for wrong in ({"nodeId": "a", "destinationIpv4": "192.0.2.10"},
                      {"nodeId": "b", "destinationIpv4": "203.0.113.20"}):
            probe = call("probe", probe="route", target=wrong)
            self.assertFalse(probe["canDiagnose"])
            no_answer(probe)
        wrong_port = call("probe", probe="port", target={"nodeId": "a", "portId": "eth0"})
        self.assertFalse(wrong_port["canDiagnose"])
        self.assertFalse(call("probe", probe="port", target=PORT)["canDiagnose"])
        no_answer(call("diagnose", 422, diagnosis="STATIC_ROUTE_MISSING"))
        lookup = call("probe", probe="route", target=REVERSE)
        self.assertTrue(lookup["canDiagnose"])
        self.assertEqual(lookup["observation"]["status"], "NO_ROUTE")
        self.assertIsNone(lookup["observation"]["selectedRoute"])
        self.assertEqual(lookup["observation"]["source"], "SIMULATED_CONFIG")
        no_answer(lookup)
        wrong = call("diagnose", diagnosis="STATIC_NEXT_HOP_UNREACHABLE")
        self.assertFalse(wrong["correct"])
        no_answer(wrong)
        no_answer(call("repair", 422))
        correct = call("diagnose", diagnosis="STATIC_ROUTE_MISSING")
        self.assertTrue(correct["correct"])
        no_answer(correct)
        recovered = call("repair")
        self.assertEqual((recovered["status"], recovered["failedEchoStatus"],
                          recovered["restoredEchoStatus"], recovered["replyMatched"]),
                         ("RECOVERED", "REPLY_FAILED", "REPLIED", True))
        self.assertEqual(recovered["repair"]["scope"], "PREVIEW_ONLY")
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(http.store.read("lesson")["sha256"], saved["sha256"])
        self.assertEqual(http.store.read("lesson")["project"], fixture)
