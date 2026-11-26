"""Independent negative IPv4 address-class boundaries (RFC 1122 / RFC 3927).

The expected outcomes come from published address scope requirements, not from
existing simulator status strings. Do not re-label successful wire delivery
for loopback, this-network or routed link-local traffic as correct.
"""
from __future__ import annotations

from copy import deepcopy
import unittest

from network_core.icmp_ping import EchoExchange
from network_core.ipv4 import IPv4Trace
from network_core.ipv4_packet import IPv4Datagram
from network_core.model import ProjectValidationError, validate_project
from test_icmp_investigation_lan import lan_lab
from test_ipv4_forwarding import lab, getport


class IPv4SpecialAddressOracles(unittest.TestCase):
    def test_loopback_and_this_network_cannot_be_ethernet_datagram_endpoints(self):
        for illegal in ("127.0.0.1", "127.15.20.30", "0.0.0.1", "0.1.2.3"):
            with self.subTest(address=illegal):
                with self.assertRaisesRegex(ProjectValidationError, "usable canonical unicast"):
                    IPv4Datagram(illegal, "192.0.2.20", 5)
                with self.assertRaisesRegex(ProjectValidationError, "usable canonical unicast"):
                    IPv4Datagram("192.0.2.10", illegal, 5)

    def test_existing_project_can_document_loopback_misconfiguration_without_false_delivery(self):
        project = lan_lab()
        project["nodes"][0]["ports"][0]["ipv4"] = "127.10.20.10/8"
        project["nodes"][2]["ports"][0]["ipv4"] = "127.10.20.20/8"
        canonical = validate_project(project)
        self.assertEqual(canonical["nodes"][0]["ports"][0]["ipv4"], "127.10.20.10/8")
        with self.assertRaisesRegex(ProjectValidationError, "usable canonical unicast"):
            IPv4Trace(canonical).send("a", "eth0", "127.10.20.20", 5)
        with self.assertRaisesRegex(ProjectValidationError, "usable canonical unicast"):
            EchoExchange(canonical).ping("a", "eth0", "127.10.20.20", 5, 19, 1)

    def test_link_local_same_l2_domain_is_not_incorrectly_banned(self):
        project = lan_lab()
        project["nodes"][0]["ports"][0]["ipv4"] = "169.254.10.10/16"
        project["nodes"][2]["ports"][0]["ipv4"] = "169.254.10.20/16"
        original = deepcopy(project)
        result = EchoExchange(project).ping("a", "eth0", "169.254.10.20", 5, 19, 1)
        self.assertEqual(result["status"], "REPLIED")
        self.assertTrue(result["replyMatched"])
        self.assertEqual(result["request"]["status"], "DELIVERED")
        self.assertEqual(result["reply"]["status"], "DELIVERED")
        self.assertEqual(project, original)

    def test_link_local_source_must_not_send_to_router_for_transit(self):
        project = lab()
        getport(project, "a", "eth0")["ipv4"] = "169.254.10.10/16"
        getport(project, "r", "wan")["ipv4"] = "169.254.10.1/16"
        project["nodes"][0]["staticRoutes"][0]["nextHop"] = "169.254.10.1"
        original = deepcopy(project)
        result = IPv4Trace(project).send("a", "eth0", "203.0.113.20", 5)
        self.assertEqual(result["status"], "LINK_LOCAL_ROUTING_FORBIDDEN")
        self.assertEqual(result["steps"], [])
        self.assertFalse(result["icmpSent"])
        ping = EchoExchange(project).ping("a", "eth0", "203.0.113.20", 5, 2, 1)
        self.assertEqual(ping["status"], "REQUEST_FAILED")
        self.assertIsNone(ping["reply"])
        self.assertEqual(ping["request"]["status"], "LINK_LOCAL_ROUTING_FORBIDDEN")
        self.assertEqual(project, original)

    def test_link_local_destination_must_not_be_sent_through_gateway(self):
        project = lab()
        project["nodes"][0]["staticRoutes"][0]["destination"] = "169.254.0.0/16"
        original = deepcopy(project)
        result = IPv4Trace(project).send("a", "eth0", "169.254.10.20", 5)
        self.assertEqual(result["status"], "LINK_LOCAL_ROUTING_FORBIDDEN")
        self.assertEqual(result["steps"], [])
        self.assertIsNone(result["routerErrorCandidate"])
        self.assertEqual(project, original)

    def test_connected_network_and_directed_broadcast_are_not_fake_arp_failures(self):
        project = lab()
        original = deepcopy(project)
        for dest in ("192.0.2.0", "192.0.2.255"):
            with self.subTest(destination=dest):
                result = IPv4Trace(project).send("a", "eth0", dest, 5)
                self.assertEqual(result["status"], "NON_UNICAST_DESTINATION")
                self.assertIn("not a modeled unicast IPv4 receiver", result["meaning"])
                self.assertEqual(result["steps"], [])
                self.assertEqual(result["macTables"], [])
                self.assertIsNone(result["receiver"])
                self.assertIsNone(result["routerErrorCandidate"])
                self.assertFalse(result["icmpSent"])
                echo = EchoExchange(project).ping("a", "eth0", dest, 5, 19, 1)
                self.assertEqual(echo["status"], "REQUEST_FAILED")
                self.assertEqual(echo["request"]["status"], "NON_UNICAST_DESTINATION")
                self.assertIsNone(echo["reply"])
                self.assertIsNone(echo["icmpError"])
        self.assertEqual(project, original)

    def test_remote_directed_broadcast_does_not_turn_into_arp_error(self):
        project = lab()
        original = deepcopy(project)
        result = IPv4Trace(project).send("a", "eth0", "203.0.113.255", 5)
        self.assertEqual(result["status"], "NON_UNICAST_DESTINATION")
        # The source sent a valid unicast datagram to the documented gateway;
        # its final connected subnet cannot provide a unicast receiver.
        self.assertEqual([step["node"] for step in result["steps"]], ["a"])
        self.assertEqual(result["steps"][0]["arp"]["status"], "RESOLVED")
        self.assertTrue(result["steps"][0]["ipv4Transmissions"])
        self.assertIsNone(result["receiver"])
        self.assertIsNone(result["routerErrorCandidate"])
        self.assertEqual(project, original)

    def test_31_peer_address_must_not_be_confused_with_broadcast(self):
        project = lan_lab()
        project["nodes"][0]["ports"][0]["ipv4"] = "192.0.2.0/31"
        project["nodes"][2]["ports"][0]["ipv4"] = "192.0.2.1/31"
        original = deepcopy(project)
        result = EchoExchange(project).ping("a", "eth0", "192.0.2.1", 5, 19, 1)
        self.assertEqual(result["status"], "REPLIED")
        self.assertTrue(result["replyMatched"])
        self.assertEqual(result["request"]["status"], "DELIVERED")
        self.assertEqual(result["reply"]["status"], "DELIVERED")
        self.assertEqual(project, original)

    def test_no_overrestriction_of_explicit_private_and_test_networks(self):
        for src, dst in (("10.0.0.10", "192.168.1.20"),
                         ("192.0.2.10", "203.0.113.20"),
                         ("198.51.100.10", "10.10.10.20")):
            with self.subTest(source=src, destination=dst):
                packet = IPv4Datagram(src, dst, 64)
                self.assertEqual(IPv4Datagram.parse(packet.serialize()), packet)


if __name__ == "__main__":
    unittest.main()
