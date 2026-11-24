"""Independent IPv4 boundary and metamorphic regression oracles.

Fixed expectations derive from RFC 791, RFC 3021, RFC 1812 and RFC 2131
and explicit physical link declarations. Historic review is in Git history.
Do not generate expected values from the engine under test.
All files are disposable test files; no production or real-network changes.
"""
from __future__ import annotations

import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from network_core.dhcp_registry import DhcpSessionRegistry
from network_core.icmp_ping import EchoExchange
from network_core.ipv4 import IPv4Trace
from network_core.model import ProjectValidationError, validate_project
from network_core.routing import ConnectedRoutingTable
from network_core.storage import ProjectStore
from test_dhcp_registry import clients
from test_ethernet import node
from test_icmp_echo import routed_reply_lab
from test_icmp_investigation_lan import lan_lab


class IndependentPrefixBoundaryOracles(unittest.TestCase):
    def test_rfc30_31_two_endpoints_and_rejected_network_broadcast(self):
        # /30: network .0, usable .1 and .2, broadcast .3.
        # /31: both addresses are endpoints under the supported model.
        pairs = [
            ("192.0.2.1/30", "192.0.2.2/30"),
            ("192.0.2.0/31", "192.0.2.1/31"),
        ]
        for source_address, destination_address in pairs:
            with self.subTest(source=source_address):
                project = lan_lab()
                project["nodes"][0]["ports"][0]["ipv4"] = source_address
                project["nodes"][2]["ports"][0]["ipv4"] = destination_address
                expected_project = copy.deepcopy(project)
                canonical = validate_project(project)
                answer = EchoExchange(canonical).ping(
                    "a", "eth0", destination_address.split("/")[0], 2, 24, 1)
                self.assertEqual(answer["status"], "REPLIED")
                self.assertTrue(answer["replyMatched"])
                self.assertEqual([s["node"] for s in answer["request"]["steps"]], ["a"])
                self.assertEqual([s["node"] for s in answer["reply"]["steps"]], ["b"])
                self.assertEqual(project, expected_project)

        for invalid in ("192.0.2.0/30", "192.0.2.3/30"):
            with self.subTest(invalid=invalid):
                project = lan_lab()
                project["nodes"][0]["ports"][0]["ipv4"] = invalid
                with self.assertRaisesRegex(ProjectValidationError, "network or broadcast"):
                    validate_project(project)

    def test_32_exact_host_route_never_invents_connected_neighbors(self):
        project = lan_lab()
        project["nodes"][0]["ports"][0]["ipv4"] = "192.0.2.7/32"
        table = ConnectedRoutingTable(project, "a")
        exact = table.lookup("192.0.2.7")
        self.assertEqual(exact["status"], "MATCH")
        self.assertEqual(exact["selectedRoute"]["destination"], "192.0.2.7/32")
        for destination in ("192.0.2.8", "192.168.10.20"):
            with self.subTest(destination=destination):
                self.assertEqual(table.lookup(destination)["status"], "NO_ROUTE")
        not_delivered = IPv4Trace(project).send("a", "eth0", "192.168.10.20", 5)
        self.assertEqual(not_delivered["status"], "NO_ROUTE")
        self.assertEqual(not_delivered["steps"], [])
        self.assertIsNone(not_delivered["receiver"])


