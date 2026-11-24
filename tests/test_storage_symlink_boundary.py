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
