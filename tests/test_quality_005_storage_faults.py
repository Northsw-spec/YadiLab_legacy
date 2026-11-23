"""QUALITY-005/5A-5B: pre-registered Linux local Save failure-boundary tests.

Expected outcomes are specified BEFORE these tests run in
docs/QUALITY_005_STORAGE_FAILURE_ORACLES.md.
Only disposable TemporaryDirectory paths are touched. Not power-loss testing.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from network_core.model import ProjectValidationError
from network_core.storage import ProjectConflictError, ProjectStore
from test_model import example


def renamed_document(label: str) -> dict:
    project = example()
    project["nodes"][0]["label"] = label
    return project


class IndependentStorageFailureOracles(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = ProjectStore(self.root)
        self.path = self.store.path("lab")

    def assert_no_temporary_files(self):
        self.assertEqual(list(self.root.glob(".pending-*")), [])

    def test_file_fsync_failure_before_first_create_is_not_a_save(self):
        incoming = renamed_document("initial")
        before = copy.deepcopy(incoming)
        with patch("network_core.storage.os.fsync",
                   side_effect=OSError("synthetic file fsync error")):
            with self.assertRaisesRegex(OSError, "synthetic file fsync error"):
                self.store.save("lab", incoming)
        self.assertFalse(self.path.exists())
        self.assertEqual(self.store.list(), [])
        self.assert_no_temporary_files()
        self.assertEqual(incoming, before)

        # A previous failed attempt must not hold the process-wide file lock.
        recovered = ProjectStore(self.root).save("lab", incoming)
        actual_bytes = self.path.read_bytes()
        self.assertEqual(recovered["sha256"], hashlib.sha256(actual_bytes).hexdigest())
        self.assertEqual(json.loads(actual_bytes), incoming)
        self.assert_no_temporary_files()

    def test_file_fsync_failure_before_overwrite_preserves_exact_old_bytes(self):
        original = self.store.save("lab", example())
        old_bytes = self.path.read_bytes()
        incoming = renamed_document("next")
        before = copy.deepcopy(incoming)
        with patch("network_core.storage.os.fsync",
                   side_effect=OSError("synthetic overwrite fsync error")):
            with self.assertRaisesRegex(OSError, "synthetic overwrite fsync error"):
                self.store.save("lab", incoming, original["sha256"])

        self.assertEqual(self.path.read_bytes(), old_bytes)
        self.assertEqual(self.store.read("lab")["sha256"], original["sha256"])
        self.assert_no_temporary_files()
        self.assertEqual(incoming, before)

        # A successful retry must be able to reuse the *unchanged* old SHA.
        second = ProjectStore(self.root).save("lab", incoming, original["sha256"])
        self.assertNotEqual(second["sha256"], original["sha256"])
        self.assertEqual(self.store.read("lab")["project"], incoming)
        self.assert_no_temporary_files()

    def test_failed_directory_fsync_after_rename_requires_actual_sha_for_retry(self):
        original = self.store.save("lab", example())
        incoming = renamed_document("was replaced before directory sync")
        real_fsync = os.fsync
        calls = []

        def fail_second_fsync(fd):
            calls.append(fd)
            if len(calls) == 2:
                raise OSError("synthetic directory fsync error")
            return real_fsync(fd)

        with patch("network_core.storage.os.fsync", side_effect=fail_second_fsync):
            with self.assertRaisesRegex(OSError, "synthetic directory fsync error"):
                self.store.save("lab", incoming, original["sha256"])
        self.assertEqual(len(calls), 2)

        # The replacement happened, though directory durability is not proven.
        raw = self.path.read_bytes()
        actual_sha = hashlib.sha256(raw).hexdigest()
        self.assertNotEqual(actual_sha, original["sha256"])
        self.assertEqual(json.loads(raw), incoming)
        self.assertEqual(self.store.read("lab")["sha256"], actual_sha)
        self.assert_no_temporary_files()

        # Retrying with the old SHA MUST NOT overwrite the already replaced file.
        with self.assertRaises(ProjectConflictError) as conflict:
            self.store.save("lab", renamed_document("blind retry"), original["sha256"])
        self.assertEqual(conflict.exception.actual_hash, actual_sha)
        self.assertEqual(self.path.read_bytes(), raw)

        # A deliberately authorized save using the real disk SHA may continue.
        authorized = renamed_document("authorized retry")
        result = ProjectStore(self.root).save("lab", authorized, actual_sha)
        self.assertEqual(self.store.read("lab")["project"], authorized)
        self.assertEqual(result["sha256"],
                         hashlib.sha256(self.path.read_bytes()).hexdigest())
        self.assert_no_temporary_files()

    def test_invalid_declared_link_cannot_partially_overwrite_existing_document(self):
        original = self.store.save("lab", example())
        old_bytes = self.path.read_bytes()
        invalid = example()
        invalid["links"][0]["b"]["port"] = "undeclared-99"
        before = copy.deepcopy(invalid)

        with self.assertRaises(ProjectValidationError):
            self.store.save("lab", invalid, original["sha256"])
        self.assertEqual(invalid, before)
        self.assertEqual(self.path.read_bytes(), old_bytes)
        self.assertEqual(self.store.read("lab")["sha256"], original["sha256"])
        self.assert_no_temporary_files()

    def test_corrupt_existing_file_cannot_be_silently_overwritten_create_only(self):
        raw = b'{"schemaVersion":'
        self.path.write_bytes(raw)  # test setup only, never a real user project
        actual_sha = hashlib.sha256(raw).hexdigest()

        with self.assertRaises(ProjectConflictError) as conflict:
            self.store.save("lab", example(), None)
        self.assertEqual(conflict.exception.actual_hash, actual_sha)
        self.assertEqual(self.path.read_bytes(), raw)
        self.assert_no_temporary_files()
        with self.assertRaisesRegex(ProjectValidationError, "invalid JSON"):
            self.store.read("lab")


if __name__ == "__main__":
    unittest.main()