class IndependentConnectivityMetamorphicOracles(unittest.TestCase):
    @staticmethod
    def ping(project):
        return EchoExchange(project).ping("a", "eth0", "203.0.113.20", 5, 391, 2)

    def test_every_essential_cable_cut_prevents_successful_ping(self):
        original = routed_reply_lab()
        before = copy.deepcopy(original)
        correct = self.ping(original)
        self.assertEqual(correct["status"], "REPLIED")
        self.assertEqual([s["node"] for s in correct["request"]["steps"]], ["a", "r"])
        self.assertEqual([s["node"] for s in correct["reply"]["steps"]], ["b", "r"])
        for link_id in ("la", "lr1", "lr2", "lb"):
            with self.subTest(link_id=link_id):
                damaged = copy.deepcopy(original)
                next(link for link in damaged["links"] if link["id"] == link_id)["enabled"] = False
                result = self.ping(damaged)
                self.assertNotEqual(result["status"], "REPLIED")
                self.assertFalse(result["replyMatched"])
                self.assertNotEqual(result["request"]["status"], "DELIVERED")
                self.assertNotEqual(result["status"], "REPLY_MISMATCH")
        self.assertEqual(original, before)

    def test_add_unrelated_host_reorder_and_move_nodes_no_network_change(self):
        original = routed_reply_lab()
        baseline = self.ping(original)
        self.assertEqual(baseline["status"], "REPLIED")
        changed = copy.deepcopy(original)
        detached = node("detached", "host", ["eth0"])
        detached["ports"][0]["ipv4"] = "10.220.1.10/24"
        detached["ports"][0]["mac"] = "02:00:00:00:5A:10"
        changed["nodes"].append(detached)  # no declared cable for this host
        changed["nodes"].reverse()
        for i, device in enumerate(changed["nodes"]):
            device["x"] = 1700 + i * 417
            device["y"] = 2900 + i * 293
        answer = self.ping(changed)
        self.assertEqual(answer["status"], "REPLIED")
        self.assertTrue(answer["replyMatched"])
        self.assertEqual([s["node"] for s in answer["request"]["steps"]], ["a", "r"])
        self.assertEqual([s["node"] for s in answer["reply"]["steps"]], ["b", "r"])
        self.assertEqual(
            [[x["linkId"] for x in s["ipv4Transmissions"]]
             for s in answer["request"]["steps"]],
            [["la", "lr1"], ["lr2", "lb"]],
        )
        for result in (answer["request"], answer["reply"]):
            self.assertNotEqual(result["receiver"]["node"], "detached")
        self.assertEqual(len(changed["links"]), 4)
        self.assertEqual(original["nodes"][0]["x"], 0)

    def test_explicit_save_reopen_same_network_result_and_file_bytes(self):
        original = routed_reply_lab()
        before = copy.deepcopy(original)
        with tempfile.TemporaryDirectory() as root:
            store = ProjectStore(Path(root))
            store.save("baseline", original)
            saved = Path(root) / "baseline.yadilab"
            bytes_before = saved.read_bytes()
            digest = hashlib.sha256(bytes_before).hexdigest()
            reopened = ProjectStore(Path(root)).read("baseline")
            self.assertEqual(reopened["sha256"], digest)
            self.assertEqual(set(x["id"] for x in reopened["project"]["links"]),
                             {"la", "lr1", "lr2", "lb"})
            original_result = self.ping(original)
            reopened_result = self.ping(reopened["project"])
            for outcome in (original_result, reopened_result):
                self.assertEqual(outcome["status"], "REPLIED")
                self.assertEqual(
                    [[x["linkId"] for x in s["ipv4Transmissions"]]
                     for s in outcome["request"]["steps"]],
                    [["la", "lr1"], ["lr2", "lb"]],
                )
                self.assertEqual(
                    [[x["linkId"] for x in s["ipv4Transmissions"]]
                     for s in outcome["reply"]["steps"]],
                    [["lb", "lr2"], ["lr1", "la"]],
                )
            self.assertEqual(saved.read_bytes(), bytes_before)
            self.assertEqual(hashlib.sha256(saved.read_bytes()).hexdigest(), digest)
            self.assertEqual(original, before)


class IndependentDhcpStateOracles(unittest.TestCase):
    def test_no_virtual_clock_progress_without_explicit_advance(self):
        project = clients()
        before = copy.deepcopy(project)
        registry = DhcpSessionRegistry()
        session = registry.start(
            project, "server", "eth0", "192.0.2.70", "192.0.2.71")["sessionId"]
        given = registry.run(session, project, "client", "eth0", 21, 80)
        self.assertEqual(given["result"]["status"], "ACK_RECEIVED")
        self.assertEqual(given["leaseCount"], 1)
        for _ in range(8):
            snapshot = registry._get(session).state()
            self.assertEqual(snapshot["clockSeconds"], 0)
            self.assertEqual(snapshot["leases"][0]["remainingSeconds"], 80)
            self.assertEqual(snapshot["leases"][0]["t1AtSeconds"], 40)
            self.assertEqual(snapshot["leases"][0]["t2AtSeconds"], 70)
            self.assertEqual(snapshot["leases"][0]["expiresAtSeconds"], 80)
        advanced = registry.advance(session, project, 39)
        self.assertEqual(advanced["clockSeconds"], 39)
        self.assertEqual(advanced["leases"][0]["remainingSeconds"], 41)
        with self.assertRaisesRegex(ProjectValidationError, "T1 not reached"):
            registry.renew(session, project, "client", "eth0", 22)
        self.assertEqual(registry._get(session).state()["leases"][0]["expiresAtSeconds"], 80)
        self.assertEqual(project, before)

    def test_pool_exhaustion_must_not_duplicate_simulated_ip(self):
        project = clients()
        before = copy.deepcopy(project)
        registry = DhcpSessionRegistry()
        session = registry.start(
            project, "server", "eth0", "192.0.2.70", "192.0.2.71")["sessionId"]
        first = registry.run(session, project, "client", "eth0", 101, 80)
        second = registry.run(session, project, "client-2", "eth0", 102, 80)
        self.assertEqual(first["result"]["status"], "ACK_RECEIVED")
        self.assertEqual(second["result"]["status"], "ACK_RECEIVED")
        self.assertEqual(first["result"]["lease"]["ipv4"], "192.0.2.70")
        self.assertEqual(second["result"]["lease"]["ipv4"], "192.0.2.71")
        with self.assertRaisesRegex(ProjectValidationError, "pool exhausted"):
            registry.run(session, project, "client-3", "eth0", 103, 80)
        leases = registry._get(session).state()["leases"]
        self.assertEqual(len(leases), 2)
        self.assertEqual({lease["ipv4"] for lease in leases},
                         {"192.0.2.70", "192.0.2.71"})
        self.assertEqual(project, before)


if __name__ == "__main__":
    unittest.main()
