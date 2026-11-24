"""Independent RFC 1122 and IANA negative oracles for the narrow ARP wire model."""
from __future__ import annotations

from copy import deepcopy
import unittest

from network_core.arp import ArpMessage, ArpSession
from network_core.model import ProjectValidationError, validate_project
from test_icmp_investigation_lan import lan_lab


def on_link_pair(first: str, second: str) -> dict:
    project = lan_lab()
    project["nodes"][0]["ports"][0]["ipv4"] = first
    project["nodes"][2]["ports"][0]["ipv4"] = second
    return validate_project(project)


class ARPSpecialAddressOracles(unittest.TestCase):
    def test_arp_wire_codec_rejects_special_ipv4_source_and_target(self):
        for invalid in ("127.0.0.1", "127.15.20.30", "0.0.0.1",
                        "0.1.2.3", "240.0.0.1", "255.255.255.254"):
            with self.subTest(address=invalid):
                with self.assertRaisesRegex(ProjectValidationError, "usable unicast"):
                    ArpMessage(1, "02:00:00:00:00:0A", invalid,
                               "00:00:00:00:00:00", "192.0.2.20")
                with self.assertRaisesRegex(ProjectValidationError, "usable unicast"):
                    ArpMessage(1, "02:00:00:00:00:0A", "192.0.2.10",
                               "00:00:00:00:00:00", invalid)

    def test_documented_loopback_and_this_network_misconfigs_stay_readable_not_deliverable(self):
        for source, target in (("127.10.0.10/8", "127.10.0.20/8"),
                               ("0.1.0.10/8", "0.1.0.20/8"),
                               ("240.0.0.10/4", "240.0.0.20/4")):
            with self.subTest(source=source, target=target):
                project = on_link_pair(source, target)
                before = deepcopy(project)
                session = ArpSession(project)
                with self.assertRaisesRegex(ProjectValidationError, "usable unicast"):
                    session.resolve("a", "eth0", target.split("/")[0])
                self.assertEqual(session.arp_table("a", "eth0"), {})
                self.assertEqual(project, before)

    def test_link_local_same_vlan_arp_remains_valid_and_does_not_save(self):
        project = on_link_pair("169.254.10.10/16", "169.254.10.20/16")
        before = deepcopy(project)
        session = ArpSession(project)
        resolved = session.resolve("a", "eth0", "169.254.10.20")
        self.assertEqual(resolved["status"], "RESOLVED")
        self.assertEqual(session.arp_table("a", "eth0")["169.254.10.20"],
                         "02:00:00:00:10:14")
        self.assertEqual(project, before)

    def test_rfc1918_and_test_net_labs_are_not_overrestricted(self):
        for source, target in (("192.168.10.10/24", "192.168.10.20/24"),
                               ("192.0.2.10/24", "192.0.2.20/24"),
                               ("10.0.10.10/24", "10.0.10.20/24")):
            with self.subTest(source=source):
                session = ArpSession(on_link_pair(source, target))
                result = session.resolve("a", "eth0", target.split("/")[0])
                self.assertEqual(result["status"], "RESOLVED")


if __name__ == "__main__":
    unittest.main()
