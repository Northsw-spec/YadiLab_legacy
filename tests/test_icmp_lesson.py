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
NEXT_HOP_FAULT = {**FAULT, "type": "STATIC_NEXT_HOP_CHANGED", "newNextHop": "203.0.113.254"}


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
        # Dict equality accepts 0 == 0.0, but the lesson's exact canonical
        # fixture (and its session signature) must not accept that edit.
        for numeric in (0.0, -0.0):
            with self.subTest(x=numeric):
                changed = project()
                changed["nodes"][0]["x"] = numeric
                self.assertEqual(changed, project())
                with self.assertRaisesRegex(ProjectValidationError, "unchanged fixture"):
                    IcmpInvestigation(changed, *ARGS, lesson="echo-reply")
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

    def test_two_cases_share_the_opening_and_recover_from_distinct_native_failures(self):
        baseline_project = project()
        outcomes = []
        for lesson, fault, expected, alternate in (
            ("echo-reply", FAULT, "NO_ROUTE", "ARP_FAILED"),
            ("echo-reply-b", NEXT_HOP_FAULT, "ARP_FAILED", "NO_ROUTE"),
        ):
            with self.subTest(lesson=lesson):
                comparison = compare_fault(baseline_project, *ARGS, 20, 1, fault)
                self.assertEqual(comparison["status"], "FAULT_CONFIRMED")
                for stage in ("baseline", "restored"):
                    self.assertEqual(comparison[stage]["status"], "REPLIED")
                    self.assertTrue(comparison[stage]["replyMatched"])
                    self.assertEqual(comparison[stage]["reply"]["receiver"], {"node": "a", "port": "eth0"})
                failed = comparison["faulted"]
                self.assertEqual(failed["request"]["status"], "DELIVERED")
                self.assertEqual(failed["request"]["receiver"], {"node": "b", "port": "eth0"})
                self.assertEqual(failed["status"], "REPLY_FAILED")
                self.assertFalse(failed["replyMatched"])
                self.assertEqual(failed["reply"]["status"], expected)
                self.assertFalse(failed["reply"]["icmpSent"])
                self.assertFalse(_lesson_echo(failed, matched=False, reply_status=alternate))
                if lesson == "echo-reply-b":
                    step, = failed["reply"]["steps"]
                    self.assertEqual(step["arp"]["status"], "NO_REPLY")
                    self.assertTrue(step["arp"]["requestTransmissions"])
                    self.assertEqual(step["arp"]["replyTransmissions"], [])
                    self.assertEqual(step["ipv4Transmissions"], [])
                    self.assertEqual(step["nextHopIpv4"], "203.0.113.254")
                else:
                    self.assertEqual(failed["reply"]["steps"], [])
                case = IcmpInvestigation(baseline_project, *ARGS, lesson=lesson)
                self.assertEqual(case._fault, fault)
                outcomes.append(case.state()["openingObservation"])
        self.assertEqual(outcomes[0], outcomes[1])
        self.assertEqual(baseline_project, project())

    def test_direction_port_and_no_spoilers_over_http(self):
        for lesson in ("echo-reply", "echo-reply-b"):
            with self.subTest(lesson=lesson):
                self._assert_direction_port_and_no_spoilers(lesson)

    def _assert_direction_port_and_no_spoilers(self, lesson):
        case_b = lesson == "echo-reply-b"
        right_diagnosis = "STATIC_NEXT_HOP_UNREACHABLE" if case_b else "STATIC_ROUTE_MISSING"
        wrong_diagnosis = "STATIC_ROUTE_MISSING" if case_b else "STATIC_NEXT_HOP_UNREACHABLE"
        http = test_icmp_investigation.IcmpInvestigationHttpTests()
        http.setUp()
        self.addCleanup(http.tearDown)
        fixture = project()
        saved = http.store.save("lesson", fixture)
        path = http.root / "lesson.yadilab"
        original = path.read_bytes()
        query = dict(project=fixture, sourceNode=ARGS[0], sourcePort=ARGS[1],
                     destinationIpv4=ARGS[2], ttl=ARGS[3], lesson=lesson)

        for bad in ({"lesson": None}, {"lesson": "unknown"}, {"fault": FAULT}, {"project": None}):
            self.assertEqual(http.post("start", {**query, **bad})[0], 422)

        def no_answer(payload):
            encoded = json.dumps(payload)
            for value in ("return-to-a", "STATIC_ROUTE_MISSING", "RESTORE_STATIC_ROUTE",
                          "STATIC_NEXT_HOP_UNREACHABLE", "RESTORE_NEXT_HOP", "expectedNextHop"):
                self.assertNotIn(value, encoded)

        for numeric in (0.0, -0.0):
            altered = deepcopy(fixture)
            altered["nodes"][0]["x"] = numeric
            code, denied = http.post("start", {**query, "project": altered})
            self.assertEqual(code, 422, denied)
            self.assertEqual(denied["error"], "INVALID_PROJECT")
            self.assertIn("unchanged fixture", denied["message"])
            no_answer(denied)
        code, opening = http.post("start", query)
        self.assertEqual(code, 200)
        self.assertEqual(opening["openingObservation"], {
            "replyMatched": False, "source": "SIMULATED",
        })
        self.assertFalse(opening["canDiagnose"])
        for marker in ("NO_ROUTE", "ARP_FAILED", "203.0.113.254", "requestReceiver"):
            self.assertNotIn(marker, json.dumps(opening))
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
        ping = call("probe", probe="ping", target={})
        self.assertEqual(ping["observation"]["replyStatus"], "ARP_FAILED" if case_b else "NO_ROUTE")
        no_answer(ping)
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
        self.assertEqual(lookup["observation"]["status"], "MATCH" if case_b else "NO_ROUTE")
        if case_b:
            self.assertEqual(lookup["observation"]["selectedRoute"]["nextHop"], "203.0.113.254")
        else:
            self.assertIsNone(lookup["observation"]["selectedRoute"])
        self.assertEqual(lookup["observation"]["source"], "SIMULATED_CONFIG")
        no_answer(lookup)
        wrong = call("diagnose", diagnosis=wrong_diagnosis)
        self.assertFalse(wrong["correct"])
        no_answer(wrong)
        no_answer(call("repair", 422))
        correct = call("diagnose", diagnosis=right_diagnosis)
        self.assertTrue(correct["correct"])
        no_answer(correct)
        recovered = call("repair")
        self.assertEqual((recovered["status"], recovered["failedEchoStatus"],
                          recovered["restoredEchoStatus"], recovered["replyMatched"]),
                         ("RECOVERED", "REPLY_FAILED", "REPLIED", True))
        self.assertEqual(recovered["repair"]["scope"], "PREVIEW_ONLY")
        if case_b:
            self.assertEqual(recovered["repair"]["action"], "RESTORE_NEXT_HOP")
            self.assertEqual(recovered["repair"]["expectedNextHop"], "203.0.113.1")
        else:
            self.assertEqual(recovered["repair"]["action"], "RESTORE_STATIC_ROUTE")
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(http.store.read("lesson")["sha256"], saved["sha256"])
        self.assertEqual(http.store.read("lesson")["project"], fixture)
