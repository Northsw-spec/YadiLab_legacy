"""Opaque, evidence-first ICMP investigation over the existing packet engine.

No new forwarding model: candidate faults use the existing controlled fault
mutation and are included only when independent real Echo Request/Reply trials
prove baseline, failed communication and restored communication. DHCP address
origin is *unknown* in the canonical schema; never claim DHCP was excluded.
"""
from __future__ import annotations

from copy import deepcopy
import ipaddress
from pathlib import Path
import secrets
from threading import RLock
from .session_idle import IdleSessions, session_activity

from .icmp_ping import EchoExchange
from .json_boundary import decode_json_document
from .model import ProjectValidationError, validate_project
from .routing import ConnectedRoutingTable
from .simulation import MAX_SESSIONS
from .troubleshooting import _mutation, _observed_wires, compare_fault

MAX_PROBES = 48
MAX_GUESSES = 3
KINDS = ("CABLE_DOWN", "PORT_SHUTDOWN", "VLAN_MISMATCH", "STATIC_ROUTE_MISSING",
         "IPV4_PREFIX_MISMATCH", "STATIC_NEXT_HOP_UNREACHABLE",
         "IPV4_HOST_ADDRESS_MISMATCH")
LAN_KINDS = ("CABLE_DOWN", "PORT_SHUTDOWN", "VLAN_MISMATCH",
             "IPV4_HOST_ADDRESS_MISMATCH", "IPV4_PREFIX_MISMATCH")
PROBES = ("address", "route", "ping", "link", "port", "vlan")


_LESSON_FIXTURE = (Path(__file__).resolve().parent.parent / "web" / "fixtures"
                   / "icmp-echo-lesson.json")
_LESSON_SOURCE = {"node": "a", "port": "eth0"}
_LESSON_TARGET = {"node": "b", "port": "eth0"}
_LESSON_SOURCE_IP = "192.0.2.10"
_LESSON_TARGET_IP = "203.0.113.20"
_LESSON_RETURN_ROUTE = {"nodeId": "b", "routeId": "return-to-a"}
_LESSON_UNREACHABLE_HOP = "203.0.113.254"
_LESSONS = {
    "echo-reply": ("STATIC_ROUTE_MISSING", "NO_ROUTE", {
        **_LESSON_RETURN_ROUTE, "type": "STATIC_ROUTE_REMOVED",
    }),
    "echo-reply-b": ("STATIC_NEXT_HOP_UNREACHABLE", "ARP_FAILED", {
        **_LESSON_RETURN_ROUTE, "type": "STATIC_NEXT_HOP_CHANGED",
        "newNextHop": _LESSON_UNREACHABLE_HOP,
    }),
}
ICMP_LESSON_IDS = tuple(_LESSONS)


def _lesson_echo(exchange: dict, *, matched: bool, reply_status: str = "NO_ROUTE") -> bool:
    request, reply = exchange["request"], exchange["reply"]
    if (request["status"] != "DELIVERED" or request["receiver"] != _LESSON_TARGET
            or request["sourceIpv4"] != _LESSON_SOURCE_IP
            or request["destinationIpv4"] != _LESSON_TARGET_IP
            or reply is None or reply["sourceIpv4"] != _LESSON_TARGET_IP
            or reply["destinationIpv4"] != _LESSON_SOURCE_IP):
        return False
    if matched:
        return (exchange["status"] == "REPLIED" and exchange["replyMatched"]
                and reply["status"] == "DELIVERED" and reply["receiver"] == _LESSON_SOURCE)
    if (exchange["status"] != "REPLY_FAILED" or exchange["replyMatched"]
            or reply["status"] != reply_status or reply["icmpSent"]
            or reply["receiver"] is not None or reply["deliveredDatagram"] is not None):
        return False
    if reply_status == "NO_ROUTE":
        return not reply["steps"]
    if reply_status != "ARP_FAILED" or len(reply["steps"]) != 1:
        return False
    step = reply["steps"][0]
    return (step["node"] == _LESSON_TARGET["node"] and step["outPort"] == _LESSON_TARGET["port"]
            and step["nextHopIpv4"] == _LESSON_UNREACHABLE_HOP
            and step["route"].get("routeId") == _LESSON_RETURN_ROUTE["routeId"]
            and step["arp"]["status"] == "NO_REPLY" and bool(step["arp"]["requestTransmissions"])
            and not step["arp"]["replyTransmissions"] and not step["ipv4Transmissions"])


def _lesson_verified(comparison: dict, reply_status: str) -> bool:
    return (comparison["status"] == "FAULT_CONFIRMED"
            and _lesson_echo(comparison["baseline"], matched=True)
            and _lesson_echo(comparison["faulted"], matched=False, reply_status=reply_status)
            and _lesson_echo(comparison["restored"], matched=True))


