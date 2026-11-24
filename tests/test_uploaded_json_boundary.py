"""Real HTTP regression: untrusted JSON must reach the strict byte decoder."""
from __future__ import annotations

import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

from network_core.server import LabHTTPServer
from network_core.storage import ProjectStore


class UploadedJsonSourceBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = ProjectStore(Path(self.tmp.name))
        self.server = LabHTTPServer(("127.0.0.1", 0), self.store)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.tmp.cleanup()

    def post_raw(self, path: str, raw: bytes) -> tuple[int, dict]:
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            connection.request("POST", path, body=raw,
                               headers={"Content-Type": "application/json"})
            response = connection.getresponse()
            return response.status, json.loads(response.read())
        finally:
            connection.close()

    def test_project_upload_with_two_names_rejected_before_canonical_validation(self):
        raw = (b'{"schemaVersion":"1.3","name":"first","name":"shadow",'
               b'"zones":[],"nodes":[],"links":[]}')
        status, response = self.post_raw("/api/validate", raw)
        self.assertEqual(status, 422)
        self.assertEqual(response["error"], "INVALID_PROJECT")
        self.assertIn("duplicate JSON member", response["message"])
        self.assertEqual(self.store.list(), [])

    def test_profile_upload_with_duplicate_fields_rejected_without_loss(self):
        raw = b'{"mappingViews":[{"role":"device_inventory","role":"cable_register"}]}'
        status, response = self.post_raw("/api/json/strict", raw)
        self.assertEqual(status, 422)
        self.assertIn("duplicate JSON member", response["message"])
        self.assertEqual(self.store.list(), [])

    def test_original_source_bundle_rejects_malformed_utf8(self):
        status, response = self.post_raw("/api/json/strict", b'{"source":"\xff"}')
        self.assertEqual(status, 422)
        self.assertEqual(response["error"], "INVALID_PROJECT")
        self.assertEqual(self.store.list(), [])

    def test_read_only_strict_json_allows_valid_profile_and_does_not_save(self):
        profile = {"profileVersion":"1", "views":[{"label":"A", "role":"device_inventory"}]}
        raw = json.dumps(profile, ensure_ascii=False).encode("utf-8")
        status, response = self.post_raw("/api/json/strict", raw)
        self.assertEqual(status, 200)
        self.assertEqual(response, {"document": profile})
        self.assertEqual(self.store.list(), [])

    def test_project_validation_accepts_utf8_and_preserves_result(self):
        project = {"schemaVersion":"1.3","name":"Nätverk – ÅÄÖ",
                   "zones":[],"nodes":[],"links":[]}
        raw = json.dumps(project, ensure_ascii=False).encode("utf-8")
        status, response = self.post_raw("/api/validate", raw)
        self.assertEqual(status, 200)
        self.assertEqual(response["project"], project)
        self.assertEqual(self.store.list(), [])


if __name__ == "__main__":
    unittest.main()
