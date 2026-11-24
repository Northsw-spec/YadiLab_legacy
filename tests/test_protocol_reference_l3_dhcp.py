"""Independent IPv4/ICMP/DHCP behavioral regression oracles.

Expected outcomes and supported scope are stated in the test assertions;
protocol references include RFC 791, RFC 792 and RFC 2131.
Test fixtures supply explicit synthetic network data, NEVER expected outputs.
No real NICs, real network traffic, time sleeps, disk saves or product edits.
"""
from __future__ import annotations

import copy
import unittest

from network_core.dhcp_registry import DhcpSessionRegistry
from network_core.icmp_errors import ICMPError
from network_core.icmp_ping import EchoExchange
from network_core.ipv4 import IPv4Trace
from network_core.model import ProjectValidationError
from test_dhcp import topology as dhcp_topology
from test_icmp_echo import multihop_reply_lab, routed_reply_lab
from test_icmp_errors import no_router_route
from test_ipv4_forwarding import multihop


class IndependentIpv4RouteOracles(unittest.TestCase):
    def test_three_hop_ttl_boundary_and_no_fabricated_transit_link(self):
        project = multihop()  # documented three-subnet, two-router fixture
        before = copy.deepcopy(project)
        delivered = IPv4Trace(project).send("a", "eth0", "198.51.100.20", 3)
        self.assertEqual(delivered["status"], "DELIVERED")
        self.assertEqual(delivered["receiver"], {"node": "b", "port": "eth0"})
        self.assertEqual([s["node"] for s in delivered["steps"]], ["a", "r", "r2"])
        self.assertEqual([s["ttlSent"] for s in delivered["steps"]], [3, 2, 1])
        self.assertEqual(delivered["finalTtl"], 1)
        self.assertEqual(project, before)

        expired = IPv4Trace(project).send("a", "eth0", "198.51.100.20", 2)
        self.assertEqual(expired["status"], "TTL_EXPIRED")
        self.assertEqual([s["node"] for s in expired["steps"]], ["a", "r"])
        self.assertIsNone(expired["receiver"])
        self.assertFalse(expired["icmpSent"])

        unplugged = copy.deepcopy(project)
        next(cable for cable in unplugged["links"]
             if cable["id"] == "to-r2")["enabled"] = False
        failed = IPv4Trace(unplugged).send("a", "eth0", "198.51.100.20", 3)
        self.assertNotEqual(failed["status"], "DELIVERED")
        self.assertIsNone(failed["receiver"])
        self.assertEqual(project, before)

    def test_echo_request_delivery_is_not_a_reply_without_reverse_route(self):
        project = multihop_reply_lab()
        before = copy.deepcopy(project)
        success = EchoExchange(project).ping("a", "eth0", "198.51.100.20", 4, 0x0137, 2)
        self.assertEqual(success["status"], "REPLIED")
        self.assertTrue(success["replyMatched"])
        self.assertEqual(success["request"]["status"], "DELIVERED")
        self.assertEqual(success["reply"]["status"], "DELIVERED")
        self.assertEqual([s["node"] for s in success["request"]["steps"]], ["a", "r", "r2"])
        self.assertEqual([s["node"] for s in success["reply"]["steps"]], ["b", "r2", "r"])
        self.assertEqual(success["request"]["finalTtl"], 2)
        self.assertEqual(success["reply"]["finalTtl"], 62)
        self.assertEqual(success["replyInitialTtl"], 64)
        self.assertEqual(success["replyTtlBasis"], "SIMULATED_DEFAULT")
        self.assertEqual(project, before)

        no_return = copy.deepcopy(project)
        next(node for node in no_return["nodes"] if node["id"] == "b").pop("staticRoutes")
        failed = EchoExchange(no_return).ping(
            "a", "eth0", "198.51.100.20", 4, 0x0137, 2)
        self.assertEqual(failed["status"], "REPLY_FAILED")
        self.assertFalse(failed["replyMatched"])
        self.assertEqual(failed["request"]["status"], "DELIVERED")
        self.assertEqual(failed["reply"]["status"], "NO_ROUTE")
        self.assertIsNone(failed["rttMs"])


