"""Protect the X11 PRIMARY regression from accidental CI detachment.

This static check validates workflow wiring. The actual browser + X11 behavior
is independently exercised by the required unit-tests job itself.
"""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
CI = ROOT / ".github" / "workflows" / "ci.yml"
MANUAL = ROOT / ".github" / "workflows" / "x11-primary-middle-paste.yml"
COMMAND = "xvfb-run -a python3 tests/browser_primary_selection_x11.py"


class RequiredX11CITests(unittest.TestCase):
    def test_primary_selection_is_part_of_required_pr_and_main_job(self):
        workflow = CI.read_text(encoding="utf-8")
        self.assertRegex(workflow, r"(?m)^on:\n  push:\n  pull_request:\n")
        self.assertIn("\n  unit-tests:\n", workflow)
        body = workflow.split("\n  unit-tests:\n", 1)[1]
        # A future independent job is not automatically protected by the
        # repository ruleset requiring the unit-tests context.
        other_job = re.search(r"(?m)^  [a-zA-Z][\w-]*:\s*$", body)
        if other_job:
            body = body[:other_job.start()]
        steps = re.split(r"(?m)^      - name: ", body)
        x11 = [step for step in steps
               if step.startswith("Real X11 PRIMARY middle-pan and clipboard regression\n")]
        self.assertEqual(len(x11), 1, "X11 must be one required unit-tests step")
        step = x11[0]
        self.assertIn("        run: " + COMMAND, step)
        self.assertNotRegex(step, r"(?m)^        (?:if|continue-on-error):")
        self.assertIn("sudo apt-get install -y xvfb xauth xclip", body)
        self.assertIn("python3 -m playwright install --with-deps chromium", body)
        self.assertLess(body.index("python3 -m playwright install --with-deps chromium"),
                        body.index(COMMAND))

    def test_old_branch_only_workflow_is_manual_not_the_release_gate(self):
        workflow = MANUAL.read_text(encoding="utf-8")
        self.assertIn("  workflow_dispatch:", workflow)
        self.assertNotIn("fix/canvas-middle-primary-selection-paste", workflow)


if __name__ == "__main__":
    unittest.main()
