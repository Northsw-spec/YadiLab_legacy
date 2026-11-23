"""Temporary negative QUALITY-002 enforcement probe. MUST NEVER BE MERGED.

This is deliberately red. No product source or workflow definition is changed.
Remove the entire branch after closing the probe pull request.
"""
import unittest


class RequiredCheckNegativeProbe(unittest.TestCase):
    def test_required_unit_tests_must_block_merge(self):
        self.fail("INTENTIONAL QUALITY-002 NEGATIVE CHECK FAILURE: DO NOT MERGE")


if __name__ == "__main__":
    unittest.main()