class IndependentIcmpRouterErrorOracles(unittest.TestCase):
    def test_exact_rfc792_error_vectors_and_modified_quote_rejection(self):
        # Fixed RFC 791 original IPv4 header plus eight RFC 792 Echo bytes.
        quote = bytes.fromhex(
            "4500001c000000000101bbc2c000020acb007114"
            "0800f7ff00000000"
        )
        golden = {
            11: bytes.fromhex(
                "0b00f4ff00000000"
                "4500001c000000000101bbc2c000020acb007114"
                "0800f7ff00000000"
            ),
            3: bytes.fromhex(
                "0300fcff00000000"
                "4500001c000000000101bbc2c000020acb007114"
                "0800f7ff00000000"
            ),
        }
        self.assertEqual(len(quote), 28)
        for icmp_type in (11, 3):
            with self.subTest(type=icmp_type):
                message = ICMPError(icmp_type, 0, quote)
                self.assertEqual(message.serialize(), golden[icmp_type])
                self.assertEqual(ICMPError.parse(golden[icmp_type]), message)
                self.assertEqual(message.quoted_source, "192.0.2.10")
                self.assertEqual(message.quoted_destination, "203.0.113.20")
                changed = bytearray(golden[icmp_type])
                changed[35] ^= 1
                with self.assertRaises(ProjectValidationError):
                    ICMPError.parse(bytes(changed))

    def test_router_only_generates_correct_error_after_real_ingress(self):
        base = routed_reply_lab()
        before = copy.deepcopy(base)
        ttl = EchoExchange(base).ping("a", "eth0", "203.0.113.20", 1, 2, 8)
        self.assertEqual(ttl["status"], "REQUEST_FAILED")
        self.assertEqual(ttl["request"]["status"], "TTL_EXPIRED")
        self.assertFalse(ttl["replyMatched"])
        self.assertIsNone(ttl["reply"])
        self.assertEqual(ttl["icmpError"]["type"], 11)
        self.assertEqual(ttl["icmpError"]["code"], 0)
        self.assertEqual(ttl["icmpError"]["status"], "RECEIVED")
        self.assertEqual(ttl["icmpError"]["sourceNode"], "r")
        self.assertEqual(ttl["icmpError"]["sourcePort"], "wan")
        self.assertEqual(ttl["icmpError"]["trace"]["receiver"], {"node": "a", "port": "eth0"})
        self.assertEqual(base, before)

        no_route = no_router_route()  # a has route; r has NO_ROUTE to 198.51.100.20
        blocked = EchoExchange(no_route).ping(
            "a", "eth0", "198.51.100.20", 4, 2, 8)
        self.assertEqual(blocked["status"], "REQUEST_FAILED")
        self.assertEqual(blocked["request"]["status"], "NO_ROUTE")
        self.assertEqual(blocked["icmpError"]["type"], 3)
        self.assertEqual(blocked["icmpError"]["code"], 0)
        self.assertEqual(blocked["icmpError"]["status"], "RECEIVED")
        self.assertFalse(blocked["replyMatched"])


