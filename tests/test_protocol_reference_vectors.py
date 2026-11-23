"""QUALITY-003: fixed external protocol vectors, specified before engine results.

The expected bytes/decisions below are independent constants taken from
published wire-format rules, not computed by the implementation under test.
References: RFC 894, RFC 826, RFC 791, RFC 792, RFC 1071, RFC 1812,
RFC 2131, RFC 3021 and IEEE 802.1Q (see docs/PROTOCOL_REFERENCE_MATRIX.md).

These tests cover only the explicitly implemented subset, never imply
complete protocol compliance or real network reachability.
"""
from __future__ import annotations

import copy
import unittest

from network_core.arp import ArpMessage
from network_core.dhcp import DhcpMessage
from network_core.ethernet_frame import EthernetFrame
from network_core.icmp import ICMPEcho
from network_core.ipv4_packet import ICMP_PROTOCOL, IPv4Datagram, checksum
from network_core.model import ProjectValidationError, blank_project
from network_core.routing import ConnectedRoutingTable
from test_ethernet import node


SOURCE_MAC = "02:00:00:00:00:0A"
TARGET_MAC = "02:00:00:00:00:0B"


class IndependentProtocolReferenceVectors(unittest.TestCase):
    def test_ethernet_rfc894_exact_ethertype_padding_and_negative_length(self):
        # 6+6+2 byte Ethernet II header, EtherType 0800; no FCS.
        golden = bytes.fromhex("02000000000b 02000000000a 0800") + b"IP!" + bytes(43)
        self.assertEqual(len(golden), 60)
        actual = EthernetFrame(TARGET_MAC, SOURCE_MAC, 0x0800, b"IP!").serialize()
        self.assertEqual(actual, golden)
        decoded = EthernetFrame.parse(golden)
        self.assertEqual((decoded.destination, decoded.source, decoded.ether_type),
                         (TARGET_MAC, SOURCE_MAC, 0x0800))
        with self.assertRaises(ProjectValidationError):
            EthernetFrame.parse(golden[:-1])

    def test_vlan_8021q_exact_single_ctag_and_invalid_tag(self):
        # TPID=8100, PCP=DEI=0, VID=37 (0025), inner EtherType=0800.
        golden = bytes.fromhex("02000000000b 02000000000a 8100 0025 0800") + b"IP!" + bytes(39)
        self.assertEqual(len(golden), 60)
        actual = EthernetFrame(TARGET_MAC, SOURCE_MAC, 0x0800, b"IP!", vlan_id=37)
        self.assertEqual(actual.serialize(), golden)
        self.assertEqual(EthernetFrame.parse(golden).vlan_id, 37)
        forbidden_pcp = golden[:14] + bytes.fromhex("2025") + golden[16:]
        with self.assertRaises(ProjectValidationError):
            EthernetFrame.parse(forbidden_pcp)  # outside supported PCP=0 model

    def test_arp_rfc826_exact_request_and_invalid_hardware_length(self):
        # Hardware=1, IPv4=0800, hlen=6, plen=4, opcode=1.
        # Sender: 02:00:00:00:00:0A / 192.0.2.10
        # Target: 00:00:00:00:00:00 / 192.0.2.20
        golden = bytes.fromhex(
            "0001 0800 06 04 0001 02000000000a c000020a"
            " 000000000000 c0000214"
        )
        self.assertEqual(len(golden), 28)
        request = ArpMessage(1, SOURCE_MAC, "192.0.2.10",
                             "00:00:00:00:00:00", "192.0.2.20")
        self.assertEqual(request.serialize(), golden)
        self.assertEqual(ArpMessage.parse(golden), request)
        invalid = bytearray(golden)
        invalid[4] = 5
        with self.assertRaises(ProjectValidationError):
            ArpMessage.parse(bytes(invalid))

    def test_rfc1071_independently_published_checksum_example(self):
        # RFC 1071 section 3 numeric example: final folded sum DDF2,
        # one's complement 220D. Not derived from an application packet.
        self.assertEqual(checksum(bytes.fromhex("0001 f203 f4f5 f6f7")), 0x220D)

    def test_icmp_rfc792_exact_echo_and_checksum_corruption(self):
        # Independent 12-byte Echo Request:
        # type=8/code=0, checksum=06FA, ID=1234, sequence=1, payload='ping'.
        request_raw = bytes.fromhex("0800 06fa 1234 0001 70696e67")
        reply_raw = bytes.fromhex("0000 0efa 1234 0001 70696e67")
        packet = ICMPEcho(8, 0x1234, 1, b"ping")
        self.assertEqual(packet.serialize(), request_raw)
        self.assertEqual(ICMPEcho.parse(request_raw), packet)
        self.assertEqual(packet.reply().serialize(), reply_raw)
        self.assertEqual(ICMPEcho.parse(reply_raw).icmp_type, 0)
        corrupt = bytearray(request_raw)
        corrupt[-1] ^= 1
        with self.assertRaises(ProjectValidationError):
            ICMPEcho.parse(bytes(corrupt))
        with self.assertRaises(ProjectValidationError):
            ICMPEcho.parse(reply_raw).reply()

    def test_ipv4_rfc791_exact_20byte_header_and_ttl(self):
        icmp = bytes.fromhex("0800 06fa 1234 0001 70696e67")
        # IPv4 v4/IHL5, len=32, ID=flags=0, TTL64, proto1, sum=8E8B.
        # Source 192.0.2.10, destination 198.51.100.20, followed by ICMP.
        golden = bytes.fromhex("4500 0020 0000 0000 4001 8e8b c000020a c6336414") + icmp
        packet = IPv4Datagram("192.0.2.10", "198.51.100.20",
                              64, icmp, ICMP_PROTOCOL)
        self.assertEqual(packet.serialize(), golden)
        self.assertEqual(IPv4Datagram.parse(golden), packet)
        self.assertEqual(packet.forwarded().ttl, 63)
        corrupt = bytearray(golden)
        corrupt[8] = 63  # TTL changed but checksum still authenticates TTL=64
        with self.assertRaises(ProjectValidationError):
            IPv4Datagram.parse(bytes(corrupt))

    def test_rfc1812_longest_prefix_and_no_inferred_reachability(self):
        p = blank_project("LPM reference, no declared cables")
        router = node("r", "router", ["wide", "narrow"])
        router["ports"][0]["ipv4"] = "10.0.0.1/8"
        router["ports"][1]["ipv4"] = "10.8.0.1/16"
        p["nodes"] = [router]
        baseline = copy.deepcopy(p)
        expected = [
            ("10.8.10.20", "10.8.0.0/16", "narrow"),
            ("10.9.2.1", "10.0.0.0/8", "wide"),
        ]
        table = ConnectedRoutingTable(p, "r")
        for dest, prefix, outport in expected:
            with self.subTest(destination=dest):
                result = table.lookup(dest)
                self.assertEqual(result["status"], "MATCH")
                self.assertEqual(result["selectedRoute"]["destination"], prefix)
                self.assertEqual(result["selectedRoute"]["outInterface"]["port"], outport)
                self.assertNotIn("transmissions", result)  # route is not IP delivery
        self.assertEqual(table.lookup("203.0.113.10")["status"], "NO_ROUTE")
        p["nodes"][0]["x"] = 5000
        self.assertEqual(ConnectedRoutingTable(p, "r").lookup("10.8.10.20")["selectedRoute"]["outInterface"]["port"], "narrow")
        p["nodes"][0]["ports"][1]["enabled"] = False
        self.assertEqual(ConnectedRoutingTable(p, "r").lookup("10.8.10.20")["selectedRoute"]["outInterface"]["port"], "wide")
        self.assertEqual(baseline["links"], [])  # no cable ever invented

    def test_dhcp_rfc2131_exact_discover_bootp_cookie_options_and_corruption(self):
        # RFC 2131 BOOTP 236-octet fixed area, cookie 63825363 and
        # option 53/length1/DISCOVER1/END255; padded to 300 octets.
        golden = (
            bytes.fromhex("01010600 10203040 00008000")
            + bytes(16)
            + bytes.fromhex("02000000000a") + bytes(10)
            + bytes(192)
            + bytes.fromhex("63825363 350101ff")
            + bytes(56)
        )
        self.assertEqual(len(golden), 300)
        discover = DhcpMessage(1, 0x10203040, SOURCE_MAC)
        self.assertEqual(discover.serialize(), golden)
        self.assertEqual(DhcpMessage.parse(golden), discover)
        offer = DhcpMessage(2, 0x10203040, SOURCE_MAC, "192.0.2.70",
                            "192.0.2.1", "255.255.255.0", 3600)
        self.assertEqual(
            offer.serialize()[240:262],
            bytes.fromhex("350102 3604c0000201 0104ffffff00 330400000e10 ff"),
        )
        bad = bytearray(golden)
        bad[236] = 0
        with self.assertRaises(ProjectValidationError):
            DhcpMessage.parse(bytes(bad))


if __name__ == "__main__":
    unittest.main()
