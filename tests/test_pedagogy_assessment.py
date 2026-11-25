"""P6 negative controls use consciously corrupted evidence."""
from copy import deepcopy
import unittest

from pedagogy_assessment import (
    Assessment, CASE_PHASES, DHCP_CASES, RETURN_CASES, STATIC_BOUNDARIES,
    check_dhcp_case, check_native_trace,
    disclosed, static_boundary_holds, wrong_answer_accepted,
)
from test_icmp_lesson import ARGS, project
from network_core.troubleshooting import compare_fault


class PedagogyAssessmentTests(unittest.TestCase):
    def test_dhcp_evidence_assessment_rejects_early_guess_and_recovers(self):
        for specification in DHCP_CASES:
            with self.subTest(cause=specification[1]):
                signals = {}
                check_dhcp_case(specification, signals)
                self.assertEqual(signals, {
                    "answer_leak": False,
                    "insufficient_evidence": True,
                    "false_diagnosis": False,
                })

    def test_native_trace_oracle_rejects_wrong_endpoint_false_success_and_arp(self):
        for _, _, fault, status, *_ in RETURN_CASES:
            reference = compare_fault(project(), *ARGS, 80, 1, fault)
            check_native_trace(reference, status)
            wrong_endpoint = deepcopy(reference)
            wrong_endpoint["faulted"]["request"]["receiver"]["node"] = "r"
            false_recovery = deepcopy(reference)
            false_recovery["restored"]["replyMatched"] = False
            wrong_mechanism = deepcopy(reference)
            reply = wrong_mechanism["faulted"]["reply"]
            if status == "NO_ROUTE":
                reply["steps"] = [{"arp": {"status": "NO_REPLY"}}]
            else:
                reply["steps"][0]["arp"]["requestTransmissions"] = []
            for mutation in (wrong_endpoint, false_recovery, wrong_mechanism):
                with self.subTest(status=status), self.assertRaises(AssertionError):
                    check_native_trace(mutation, status)

    def test_static_oracle_rejects_overclaim_even_when_approved_sentence_remains(self):
        for card, (approved, contradictory) in STATIC_BOUNDARIES.items():
            with self.subTest(card=card):
                self.assertTrue(static_boundary_holds(card, approved))
                self.assertFalse(static_boundary_holds(card, contradictory))
                self.assertFalse(static_boundary_holds(card, approved + ". " + contradictory))

    def test_answer_detector_distinguishes_observation_and_facit(self):
        self.assertFalse(disclosed({"status": "ARP_FAILED", "repair": None}))
        for leak in ({"feedback": "Återställ return-to-a"},
                     {"observation": {"routeId": "return-to-a"}},
                     {"report": "Avslöjad reparation"},
                     {"state": [{"verification": {"status": "RECOVERED"}}]}):
            with self.subTest(leak=leak):
                self.assertTrue(disclosed(leak))

    def test_report_counts_executed_failed_and_checked_signals_separately(self):
        assessment = Assessment()
        with assessment.case("return-route-engine") as signals:
            signals["false_diagnosis"] = wrong_answer_accepted("Underlaget räcker inte")
        with self.assertRaises(AssertionError):
            with assessment.case("return-arp-engine") as signals:
                signals["false_diagnosis"] = wrong_answer_accepted("Tolkningen stöds")
                signals["answer_leak"] = disclosed({"repair": "return-to-a"})
                assert not signals["false_diagnosis"]
        summary = assessment.summary()
        self.assertEqual(summary["executed"], 2)
        self.assertEqual((summary["PASS"], summary["FAIL"], summary["NOT_RUN"]),
                         (1, 1, len(CASE_PHASES) - 2))
        self.assertEqual(summary["false_diagnosis"], {"count": 1, "checked": 2})
        self.assertEqual(summary["answer_leak"], {"count": 1, "checked": 1})
        self.assertEqual(summary["insufficient_evidence"], {"count": 0, "checked": 0})
