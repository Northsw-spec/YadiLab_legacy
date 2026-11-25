"""True DHCP DISCOVER/OFFER bytes, L2 forwarding and real HTTP negative tests."""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from network_core.dhcp import (
    DhcpMessage, _datagram, _decode_datagram, discover_offer,
)
from network_core.ethernet_frame import BROADCAST, EthernetFrame
from network_core.model import ProjectValidationError, blank_project
from network_core.server import LabHTTPServer
from network_core.storage import ProjectStore
from test_ethernet import link, node

CLIENT_MAC = "02:00:00:00:00:0A"
SERVER_MAC = "02:00:00:00:00:0B"


def topology():
    p = blank_project("Explicit DHCP lesson")
    p["nodes"] = [
        node("client", "host", ["eth0"]),
        node("sw", "switch", ["c", "s"]),
        node("server", "host", ["eth0"]),
    ]
    p["nodes"][0]["ports"][0]["mac"] = CLIENT_MAC
    p["nodes"][2]["ports"][0]["mac"] = SERVER_MAC
    p["nodes"][2]["ports"][0]["ipv4"] = "192.0.2.1/24"
    p["links"] = [
        link("to-client", "client", "eth0", "sw", "c"),
        link("to-server", "sw", "s", "server", "eth0"),
    ]
    return p


def exchange(p=None, *, proposed="192.0.2.70"):
    return discover_offer(
        topology() if p is None else p, "client", "eth0", "server", "eth0",
        proposed, 0x12345678, 3600,
    )