class IndependentDhcpVirtualLeaseOracles(unittest.TestCase):
    @staticmethod
    def start(project):
        registry = DhcpSessionRegistry()
        session_id = registry.start(
            project, "server", "eth0", "192.0.2.70", "192.0.2.71"
        )["sessionId"]
        return registry, session_id

    def test_dora_then_t1_unicast_renews_only_after_real_ack(self):
        project = dhcp_topology()
        before = copy.deepcopy(project)
        registry, sid = self.start(project)
        initial = registry.run(sid, project, "client", "eth0", 111, 80)
        self.assertEqual(initial["result"]["status"], "ACK_RECEIVED")
        self.assertTrue(initial["result"]["leaseCommitted"])
        for stage, expected in (
            ("discover", ["to-client", "to-server"]),
            ("offer", ["to-server", "to-client"]),
            ("request", ["to-client", "to-server"]),
            ("ack", ["to-server", "to-client"]),
        ):
            self.assertEqual(
                [item["linkId"] for item in initial["result"][stage]["transmissions"]],
                expected, stage)
        self.assertEqual(initial["leaseCount"], 1)
        lease = initial["leases"][0]
        self.assertEqual(lease["state"], "BOUND")
        self.assertEqual(lease["ipv4"], "192.0.2.70")
        self.assertEqual((
            lease["startedAtSeconds"], lease["t1AtSeconds"],
            lease["t2AtSeconds"], lease["expiresAtSeconds"],
        ), (0, 40, 70, 80))

        registry.advance(sid, project, 39)
        with self.assertRaisesRegex(ProjectValidationError, "T1 not reached"):
            registry.renew(sid, project, "client", "eth0", 112)
        self.assertEqual(registry._get(sid).state()["leases"][0]["expiresAtSeconds"], 80)
        registry.advance(sid, project, 1)
        renewal = registry.renew(sid, project, "client", "eth0", 113)
        self.assertEqual(renewal["result"]["phase"], "RENEWING")
        self.assertEqual(renewal["result"]["status"], "ACK_RECEIVED")
        self.assertTrue(renewal["result"]["leaseRenewed"])
        self.assertEqual(renewal["result"]["request"]["ipDestination"], "192.0.2.1")
        self.assertEqual(renewal["result"]["request"]["ethernetDestination"], "02:00:00:00:00:0B")
        self.assertTrue(renewal["result"]["request"]["receivedAtServer"])
        self.assertTrue(renewal["result"]["ack"]["receivedAtClient"])
        current = renewal["leases"][0]
        self.assertEqual((
            current["startedAtSeconds"], current["t1AtSeconds"],
            current["t2AtSeconds"], current["expiresAtSeconds"],
            current["renewalCount"],
        ), (40, 80, 110, 120, 1))
        self.assertEqual(project, before)
        self.assertIsNone(project["nodes"][0]["ports"][0]["ipv4"])

    def test_lost_server_cable_prevents_t1_t2_and_lease_expires(self):
        project = dhcp_topology()
        before = copy.deepcopy(project)
        registry, sid = self.start(project)
        first = registry.run(sid, project, "client", "eth0", 221, 80)
        self.assertEqual(first["result"]["status"], "ACK_RECEIVED")
        fault = registry.link_fault(sid, project, "to-server", True)
        self.assertEqual(fault["faultedLinks"], ["to-server"])

        registry.advance(sid, project, 40)
        t1 = registry.renew(sid, project, "client", "eth0", 222)
        self.assertEqual(t1["result"]["phase"], "RENEWING")
        self.assertEqual(t1["result"]["status"], "REQUEST_NOT_RECEIVED")
        self.assertFalse(t1["result"]["leaseRenewed"])
        self.assertEqual(t1["result"]["ack"]["transmissions"], [])
        self.assertEqual(t1["result"]["request"]["ipDestination"], "192.0.2.1")
        self.assertEqual(t1["leases"][0]["expiresAtSeconds"], 80)

        registry.advance(sid, project, 30)
        t2 = registry.renew(sid, project, "client", "eth0", 223)
        self.assertEqual(t2["result"]["phase"], "REBINDING")
        self.assertEqual(t2["result"]["request"]["ipDestination"], "255.255.255.255")
        self.assertEqual(t2["result"]["request"]["ethernetDestination"], "FF:FF:FF:FF:FF:FF")
        self.assertEqual(t2["result"]["status"], "REQUEST_NOT_RECEIVED")
        self.assertEqual(t2["leases"][0]["expiresAtSeconds"], 80)
        self.assertFalse(t2["result"]["leaseRenewed"])

        expired = registry.advance(sid, project, 10)
        self.assertEqual(expired["clockSeconds"], 80)
        self.assertEqual(expired["leaseCount"], 0)
        self.assertEqual(
            [item["ipv4"] for item in expired["expiredLeases"]], ["192.0.2.70"])
        self.assertEqual(project, before)
        with self.assertRaisesRegex(ProjectValidationError, "no active BOUND"):
            registry.renew(sid, project, "client", "eth0", 224)


if __name__ == "__main__":
    unittest.main()
