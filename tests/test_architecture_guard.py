"""Positive and negative tests for enforceable architecture contracts (A1)."""
from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.architecture_guard import compare_policies, validate

ROOT = Path(__file__).resolve().parents[1]
POLICY = json.loads((ROOT / "architecture" / "baseline.json").read_text("utf-8"))


class ArchitectureGuardTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory(prefix="architecture-guard-")
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name)
        self.policy = copy.deepcopy(POLICY)
        paths = (set(self.policy["critical_files"]) |
                 set(self.policy["required_tests"]) |
                 set(self.policy["frontend_contracts"]) |
                 set(self.policy["required_backend_modules"]) |
                 set(self.policy["line_budgets"]))
        for relative in paths:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            source = ROOT / relative
            if source.exists():
                shutil.copy2(source, target)
            else:
                raise AssertionError(f"baseline path missing from checkout: {relative}")

    def assertProblem(self, token, old=None):
        errors, _ = validate(self.root, self.policy, old)
        self.assertTrue(any(token in issue for issue in errors),
                        f"expected {token} among {errors}")

    def test_positive_current_baseline_passes(self):
        issues, report = validate(self.root, self.policy)
        self.assertEqual(issues, [])
        self.assertEqual(report["frontend_module_count"], 18)
        self.assertEqual(report["import_edge_count"], 29)
        self.assertEqual(report["module_owner_counts"]["session"], 4)
        self.assertEqual(report["source_line_trend"]["web/app.js"]["actual_lines"], 2977)

    def test_negative_deleted_icmp_session_module(self):
        (self.root / "web/features/sessions/icmp-investigation.js").unlink()
        self.assertProblem("REQUIRED_MODULE_MISSING")

    def test_negative_import_cycle(self):
        path = self.root / "web/model.js"
        path.write_text(path.read_text("utf-8") + "\nimport { api } from './app.js';\n",
                        encoding="utf-8")
        self.assertProblem("CYCLIC_IMPORT")

    def test_negative_orphan_module(self):
        path = self.root / "web/app.js"
        source = path.read_text("utf-8")
        self.assertIn("from './features/diagnostics/protocol-lessons.js'", source)
        path.write_text(source.replace(
            "import {setupProtocolLessons} from './features/diagnostics/protocol-lessons.js';",
            "", 1), encoding="utf-8")
        self.assertProblem("ORPHAN_MODULE")

    def test_negative_presentation_imports_storage(self):
        path = self.root / "web/features/diagnostics/presenters.js"
        path.write_text(
            path.read_text("utf-8") +
            "\nimport {prepareSave} from '../projects/persistence.js';\n",
            encoding="utf-8")
        self.assertProblem("FORBIDDEN_LAYER_DEPENDENCY")

    def test_negative_forged_module_owner_is_rejected(self):
        self.policy["frontend_contracts"]["web/features/diagnostics/presenters.js"][
            "owner"] = "projects"
        self.assertProblem("MODULE_OWNER_PATH_MISMATCH")

    def test_negative_role_laundering_cannot_bypass_presentation_storage_boundary(self):
        path = self.root / "web/features/diagnostics/presenters.js"
        path.write_text(path.read_text("utf-8") +
                        "\nimport {prepareSave} from '../projects/persistence.js';\n",
                        encoding="utf-8")
        contract = self.policy["frontend_contracts"]["web/features/diagnostics/presenters.js"]
        contract["owner"] = "projects"
        contract["imports"].append("web/features/projects/persistence.js")
        self.assertProblem("FORBIDDEN_LAYER_DEPENDENCY")

    def test_negative_presenter_copied_into_entrypoint(self):
        path = self.root / "web/app.js"
        path.write_text(path.read_text("utf-8") +
                        "\nfunction presentPing(result) { return result; }\n",
                        encoding="utf-8")
        self.assertProblem("DUPLICATED_MODULE_OWNER_IN_APP")

    def test_negative_session_state_copied_into_entrypoint(self):
        path = self.root / "web/app.js"
        path.write_text(path.read_text("utf-8") + "\nlet icmpSessionId = null;\n",
                        encoding="utf-8")
        self.assertProblem("APP_STATE_OWNERSHIP_DRIFT")

    def test_negative_budget_raise_even_if_manifest_is_altered(self):
        old = copy.deepcopy(self.policy)
        self.policy["line_budgets"]["web/app.js"] += 1
        path = self.root / "web/app.js"
        path.write_text(path.read_text("utf-8") + "\n", encoding="utf-8")
        self.assertProblem("BUDGET_RAISED_OR_REMOVED", old=old)

    def test_negative_lost_regression_file(self):
        (self.root / "tests/test_web_import_graph.py").unlink()
        self.assertProblem("REGRESSION_TEST_INVENTORY_DRIFT")

    def test_negative_lost_guard_source(self):
        (self.root / "tools/architecture_guard.py").unlink()
        self.assertProblem("CRITICAL_FILE_MISSING")

    def test_negative_retired_module_contract(self):
        old = copy.deepcopy(self.policy)
        self.policy["frontend_contracts"].pop("web/features/sessions/icmp-investigation.js")
        self.assertProblem("MODULE_CONTRACT_REMOVED", old=old)

    def test_negative_weakened_public_interface_contract(self):
        old = copy.deepcopy(self.policy)
        self.policy["frontend_contracts"]["web/features/diagnostics/presenters.js"]["exports"] = []
        self.assertProblem("PUBLIC_API_REMOVED", old=old)

    def test_negative_backend_second_project_validator(self):
        path = self.root / "network_core/import_plan.py"
        path.write_text(path.read_text("utf-8") + "\ndef validate_project(project):\n    return project\n",
                        encoding="utf-8")
        self.assertProblem("SECOND_PROJECT_VALIDATOR")

    def test_positive_reduction_ratches_without_regressing_api(self):
        old = copy.deepcopy(self.policy)
        path = self.root / "web/app.js"
        source = path.read_text("utf-8")
        self.assertIn("\n\n", source)
        path.write_text(source.replace("\n\n", "\n", 1), encoding="utf-8")
        self.policy["line_budgets"]["web/app.js"] -= 1
        issues, report = validate(self.root, self.policy, old)
        self.assertEqual(issues, [])
        self.assertEqual(report["source_line_trend"]["web/app.js"]["delta_vs_base"], -1)
        self.assertEqual(report["frontend_module_delta_vs_base"], 0)

    def test_negative_policy_removes_required_test(self):
        modified = copy.deepcopy(self.policy)
        modified["required_tests"].remove("tests/test_web_import_graph.py")
        self.assertIn("PROTECTION_REMOVED: required_tests",
                      compare_policies(self.policy, modified))


if __name__ == "__main__":
    unittest.main()
