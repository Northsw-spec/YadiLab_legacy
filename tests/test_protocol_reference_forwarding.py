"""Independent L2, VLAN and ARP behavior regression oracles.

Expected link traces, endpoint identities, learning decisions and ARP cache
contents are fixed in the assertions rather than copied from the engine.
Sources: RFC 826 and IEEE 802.1Q, within the explicitly limited
Ethernet forwarding model. No physical network access or disk writes.
"""
from __future__ import annotations

import copy
import unittest

from network_core.arp import ArpSession
from network_core.ethernet import EthernetFabric
from test_ethernet import A, B, C, star
from test_vlan import two_switches, trunk


BROADCAST = "FF:FF:FF:FF:FF:FF"
D = "02:00:00:00:00:0D"


def _links(result):
    return [x["linkId"] for x in result["transmissions"]]


def _endpoints(result):
    return [(x["node"], x["port"]) for x in result["endpointArrivals"]]


class IndependentEthernetForwardingTests(unittest.TestCase):
    def test_empty_mac_table_flood_then_two_learned_unicast_directions(self):
        project = star()
        source = copy.deepcopy(project)
        engine = EthernetFabric(project)
        first = engine.inject("a", "eth0", A, B)
        self.assertEqual(_links(first), ["la", "lb", "lc"])
        self.assertEqual(set(_endpoints(first)), {("b", "eth0"), ("c", "eth0")})
        self.assertEqual(first["switchDecisions"][0]["action"], "FLOOD")
        self.assertEqual(engine.mac_table("sw"), {A: "p1"})

        second = engine.inject("b", "eth0", B, A)
        self.assertEqual(_links(second), ["lb", "la"])
        self.assertEqual(_endpoints(second), [("a", "eth0")])
        self.assertEqual(second["switchDecisions"][0]["action"], "FORWARD_UNICAST")
        self.assertEqual(engine.mac_table("sw"), {A: "p1", B: "p2"})

        third = engine.inject("c", "eth0", C, B)
        self.assertEqual(_links(third), ["lc", "lb"])
        self.assertEqual(_endpoints(third), [("b", "eth0")])
        self.assertEqual(third["switchDecisions"][0]["action"], "FORWARD_UNICAST")
        self.assertEqual(engine.mac_table("sw"), {A: "p1", B: "p2", C: "p3"})
        self.assertEqual(project, source, "simulation must not persist learned state")

    def test_document_order_and_coordinates_cannot_make_network_links(self):
        original = star()
        transformed = copy.deepcopy(original)
        transformed["nodes"].reverse()
        transformed["links"].reverse()
        for idx, n in enumerate(transformed["nodes"]):
            n["x"] = 1200 + idx * 360
            n["y"] = 800 + idx * 220
        ref = EthernetFabric(original).inject("a", "eth0", A, BROADCAST)
        test = EthernetFabric(transformed).inject("a", "eth0", A, BROADCAST)
        self.assertEqual(set(_links(ref)), {"la", "lb", "lc"})
        self.assertEqual(set(_links(test)), {"la", "lb", "lc"})
        self.assertEqual(set(_endpoints(ref)), {("b", "eth0"), ("c", "eth0")})
        self.assertEqual(set(_endpoints(test)), {("b", "eth0"), ("c", "eth0")})
        self.assertEqual(test["switchDecisions"][0]["action"], "FLOOD")

        broken = copy.deepcopy(transformed)
        next(link for link in broken["links"] if link["id"] == "lb")["enabled"] = False
        dropped = EthernetFabric(broken).inject("a", "eth0", A, B)
        self.assertEqual(set(_links(dropped)), {"la", "lc"})
        self.assertEqual(_endpoints(dropped), [("c", "eth0")])
        self.assertNotIn("lb", _links(dropped))
        self.assertEqual(set(_endpoints(dropped)), {("c", "eth0")})
        self.assertEqual(
            next(link for link in broken["links"] if link["id"] == "lb")["enabled"],
            False,
        )


