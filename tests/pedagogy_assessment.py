"""Independent P6 case expectations and counters for the existing test harness."""
from contextlib import contextmanager
from dataclasses import dataclass, field
from unittest.mock import patch

from test_icmp_lesson import ARGS, FAULT, NEXT_HOP_FAULT, PORT, REVERSE, project
from network_core.icmp_investigation import IcmpInvestigation
from network_core.model import ProjectValidationError
from network_core.troubleshooting import compare_fault


CASE_PHASES = {
    "return-route-engine": "P1/P3",
    "return-arp-engine": "P3",
    "shared-symptom": "P3",
    "unverified-repair": "P1/P3",
    "insensitive-test": "P2",
    "icmp-route-browser": "P1/P2/P3",
    "icmp-arp-browser": "P2/P3",
    "same-opening-browser": "P3",
    "workspace-isolation-route": "P1–P5",
    "workspace-isolation-arp": "P1–P5",
    "save-open": "P1–P5",
    **{f"tool-{name}": "P4" for name in ("wireshark", "suzieq", "netshot", "batfish")},
    **{f"lesson-{name}-{choice}": "P5" for name, choices in (
        ("ospf", ("hello", "roles", "other")),
        ("snmp", ("path", "control", "other")),
        ("acl", ("match", "actual", "other")),
    ) for choice in choices},
}

NATIVE_CASES = frozenset((
    "return-route-engine", "return-arp-engine", "shared-symptom",
    "unverified-repair", "insensitive-test",
))
METRICS = ("false_diagnosis", "insufficient_evidence", "answer_leak")


@dataclass
class Assessment:
    cases: dict = field(default_factory=dict)
    browser_version: str | None = None
    browser_transport: str | None = None

    @contextmanager
    def case(self, name):
        if name not in CASE_PHASES or name in self.cases:
            raise ValueError(f"Okänt eller upprepat utvärderingsfall: {name}")
        signals = {}
        result = {"phase": CASE_PHASES[name], "surface": surface(name), "signals": signals}
        self.cases[name] = result
        try:
            yield signals
        except Exception as error:
            result.update(status="FAIL", error=f"{type(error).__name__}: {str(error)[:600]}")
            raise
        else:
            result["status"] = "PASS"

    def results(self):
        return {name: self.cases.get(name, {"phase": phase, "surface": surface(name), "status": "NOT_RUN", "signals": {}})
                for name, phase in CASE_PHASES.items()}

    def summary(self):
        cases = self.results().values()
        counts = dict(defined=len(CASE_PHASES), executed=len(self.cases))
        counts.update({state: sum(row["status"] == state for row in cases)
                       for state in ("PASS", "FAIL", "NOT_RUN")})
        counts.update({
            name: {"count": sum(row["signals"].get(name) is True for row in cases),
                   "checked": sum(name in row["signals"] for row in cases)}
            for name in METRICS
        })
        counts["surfaces"] = {
            kind: {"defined": sum(row["surface"] == kind for row in cases),
                   "passed": sum(row["surface"] == kind and row["status"] == "PASS" for row in cases)}
            for kind in ("native", "chromium")
        }
        return counts


def surface(name):
    return "native" if name in NATIVE_CASES else "chromium"


# Curated table keyed by the course card, not extracted from production HTML.
# Normalize whitespace only. Positive control phrases require the actual
# epistemic boundary. Negative control phrases catch known contradictory claims.
STATIC_BOUNDARIES = {
    "wireshark": (
        "bevisar inte att inget svar sändes på en annan mätpunkt",
        "inget svar existerade någon annanstans",
    ),
    "suzieq": (
        "En registrerad route bevisar inte lyckad paketleverans",
        "En registrerad route bevisar lyckad paketleverans",
    ),
    "netshot": (
        "En konfigurationsskillnad bevisar inte driftorsaken",
        "En konfigurationsskillnad bevisar driftorsaken",
    ),
    "batfish": (
        "bevisar inte att trafik levererades på den faktiska utrustningen",
        "bevisar att trafik levererades på den faktiska utrustningen",
    ),
}


def static_boundary_holds(card, text):
    required, contradictory = STATIC_BOUNDARIES[card]
    normalized = " ".join(text.split()).casefold()
    return required.casefold() in normalized and contradictory.casefold() not in normalized


def wrong_answer_accepted(feedback):
    return "Tolkningen stöds" in feedback


def disclosed(payload):
    """Recognize authoritative answers at a gate, not evidence such as ARP_FAILED."""
    fields = ("faultCategory", "repair", "report", "verification",
              "expectedNextHop", "expectedRoute", "routeId")
    tokens = ("return-to-a", "RESTORE_NEXT_HOP", "RESTORE_STATIC_ROUTE",
              "STATIC_ROUTE_MISSING", "STATIC_NEXT_HOP_UNREACHABLE")
    if isinstance(payload, dict):
        return any((key in fields and value is not None)
                   or disclosed(value) for key, value in payload.items())
    if isinstance(payload, list):
        return any(map(disclosed, payload))
    return isinstance(payload, str) and any(token in payload for token in tokens)


# RFC 792 plus the two fixed interventions on the shipped fixture determine
# these expectations. No production classifier or lesson answer key is read.
RETURN_CASES = (
    ("return-route-engine", "echo-reply", FAULT, "NO_ROUTE", "STATIC_ROUTE_MISSING",
     "STATIC_NEXT_HOP_UNREACHABLE", "RESTORE_STATIC_ROUTE"),
    ("return-arp-engine", "echo-reply-b", NEXT_HOP_FAULT, "ARP_FAILED", "STATIC_NEXT_HOP_UNREACHABLE",
     "STATIC_ROUTE_MISSING", "RESTORE_NEXT_HOP"),
)