def _candidates(project: dict, baseline: dict) -> list[tuple[str, dict]]:
    """Only documented interventions in observed successful packet paths."""
    visited = set(_observed_wires(baseline))
    candidates: list[tuple[str, dict]] = []
    for link in project["links"]:
        if link["id"] in visited and link["enabled"]:
            candidates.append(("CABLE_DOWN", {
                "type": "LINK_DISABLED", "linkId": link["id"],
            }))
    for node in project["nodes"]:
        if node["kind"] != "switch":
            for route in node.get("staticRoutes", []):
                candidates.append(("STATIC_ROUTE_MISSING", {
                    "type": "STATIC_ROUTE_REMOVED",
                    "nodeId": node["id"], "routeId": route["id"],
                }))
    # A changed next-hop must belong to a STATIC route actually selected
    # during the real successful request/reply exchange, not merely a
    # documented but unused route. Choose a bounded, unassigned on-link
    # host address to simulate a wrong gateway; it is NOT a discovered
    # network device. Only a proven ARP failure can admit the candidate.
    used_static_routes = {
        (step["node"], step["route"]["routeId"])
        for trace in (baseline["request"], baseline["reply"]) if trace is not None
        for step in trace["steps"]
        if step["route"]["type"] == "STATIC"
    }
    configured_addresses = {
        ipaddress.IPv4Interface(port["ipv4"]).ip
        for node in project["nodes"] for port in node["ports"]
        if port["ipv4"] is not None
    }
    receiver = baseline["request"]["receiver"]
    target = next(n for n in project["nodes"] if n["id"] == receiver["node"])
    if target["kind"] == "host":
        port = next(p for p in target["ports"] if p["id"] == receiver["port"])
        configured = ipaddress.IPv4Interface(port["ipv4"])
        network = configured.network
        first, last = int(network.network_address), int(network.broadcast_address)
        possible = [first + offset for offset in range(1, 9)]
        possible += [last - offset for offset in range(1, 5)]
        alternative = next((str(address) for number in possible
                            if first < number < last
                            for address in (ipaddress.IPv4Address(number),)
                            if address not in configured_addresses
                            and not address.is_reserved), None)
        if alternative is not None:
            candidates.append(("IPV4_HOST_ADDRESS_MISMATCH", {
                "type": "IPV4_HOST_ADDRESS_CHANGED", "nodeId": target["id"],
                "portId": port["id"], "newIpv4": alternative,
            }))
    for node in project["nodes"]:
        if node["kind"] == "switch":
            continue
        ports = {port["id"]: port for port in node["ports"]}
        for route in node.get("staticRoutes", []):
            if (node["id"], route["id"]) not in used_static_routes:
                continue
            out_port = ports[route["outPort"]]
            if not out_port["enabled"] or out_port["ipv4"] is None:
                continue
            network = ipaddress.IPv4Interface(out_port["ipv4"]).network
            start, end = int(network.network_address), int(network.broadcast_address)
            possible = [start + i for i in range(1, 9)]
            possible += [end - i for i in range(1, 5)]
            alternative = next((
                str(address) for number in possible if start < number < end
                for address in (ipaddress.IPv4Address(number),)
                if address not in configured_addresses
                and str(address) != route["nextHop"]
            ), None)
            if alternative is not None:
                candidates.append(("STATIC_NEXT_HOP_UNREACHABLE", {
                    "type": "STATIC_NEXT_HOP_CHANGED", "nodeId": node["id"],
                    "routeId": route["id"], "newNextHop": alternative,
                }))

    # Disabling an enabled switchport is eligible only if its cable was
    # traversed in the real baseline. compare_fault below must still prove
    # independently that the shutdown breaks Echo and can be restored.
    switches = {n["id"]: n for n in project["nodes"] if n["kind"] == "switch"}
    seen_ports = set()
    for link in project["links"]:
        if link["id"] not in visited or not link["enabled"]:
            continue
        for endpoint in (link["a"], link["b"]):
            node = switches.get(endpoint["node"])
            if node is None:
                continue
            identity = (node["id"], endpoint["port"])
            if identity in seen_ports:
                continue
            seen_ports.add(identity)
            port = next(p for p in node["ports"] if p["id"] == endpoint["port"])
            if port["enabled"]:
                candidates.append(("PORT_SHUTDOWN", {
                    "type": "PORT_DISABLED", "nodeId": node["id"],
                    "portId": port["id"],
                }))
    # Limit possible prefix mistakes to interfaces on cables that carried
    # real baseline Echo traffic. The peer addresses are documented facts,
    # not inferred connectivity; compare_fault must verify the causal effect.
    observed_endpoints = {
        (end["node"], end["port"])
        for link in project["links"] if link["id"] in visited
        for end in (link["a"], link["b"])
    }
    interfaces = [
        (node, port, ipaddress.IPv4Interface(port["ipv4"]))
        for node in project["nodes"] if node["kind"] != "switch"
        for port in node["ports"] if port["enabled"] and port["ipv4"] is not None
        and (node["id"], port["id"]) in observed_endpoints
    ]
    for node, port, configured in interfaces:
        peers = [
            other.ip for _, _, other in interfaces
            if other.ip != configured.ip and other.ip in configured.network
        ]
        if not peers:
            continue
        new_prefix = next((
            prefix for prefix in range(configured.network.prefixlen + 1, 31)
            if any(peer not in ipaddress.IPv4Network(
                (configured.ip, prefix), strict=False) for peer in peers)
        ), None)
        if new_prefix is not None:
            candidates.append(("IPV4_PREFIX_MISMATCH", {
                "type": "IPV4_PREFIX_CHANGED", "nodeId": node["id"],
                "portId": port["id"], "newPrefix": new_prefix,
            }))
    documented_vlans = sorted({
        number
        for node in project["nodes"] if node["kind"] == "switch"
        for port in node["ports"] if port["vlan"] is not None
        for number in (port["vlan"]["allowedVlans"]
                       if port["vlan"]["mode"] == "trunk"
                       else (port["vlan"]["vlan"],))
    })
    for node in project["nodes"]:
        if node["kind"] != "switch":
            continue
        for port in node["ports"]:
            vlan = port["vlan"]
            if not port["enabled"] or vlan is None or vlan["mode"] != "access":
                continue
            if not any(
                link["id"] in visited and (
                    (link["a"]["node"], link["a"]["port"]) == (node["id"], port["id"])
                    or (link["b"]["node"], link["b"]["port"]) == (node["id"], port["id"]))
                for link in project["links"]
            ):
                continue
            alternative = next((v for v in documented_vlans
                                if v != vlan["vlan"]), None)
            if alternative is not None:
                candidates.append(("VLAN_MISMATCH", {
                    "type": "ACCESS_VLAN_CHANGED", "nodeId": node["id"],
                    "portId": port["id"], "newVlan": alternative,
                }))
    return candidates


