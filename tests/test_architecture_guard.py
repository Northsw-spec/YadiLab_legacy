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
        contracts = self.policy["frontend_contracts"]
        self.assertEqual(report["frontend_module_count"], len(contracts))
        self.assertEqual(report["import_edge_count"],
                         sum(len(spec["imports"]) for spec in contracts.values()))
        self.assertEqual(report["module_owner_counts"]["session"], 4)
        self.assertEqual(report["source_line_trend"]["web/app.js"]["actual_lines"],
                         self.policy["line_budgets"]["web/app.js"])
        self.assertEqual(contracts["web/ui/workspace-panels.js"]["owner"], "dom")
        self.assertEqual(contracts["web/ui/workspace-panels.js"]["exports"],
                         ["setupWorkspacePanels"])
        self.assertEqual(contracts["web/features/projects/workspace-revisions.js"]["owner"],
                         "projects")
        self.assertEqual(contracts["web/features/projects/workspace-revisions.js"]["exports"],
                         ["createWorkspaceRevisions"])
        self.assertNotIn("editRevision", self.policy["app_top_level_bindings"])
        self.assertNotIn("builderValidationGeneration", self.policy["app_top_level_bindings"])

    def test_negative_deleted_workspace_revision_owner(self):
        (self.root / "web/features/projects/workspace-revisions.js").unlink()
        self.assertProblem("REQUIRED_MODULE_MISSING")

    def test_negative_duplicate_workspace_version_state_in_entrypoint(self):
        path = self.root / "web/app.js"
        path.write_text(path.read_text("utf-8") +
                        "\nlet editRevision = 0;\n", encoding="utf-8")
        self.assertProblem("APP_STATE_OWNERSHIP_DRIFT")

    def test_negative_deleted_extracted_workspace_module(self):
        (self.root / "web/ui/workspace-panels.js").unlink()
        self.assertProblem("REQUIRED_MODULE_MISSING")

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


    def test_positive_register_nested_fresh_engine_module(self):
        fresh = "network_core/engine/event_queue.py"
        file = self.root / fresh
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("class EventQueue:\n    pass\n", encoding="utf-8")
        self.policy["required_backend_modules"].append(fresh)
        issues, report = validate(self.root, self.policy)
        self.assertEqual(issues, [])
        self.assertEqual(report["backend_module_count"],
                         len(self.policy["required_backend_modules"]))

    def test_negative_unregistered_nested_engine_is_detected(self):
        file = self.root / "network_core/engine/untracked.py"
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("class Unknown:\n    pass\n", encoding="utf-8")
        self.assertProblem("BACKEND_MODULE_INVENTORY_DRIFT")

    def _engine_retirement_fixture(self):
        old_file = "network_core/ethernet.py"
        new_file = "network_core/engine/l2_runtime.py"
        test_file = "tests/test_new_engine_oracle.py"
        decision = "docs/architecture/TEST_ENGINE_RETIREMENT.md"
        (self.root / old_file).unlink()
        module = self.root / new_file
        module.parent.mkdir(parents=True, exist_ok=True)
        module.write_text("class L2Runtime:\n    pass\n", encoding="utf-8")
        oracle = self.root / test_file
        oracle.write_text(
            "import unittest\nclass Oracle(unittest.TestCase):\n"
            "    def test_new_l2(self):\n        self.assertTrue(True)\n",
            encoding="utf-8")
        doc = self.root / decision
        doc.parent.mkdir(parents=True, exist_ok=True)
        doc.write_text("approved: " + old_file + " -> " + new_file + "\n",
                       encoding="utf-8")
        self.policy["required_backend_modules"].remove(old_file)
        self.policy["required_backend_modules"].append(new_file)
        self.policy["required_tests"].append(test_file)
        self.policy["retirement_receipts"]["backend"][old_file] = {
            "replacements": [new_file],
            "acceptance_tests": [test_file],
            "decision": decision,
        }
        return old_file, new_file, test_file, decision

    def test_positive_retirement_with_live_successor_and_acceptance(self):
        old = copy.deepcopy(self.policy)
        self._engine_retirement_fixture()
        issues, report = validate(self.root, self.policy, old)
        self.assertEqual(issues, [])
        self.assertEqual(report["retirement_receipts"]["backend"], 1)

    def test_negative_retire_without_receipt_fails_closed(self):
        old = copy.deepcopy(self.policy)
        former = "network_core/ethernet.py"
        (self.root / former).unlink()
        self.policy["required_backend_modules"].remove(former)
        self.assertProblem("PROTECTION_REMOVED: required_backend_modules", old=old)

    def test_negative_forged_retirement_missing_successor(self):
        old = copy.deepcopy(self.policy)
        _, new_file, _, _ = self._engine_retirement_fixture()
        (self.root / new_file).unlink()
        self.policy["required_backend_modules"].remove(new_file)
        self.assertProblem("NO_LIVE_RETIREMENT_SUCCESSOR", old=old)

    def test_negative_retirement_missing_tests_and_decision(self):
        old = copy.deepcopy(self.policy)
        former, _, _, decision = self._engine_retirement_fixture()
        self.policy["retirement_receipts"]["backend"][former][
            "acceptance_tests"] = ["tests/missing_oracle.py"]
        (self.root / decision).unlink()
        self.assertProblem("UNVERIFIED_RETIREMENT_TESTS", old=old)
        self.assertProblem("MISSING_RETIREMENT_DECISION", old=old)

    def test_negative_rewrite_prior_retirement_history(self):
        old = copy.deepcopy(self.policy)
        self._engine_retirement_fixture()
        old["retirement_receipts"]["backend"] = copy.deepcopy(
            self.policy["retirement_receipts"]["backend"])
        self.policy["retirement_receipts"]["backend"] = {}
        self.assertProblem("RETIREMENT_HISTORY_REWRITTEN", old=old)

    def test_negative_critical_governance_file_cannot_be_retired(self):
        old = copy.deepcopy(self.policy)
        critical = "tools/architecture_guard.py"
        self.policy["critical_files"].remove(critical)
        self.assertProblem("PROTECTION_REMOVED: critical_files", old=old)


    def test_negative_fresh_engine_imports_legacy_runtime(self):
        path = "network_core/engine/bad.py"
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(
            "from network_core.ethernet import EthernetFabric\n", encoding="utf-8")
        self.policy["required_backend_modules"].append(path)
        self.assertProblem("ENGINE_IMPORTS_LEGACY_RUNTIME")



if __name__ == "__main__":
    unittest.main()