def check_native_trace(comparison, status):
    assert comparison["status"] == "FAULT_CONFIRMED", comparison["status"]
    for stage in ("baseline", "restored"):
        echo = comparison[stage]
        assert echo["status"] == "REPLIED" and echo["replyMatched"], stage
        assert echo["request"]["status"] == "DELIVERED", stage
        assert echo["request"]["receiver"] == {"node": "b", "port": "eth0"}, stage
        assert echo["reply"]["status"] == "DELIVERED", stage
        assert echo["reply"]["receiver"] == {"node": "a", "port": "eth0"}, stage
    faulted = comparison["faulted"]
    assert faulted["request"]["status"] == "DELIVERED"
    assert faulted["request"]["receiver"] == {"node": "b", "port": "eth0"}
    assert faulted["status"] == "REPLY_FAILED" and not faulted["replyMatched"]
    reply = faulted["reply"]
    assert reply["status"] == status and not reply["icmpSent"] and reply["receiver"] is None
    if status == "NO_ROUTE":
        assert reply["steps"] == []
    else:
        step, = reply["steps"]
        assert (step["node"], step["outPort"], step["nextHopIpv4"]) == ("b", "eth0", "203.0.113.254")
        assert step["route"]["routeId"] == "return-to-a"
        assert step["arp"]["status"] == "NO_REPLY"
        assert step["arp"]["requestTransmissions"] and not step["arp"]["replyTransmissions"]
        assert not step["ipv4Transmissions"]


def check_native_case(specification, signals):
    _, lesson, fault, status, right, wrong, action = specification
    fixture = project()
    check_native_trace(compare_fault(fixture, *ARGS, 70, 1, fault), status)
    session = IcmpInvestigation(fixture, *ARGS, lesson=lesson)
    opening = session.state()
    ping = session.probe("ping", {})
    route = session.probe("route", REVERSE)
    port = session.probe("port", PORT)
    signals["answer_leak"] = any(disclosed(payload) for payload in (opening, ping, route, port))
    assert not signals["answer_leak"], "Facit före rätt diagnos och återställning"
    assert not ping["canDiagnose"] and not route["canDiagnose"] and port["canDiagnose"]
    assert ping["observation"]["replyStatus"] == status
    lookup = route["observation"]
    if status == "NO_ROUTE":
        assert lookup["status"] == "NO_ROUTE" and lookup["selectedRoute"] is None
    else:
        assert lookup["status"] == "MATCH"
        assert lookup["selectedRoute"]["nextHop"] == "203.0.113.254"

    denied = session.diagnose(wrong)
    signals["false_diagnosis"] = bool(denied["correct"] or denied["repairAvailable"])
    signals["answer_leak"] |= disclosed(denied)
    assert not signals["false_diagnosis"] and not signals["answer_leak"]
    correct = session.diagnose(right)
    signals["answer_leak"] |= disclosed(correct)
    assert correct["correct"] and not signals["answer_leak"]
    outcome = session.repair()
    assert outcome["status"] == "RECOVERED"
    assert outcome["replyMatched"] and outcome["restoredEchoStatus"] == "REPLIED"
    assert outcome["repair"]["scope"] == "PREVIEW_ONLY" and outcome["repair"]["action"] == action
    assert fixture == project()


def check_shared_symptom():
    observations = [IcmpInvestigation(project(), *ARGS, lesson=specification[1]).state()
                    ["openingObservation"] for specification in RETURN_CASES]
    assert observations == [{"replyMatched": False, "source": "SIMULATED"}] * 2
    assert all(not disclosed(item) for item in observations)


def check_insensitive_test(signals):
    """Forward route and ping are the same in both cases. A reverse lookup separates them."""
    actual = []
    for _, lesson, *_ in RETURN_CASES:
        session = IcmpInvestigation(project(), *ARGS, lesson=lesson)
        ping = session.probe("ping", {})
        forward = session.probe("route", {"nodeId": "a", "destinationIpv4": "203.0.113.20"})
        wrong_port = session.probe("port", {"nodeId": "a", "portId": "eth0"})
        try:
            verdict = session.diagnose("STATIC_ROUTE_MISSING")
        except ProjectValidationError as error:
            assert "lesson requires" in str(error)
            rejected = True
        else:
            rejected = False
            signals["false_diagnosis"] = signals.get("false_diagnosis", False) or verdict["correct"]
        actual.append((ping["observation"]["status"], forward["observation"]["status"],
                       wrong_port["canDiagnose"], rejected))
    signals.setdefault("false_diagnosis", False)
    signals["insufficient_evidence"] = all(not can_diagnose and rejected
                                           for _, _, can_diagnose, rejected in actual)
    assert actual == [("REPLY_FAILED", "MATCH", False, True)] * 2


def check_unverified_repair(signals):
    """Feed the real repair gate a comparison for the wrong intervention."""
    session = IcmpInvestigation(project(), *ARGS, lesson="echo-reply")
    session.probe("ping", {})
    session.probe("route", REVERSE)
    session.probe("port", PORT)
    assert session.diagnose("STATIC_ROUTE_MISSING")["correct"]
    mismatched = compare_fault(project(), *ARGS, 71, 1, {
        "type": "STATIC_ROUTE_REMOVED", "nodeId": "a", "routeId": "via-router",
    })
    assert mismatched["faulted"]["status"] == "REQUEST_FAILED"
    with patch.object(session, "_compare_lesson", return_value=mismatched):
        outcome = session.repair()
    signals["insufficient_evidence"] = outcome["status"] == "NOT_VERIFIED"
    signals["answer_leak"] = disclosed(outcome)
    assert signals["insufficient_evidence"] and not signals["answer_leak"]
    assert not outcome["replyMatched"] and not outcome["repaired"]