class IcmpInvestigation:
    def __init__(self, project: object, source_node: str, source_port: str,
                 destination_ipv4: str, ttl: int, *, lesson: str | None = None,
                 _test_kind: str | None = None):
        self.project = validate_project(project)
        if type(source_node) is not str or type(source_port) is not str:
            raise ProjectValidationError("icmp investigation: source must be declared")
        if type(ttl) is not int or not 2 <= ttl <= 255:
            raise ProjectValidationError("icmp investigation: TTL must be integer 2..255")
        self.source_node, self.source_port = source_node, source_port
        self.destination_ipv4, self.ttl = destination_ipv4, ttl
        self._lesson = lesson
        self._lesson_evidence: set[str] = set()
        if lesson is not None:
            self._validate_lesson()
            self._kind, self._lesson_reply_status, fault = _LESSONS[lesson]
            self._fault = deepcopy(fault)
            comparison = self._compare_lesson(101, 1)
            if not _lesson_verified(comparison, self._lesson_reply_status):
                raise ProjectValidationError(
                    "icmp investigation: lesson exchange could not be verified")
            baseline = comparison["baseline"]
        else:
            baseline = EchoExchange(self.project).ping(
                source_node, source_port, destination_ipv4, ttl, 101, 1)
        if baseline["status"] != "REPLIED" or not baseline["replyMatched"]:
            raise ProjectValidationError(
                "icmp investigation: initial Echo Request/Reply must be proven")
        self.source_ipv4 = baseline["request"]["sourceIpv4"]
        self.target_node = baseline["request"]["receiver"]["node"]
        self.target_port = baseline["request"]["receiver"]["port"]
        if not self._lesson:
            self._kind, self._fault = self._choose_fault(baseline, _test_kind)
        self._fault_detail, self._repair_hint, inject, _ = _mutation(self.project, self._fault)
        self._faulted = deepcopy(self.project)
        inject(self._faulted)
        self._faulted = validate_project(self._faulted)
        # Final independent proof for chosen candidate: do not admit a
        # baseline-only or disconnected-by-coincidence exercise.
        broken = EchoExchange(self._faulted).ping(
            source_node, source_port, destination_ipv4, ttl, 101, 2)
        if broken["status"] == "REPLIED":
            raise ProjectValidationError("icmp investigation: fault did not affect Echo")
        if self._lesson:
            if not _lesson_echo(broken, matched=False, reply_status=self._lesson_reply_status):
                raise ProjectValidationError("icmp investigation: lesson exchange changed")
            self.opening_observation = {
                "replyMatched": broken["replyMatched"],
                "source": "SIMULATED",
            }
        else:
            direction = "request" if broken["request"]["status"] != "DELIVERED" else "reply"
            path = baseline[direction]
            self._exercise_destination = path["destinationIpv4"]
            self._exercise_routes = {step["node"]: step["route"] for step in path["steps"]}
            self._exercise_evidence: set[str] = set()
        self._probes: list[str] = []
        self._guesses = 0
        self._diagnosed = False
        self._repaired = False
        self._sequence = 2
        self._source_nodes = {
            node["id"] for node in self.project["nodes"]
            if node["kind"] != "switch"
        }

    def _validate_lesson(self) -> None:
        if (self._lesson not in ICMP_LESSON_IDS
                or (self.source_node, self.source_port, self.destination_ipv4, self.ttl)
                != (_LESSON_SOURCE["node"], _LESSON_SOURCE["port"], _LESSON_TARGET_IP, 5)):
            raise ProjectValidationError("icmp investigation: invalid lesson or endpoints")
        try:
            expected = validate_project(decode_json_document(
                _LESSON_FIXTURE.read_bytes(), context="icmp lesson"))
        except (OSError, ProjectValidationError):
            raise ProjectValidationError("icmp investigation: lesson fixture unavailable") from None
        if self.project != expected:
            raise ProjectValidationError("icmp investigation: lesson requires the unchanged fixture")

    def _compare_lesson(self, identifier: int, sequence: int) -> dict:
        return compare_fault(
            self.project, self.source_node, self.source_port, self.destination_ipv4,
            self.ttl, identifier, sequence, self._fault)

    def _lesson_route_matches(self, lookup: dict) -> bool:
        if self._lesson_reply_status == "NO_ROUTE":
            return lookup["status"] == "NO_ROUTE"
        selected = lookup["selectedRoute"]
        return (lookup["status"] == "MATCH" and selected is not None
                and selected.get("routeId") == _LESSON_RETURN_ROUTE["routeId"]
                and selected["nextHop"] == _LESSON_UNREACHABLE_HOP
                and selected["outInterface"] == _LESSON_TARGET)

    def _choose_fault(self, baseline: dict, _test_kind: str | None) -> tuple[str, dict]:
        source_node, source_port = self.source_node, self.source_port
        destination_ipv4, ttl = self.destination_ipv4, self.ttl
        # A one-hop host exchange uses connected route lookups in both
        # directions. Keep the routed candidate set for all other exchanges.
        source_port_config = next(port for node in self.project["nodes"]
                                  if node["id"] == source_node
                                  for port in node["ports"] if port["id"] == source_port)
        target_port_config = next(port for node in self.project["nodes"]
                                  if node["id"] == self.target_node
                                  for port in node["ports"] if port["id"] == self.target_port)
        direct_lan = (
            all(len(baseline[direction]["steps"]) == 1 and
                baseline[direction]["steps"][0]["route"]["type"] == "CONNECTED"
                for direction in ("request", "reply"))
            and ipaddress.IPv4Interface(source_port_config["ipv4"]).network ==
                ipaddress.IPv4Interface(target_port_config["ipv4"]).network
            and next(node for node in self.project["nodes"]
                     if node["id"] == self.target_node)["kind"] == "host"
        )
        allowed = []
        for kind, fault in _candidates(self.project, baseline):
            if direct_lan and kind not in LAN_KINDS:
                continue
            try:
                confirmed = compare_fault(
                    self.project, source_node, source_port,
                    destination_ipv4, ttl, 101, 1, fault)
            except ProjectValidationError:
                continue
            if confirmed["status"] != "FAULT_CONFIRMED":
                continue
            if kind in ("STATIC_NEXT_HOP_UNREACHABLE", "IPV4_HOST_ADDRESS_MISMATCH"):
                # The failure must be the modeled lack of an ARP reply to
                # the injected next-hop, not an unrelated packet failure.
                traces = (confirmed["faulted"]["request"],
                          confirmed["faulted"]["reply"])
                if not any(
                    trace is not None and trace["status"] == "ARP_FAILED"
                    and any(step["arp"]["status"] == "NO_REPLY"
                            and (kind != "IPV4_HOST_ADDRESS_MISMATCH"
                                 or step["nextHopIpv4"] == destination_ipv4)
                            for step in trace["steps"])
                    for trace in traces
                ):
                    continue
            allowed.append((kind, fault))
        if not allowed:
            raise ProjectValidationError(
                "icmp investigation: no verified reversible link/port/VLAN/address/route/prefix/next-hop fault")
        if _test_kind is None:
            # Every candidate has independently proven failure and recovery.
            # Do not silently force LAN exercises to always be cable faults.
            choice = allowed[secrets.randbelow(len(allowed))]
        else:
            choice = next((candidate for candidate in allowed
                           if candidate[0] == _test_kind), None)
            if choice is None:
                raise ProjectValidationError(
                    "icmp investigation: category is not verified for this topology")
        return choice

    def check_project(self, project: object) -> None:
        if validate_project(project) != self.project:
            raise ProjectValidationError("icmp investigation: project changed since session start")

    def _record_exercise_evidence(self, kind: str, target: dict, result: dict) -> None:
        fault = self._fault
        if kind == "ping":
            if result["status"] != "REPLIED" and not result["replyMatched"]:
                self._exercise_evidence.add("ping")
            return
        if kind == "route":
            original = self._exercise_routes.get(target["nodeId"])
            if original is None or target["destinationIpv4"] != self._exercise_destination:
                return
            if "routeId" in fault:
                if target["nodeId"] != fault["nodeId"] or original.get("routeId") != fault["routeId"]:
                    return
                if fault["type"] == "STATIC_ROUTE_REMOVED":
                    changed = not any(r.get("routeId") == fault["routeId"] for r in result["routes"])
                else:
                    selected = result["selectedRoute"]
                    changed = (selected is not None and selected.get("routeId") == fault["routeId"]
                               and selected["nextHop"] != original["nextHop"])
                if changed:
                    self._exercise_evidence.add("difference")
            self._exercise_evidence.add("route")
            return
        if kind == "link" and fault["type"] == "LINK_DISABLED":
            if target["linkId"] == fault["linkId"] and (
                    result["documentedEnabled"] and not result["observedEnabled"]):
                self._exercise_evidence.add("difference")
            return
        if kind not in ("port", "vlan") or (target["nodeId"], target["portId"]) != (
                fault.get("nodeId"), fault.get("portId")):
            return
        if kind == "vlan":
            changed = (fault["type"] == "ACCESS_VLAN_CHANGED"
                       and result["documentedVlan"] != result["observedVlan"])
        elif fault["type"] == "PORT_DISABLED":
            changed = result["documentedEnabled"] and not result["observedEnabled"]
        else:
            changed = (fault["type"] in ("IPV4_PREFIX_CHANGED", "IPV4_HOST_ADDRESS_CHANGED")
                       and result["documentedIpv4"] != result["observedIpv4"])
        if changed:
            self._exercise_evidence.add("difference")

    def state(self) -> dict:
        can_diagnose = (
            self._lesson_evidence == {"ping", "route", "port"} if self._lesson else
            self._exercise_evidence == {"ping", "route", "difference"}
        )
        state = {
            "sourceNode": self.source_node,
            "sourcePort": self.source_port,
            "sourceIpv4": self.source_ipv4,
            "destinationIpv4": self.destination_ipv4,
            "ttl": self.ttl,
            "observations": len(self._probes),
            "probesPerformed": list(self._probes),
            "canDiagnose": can_diagnose,
            "diagnosisAttempts": self._guesses,
            "diagnosed": self._diagnosed,
            "repaired": self._repaired,
            "maxProbes": MAX_PROBES,
            "dhcpAddressOrigin": "UNKNOWN",
            "dhcpCheck": "NOT_VERIFIED",
            "ephemeral": True,
        }

        if self._lesson:
            state["lesson"] = self._lesson
            state["openingObservation"] = deepcopy(self.opening_observation)
        return state

    def probe(self, kind: object, target: object) -> dict:
        if self._repaired:
            raise ProjectValidationError("icmp investigation: exercise already repaired")
        if type(kind) is not str or kind not in PROBES or type(target) is not dict:
            raise ProjectValidationError("icmp investigation: unsupported probe")
        if len(self._probes) >= MAX_PROBES:
            raise ProjectValidationError("icmp investigation: observation limit reached")
        if kind == "address":
            if target:
                raise ProjectValidationError("icmp investigation: address target must be empty")
            original = next(node for node in self.project["nodes"]
                            if node["id"] == self.source_node)
            port = next(p for p in original["ports"] if p["id"] == self.source_port)
            result = {
                "documentedIpv4": port["ipv4"], "interfaceEnabled": port["enabled"],
                "origin": "UNKNOWN", "dhcpStatus": "NOT_VERIFIED",
                "reason": "IPv4 source (static/DHCP) is not encoded in the project schema.",
                "source": "DOCUMENTED",
            }
        elif kind == "ping":
            if target:
                raise ProjectValidationError("icmp investigation: ping target must be empty")
            self._sequence += 1
            result_echo = EchoExchange(self._faulted).ping(
                self.source_node, self.source_port, self.destination_ipv4,
                self.ttl, 101, self._sequence)
            result = {
                "status": result_echo["status"],
                "replyMatched": result_echo["replyMatched"],
                "requestStatus": result_echo["request"]["status"],
                "replyStatus": (result_echo["reply"]["status"]
                                if result_echo["reply"] else None),
                "requestSteps": [
                    {"node": step["node"], "route": step["route"],
                     "arpStatus": step["arp"]["status"],
                     "nextHopIpv4": step["nextHopIpv4"],
                     "transmissions": step["ipv4Transmissions"],
                     "vlanDrops": step["vlanDrops"]}
                    for step in result_echo["request"]["steps"]
                ],
                "replySteps": [
                    {"node": step["node"], "route": step["route"],
                     "arpStatus": step["arp"]["status"],
                     "nextHopIpv4": step["nextHopIpv4"],
                     "transmissions": step["ipv4Transmissions"],
                     "vlanDrops": step["vlanDrops"]}
                    for step in (result_echo["reply"] or {}).get("steps", [])
                ],
                "observedLinkIds": _observed_wires(result_echo),
                "source": "SIMULATED",
            }
            if self._lesson:
                result["requestReceiver"] = result_echo["request"]["receiver"]
                if _lesson_echo(result_echo, matched=False, reply_status=self._lesson_reply_status):
                    self._lesson_evidence.add("ping")
                for step in result["requestSteps"] + result["replySteps"]:
                    step["route"] = {key: value for key, value in step["route"].items()
                                     if key != "routeId"}
        elif kind == "route":
            if set(target) != {"nodeId", "destinationIpv4"}:
                raise ProjectValidationError(
                    "icmp investigation: route needs nodeId and destinationIpv4")
            node, address = target["nodeId"], target["destinationIpv4"]
            if type(node) is not str or node not in self._source_nodes:
                raise ProjectValidationError("icmp investigation: route node must exist")
            if type(address) is not str or address not in (
                    self.source_ipv4, self.destination_ipv4):
                raise ProjectValidationError(
                    "icmp investigation: route target must be source or destination IPv4")
            result = {
                **ConnectedRoutingTable(self._faulted, node).lookup(address),
                "documentedStaticRoutes": deepcopy(next(
                    n.get("staticRoutes", []) for n in self.project["nodes"]
                    if n["id"] == node
                )),
                "source": "SIMULATED_CONFIG",
            }
            if self._lesson:
                if (node == _LESSON_TARGET["node"] and address == _LESSON_SOURCE_IP
                        and self._lesson_route_matches(result)):
                    self._lesson_evidence.add("route")
                # Keep observed next hops and prefixes. Authoritative route
                # identities appear with the verified repair.
                for route in result["documentedStaticRoutes"]:
                    del route["id"]
                for route in result["routes"] + result["candidates"]:
                    route.pop("routeId", None)
                if result["selectedRoute"] is not None:
                    result["selectedRoute"].pop("routeId", None)
        elif kind == "link":
            if set(target) != {"linkId"} or type(target["linkId"]) is not str:
                raise ProjectValidationError("icmp investigation: link requires linkId")
            link = next((x for x in self._faulted["links"]
                         if x["id"] == target["linkId"]), None)
            documented = next((x for x in self.project["links"]
                               if x["id"] == target["linkId"]), None)
            if link is None or documented is None:
                raise ProjectValidationError("icmp investigation: unknown declared link")
            result = {
                "linkId": link["id"],
                "documentedEnabled": documented["enabled"],
                "observedEnabled": link["enabled"],
                "endpoints": [dict(link["a"]), dict(link["b"])],
                "source": "SIMULATED_CONFIG",
            }
        elif kind == "port":
            if set(target) != {"nodeId", "portId"} or any(
                    type(target[key]) is not str for key in ("nodeId", "portId")):
                raise ProjectValidationError("icmp investigation: port needs nodeId, portId")
            node_id, port_id = target["nodeId"], target["portId"]
            doc_node = next((n for n in self.project["nodes"]
                             if n["id"] == node_id), None)
            sim_node = next((n for n in self._faulted["nodes"]
                             if n["id"] == node_id), None)
            if doc_node is None or sim_node is None:
                raise ProjectValidationError("icmp investigation: unknown declared node")
            original = next((p for p in doc_node["ports"]
                             if p["id"] == port_id), None)
            observed = next((p for p in sim_node["ports"]
                             if p["id"] == port_id), None)
            if original is None or observed is None:
                raise ProjectValidationError("icmp investigation: unknown declared port")
            result = {
                "nodeId": node_id, "portId": port_id,
                "documentedEnabled": original["enabled"],
                "observedEnabled": observed["enabled"],
                "documentedIpv4": original["ipv4"],
                "observedIpv4": observed["ipv4"],
                "source": "SIMULATED_CONFIG",
            }
        else:
            if set(target) != {"nodeId", "portId"}:
                raise ProjectValidationError("icmp investigation: VLAN needs nodeId, portId")
            node_id, port_id = target["nodeId"], target["portId"]
            if type(node_id) is not str or type(port_id) is not str:
                raise ProjectValidationError("icmp investigation: VLAN endpoints must be strings")
            doc_node = next((x for x in self.project["nodes"]
                             if x["id"] == node_id and x["kind"] == "switch"), None)
            fault_node = next((x for x in self._faulted["nodes"]
                               if x["id"] == node_id and x["kind"] == "switch"), None)
            if doc_node is None or fault_node is None:
                raise ProjectValidationError("icmp investigation: VLAN requires declared switch")
            original = next((x for x in doc_node["ports"]
                             if x["id"] == port_id), None)
            observed = next((x for x in fault_node["ports"]
                             if x["id"] == port_id), None)
            if original is None or observed is None or original["vlan"] is None:
                raise ProjectValidationError("icmp investigation: VLAN requires configured port")
            result = {
                "nodeId": node_id, "portId": port_id,
                "documentedVlan": deepcopy(original["vlan"]),
                "observedVlan": deepcopy(observed["vlan"]),
                "source": "SIMULATED_CONFIG",
            }
        if self._lesson and kind == "port" and target == {
                "nodeId": _LESSON_TARGET["node"], "portId": _LESSON_TARGET["port"]}:
            if (result["observedEnabled"] and result["documentedEnabled"]
                    and result["observedIpv4"] == result["documentedIpv4"]):
                self._lesson_evidence.add("port")
        if not self._lesson:
            self._record_exercise_evidence(kind, target, result)
        self._probes.append(kind)
        return {"probe": kind, "observation": result, **self.state()}

    def diagnose(self, diagnosis: object) -> dict:
        if self._repaired:
            raise ProjectValidationError("icmp investigation: exercise already repaired")
        if type(diagnosis) is not str or diagnosis not in KINDS:
            raise ProjectValidationError("icmp investigation: unsupported diagnosis")
        if not self.state()["canDiagnose"]:
            raise ProjectValidationError(
                "icmp investigation: lesson requires ping, reverse lookup and target port check"
                if self._lesson else
                "icmp investigation: real failed ping and relevant observations on that path required")
        if self._guesses >= MAX_GUESSES:
            raise ProjectValidationError("icmp investigation: maximum guesses reached")
        self._guesses += 1
        correct = diagnosis == self._kind
        self._diagnosed = self._diagnosed or correct
        return {
            "correct": correct, "repairAvailable": self._diagnosed,
            "feedback": ("Diagnosen stöds av den verifierade nätverksmodellen."
                         if correct else "Hypotesen avvisades. Undersök paket och tabeller."),
            **self.state(),
        }

    def repair(self) -> dict:
        if self._repaired:
            raise ProjectValidationError("icmp investigation: already repaired")
        if not self._diagnosed:
            raise ProjectValidationError("icmp investigation: correct diagnosis required")
        if self._lesson:
            comparison = self._compare_lesson(102, 1)
            broken, restored = comparison["faulted"], comparison["restored"]
            verified = _lesson_verified(comparison, self._lesson_reply_status)
        else:
            # Independent fresh packet engines before and after the isolated change.
            broken = EchoExchange(self._faulted).ping(
                self.source_node, self.source_port, self.destination_ipv4,
                self.ttl, 102, 1)
            restored = EchoExchange(self.project).ping(
                self.source_node, self.source_port, self.destination_ipv4,
                self.ttl, 102, 2)
            verified = (broken["status"] != "REPLIED" and not broken["replyMatched"]
                        and restored["status"] == "REPLIED"
                        and restored["replyMatched"])
        self._repaired = verified
        result = {
            "status": "RECOVERED" if verified else "NOT_VERIFIED",
            "failedEchoStatus": broken["status"],
            "restoredEchoStatus": "NOT_VERIFIED" if self._lesson and not verified else restored["status"],
            "replyMatched": restored["replyMatched"] and (not self._lesson or verified),
            "faultCategory": self._kind if verified else None,
            "repair": deepcopy(self._repair_hint) if verified else None,
            "report": self._report(broken, restored) if verified else None,
            **self.state(),
        }

        if self._lesson and verified:
            result["verification"] = {
                "baselineStatus": comparison["baseline"]["status"],
                "requestReceiver": restored["request"]["receiver"],
                "replyReceiver": restored["reply"]["receiver"],
                "sourceIpv4": restored["request"]["sourceIpv4"],
                "destinationIpv4": restored["request"]["destinationIpv4"],
                "source": "SIMULATED",
            }
        return result

    def _report(self, broken: dict, restored: dict) -> dict:
        fault, repair = self._fault_detail, self._repair_hint
        kind = self._kind
        place = f"{fault['nodeId']}/{fault['portId']}" if "portId" in fault else None
        if kind == "CABLE_DOWN":
            cause = f"Kabel {fault['linkId']} var avstängd."
            action = f"Kabel {repair['linkId']} aktiverades igen."
        elif kind == "PORT_SHUTDOWN":
            cause = f"Switchport {place} var administrativt avstängd."
            action = f"Switchport {place} aktiverades igen."
        elif kind == "VLAN_MISMATCH":
            cause = (f"Access-VLAN på {place} ändrades från "
                     f"{repair['expectedVlan']['vlan']} till {fault['toVlan']}.")
            action = f"Access-VLAN på {place} återställdes till {repair['expectedVlan']['vlan']}."
        elif kind == "STATIC_ROUTE_MISSING":
            cause = f"Statisk route {fault['routeId']} på {fault['nodeId']} saknades."
            action = f"Route {repair['routeId']} på {repair['nodeId']} återställdes."
        elif kind == "STATIC_NEXT_HOP_UNREACHABLE":
            cause = (f"Next-hop för route {fault['routeId']} på {fault['nodeId']} "
                     f"ändrades från {fault['fromNextHop']} till {fault['toNextHop']}.")
            action = (f"Next-hop för route {repair['routeId']} återställdes till "
                      f"{repair['expectedNextHop']}.")
        else:
            setting = "IPv4-prefix" if kind == "IPV4_PREFIX_MISMATCH" else "IPv4-adress"
            cause = (f"{setting} på {place} ändrades från "
                     f"{fault['fromIpv4']} till {fault['toIpv4']}.")
            action = f"IPv4-konfiguration på {place} återställdes till {repair['expectedIpv4']}."
            if kind == "IPV4_PREFIX_MISMATCH":
                cause += " Värdadressen var oförändrad; nätmasken ändrade det direktanslutna nätet."
        trace = broken["request"]
        if broken["reply"] is not None and broken["reply"]["status"] != "DELIVERED":
            trace = broken["reply"]
        failed_step = next((step for step in trace["steps"]
                            if step["arp"]["status"] not in ("RESOLVED", "NOT_NEEDED")), None)
        evidence = (f"Echo Request: {broken['request']['status']}; "
                    f"Echo Reply: {broken['reply']['status'] if broken['reply'] else 'inget svar'}. ")
        if failed_step is not None:
            evidence += (f"På {failed_step['node']} gav ARP för "
                         f"{failed_step['nextHopIpv4']} status "
                         f"{failed_step['arp']['status']}.")
        elif trace["status"] == "NO_ROUTE":
            evidence += f"Routing för {trace['destinationIpv4']} gav NO_ROUTE."
        else:
            evidence += f"Paketspåret slutade med {trace['status']}."
        return {
            "symptom": (f"Simulerat Echo från {self.source_ipv4} till "
                        f"{self.destination_ipv4} misslyckades ({broken['status']})."),
            "rootCause": cause,
            "evidence": evidence,
            "action": action,
            "verification": (f"Efter återställning levererades Echo Request och ett matchande "
                             f"Echo Reply från {self.destination_ipv4} till {self.source_ipv4} "
                             f"({restored['status']})."),
        }