class DhcpCodecTests(unittest.TestCase):
    def test_real_bootp_options_udp_ipv4_checksum_and_roundtrip(self):
        request = DhcpMessage(1, 0x12345678, CLIENT_MAC)
        offer = DhcpMessage(2, 0x12345678, CLIENT_MAC,
                            "192.0.2.70", "192.0.2.1", "255.255.255.0", 3600)
        for message, source, src_port, dst_port in (
            (request, "0.0.0.0", 68, 67),
            (offer, "192.0.2.1", 67, 68),
        ):
            with self.subTest(type=message.message_type):
                payload = message.serialize()
                self.assertEqual(len(payload), 300)
                self.assertEqual(payload[236:240], bytes.fromhex("63825363"))
                self.assertEqual(DhcpMessage.parse(payload), message)
                wire = _datagram(message, source)
                self.assertEqual(wire[:1], b"\x45")
                self.assertEqual(wire[9], 17)
                self.assertEqual(int.from_bytes(wire[20:22], "big"), src_port)
                self.assertEqual(int.from_bytes(wire[22:24], "big"), dst_port)
                frame = EthernetFrame.parse(
                    EthernetFrame(BROADCAST,
                                  CLIENT_MAC if message.message_type == 1 else SERVER_MAC,
                                  0x0800, wire).serialize())
                self.assertEqual(_decode_datagram(frame), (source, message))
                self.assertEqual(int.from_bytes(wire[2:4], "big"), len(wire))

    def test_dhcp_offer_and_ack_reject_loopback_and_this_network_addresses(self):
        # RFC 1122: 127/8 stays inside a host; 0/8 is special for
        # initialization. Neither is a usable leased address or server ID
        # on the simulated Ethernet. DHCPDISCOVER's actual 0.0.0.0 source
        # remains permitted by the separate bootstrap IPv4 codec.
        for illegal in ("127.0.0.70", "0.0.0.70"):
            with self.subTest(offered=illegal):
                for kind in (2, 5):
                    with self.assertRaisesRegex(ProjectValidationError,
                                                "usable canonical unicast"):
                        DhcpMessage(kind, 55, CLIENT_MAC, illegal,
                                    "192.0.2.1", "255.255.255.0", 3600)
            with self.subTest(server=illegal):
                for kind in (2, 5):
                    with self.assertRaisesRegex(ProjectValidationError,
                                                "usable canonical unicast"):
                        DhcpMessage(kind, 55, CLIENT_MAC, "192.0.2.70",
                                    illegal, "255.255.255.0", 3600)

    def test_offer_ack_reject_subnet_network_and_broadcast_yiaddr(self):
        # RFC 2131 yiaddr assigns a *host* IP. A globally valid unicast
        # address is not necessarily usable for the offered subnet mask.
        from ipaddress import IPv4Address

        cases = (
            ("192.0.2.0", "192.0.2.70", "192.0.2.1", "255.255.255.0"),
            ("192.0.2.255", "192.0.2.70", "192.0.2.1", "255.255.255.0"),
            ("198.51.100.4", "198.51.100.6", "198.51.100.5", "255.255.255.252"),
            ("198.51.100.7", "198.51.100.6", "198.51.100.5", "255.255.255.252"),
        )
        for offered, usable, server, mask in cases:
            for kind in (2, 5):
                with self.subTest(offered=offered, kind=kind):
                    # First prove the independent positive case with the
                    # SAME mask/server, to isolate the proposed host address.
                    valid = DhcpMessage(kind, 0x120301, CLIENT_MAC,
                                        usable, server, mask, 3600)
                    self.assertEqual(DhcpMessage.parse(valid.serialize()), valid)

                    # Native constructor and independently altered raw BOOTP
                    # must agree that subnet network/broadcast is not a lease.
                    with self.assertRaisesRegex(ProjectValidationError,
                                                "network or broadcast"):
                        DhcpMessage(kind, 0x120301, CLIENT_MAC,
                                    offered, server, mask, 3600)
                    raw = bytearray(valid.serialize())
                    raw[16:20] = IPv4Address(offered).packed
                    with self.assertRaisesRegex(ProjectValidationError,
                                                "network or broadcast"):
                        DhcpMessage.parse(bytes(raw))

        # DHCPDISCOVER's 0.0.0.0 bootstrap source remains a distinct,
        # separately validated wire case; no yiaddr is assigned yet.
        self.assertEqual(DhcpMessage.parse(
            DhcpMessage(1, 5, CLIENT_MAC).serialize()).message_type, 1)

    def test_reject_corrupt_udp_and_ipv4_checksums(self):
        request = DhcpMessage(1, 1, CLIENT_MAC)
        wire = _datagram(request, "0.0.0.0")
        for offset in (10, 21, 40):
            bad = bytearray(wire)
            bad[offset] ^= 1
            frame = EthernetFrame(BROADCAST, CLIENT_MAC, 0x0800, bytes(bad))
            with self.subTest(offset=offset), self.assertRaises(ProjectValidationError):
                _decode_datagram(frame)

    def test_reject_corrupt_bootp_cookie_options_mac_and_id(self):
        message = DhcpMessage(1, 2, CLIENT_MAC)
        for position, value in ((236, 0), (240, 42), (242, 9),
                                (243, 0), (299, 1), (0, 3)):
            bad = bytearray(message.serialize())
            bad[position] = value
            with self.subTest(position=position), self.assertRaises(ProjectValidationError):
                DhcpMessage.parse(bytes(bad))
        with self.assertRaises(ProjectValidationError):
            DhcpMessage(1, 0, CLIENT_MAC)
        with self.assertRaises(ProjectValidationError):
            DhcpMessage(1, True, CLIENT_MAC)
        with self.assertRaises(ProjectValidationError):
            DhcpMessage(1, 2, CLIENT_MAC, "192.0.2.70")
        with self.assertRaises(ProjectValidationError):
            DhcpMessage(2, 2, CLIENT_MAC, "192.0.2.70",
                        "192.0.2.1", "255.0.255.0", 3600)
        with self.assertRaises(ProjectValidationError):
            DhcpMessage(2, 2, CLIENT_MAC, "192.0.2.70",
                        "192.0.2.1", "255.255.255.0", True)