class IndependentVlanForwardingTests(unittest.TestCase):
    def test_two_vlan_domains_have_distinct_real_traces_and_learning(self):
        project, ports = two_switches()
        baseline = copy.deepcopy(project)
        fabric = EthernetFabric(project, vlan_ports=ports)

        ten = fabric.inject("a", "eth0", A, BROADCAST)
        self.assertEqual(_links(ten), ["la", "lt", "lb"])
        self.assertEqual(_endpoints(ten), [("b", "eth0")])
        self.assertEqual([(x["tagged"], x["vlanId"]) for x in ten["transmissions"]],
                         [(False, None), (True, 10), (False, 10)])
        self.assertEqual(fabric.mac_table("s1", 10), {A: "h"})
        self.assertEqual(fabric.mac_table("s2", 10), {A: "t"})
        self.assertEqual(fabric.mac_table("s2", 20), {})

        twenty = fabric.inject("c", "eth0", C, BROADCAST)
        self.assertEqual(_links(twenty), ["lc", "lt", "ld"])
        self.assertEqual(_endpoints(twenty), [("d", "eth0")])
        self.assertEqual([(x["tagged"], x["vlanId"]) for x in twenty["transmissions"]],
                         [(False, None), (True, 20), (False, 20)])
        self.assertEqual(fabric.mac_table("s1", 20), {C: "x"})
        self.assertEqual(fabric.mac_table("s2", 20), {C: "t"})
        self.assertEqual(fabric.mac_table("s1", 10), {A: "h"})
        self.assertEqual(project, baseline)

    def test_trunk_disallows_vlan_twenty_without_breaking_vlan_ten(self):
        project, ports = two_switches()
        ports[("s2", "t")] = trunk(10)
        fabric = EthernetFabric(project, vlan_ports=ports)
        denied = fabric.inject("c", "eth0", C, BROADCAST)
        self.assertEqual(_links(denied), ["lc", "lt"])
        self.assertEqual(_endpoints(denied), [])
        self.assertEqual(denied["vlanDrops"], [
            {"switch": "s2", "port": "t", "reason": "TRUNK_NOT_ALLOWED", "vlanId": 20}
        ])
        self.assertEqual(fabric.mac_table("s2", 20), {})
        self.assertEqual(fabric.mac_table("s1", 20), {C: "x"})

        admitted = fabric.inject("a", "eth0", A, BROADCAST)
        self.assertEqual(_links(admitted), ["la", "lt", "lb"])
        self.assertEqual(_endpoints(admitted), [("b", "eth0")])
        self.assertEqual(admitted["vlanDrops"], [])
        self.assertEqual(fabric.mac_table("s2", 10), {A: "t"})


class IndependentArpBroadcastDomainTests(unittest.TestCase):
    def test_same_ipv4_prefix_never_crosses_vlan_and_cache_needs_reply(self):
        project, ports = two_switches()
        configured = {
            "a": ("192.0.2.10/24", A),
            "b": ("192.0.2.20/24", B),
            "c": ("192.0.2.30/24", C),
            "d": ("192.0.2.40/24", D),
        }
        for n in project["nodes"]:
            if n["id"] in configured:
                n["ports"][0]["ipv4"] = configured[n["id"]][0]
        before = copy.deepcopy(project)
        macs = {(n, "eth0"): pair[1] for n, pair in configured.items()}
        session = ArpSession(project, interface_macs=macs, vlan_ports=ports)

        isolated = session.resolve("a", "eth0", "192.0.2.40")
        self.assertEqual(isolated["status"], "NO_REPLY")
        self.assertIsNone(isolated["resolvedMac"])
        self.assertEqual([x["linkId"] for x in isolated["requestTransmissions"]],
                         ["la", "lt", "lb"])
        self.assertEqual(isolated["replyTransmissions"], [])
        self.assertEqual(session.arp_table("a", "eth0"), {})

        found = session.resolve("a", "eth0", "192.0.2.20")
        self.assertEqual(found["status"], "RESOLVED")
        self.assertEqual(found["resolvedMac"], B)
        self.assertEqual([x["linkId"] for x in found["requestTransmissions"]],
                         ["la", "lt", "lb"])
        self.assertEqual([x["linkId"] for x in found["replyTransmissions"]],
                         ["lb", "lt", "la"])
        self.assertEqual(session.arp_table("a", "eth0"), {"192.0.2.20": B})

        cached = session.resolve("a", "eth0", "192.0.2.20")
        self.assertEqual(cached["status"], "CACHE_HIT")
        self.assertEqual(cached["requestTransmissions"], [])
        self.assertEqual(cached["replyTransmissions"], [])
        self.assertEqual(project, before)

        fresh = ArpSession(project, interface_macs=macs, vlan_ports=ports)
        self.assertEqual(fresh.arp_table("a", "eth0"), {})


if __name__ == "__main__":
    unittest.main()