class IcmpInvestigationRegistry(IdleSessions):
    def __init__(self, *, clock=None):
        self._lock = RLock()
        self._sessions: dict[str, IcmpInvestigation] = {}
        self._init_idle(clock)

    def _get(self, session_id: object) -> IcmpInvestigation:
        if type(session_id) is not str or not self._live(session_id):
            raise ProjectValidationError("icmp investigation: unknown or expired session")
        return self._sessions[session_id]

    def start(self, project: object, source_node: str, source_port: str,
              destination_ipv4: str, ttl: int, *, lesson: str | None = None) -> dict:
        with self._lock:
            self._reap_expired()
            if len(self._sessions) >= MAX_SESSIONS:
                raise ProjectValidationError("icmp investigation: session limit reached")
            instance = IcmpInvestigation(
                project, source_node, source_port, destination_ipv4, ttl, lesson=lesson)
            session_id = secrets.token_urlsafe(24)
            self._sessions[session_id] = instance
            self._track(session_id)
            return {"sessionId": session_id, **instance.state()}

    @session_activity
    def probe(self, session_id: object, project: object, kind: object,
              target: object) -> dict:
        with self._lock:
            instance = self._get(session_id)
            instance.check_project(project)
            return {"sessionId": session_id, **instance.probe(kind, target)}

    @session_activity
    def diagnose(self, session_id: object, project: object,
                 diagnosis: object) -> dict:
        with self._lock:
            instance = self._get(session_id)
            instance.check_project(project)
            return {"sessionId": session_id, **instance.diagnose(diagnosis)}

    @session_activity
    def repair(self, session_id: object, project: object) -> dict:
        with self._lock:
            instance = self._get(session_id)
            instance.check_project(project)
            return {"sessionId": session_id, **instance.repair()}

    def stop(self, session_id: object) -> dict:
        with self._lock:
            self._get(session_id)
            del self._sessions[session_id]
            self._forget(session_id)
            return {"status": "STOPPED"}