class DhcpSimulationTests(unittest.TestCase):
    def test_discover_offer_exercises_two_real_l2_broadcasts_without_assignment(self):
        project = topology()
        original = copy.deepcopy(project)
        result = exchange(project)
        self.assertEqual(result["status"], "OFFER_RECEIVED")
        self.assertTrue(result["discover"]["receivedAtServer"])
        self.assertEqual([t["linkId"] for t in result["discover"]["transmissions"]],
                         ["to-client", "to-server"])
        self.assertEqual([t["linkId"] for t in result["offer"]["transmissions"]],
                         ["to-server", "to-client"])
        self.assertEqual(result["offeredIpv4"], "192.0.2.70")
        self.assertEqual(result["subnetMask"], "255.255.255.0")
        self.assertEqual(result["serverIdentifier"], "192.0.2.1")
        self.assertFalse(result["leaseCommitted"])
        self.assertTrue(result["ephemeral"])
        self.assertEqual(project, original)
        self.assertIsNone(project["nodes"][0]["ports"][0]["ipv4"])
        self.assertEqual(result["macTables"][0]["entries"][CLIENT_MAC], "c")
        self.assertEqual(result["macTables"][0]["entries"][SERVER_MAC], "s")

    def test_disabled_link_no_offer_and_no_fabricated_sender(self):
        p = topology()
        p["links"][0]["enabled"] = False
        r = exchange(p)
        self.assertEqual(r["status"], "NO_ACTIVE_LINK")
        self.assertEqual(r["discover"]["transmissions"], [])
        self.assertEqual(r["offer"]["transmissions"], [])
        self.assertEqual(r["macTables"], [])
        p = topology()
        p["links"][1]["enabled"] = False
        r = exchange(p)
        self.assertEqual(r["status"], "DISCOVER_NOT_RECEIVED")
        self.assertEqual([t["linkId"] for t in r["discover"]["transmissions"]], ["to-client"])
        self.assertEqual(r["offer"]["transmissions"], [])
        self.assertIsNone(r["offeredIpv4"])

    def test_vlan_isolated_server_does_not_offer_but_same_vlan_does(self):
        p = topology()
        p["nodes"][1]["ports"][0]["vlan"] = {"mode":"access","vlan":10}
        p["nodes"][1]["ports"][1]["vlan"] = {"mode":"access","vlan":20}
        self.assertEqual(exchange(p)["status"], "DISCOVER_NOT_RECEIVED")
        p["nodes"][1]["ports"][1]["vlan"] = {"mode":"access","vlan":10}
        r = exchange(p)
        self.assertEqual(r["status"], "OFFER_RECEIVED")
        self.assertEqual([v["vlanId"] for v in r["discover"]["transmissions"]], [None, 10])
        self.assertEqual([v["vlanId"] for v in r["offer"]["transmissions"]], [None, 10])

    def test_unconfigured_server_or_client_is_not_inferred(self):
        p = topology()
        p["nodes"][0]["ports"][0].pop("mac")
        with self.assertRaisesRegex(ProjectValidationError, "explicit MAC"):
            exchange(p)
        p = topology()
        p["nodes"][2]["ports"][0].pop("mac")
        with self.assertRaisesRegex(ProjectValidationError, "explicit MAC"):
            exchange(p)
        p = topology()
        p["nodes"][2]["ports"][0]["ipv4"] = None
        with self.assertRaisesRegex(ProjectValidationError, "IPv4/CIDR"):
            exchange(p)
        p = topology()
        p["nodes"][0]["ports"][0]["ipv4"] = "192.0.2.20/24"
        with self.assertRaisesRegex(ProjectValidationError, "unconfigured"):
            exchange(p)

    def test_bad_candidate_reserved_duplicate_offlink_and_invalid_input(self):
        for addr in ("192.0.2.1", "192.0.2.0", "192.0.2.255",
                     "203.0.113.2", "junk", "192.0.2.070"):
            with self.subTest(addr=addr), self.assertRaises(ProjectValidationError):
                exchange(proposed=addr)
        p = topology()
        p["nodes"][0]["ports"][0]["ipv4"] = "192.0.2.70/24"
        with self.assertRaises(ProjectValidationError):
            exchange(p)
        for xid, lease in ((0,3600), (2,0), (True,3600), (5,True), (5,604801)):
            with self.subTest(xid=xid,lease=lease), self.assertRaises(ProjectValidationError):
                discover_offer(topology(), "client", "eth0", "server", "eth0",
                               "192.0.2.70", xid, lease)

    def test_no_router_as_hidden_relay_and_wrong_selected_ports_rejected(self):
        p = topology()
        for args in (
            ("ghost", "eth0", "server", "eth0"),
            ("client", "bad", "server", "eth0"),
            ("client", "eth0", "sw", "s"),
            ("client", "eth0", "client", "eth0"),
        ):
            with self.subTest(args=args), self.assertRaises(ProjectValidationError):
                discover_offer(p, *args, "192.0.2.70", 5, 3600)
        # A router endpoint does not bridge two attached Ethernet segments.
        p = topology()
        p["nodes"][1]["kind"] = "router"
        # Router ports may not act as unspecified DHCP relay agents.
        for port in p["nodes"][1]["ports"]:
            port["mac"] = "02:00:00:00:00:2" + ("0" if port["id"] == "c" else "1")
            port["ipv4"] = "198.51.100.1/24" if port["id"] == "c" else "203.0.113.1/24"
        self.assertEqual(exchange(p)["status"], "DISCOVER_NOT_RECEIVED")


class DhcpRealHTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = ProjectStore(Path(self.tmp.name))
        self.server = LabHTTPServer(("127.0.0.1", 0), self.store)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}/api/dhcp/discover-offer"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.tmp.cleanup()

    def post(self, request):
        req = Request(self.url, data=json.dumps(request).encode(),
                      headers={"Content-Type":"application/json"})
        try:
            with urlopen(req, timeout=10) as response:
                return response.status, json.loads(response.read())
        except HTTPError as err:
            return err.code, json.loads(err.read())

    @staticmethod
    def body(p):
        return {
            "project": p, "clientNode": "client", "clientPort": "eth0",
            "serverNode": "server", "serverPort": "eth0",
            "proposedIpv4": "192.0.2.70", "transactionId": 7, "leaseSeconds": 3600,
        }

    def test_real_server_and_unmodified_saved_bytes_across_reopened_store(self):
        p = topology()
        self.store.save("baseline", p)
        saved = Path(self.tmp.name) / "baseline.yadilab"
        digest = hashlib.sha256(saved.read_bytes()).hexdigest()
        for _ in range(2):
            code, data = self.post(self.body(p))
            self.assertEqual(code, 200)
            self.assertEqual(data["status"], "OFFER_RECEIVED")
            self.assertTrue(data["discover"]["transmissions"])
            self.assertEqual(hashlib.sha256(saved.read_bytes()).hexdigest(), digest)
            self.assertIsNone(ProjectStore(Path(self.tmp.name)).read("baseline")["project"]["nodes"][0]["ports"][0]["ipv4"])
        self.assertEqual(list(Path(self.tmp.name).glob("*.yadilab")), [saved])

    def test_http_refuses_loopback_and_this_network_dhcp_offers(self):
        baseline = topology()
        self.store.save("baseline", baseline)
        saved = Path(self.tmp.name) / "baseline.yadilab"
        before = saved.read_bytes()
        for server_address, offered in (
                ("127.0.0.1/24", "127.0.0.70"),
                ("0.0.0.1/24", "0.0.0.70")):
            with self.subTest(server=server_address):
                candidate = copy.deepcopy(baseline)
                candidate["nodes"][2]["ports"][0]["ipv4"] = server_address
                body = self.body(candidate)
                body["proposedIpv4"] = offered
                code, response = self.post(body)
                self.assertEqual(code, 422)
                self.assertEqual(response["error"], "INVALID_PROJECT")
                self.assertIn("usable canonical unicast", response["message"])
                self.assertEqual(saved.read_bytes(), before)

    def test_reject_incomplete_http_and_illegal_candidate_preserving_disk(self):
        p = topology()
        self.store.save("baseline", p)
        saved = Path(self.tmp.name) / "baseline.yadilab"
        before = saved.read_bytes()
        good = self.body(p)
        for bad in (
            {k:v for k,v in good.items() if k != "leaseSeconds"},
            {**good, "unrequested": True},
            {**good, "proposedIpv4":"192.0.2.1"},
            {**good, "clientNode":"unknown"},
            {**good, "transactionId":0},
            {**good, "leaseSeconds":True},
            ["not", "a", "request"],
        ):
            code, result = self.post(bad)
            self.assertEqual(code, 422)
            self.assertEqual(result["error"], "INVALID_PROJECT")
            self.assertEqual(saved.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
