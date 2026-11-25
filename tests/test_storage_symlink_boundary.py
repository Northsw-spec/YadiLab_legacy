"""Linux project-file boundary: do not follow symlinks or open special files.

All resources are temporary and no actual user project paths are modified.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from network_core.model import ProjectValidationError
from network_core.server import LabHTTPServer
from network_core.storage import ProjectStore
from test_model import example


class ProjectStorageBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "projects"
        self.external = Path(self.temp.name) / "outside"
        self.store = ProjectStore(self.root)
        external_store = ProjectStore(self.external)
        external_store.save("private", example())
        self.external_file = self.external / "private.yadilab"
        self.external_bytes = self.external_file.read_bytes()

    def tearDown(self):
        self.temp.cleanup()

    def test_external_and_internal_links_cannot_be_read_listed_or_saved(self):
        good = self.store.save("normal", example())
        self.assertEqual(self.store.read("normal")["sha256"], good["sha256"])
        os.symlink(self.external_file, self.root / "outside-link.yadilab")
        os.symlink(self.root / "normal.yadilab", self.root / "inside-link.yadilab")
        for slug in ("outside-link", "inside-link"):
            with self.subTest(slug=slug):
                self.assertTrue((self.root / (slug + ".yadilab")).is_symlink())
                with self.assertRaises(ProjectValidationError):
                    self.store.read(slug)
                with self.assertRaises(ProjectValidationError):
                    self.store.save(slug, example())
                with self.assertRaises(ProjectValidationError):
                    self.store.save(slug, example(), hashlib.sha256(self.external_bytes).hexdigest())
        self.assertEqual([item["filename"] for item in self.store.list()], ["normal"])
        self.assertEqual(self.external_file.read_bytes(), self.external_bytes)
        self.assertTrue((self.root / "outside-link.yadilab").is_symlink())
        self.assertEqual(self.store.read("normal")["project"], example())

    def test_dangling_symlink_cannot_become_create_only_project(self):
        link = self.root / "dangling.yadilab"
        os.symlink(self.external / "missing.yadilab", link)
        with self.assertRaises(ProjectValidationError):
            self.store.read("dangling")
        with self.assertRaises(ProjectValidationError):
            self.store.save("dangling", example())
        self.assertTrue(link.is_symlink())
        self.assertEqual(self.store.list(), [])
        with self.assertRaises(FileNotFoundError):
            self.store.read("absent")
        self.assertFalse((self.root / "absent.yadilab").exists())

    def test_fifo_and_directory_are_not_read_or_listed_as_projects(self):
        fifo = self.root / "pipe.yadilab"
        os.mkfifo(fifo, mode=0o600)
        (self.root / "directory.yadilab").mkdir()
        for slug in ("pipe", "directory"):
            with self.subTest(slug=slug):
                with self.assertRaises(ProjectValidationError):
                    self.store.read(slug)
                with self.assertRaises(ProjectValidationError):
                    self.store.save(slug, example())
        self.assertEqual(self.store.list(), [])

    def test_nonregular_lock_file_rejected_before_existing_project_overwrite(self):
        saved = self.store.save("locked", example())
        project_path = self.root / "locked.yadilab"
        before = project_path.read_bytes()
        lock_path = self.root / ".lock-locked"
        lock_path.unlink()  # Reproduce an externally substituted lock inode.
        edited = example()
        edited["nodes"][0]["label"] = "proposed replacement"
        for kind in ("symlink", "directory", "fifo"):
            with self.subTest(kind=kind):
                if kind == "symlink":
                    os.symlink(self.external_file, lock_path)
                elif kind == "directory":
                    lock_path.mkdir()
                else:
                    os.mkfifo(lock_path, mode=0o600)
                try:
                    with self.assertRaisesRegex(ProjectValidationError, "project lock"):
                        self.store.save("locked", edited, saved["sha256"])
                    self.assertEqual(project_path.read_bytes(), before)
                    self.assertEqual(self.store.read("locked")["sha256"], saved["sha256"])
                    self.assertEqual(self.external_file.read_bytes(), self.external_bytes)
                    self.assertEqual([item["filename"] for item in self.store.list()], ["locked"])
                    self.assertEqual(list(self.root.glob(".pending-*")), [])
                finally:
                    if kind == "directory":
                        lock_path.rmdir()
                    else:
                        lock_path.unlink()
        # A normal regular lock may be re-created and the same old SHA is valid.
        updated = self.store.save("locked", edited, saved["sha256"])
        self.assertEqual(self.store.read("locked")["project"], edited)
        self.assertEqual(updated["sha256"], hashlib.sha256(project_path.read_bytes()).hexdigest())
        self.assertNotEqual(updated["sha256"], saved["sha256"])
        self.assertEqual(self.external_file.read_bytes(), self.external_bytes)

    def test_http_special_lock_returns_422_and_preserves_saved_bytes(self):
        saved = self.store.save("locked", example())
        project_path = self.root / "locked.yadilab"
        before = project_path.read_bytes()
        lock_path = self.root / ".lock-locked"
        lock_path.unlink()
        os.symlink(self.external_file, lock_path)
        server = LabHTTPServer(("127.0.0.1", 0), self.store)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{server.server_port}/api/save"
        edited = example()
        edited["nodes"][0]["label"] = "should not be written"
        body = json.dumps({"filename": "locked", "project": edited,
                           "expectedSha256": saved["sha256"]}).encode("utf-8")
        try:
            with self.assertRaises(HTTPError) as failed:
                urlopen(Request(url, data=body, headers={
                    "Content-Type": "application/json",
                }, method="POST"), timeout=5)
            self.assertEqual(failed.exception.code, 422)
            error = json.loads(failed.exception.read())
            self.assertEqual(error["error"], "INVALID_PROJECT")
            self.assertIn("project lock", error["message"])
            self.assertEqual(project_path.read_bytes(), before)
            self.assertEqual(self.store.read("locked")["sha256"], saved["sha256"])
            self.assertEqual(self.external_file.read_bytes(), self.external_bytes)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=4)
            lock_path.unlink()
        recovered = self.store.save("locked", edited, saved["sha256"])
        self.assertEqual(recovered["sha256"], hashlib.sha256(project_path.read_bytes()).hexdigest())

    def test_loopback_http_refuses_symlink_without_leaking_external_file(self):
        os.symlink(self.external_file, self.root / "leaked.yadilab")
        server = LabHTTPServer(("127.0.0.1", 0), self.store)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{server.server_port}"
        try:
            with self.assertRaises(HTTPError) as failed:
                urlopen(Request(url + "/api/projects/leaked"), timeout=5)
            self.assertEqual(failed.exception.code, 422)
            response = json.loads(failed.exception.read())
            self.assertEqual(response["error"], "INVALID_PROJECT")
            self.assertNotIn("pc-a", response["message"])
            self.assertNotIn("private", response["message"])
            with urlopen(Request(url + "/api/projects"), timeout=5) as response:
                self.assertEqual(json.loads(response.read())["projects"], [])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=4)
        self.assertEqual(self.external_file.read_bytes(), self.external_bytes)


if __name__ == "__main__":
    unittest.main()
