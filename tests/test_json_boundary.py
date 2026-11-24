"""Independent JSON-boundary regression oracles for source identity and Save."""
from __future__ import annotations

import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

from network_core.json_boundary import decode_json_document
from network_core.model import ProjectValidationError, blank_project
from network_core.server import LabHTTPServer
from network_core.storage import ProjectStore


class StrictJsonBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = ProjectStore(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_duplicate_members_in_saved_project_are_rejected_without_rewriting_bytes(self):
        raw = (b'{"schemaVersion":"1.3","name":"original","name":"shadow",'
               b'"zones":[],"nodes":[],"links":[]}')
        path = self.store.path("duplicate")
        path.write_bytes(raw)
        with self.assertRaisesRegex(ProjectValidationError, "duplicate JSON member"):
            self.store.read("duplicate")
        self.assertEqual(path.read_bytes(), raw)
        self.assertEqual(self.store.list()[0]["filename"], "duplicate")

    def test_nested_duplicate_members_are_rejected_even_if_semantics_match(self):
        raw = b'{"outer":{"ip":"192.0.2.1","ip":"192.0.2.1"}}'
        with self.assertRaisesRegex(ProjectValidationError, "duplicate JSON member"):
            decode_json_document(raw, context="test")

    def test_invalid_unicode_utf16_and_nonfinite_inputs_are_rejected(self):
        for raw in (b'{"name":"\\ud800"}',
                    b'{"name":1e999}',
                    b'{"name":NaN}',
                    b'{"ok":true}'.decode("ascii").encode("utf-16")):
            with self.subTest(raw=raw[:50]):
                with self.assertRaises(ProjectValidationError):
                    decode_json_document(raw, context="test")
        invalid_project = blank_project("bad\ud800")
        with self.assertRaisesRegex(ProjectValidationError, "invalid Unicode surrogate"):
            self.store.save("invalid", invalid_project)
        self.assertFalse(self.store.path("invalid").exists())

    def test_deeply_nested_input_is_rejected_not_exposed_as_recursion_crash(self):
        data = b"[" * 1500 + b"0" + b"]" * 1500
        with self.assertRaises(ProjectValidationError):
            decode_json_document(data, context="test")

    def test_valid_unicode_and_explicit_project_facts_are_preserved(self):
        project = blank_project("Ångström – nätverk 🧪")
        output = self.store.save("valid", project)
        self.assertEqual(self.store.read("valid")["project"], project)
        self.assertEqual(len(output["sha256"]), 64)
        raw = json.dumps(project, ensure_ascii=False).encode("utf-8")
        self.assertEqual(decode_json_document(raw, context="test"), project)


class StrictJsonHttpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = ProjectStore(Path(self.tmp.name))
        self.server = LabHTTPServer(("127.0.0.1", 0), self.store)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=4)
        self.tmp.cleanup()

    def _post_raw(self, path: str, raw: bytes) -> tuple[int, dict]:
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            conn.request("POST", path, body=raw,
                         headers={"Content-Type": "application/json"})
            resp = conn.getresponse()
            return resp.status, json.loads(resp.read())
        finally:
            conn.close()

    def test_duplicate_key_http_save_is_422_and_does_not_create_file(self):
        raw = (b'{"filename":"lab","project":{"schemaVersion":"1.3",'
               b'"name":"correct","name":"shadow","zones":[],"nodes":[],"links":[]},'
               b'"expectedSha256":null}')
        status, body = self._post_raw("/api/save", raw)
        self.assertEqual(status, 422)
        self.assertEqual(body["error"], "INVALID_PROJECT")
        self.assertIn("duplicate JSON member", body["message"])
        self.assertEqual(self.store.list(), [])

    def test_invalid_surrogate_http_validate_is_422_not_server_error(self):
        raw = (b'{"schemaVersion":"1.3","name":"\\ud800",'
               b'"zones":[],"nodes":[],"links":[]}')
        status, body = self._post_raw("/api/validate", raw)
        self.assertEqual(status, 422)
        self.assertEqual(body["error"], "INVALID_PROJECT")
        self.assertEqual(self.store.list(), [])

    def test_regular_unicode_http_validate_still_works(self):
        raw = json.dumps(blank_project("Säker testmiljö"), ensure_ascii=False).encode("utf-8")
        status, body = self._post_raw("/api/validate", raw)
        self.assertEqual(status, 200)
        self.assertEqual(body["project"]["name"], "Säker testmiljö")


if __name__ == "__main__":
    unittest.main()
