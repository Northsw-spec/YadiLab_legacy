"""Functional CSV interchange: preserve declarations or reject the entire import."""
import unittest

from network_core.csv_import import import_csv_tables
from network_core.model import ProjectValidationError, topology_trace


DEV = "id,label,kind,x,y,zoneId\npc-a,Klient,host,80,120,office\nsw-a,Switch,switch,320,120,office\n"
PORTS = "nodeId,id,name,enabled,ipv4\npc-a,eth0,eth0,true,192.0.2.5/24\nsw-a,gi1,Gi1,true,\n"
LINKS = "id,aNode,aPort,bNode,bPort,enabled\ncable-1,pc-a,eth0,sw-a,gi1,true\n"
ZONES = "id,label\noffice,Office\n"


def source(**overrides):
    mapping = {"Devices.csv": DEV, "Interfaces.csv": PORTS, "Links.csv": LINKS, "Zones.csv": ZONES}
    mapping.update(overrides)
    return {"projectName": "Explicit CSV lab", "files": [{"name": name, "text": text} for name, text in mapping.items()]}


class CsvImportTests(unittest.TestCase):
    def test_coordinate_free_explicit_layer2_network_and_stable_positions(self):
        devices = "zoneId,kind,label,id\noffice,switch,Switch,sw-a\noffice,host,Client,pc-a\n"
        project = import_csv_tables(source(**{"Devices.csv": devices,
            "Interfaces.csv": PORTS.replace("192.0.2.5/24", "")}))
        self.assertEqual([(n["id"], n["x"], n["y"]) for n in project["nodes"]],
                         [("sw-a", 370, 110), ("pc-a", 110, 110)])
        self.assertEqual(project["links"][0]["b"], {"node": "sw-a", "port": "gi1"})
        self.assertIsNone(project["nodes"][1]["ports"][0]["ipv4"])
        reversed_rows = devices.splitlines()
        reversed_rows[1:] = reversed(reversed_rows[1:])
        other = import_csv_tables(source(**{"Devices.csv": "\n".join(reversed_rows) + "\n"}))
        self.assertEqual({n["id"]: (n["x"], n["y"]) for n in other["nodes"]},
                         {n["id"]: (n["x"], n["y"]) for n in project["nodes"]})

    def test_coordinate_free_header_and_network_errors_rejected(self):
        good = "id,label,kind,zoneId\npc-a,Client,host,office\nsw-a,Switch,switch,office\n"
        bad = [good.replace("zoneId", "x,zoneId"), good.replace("zoneId", "y,zoneId"),
               good.replace("zoneId", "zoneId,zoneId"), good.replace("zoneId", "unknown"),
               good.replace("pc-a,Client", "bad id,Client")]
        for devices in bad:
            with self.subTest(devices=devices), self.assertRaises(ProjectValidationError):
                import_csv_tables(source(**{"Devices.csv": devices}))
        with self.assertRaises(ProjectValidationError):
            import_csv_tables(source(**{"Devices.csv": good,
                "Links.csv": LINKS.replace("sw-a,gi1", "sw-a,unknown")}))

    def test_coordinate_free_model_limit_and_bounds(self):
        text = "id,label,kind,zoneId\n" + "".join(
            f"n-{i:04},Node {i},switch,\n" for i in range(2000))
        project = import_csv_tables({"projectName": "Large Layer 2", "files": [
            {"name": "Devices.csv", "text": text}]})
        self.assertEqual(len(project["nodes"]), 2000)
        self.assertEqual(len({(n["x"], n["y"]) for n in project["nodes"]}), 2000)
        self.assertTrue(all(max(abs(n["x"]), abs(n["y"])) <= 100000
                            for n in project["nodes"]))
        with self.assertRaises(ProjectValidationError):
            import_csv_tables({"projectName": "Too many", "files": [
                {"name": "Devices.csv", "text": text + "n-2000,Extra,switch,\n"}]})

    def test_source_identity_and_literal_ports(self):
        doc = import_csv_tables(source())
        self.assertEqual([x["id"] for x in doc["nodes"]], ["pc-a", "sw-a"])
        self.assertEqual(doc["links"][0]["a"], {"node": "pc-a", "port": "eth0"})
        self.assertEqual(doc["nodes"][0]["ports"][0]["ipv4"], "192.0.2.5/24")
        self.assertEqual(topology_trace(doc, "pc-a", "sw-a")["status"], "PATH_PRESENT")

    def test_reordered_columns_and_multiline_label(self):
        test = source(**{"Devices.csv": "label,id,kind,x,y,zoneId\n\"Client, Office\",pc-a,host,80,120,office\n\"Switch\nSecond Floor\",sw-a,switch,320,120,office\n"})
        doc = import_csv_tables(test)
        self.assertEqual(doc["nodes"][0]["label"], "Client, Office")
        self.assertEqual(doc["nodes"][1]["label"], "Switch\nSecond Floor")

    def test_bom_and_crlf(self):
        test = source(**{"Devices.csv": "\ufeff" + DEV.replace("\n", "\r\n")})
        self.assertEqual(len(import_csv_tables(test)["nodes"]), 2)

    def test_no_links_or_ports_are_inferred(self):
        test = {"projectName": "No connections", "files": [{"name": "Devices.csv", "text": DEV.replace(",office", ",")}]}
        doc = import_csv_tables(test)
        self.assertEqual(doc["links"], [])
        self.assertTrue(all(not n["ports"] for n in doc["nodes"]))

    def test_explicit_fault_remains_disabled(self):
        test = source(**{"Links.csv": LINKS.replace("true", "false")})
        doc = import_csv_tables(test)
        self.assertEqual(topology_trace(doc, "pc-a", "sw-a")["status"], "NO_PATH")

    def test_bad_inputs_reject_without_partial_document(self):
        variants = [
            source(**{"Devices.csv": DEV + "pc-a,Duplicate,host,9,9,office\n"}),
            source(**{"Devices.csv": DEV.replace("x,y", "longitude,y")}),
            source(**{"Devices.csv": DEV.replace("80,120", ",120")}),
            source(**{"Interfaces.csv": PORTS.replace("true", "maybe")}),
            source(**{"Interfaces.csv": PORTS.replace("sw-a,gi1", "missing,gi1")}),
            source(**{"Links.csv": LINKS.replace("sw-a,gi1", "sw-a,missing")}),
            source(**{"Links.csv": LINKS + "cable-2,pc-a,eth0,sw-a,gi1,true\n"}),
            source(**{"Devices.csv": DEV.replace("id,label,kind,x,y,zoneId", "id,label,kind,x,y,zoneId,extra")}),
            source(**{"Devices.csv": DEV.replace("pc-a,Klient,host,80,120,office", "pc-a,Klient,host,80,120")}),
            source(**{"Devices.csv": DEV + ",,,,,\n"}),
            source(**{"Devices.csv": DEV.replace("pc-a,Klient", '"pc-a,Klient')}),
            source(**{"Zones.csv": ZONES.replace("office,Office", "else,Other")}),
            {"projectName": "Missing devices", "files": [{"name": "Links.csv", "text": LINKS}]},
            {"projectName": "Double", "files": [{"name": "Devices.csv", "text": DEV}] * 2},
            {"projectName": "Unknown", "files": [{"name": "Nodes.csv", "text": DEV}]},
            {"projectName": "Missing field", "files": [{"name": "Devices.csv"}]},
        ]
        for v in variants:
            with self.subTest(v=v):
                with self.assertRaises(ProjectValidationError):
                    import_csv_tables(v)

    def test_unknown_columns_and_bogus_ipv4_fail(self):
        with self.assertRaisesRegex(ProjectValidationError, 'expected exactly these columns'):
            import_csv_tables(source(**{"Interfaces.csv": PORTS.replace("ipv4", "IP-address")}))
        with self.assertRaises(ProjectValidationError):
            import_csv_tables(source(**{"Interfaces.csv": PORTS.replace("192.0.2.5/24", "192.0.2.5")}))

    def test_reject_nul_and_replacement_character(self):
        for text in [DEV + "\x00", DEV.replace("Klient", "\ufffd")]:
            with self.assertRaises(ProjectValidationError):
                import_csv_tables(source(**{"Devices.csv": text}))


if __name__ == '__main__':
    unittest.main()
