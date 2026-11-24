"""Bounded CI supply-chain and vendored asset regression checks.

This tests repository policies, not proof of zero vulnerabilities.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parent.parent
ACTION_REF = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[a-f0-9]{40}$")
USES = re.compile(r"(?m)^\s*-\s*uses:\s*(\S+)")


class WorkflowSupplyChainTests(unittest.TestCase):
    def test_all_workflows_have_full_sha_pinned_actions(self):
        workflows = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
        self.assertGreaterEqual(len(workflows), 5)
        for path in workflows:
            content = path.read_text(encoding="utf-8")
            found = USES.findall(content)
            self.assertTrue(found, f"{path.name}: no external actions found")
            for ref in found:
                with self.subTest(workflow=path.name, action=ref):
                    self.assertRegex(ref, ACTION_REF,
                                     f"{path.name}: action must use verified 40-hex commit")
            self.assertRegex(content, r"(?m)^permissions:\n  contents: read$",
                             f"{path.name}: require minimal repository permissions")
            self.assertNotRegex(content, r"(?m)^\s*(?:id-token|actions|checks|issues|packages|pull-requests|security-events|workflows):\s*write\b",
                                f"{path.name}: unreviewed write access")

    def test_git_checkout_never_leaves_workflow_token_on_disk(self):
        workflows = list((ROOT / ".github" / "workflows").glob("*.yml"))
        for path in workflows:
            content = path.read_text(encoding="utf-8")
            checkout = re.compile(r"(?m)^\s*- uses: actions/checkout@[a-f0-9]{40}[^\n]*\n"
                                  r"\s+with:\n\s+persist-credentials: false(?:\n|$)")
            self.assertRegex(content, checkout, f"{path.name}: checkout credentials persisted")

    def test_reject_unpinned_action_examples(self):
        self.assertFalse(ACTION_REF.fullmatch("actions/checkout@v4"))
        self.assertFalse(ACTION_REF.fullmatch("actions/checkout@main"))
        self.assertFalse(ACTION_REF.fullmatch("actions/checkout@123abc"))
        self.assertTrue(ACTION_REF.fullmatch("actions/checkout@" + "1" * 40))


class VendorAssetIntegrityTests(unittest.TestCase):
    def test_offline_elk_worker_matches_documented_sha256(self):
        notice = (ROOT / "web" / "vendor" / "NOTICE.md").read_text(encoding="utf-8")
        match = re.search(r"(?m)^Worker SHA-256:\s*([a-f0-9]{64})\s*$", notice)
        self.assertIsNotNone(match, "Offline worker must have an explicit digest")
        digest = hashlib.sha256((ROOT / "web" / "vendor" / "elk-worker.js").read_bytes()).hexdigest()
        self.assertEqual(digest, match.group(1), "Vendored worker differs from declared bytes")

    def test_vendor_license_is_not_mistaken_for_first_party_license(self):
        notice = (ROOT / "web" / "vendor" / "NOTICE.md").read_text(encoding="utf-8")
        self.assertIn("elkjs 0.13.0", notice)
        self.assertIn("EPL-2.0 OR GPL-3.0-or-later", notice)
        self.assertTrue((ROOT / "web" / "vendor" / "ELK-LICENSE.md").is_file())
        # The root project's license is a rights-holder decision (issue #115).
        # These assertions neither grant one nor imply license compliance.


if __name__ == "__main__":
    unittest.main()
