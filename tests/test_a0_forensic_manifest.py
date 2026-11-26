"""A0 source-evidence integrity tests (NOT the A1 architecture-guard).

The snapshot pins the *historical* main/3E Git trees. It must not compare
future changes with a frozen row budget: A1 will install the enforced ratchet.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "architecture" / "a0_baseline.json"
GRAPH = ROOT / "architecture" / "a0_frontend_imports.json"
SHA = re.compile(r"[0-9a-f]{40}\Z")


def manifest_issues(baseline: dict, graph: dict) -> list[str]:
    """Check pinned audit evidence for internal consistency (no live-code gate)."""
    errors = []
    if baseline.get("schema") != "yadilab.a0.forensic-baseline.v1":
        errors.append("schema")
    if baseline.get("status") != "BASELINE_NOT_ENFORCEMENT":
        errors.append("scope")
    if graph.get("schema") != "yadilab.a0.frontend-import-graph.v1":
        errors.append("graph schema")
    revision = baseline.get("baseline_main_sha")
    if not isinstance(revision, str) or not SHA.fullmatch(revision):
        errors.append("revision")
    if graph.get("baseline_main_sha") != revision:
        errors.append("graph revision")

    actual = baseline.get("current", {})
    historic = baseline.get("historical_3e", {})
    current_paths = actual.get("frontend_module_paths", [])
    prior_paths = historic.get("frontend_module_paths", [])
    if len(current_paths) != len(set(current_paths)):
        errors.append("duplicate frontend module")
    if not set(prior_paths).issubset(set(current_paths)):
        errors.append("missing historical 3E module")
    if actual.get("missing_3e_module_paths") != sorted(set(prior_paths) - set(current_paths)):
        errors.append("historical difference")
    delta = actual.get("app", {}).get("display_lines", 0) - historic.get("app", {}).get("display_lines", 0)
    if delta != 740:
        errors.append("historical line delta")
    if actual.get("top_level_named_functions", 0) - historic.get("top_level_named_functions", 0) != 31:
        errors.append("function delta")

    inventories = baseline.get("inventories", {})
    module_rows = inventories.get("modules", [])
    test_rows = inventories.get("regression_tests_and_fixtures", [])
    modules = [row.get("path") for row in module_rows]
    tests = [row.get("path") for row in test_rows]
    if len(modules) != len(set(modules)) or len(tests) != len(set(tests)):
        errors.append("duplicate inventory path")
    if len(module_rows) != 52 or len(test_rows) != 94:
        errors.append("inventory count")
    if not set(current_paths).issubset(set(modules)):
        errors.append("graph/inventory mismatch")
    if not {"tests/test_web_import_graph.py", "tests/test_documentation_policy.py",
            "tests/browser_smoke.py"}.issubset(set(tests)):
        errors.append("missing core regression inventory")
    for row in module_rows + test_rows:
        blob = row.get("blob_sha")
        if not isinstance(blob, str) or not SHA.fullmatch(blob):
            errors.append("invalid Git blob SHA")
            break
        if type(row.get("bytes")) is not int or row["bytes"] <= 0:
            errors.append("invalid blob byte length")
            break

    adjacency = graph.get("adjacency", {})
    nodes = set(current_paths)
    if not isinstance(adjacency, dict) or set(adjacency) != nodes:
        errors.append("graph node list")
        return errors
    if graph.get("module_count") != len(nodes):
        errors.append("graph size")
    if sum(len(targets) for targets in adjacency.values()) != graph.get("direct_import_count"):
        errors.append("graph edge count")
    for target_list in adjacency.values():
        for target in target_list:
            if target not in nodes:
                errors.append("missing import target")

    visited: set[str] = set()
    active: set[str] = set()

    def visit(path: str) -> None:
        if path in active:
            errors.append("import cycle")
            return
        if path in visited:
            return
        active.add(path)
        for target in adjacency.get(path, []):
            if target in nodes:
                visit(target)
        active.remove(path)
        visited.add(path)

    entrypoint = graph.get("entrypoint")
    if entrypoint not in nodes:
        errors.append("missing entrypoint")
    else:
        visit(entrypoint)
    if visited != nodes:
        errors.append("orphan module")
    if graph.get("graph_check", {}).get("orphan_paths") != []:
        errors.append("captured orphan evidence")
    if graph.get("graph_check", {}).get("unresolved_imports") != []:
        errors.append("captured unresolved evidence")
    if graph.get("graph_check", {}).get("cycles_reported") != []:
        errors.append("captured cyclic evidence")
    return errors


class A0ForensicBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = json.loads(BASE.read_text(encoding="utf-8"))
        cls.graph = json.loads(GRAPH.read_text(encoding="utf-8"))

    def test_complete_pinned_architecture_and_regression_file_inventory(self):
        self.assertEqual(manifest_issues(self.baseline, self.graph), [])
        self.assertEqual(self.baseline["baseline_main_sha"],
                         "f36435dd7b108756bdac6e3919c1cb1c61cf58d7")
        self.assertEqual(self.baseline["historical_3e_sha"],
                         "17acb51c8c64c3b4b7a1026514cb8b0a2177a127")
        self.assertEqual(self.baseline["current"]["app"]["display_lines"], 2978)
        self.assertEqual(self.baseline["historical_3e"]["app"]["display_lines"], 2238)

    def test_negative_missing_historical_session_module_is_rejected(self):
        item = copy.deepcopy(self.baseline)
        item["current"]["frontend_module_paths"].remove(
            "web/features/sessions/icmp-investigation.js")
        self.assertIn("missing historical 3E module", manifest_issues(item, self.graph))

    def test_negative_missing_independently_expected_test_file_is_rejected(self):
        item = copy.deepcopy(self.baseline)
        item["inventories"]["regression_tests_and_fixtures"] = [
            r for r in item["inventories"]["regression_tests_and_fixtures"]
            if r["path"] != "tests/test_web_import_graph.py"]
        self.assertIn("missing core regression inventory", manifest_issues(item, self.graph))

    def test_negative_orphan_import_is_rejected(self):
        graph = copy.deepcopy(self.graph)
        graph["adjacency"]["web/app.js"].remove(
            "web/features/diagnostics/protocol-lessons.js")
        self.assertIn("orphan module", manifest_issues(self.baseline, graph))

    def test_negative_cycle_is_rejected(self):
        graph = copy.deepcopy(self.graph)
        graph["adjacency"]["web/model.js"].append("web/app.js")
        self.assertIn("import cycle", manifest_issues(self.baseline, graph))

    def test_negative_nonexistent_import_target_is_rejected(self):
        graph = copy.deepcopy(self.graph)
        graph["adjacency"]["web/model.js"].append("web/features/missing-module.js")
        self.assertIn("missing import target", manifest_issues(self.baseline, graph))

    def test_negative_fake_blob_sha_and_byte_size_are_rejected(self):
        fake_sha = copy.deepcopy(self.baseline)
        fake_sha["inventories"]["modules"][0]["blob_sha"] = "not-a-git-sha"
        self.assertIn("invalid Git blob SHA", manifest_issues(fake_sha, self.graph))
        fake_size = copy.deepcopy(self.baseline)
        fake_size["inventories"]["modules"][0]["bytes"] = 0
        self.assertIn("invalid blob byte length", manifest_issues(fake_size, self.graph))


if __name__ == "__main__":
    unittest.main()
