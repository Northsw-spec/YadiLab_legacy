#!/usr/bin/env python3
"""Enforced architecture regression guard for the approved remediation program.

No package dependencies. This is structural/static evidence, not a proof of
correctness or a complete JS AST. Native node --check and real browser tests
remain independent required functional gates.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

POLICY = "architecture/baseline.json"
IMPORT = re.compile(r"""(?m)^import\s+[^\n]+?\s+from\s+['"]([^'"]+)['"]\s*;""")
EXPORTED = re.compile(r"(?m)^export\s+(?:async\s+)?(?:function|class|const|let)\s+([A-Za-z_$][\w$]*)")
EXPORT_GROUP = re.compile(r"(?m)^export\s*\{([^}]+)\}")
FUNCTION = re.compile(r"(?m)^(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(")
BINDING = re.compile(r"(?m)^(?:let|const|var)\s+([A-Za-z_$][\w$]*)\b")
DOM_TOUCH = re.compile(
    r"\b(document\.(getElementById|querySelector|querySelectorAll|createElement|addEventListener)"
    r"|\$\(|\.addEventListener\(|\.appendChild\(|\.replaceChildren\(|\.innerHTML\s*="
    r"|\.textContent\s*=)")
SHA = re.compile(r"[0-9a-f]{40}\Z")
VALID_OWNERS = frozenset(("composition", "canvas", "model", "dom", "api",
                          "diagnostics", "projects", "session", "layout"))


def source_lines(source: str) -> int:
    return len(source.splitlines())


def exports(source: str) -> list[str]:
    names = EXPORTED.findall(source)
    for group in EXPORT_GROUP.findall(source):
        for part in group.split(","):
            token = part.strip().split(" as ")
            names.append(token[-1].strip())
    return sorted(names)


def frontend_paths(root: Path) -> set[str]:
    return {p.relative_to(root).as_posix()
            for p in (root / "web").rglob("*.js")
            if "vendor" not in p.relative_to(root / "web").parts}


def regression_paths(root: Path) -> set[str]:
    # Checkout-only; exclude Python generated cache/coverage files.
    return {p.relative_to(root).as_posix()
            for p in (root / "tests").rglob("*")
            if p.is_file() and not any(part.startswith(".") or part == "__pycache__"
                                      for part in p.relative_to(root / "tests").parts)}


def import_targets(root: Path, path: str, source: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    targets: list[str] = []
    imports = IMPORT.findall(source)
    # Do not silently overlook side-effect or dynamic imports not in the contract.
    statements = re.findall(r"(?m)^import\s+", source)
    if len(imports) != len(statements) or re.search(r"\bimport\s*\(", source):
        errors.append(f"UNMODELED_IMPORT: {path}")
    if re.search(r"(?m)^export\s+\*\s+from\b|\brequire\s*\(", source):
        errors.append(f"UNMODELED_MODULE_EDGE: {path}")
    for specifier in imports:
        if not specifier.startswith("."):
            errors.append(f"NON_RELATIVE_IMPORT: {path} -> {specifier}")
            continue
        target = ((root / path).parent / specifier).resolve()
        try:
            relative = target.relative_to(root.resolve()).as_posix()
        except ValueError:
            errors.append(f"IMPORT_ESCAPES_ROOT: {path} -> {specifier}")
            continue
        if not relative.startswith("web/") or not relative.endswith(".js"):
            errors.append(f"IMPORT_OUTSIDE_WEB: {path} -> {relative}")
        targets.append(relative)
    return targets, errors


def expected_owner(path: str) -> str | None:
    """Ownership comes from source location, not from editable JSON labels."""
    if path == "web/app.js":
        return "composition"
    if path == "web/canvas.js":
        return "canvas"
    if path == "web/model.js":
        return "model"
    if path.startswith("web/ui/"):
        return "dom"
    if path.startswith("web/services/"):
        return "api"
    for part, owner in (("diagnostics", "diagnostics"),
                        ("projects", "projects"), ("sessions", "session"),
                        ("layout", "layout")):
        if path.startswith(f"web/features/{part}/"):
            return owner
    return None


def forbidden_edge(path: str, target: str, owner: str) -> bool:
    if target == "web/app.js":
        return True  # composition root cannot be a downstream dependency
    if owner == "diagnostics" and target.startswith("web/features/projects/"):
        return True
    if owner == "session" and (target.startswith("web/features/projects/")
                               or target.startswith("web/features/diagnostics/")
                               or target.startswith("web/ui/")):
        return True
    if owner == "projects" and (target.startswith("web/features/sessions/")
                               or target.startswith("web/features/diagnostics/")):
        return True
    if owner in {"model", "layout", "api"} and target.startswith("web/features/"):
        return True
    return False



RETIREMENT_GROUPS = ("backend", "frontend", "tests")

# New engine cannot route execution back into the legacy synchronous dataplane.
LEGACY_RUNTIME = frozenset({
    "ethernet", "arp", "ipv4", "routing", "dhcp", "dhcp_registry",
    "simulation", "icmp_ping", "icmp_errors", "dhcp_investigation",
    "icmp_investigation",
})



def retirement_receipts(policy: dict) -> dict:
    result = policy.get("retirement_receipts", {})
    return result if isinstance(result, dict) else {}


def retirement_issues(root: Path, policy: dict,
                      inventory: dict[str, set[str]]) -> list[str]:
    """Retire legacy files only with real replacements, tests and a decision.

    Structural verification is a necessary condition, never proof of
    functional parity; Required CI and external protocol oracles remain.
    """
    errors: list[str] = []
    records = policy.get("retirement_receipts")
    if not isinstance(records, dict) or set(records) != set(RETIREMENT_GROUPS):
        return ["INVALID_RETIREMENT_REGISTRY"]
    for group in RETIREMENT_GROUPS:
        entries = records[group]
        if not isinstance(entries, dict):
            errors.append(f"INVALID_RETIREMENT_GROUP: {group}")
            continue
        prefix = {"backend": "network_core/", "frontend": "web/",
                  "tests": "tests/"}[group]
        for path, evidence in entries.items():
            if not isinstance(path, str) or not path.startswith(prefix):
                errors.append(f"INVALID_RETIREMENT_PATH: {group}: {path}")
                continue
            if path in inventory[group]:
                errors.append(f"RETIRED_PATH_STILL_ACTIVE: {group}: {path}")
            if not isinstance(evidence, dict) or set(evidence) != {
                    "replacements", "acceptance_tests", "decision"}:
                errors.append(f"INVALID_RETIREMENT_RECEIPT: {group}: {path}")
                continue
            replacements = evidence["replacements"]
            acceptance = evidence["acceptance_tests"]
            decision = evidence["decision"]
            valid_successors = (
                isinstance(replacements, list) and len(replacements) > 0
                and all(isinstance(x, str) and x != path for x in replacements))
            if not valid_successors or (
                    len(set(replacements)) != len(replacements)
                    or not all(x in inventory[group] for x in replacements)):
                errors.append(f"NO_LIVE_RETIREMENT_SUCCESSOR: {group}: {path}")
            valid_tests = (
                isinstance(acceptance, list) and len(acceptance) > 0
                and all(isinstance(x, str) for x in acceptance))
            if not valid_tests or (
                    len(set(acceptance)) != len(acceptance)
                    or not all(x in inventory["tests"] for x in acceptance)):
                errors.append(f"UNVERIFIED_RETIREMENT_TESTS: {group}: {path}")
            if (not isinstance(decision, str)
                    or not decision.startswith("docs/")
                    or not decision.endswith(".md")
                    or ".." in Path(decision).parts
                    or not (root / decision).is_file()):
                errors.append(f"MISSING_RETIREMENT_DECISION: {group}: {path}")
            else:
                doc = (root / decision).read_text(encoding="utf-8")
                if path not in doc or not valid_successors or any(
                        successor not in doc for successor in replacements):
                    errors.append(f"UNTRACKED_RETIREMENT_DECISION: {group}: {path}")
    return errors


def compare_policies(old: dict, new: dict) -> list[str]:
    """No self-approved expansion of guarded budgets/ownership across a PR."""
    errors: list[str] = []
    if old.get("schema") != new.get("schema") or old.get("version") != new.get("version"):
        errors.append("POLICY_SCHEMA_CHANGED")
    records = retirement_receipts(new)
    for path, amount in old.get("line_budgets", {}).items():
        current = new.get("line_budgets", {}).get(path)
        group = "frontend" if path.startswith("web/") else "backend"
        if current is None and path in records.get(group, {}):
            continue
        if type(current) is not int or current > amount:
            errors.append(f"BUDGET_RAISED_OR_REMOVED: {path}")
    for name, amount in old.get("app_limits", {}).items():
        current = new.get("app_limits", {}).get(name)
        if type(current) is not int or current > amount:
            errors.append(f"APP_LIMIT_RAISED_OR_REMOVED: {name}")
    if not set(old.get("critical_files", [])).issubset(set(new.get("critical_files", []))):
        errors.append("PROTECTION_REMOVED: critical_files")
    for key, group in (("required_tests", "tests"),
                       ("required_backend_modules", "backend")):
        removed = set(old.get(key, [])) - set(new.get(key, []))
        if any(path not in records.get(group, {}) for path in removed):
            errors.append(f"PROTECTION_REMOVED: {key}")
    previous = retirement_receipts(old)
    for group in RETIREMENT_GROUPS:
        earlier, now = previous.get(group, {}), records.get(group, {})
        if not isinstance(earlier, dict) or not isinstance(now, dict):
            errors.append(f"INVALID_RETIREMENT_GROUP: {group}")
            continue
        for name, evidence in earlier.items():
            if now.get(name) != evidence:
                errors.append(f"RETIREMENT_HISTORY_REWRITTEN: {group}: {name}")
        inventory_key = {"backend": "required_backend_modules",
                         "frontend": "frontend_contracts",
                         "tests": "required_tests"}[group]
        for name in set(now) - set(earlier):
            if name not in old.get(inventory_key, {}):
                errors.append(f"UNTRACKED_RETIREMENT: {group}: {name}")
    for key in ("app_functions", "app_top_level_bindings"):
        if not set(new.get(key, [])).issubset(set(old.get(key, []))):
            errors.append(f"APP_RESPONSIBILITY_EXPANDED: {key}")
    old_modules = old.get("frontend_contracts", {})
    new_modules = new.get("frontend_contracts", {})
    if any(path not in records.get("frontend", {})
           for path in set(old_modules) - set(new_modules)):
        errors.append("MODULE_CONTRACT_REMOVED")
    for path, previous in old_modules.items():
        if path not in new_modules:
            continue
        current = new_modules[path]
        if previous.get("owner") != current.get("owner"):
            errors.append(f"OWNER_CHANGED: {path}")
        if not set(previous.get("exports", [])).issubset(set(current.get("exports", []))):
            errors.append(f"PUBLIC_API_REMOVED: {path}")
        new_deps = set(current.get("imports", [])) - set(previous.get("imports", []))
        # Existing modules may depend on newly extracted modules, never
        # silently acquire more access to pre-existing responsibilities.
        for dep in sorted(new_deps):
            if dep in old_modules:
                errors.append(f"EXISTING_DEPENDENCY_EXPANDED: {path} -> {dep}")
    return errors


def validate(root: Path, policy: dict, old: dict | None = None) -> tuple[list[str], dict]:
    """Inspect checkout content and approved contracts; no checkout mutation."""
    issues: list[str] = []
    if policy.get("schema") != "architecture.guard.v1" or policy.get("version") != 1:
        issues.append("INVALID_POLICY_SCHEMA")
    required = policy.get("critical_files", [])
    if len(required) != len(set(required)):
        issues.append("DUPLICATE_CRITICAL_FILES")
    for path in required:
        if not (root / path).is_file():
            issues.append(f"CRITICAL_FILE_MISSING: {path}")
    budgets = policy.get("line_budgets", {})
    actual_budgets = {}
    for path, expected in budgets.items():
        file = root / path
        if not file.is_file():
            issues.append(f"BUDGETED_SOURCE_MISSING: {path}")
            continue
        count = source_lines(file.read_text(encoding="utf-8"))
        actual_budgets[path] = count
        if type(expected) is not int or expected != count:
            issues.append(f"BUDGET_NOT_RATCHETED: {path} actual={count} accepted={expected}")
    # A retired file's budget may vanish only with BASE-verified receipt.
    if not isinstance(budgets, dict) or not budgets:
        issues.append("BUDGETED_SOURCE_SET_CHANGED")

    all_modules = frontend_paths(root)
    contracts = policy.get("frontend_contracts", {})
    if all_modules != set(contracts):
        issues.append("FRONTEND_MODULE_INVENTORY_DRIFT: " +
                      repr(sorted(all_modules ^ set(contracts))))
    graph: dict[str, list[str]] = {}
    for path, spec in contracts.items():
        file = root / path
        if not file.is_file():
            issues.append(f"REQUIRED_MODULE_MISSING: {path}")
            continue
        source = file.read_text(encoding="utf-8")
        owner = spec.get("owner")
        derived_owner = expected_owner(path)
        if owner not in VALID_OWNERS:
            issues.append(f"UNDEFINED_MODULE_OWNER: {path}")
        if derived_owner is None or owner != derived_owner:
            issues.append(f"MODULE_OWNER_PATH_MISMATCH: {path}")
        targets, edge_errors = import_targets(root, path, source)
        issues.extend(edge_errors)
        graph[path] = targets
        if targets != spec.get("imports"):
            issues.append(f"MODULE_DEPENDENCY_CONTRACT_DRIFT: {path}")
        current_exports = exports(source)
        if current_exports != spec.get("exports"):
            issues.append(f"PUBLIC_EXPORT_CONTRACT_DRIFT: {path}")
        for target in targets:
            if target not in contracts:
                issues.append(f"MISSING_DEPENDENCY_MODULE: {path} -> {target}")
            # Derive the layer from path so an edited policy cannot relabel
            # a session/presenter as 'composition' to bypass the boundary.
            if forbidden_edge(path, target, derived_owner or ""):
                issues.append(f"FORBIDDEN_LAYER_DEPENDENCY: {path} -> {target}")

    visited: set[str] = set()
    active: set[str] = set()

    def visit(path: str) -> None:
        if path in active:
            issues.append(f"CYCLIC_IMPORT: {path}")
            return
        if path in visited:
            return
        active.add(path)
        for target in graph.get(path, []):
            if target in graph:
                visit(target)
        active.remove(path)
        visited.add(path)

    if "web/app.js" not in graph:
        issues.append("ENTRYPOINT_MISSING")
    else:
        visit("web/app.js")
    for orphan in sorted(all_modules - visited):
        issues.append(f"ORPHAN_MODULE: {orphan}")

    app = root / "web/app.js"
    app_metrics = {}
    if app.is_file():
        code = app.read_text(encoding="utf-8")
        names = sorted(FUNCTION.findall(code))
        bindings = sorted(set(BINDING.findall(code)))
        if names != policy.get("app_functions"):
            issues.append("APP_NAMED_FUNCTION_DRIFT")
        if bindings != policy.get("app_top_level_bindings"):
            issues.append("APP_STATE_OWNERSHIP_DRIFT")
        app_metrics = {"functions": len(names), "bindings": len(bindings),
                       "direct_event_listeners": code.count(".addEventListener("),
                       "dom_reference_heuristic": len(DOM_TOUCH.findall(code))}
        for metric in ("direct_event_listeners", "dom_reference_heuristic"):
            if app_metrics[metric] != policy.get("app_limits", {}).get(metric):
                issues.append(f"APP_RESPONSIBILITY_COUNTER_DRIFT: {metric}")
        # Exported session and presenter responsibilities must not be copied
        # into composition-root declarations; module-level lexical constraint.
        reserved = {entry for p, spec in contracts.items() if p != "web/app.js"
                    for entry in spec.get("exports", []) if spec.get("owner") in
                    ("session", "diagnostics")}
        if (set(names) | set(bindings)) & reserved:
            issues.append("DUPLICATED_MODULE_OWNER_IN_APP")

    protected_backend = set(policy.get("required_backend_modules", []))
    actual_backend = {p.relative_to(root).as_posix()
                      for p in (root / "network_core").rglob("*.py")
                      if "__pycache__" not in p.parts}
    if not protected_backend.issubset(actual_backend):
        issues.append("BACKEND_MODULE_REMOVED: " +
                      repr(sorted(protected_backend - actual_backend)))
    if actual_backend != protected_backend:
        issues.append("BACKEND_MODULE_INVENTORY_DRIFT")
    for file in (root / "network_core").rglob("*.py"):
        if "__pycache__" in file.parts:
            continue
        rel = file.relative_to(root).as_posix()
        try:
            tree = ast.parse(file.read_text(encoding="utf-8"), filename=rel)
        except SyntaxError:
            issues.append(f"BACKEND_PYTHON_SYNTAX_ERROR: {rel}")
            continue
        if rel.startswith("network_core/engine/"):
            for node in ast.walk(tree):
                name = None
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module = alias.name
                        if (module.startswith("network_core.")
                                and module.split(".")[1] in LEGACY_RUNTIME):
                            issues.append(f"ENGINE_IMPORTS_LEGACY_RUNTIME: {rel} -> {module}")
                if isinstance(node, ast.ImportFrom):
                    if node.level >= 2:
                        name = (node.module or "").split(".")[0]
                        if not name and node.names:
                            name = node.names[0].name
                    elif node.level == 0 and node.module:
                        parts = node.module.split(".")
                        name = parts[1] if len(parts) > 1 and parts[0] == "network_core" else None
                    if name in LEGACY_RUNTIME:
                        issues.append(f"ENGINE_IMPORTS_LEGACY_RUNTIME: {rel} -> {name}")
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == "validate_project" and rel != "network_core/model.py":
                    issues.append(f"SECOND_PROJECT_VALIDATOR: {rel}")
            if isinstance(node, ast.ClassDef):
                if node.name == "EchoExchange" and rel != "network_core/icmp_ping.py":
                    issues.append(f"SECOND_ECHO_ENGINE: {rel}")
            if rel.startswith("network_core/import_") and isinstance(node, ast.ImportFrom):
                if node.module == "server":
                    issues.append(f"IMPORT_DEPENDS_ON_HTTP: {rel}")

    tests = regression_paths(root)
    expected_tests = set(policy.get("required_tests", []))
    if tests != expected_tests:
        issues.append("REGRESSION_TEST_INVENTORY_DRIFT: " +
                      repr(sorted(tests ^ expected_tests)))

    issues.extend(retirement_issues(root, policy, {
        "backend": actual_backend, "frontend": all_modules, "tests": tests,
    }))
    if old is not None:
        issues.extend(compare_policies(old, policy))
    base_budgets = old.get("line_budgets", {}) if old is not None else {}
    source_trend = {
        path: {"actual_lines": actual, "base_budget": base_budgets.get(path),
               "delta_vs_base": (actual - base_budgets[path]
                                 if path in base_budgets else None)}
        for path, actual in actual_budgets.items()
    }
    owner_counts: dict[str, int] = {}
    for spec in contracts.values():
        name = spec.get("owner", "UNKNOWN")
        owner_counts[name] = owner_counts.get(name, 0) + 1
    report = {"policy_schema": policy.get("schema"),
              "baseline_source": policy.get("source_baseline"),
              "source_lines": actual_budgets,
              "source_line_trend": source_trend,
              "frontend_module_count": len(all_modules),
              "frontend_module_delta_vs_base": (
                  len(all_modules) - len(old.get("frontend_contracts", {}))
                  if old is not None else None),
              "module_owner_counts": dict(sorted(owner_counts.items())),
              "import_edge_count": sum(map(len, graph.values())),
              "backend_module_count": len(actual_backend),
              "retirement_receipts": {group: len(evidence)
                                      for group, evidence in
                                      retirement_receipts(policy).items()},
              "regression_files": len(tests),
              "app": app_metrics,
              "base_policy_comparison": "enforced" if old is not None else "none",
              "issues": sorted(set(issues))}
    return sorted(set(issues)), report


def read_base_policy(ref: str, root: Path) -> dict | None:
    if not SHA.fullmatch(ref):
        raise ValueError("base must be an exact 40-character commit SHA")
    process = subprocess.run(["git", "show", f"{ref}:{POLICY}"],
                             cwd=root, capture_output=True, text=True, check=False)
    if process.returncode == 0:
        return json.loads(process.stdout)
    # The first installation PR has no architecture/baseline.json in main.
    tree = subprocess.run(["git", "ls-tree", "--name-only", ref, "architecture"],
                          cwd=root, capture_output=True, text=True, check=True)
    if "architecture" not in tree.stdout.splitlines():
        raise RuntimeError("base revision has no architecture directory; abort")
    exists = subprocess.run(["git", "cat-file", "-e", f"{ref}:architecture/a0_baseline.json"],
                            cwd=root, capture_output=True, text=True, check=False)
    if exists.returncode != 0:
        raise RuntimeError("base policy missing outside initial A1 installation")
    # A0 predecessor is permitted to lack this new policy exactly once.
    if ref != "fcf81716285ef3a4d927d3ac05556b5c2fb6f7f5":
        raise RuntimeError("unexpected base missing architecture policy")
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--base-ref", default=None)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()
    root = args.root.resolve()
    policy = json.loads((root / POLICY).read_text(encoding="utf-8"))
    try:
        old = read_base_policy(args.base_ref, root) if args.base_ref else None
        errors, report = validate(root, policy, old)
    except (ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        errors = [f"BASE_REF_VERIFICATION_FAILED: {error}"]
        report = {"issues": errors}
    if args.report is not None:
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
