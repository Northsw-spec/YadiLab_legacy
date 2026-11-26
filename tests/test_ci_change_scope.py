"""Safety regression oracles for fail-closed documentation-only CI."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools.ci_change_scope import classify, documentation_only, is_document_path, main


class DocumentationScopeTests(unittest.TestCase):
    def test_only_explicit_documentation_paths_are_eligible(self):
        allowed = ["AGENTS.md", "README.md", ".github/pull_request_template.md",
                   ".github/copilot-instructions.md",
                   "docs/CODEX_EXECUTION_POLICY.md", "docs/architecture/a.md"]
        for name in allowed:
            with self.subTest(name=name):
                self.assertTrue(is_document_path(name))
        for name in ["foo.md", "web/vendor/NOTICE.md", "docs/../web/foo.md",
                     ".github/workflows/ci.yml", "tests/test_ci_integrity.py",
                     "tools/ci_change_scope.py", "docs/a.rst"]:
            with self.subTest(name=name):
                self.assertFalse(is_document_path(name))

    def test_full_acceptance_for_mixed_or_unknown_or_deleted_changes(self):
        self.assertTrue(documentation_only([("M", "AGENTS.md"),
                                            ("A", "docs/new.md")]))
        self.assertFalse(documentation_only([]))
        for status, name in [("M", "web/app.js"), ("A", "tests/new.py"),
                             ("M", ".github/workflows/ci.yml"),
                             ("D", "docs/old.md"), ("R100", "docs/a.md"),
                             ("T", "docs/a.md"), ("M", "web/vendor/NOTICE.md")]:
            self.assertFalse(documentation_only([("M", "README.md"),
                                                 (status, name)]))

    def test_real_git_diff_succeeds_only_for_proven_regular_markdown(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            def run(*args):
                return subprocess.check_output(["git", *args], cwd=root).decode().strip()
            run("init", "-q")
            run("config", "user.email", "ci@example.invalid")
            run("config", "user.name", "CI Fixture")
            (root / "README.md").write_text("# Base\n")
            (root / "app.py").write_text("print(1)\n")
            run("add", ".")
            run("commit", "-qm", "base")
            base = run("rev-parse", "HEAD")
            original = os.getcwd()
            try:
                os.chdir(root)
                (root / "README.md").write_text("# Document\n")
                run("add", ".")
                run("commit", "-qm", "docs")
                self.assertTrue(classify(base))
                (root / "app.py").write_text("print(2)\n")
                run("add", ".")
                run("commit", "-qm", "runtime")
                self.assertFalse(classify(base))
                with self.assertRaises(ValueError):
                    classify("main")
            finally:
                os.chdir(original)

    def test_untrusted_or_missing_base_never_proves_documentation_only(self):
        with tempfile.TemporaryDirectory() as d:
            output = Path(d) / "out"
            with patch.dict(os.environ, {"GITHUB_EVENT_NAME": "pull_request",
                                         "PR_BASE_SHA": "not-a-sha",
                                         "GITHUB_OUTPUT": str(output)}):
                self.assertEqual(main(), 0)
            self.assertIn("docs_only=false", output.read_text())


if __name__ == "__main__":
    unittest.main()
