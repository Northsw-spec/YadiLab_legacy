"""Real socket checks for the loopback HTTP trust boundary."""
import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

from network_core.server import LabHTTPServer
from network_core.storage import ProjectStore
from test_model import example


class LocalHTTPBoundaryTests(unittest.TestCase):
    def test_server_refuses_non_loopback_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "127.0.0.1"):
                LabHTTPServer(("0.0.0.0", 0), ProjectStore(Path(directory)))

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = ProjectStore(Path(self.tmp.name))
        self.server = LabHTTPServer(("127.0.0.1", 0), self.store)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.host = f"127.0.0.1:{self.server.server_port}"
        self.origin = f"http://{self.host}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=4)
        self.tmp.cleanup()

    def request(self, method, path, headers=(), data=None):
        payload = None if data is None else json.dumps(data).encode("utf-8")
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port,
                                                timeout=5)
        connection.putrequest(method, path, skip_host=True)
        for key, value in headers:
            connection.putheader(key, value)
        if payload is not None:
            connection.putheader("Content-Type", "application/json")
            connection.putheader("Content-Length", str(len(payload)))
        connection.endheaders(payload)
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return result

    def test_exact_host_and_same_origin_allow_browser_and_local_client(self):
        for headers in ((("Host", self.host),),
                        (("Host", self.host), ("Origin", self.origin),
                         ("Sec-Fetch-Site", "same-origin"))):
            with self.subTest(headers=headers):
                status, _, _ = self.request("GET", "/api/health", headers)
                self.assertEqual(status, 200)
        payload = {"filename": "local", "project": example(), "expectedSha256": None}
        status, _, _ = self.request("POST", "/api/save", (("Host", self.host),), payload)
        self.assertEqual(status, 200)
        self.assertEqual(self.store.read("local")["project"], example())

    def test_reject_ambiguous_post_framing_without_saving_a_project(self):
        project = {"filename": "framing", "project": example(), "expectedSha256": None}
        payload = json.dumps(project).encode("utf-8")
        length = str(len(payload))
        variants = (
            ("conflicting duplicate", (("Content-Length", length),
                                       ("Content-Length", str(len(payload) + 1)))),
            ("identical duplicate", (("Content-Length", length),
                                     ("Content-Length", length))),
            ("transfer and length", (("Content-Length", length),
                                     ("Transfer-Encoding", "chunked"))),
            ("transfer only", (("Transfer-Encoding", "chunked"),)),
            ("missing length", ()),
            ("signed length", (("Content-Length", "+" + length),)),
            ("comma list", (("Content-Length", length + ", " + length),)),
            ("huge decimal", (("Content-Length", "9" * 5000),)),
        )
        for label, framing_headers in variants:
            with self.subTest(case=label):
                connection = http.client.HTTPConnection(
                    "127.0.0.1", self.server.server_port, timeout=5)
                try:
                    connection.putrequest("POST", "/api/save", skip_host=True)
                    connection.putheader("Host", self.host)
                    connection.putheader("Content-Type", "application/json")
                    for field, value in framing_headers:
                        connection.putheader(field, value)
                    connection.endheaders(payload)
                    response = connection.getresponse()
                    self.assertEqual(response.status, 400)
                    self.assertEqual(json.loads(response.read())["error"], "INVALID_REQUEST")
                    self.assertTrue(response.will_close)
                finally:
                    connection.close()
                self.assertEqual(self.store.list(), [])
        # The malformed requests must not disable normal, explicitly saved JSON.
        status, _, raw = self.request("POST", "/api/save",
                                      (("Host", self.host),), project)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw)["filename"], "framing")
        self.assertEqual(self.store.read("framing")["project"], example())

    def test_trace_rejects_non_string_node_ids_with_422(self):
        headers = (("Host", self.host),)
        project = example()
        for source, target in (
                ([], "pc-b"), ("pc-a", {}),
                ({}, "pc-b"), ("pc-a", []),
                (None, "pc-b"), ("pc-a", False)):
            with self.subTest(source=source, target=target):
                status, _, raw = self.request("POST", "/api/trace", headers, {
                    "project": project, "source": source, "target": target,
                })
                self.assertEqual(status, 422)
                response = json.loads(raw)
                self.assertEqual(response["error"], "INVALID_PROJECT")
                self.assertIn("node ID strings", response["message"])

        status, _, raw = self.request("POST", "/api/trace", headers, {
            "project": project, "source": "pc-a", "target": "pc-b",
        })
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw)["status"], "PATH_PRESENT")

    def test_huge_json_coordinate_returns_422_without_project_write(self):
        headers = (("Host", self.host),)
        for axis in ("x", "y"):
            for value in (10 ** 400, -(10 ** 400)):
                with self.subTest(axis=axis, negative=value < 0):
                    project = example()
                    project["nodes"][0][axis] = value
                    status, _, raw = self.request("POST", "/api/trace", headers, {
                        "project": project, "source": "pc-a", "target": "pc-b",
                    })
                    self.assertEqual(status, 422)
                    response = json.loads(raw)
                    self.assertEqual(response["error"], "INVALID_PROJECT")
                    self.assertIn("finite coordinate", response["message"])
        self.assertEqual(list(Path(self.tmp.name).glob("*.yadilab")), [])

        project = example()
        project["nodes"][0]["x"] = 10 ** 400
        status, _, raw = self.request("POST", "/api/save", headers, {
            "filename": "rejected", "project": project, "expectedSha256": None,
        })
        self.assertEqual(status, 422)
        self.assertEqual(json.loads(raw)["error"], "INVALID_PROJECT")
        self.assertEqual(list(Path(self.tmp.name).glob("*.yadilab")), [])

    def test_static_modules_are_explicitly_allowed_without_directory_access(self):
        headers = (("Host", self.host),)
        for path in ("/ui/dom.js", "/ui/workspace-panels.js", "/services/api.js",
                     "/features/projects/workspace-revisions.js", "/features/projects/persistence.js", "/features/projects/transfer.js",
                     "/features/diagnostics/queries.js", "/features/diagnostics/presenters.js",
                     "/features/diagnostics/icmp-investigation-panel.js",
                     "/features/diagnostics/protocol-lessons.js",
                     "/features/sessions/dhcp-investigation.js",
                     "/features/sessions/icmp-investigation.js",
                     "/features/sessions/dora-session.js",
                     "/features/sessions/simulation-session.js"):
            with self.subTest(path=path):
                status, response_headers, body = self.request("GET", path, headers)
                self.assertEqual(status, 200)
                self.assertIn(response_headers["Content-Type"].split(";", 1)[0],
                              ("text/javascript", "application/javascript"))
                self.assertIn(b"export ", body)
        for path in ("/ui/", "/services/", "/features/", "/features/projects/",
                     "/features/diagnostics/", "/features/diagnostics/queries.js/extra",
                     "/features/diagnostics/icmp-investigation-panel.js/extra",
                     "/features/sessions/", "/features/sessions/dhcp-investigation.js/extra",
                     "/features/sessions/unknown.js",
                     "/features/sessions/icmp-investigation.js/extra",
                     "/features/sessions/dora-session.js/extra",
                     "/features/sessions/simulation-session.js/extra",
                     "/features/sessions/../app.js",
                     "/features/projects/transfer.js/extra",
                     "/features/projects/../projects/persistence.js",
                     "/ui/../services/api.js",
                     "/network_core/server.py", "/docs/PEDAGOGICAL_TROUBLESHOOTING_PLAN.md"):
            with self.subTest(path=path):
                status, _, body = self.request("GET", path, headers)
                self.assertEqual(status, 404)
                self.assertNotIn(b"export ", body)

    def test_reject_bad_host_before_project_read_or_write(self):
        self.store.save("private", example())
        bad_hosts = ("evil.example", "localhost", "127.0.0.1",
                     f"127.0.0.1:{self.server.server_port + 1}",
                     f"127.0.0.1:{self.server.server_port}.evil.example")
        for host in bad_hosts:
            with self.subTest(host=host):
                status, _, body = self.request("GET", "/api/projects/private",
                                               (("Host", host),))
                self.assertEqual(status, 403)
                self.assertNotIn(b"private", body)
                status, _, _ = self.request("POST", "/api/save", (("Host", host),),
                                             {"filename": "intruder", "project": example(),
                                              "expectedSha256": None})
                self.assertEqual(status, 403)
        for hosts in ((), (("Host", self.host), ("Host", self.host))):
            with self.subTest(hosts=hosts):
                self.assertEqual(self.request("GET", "/api/projects/private", hosts)[0],
                                 403)
        self.assertFalse(self.store.path("intruder").exists())

    def test_reject_cross_origin_and_fetch_metadata_without_origin(self):
        self.store.save("private", example())
        for origin in ("http://evil.example", "null", "https://" + self.host,
                       self.origin + "/", f"http://127.0.0.1:{self.server.server_port + 1}"):
            with self.subTest(origin=origin):
                headers = (("Host", self.host), ("Origin", origin))
                self.assertEqual(self.request("GET", "/api/projects/private", headers)[0],
                                 403)
                self.assertEqual(self.request("POST", "/api/save", headers,
                                              {"filename": "intruder", "project": example(),
                                               "expectedSha256": None})[0], 403)
        for site in ("cross-site", "same-site"):
            headers = (("Host", self.host), ("Sec-Fetch-Site", site))
            self.assertEqual(self.request("GET", "/api/projects/private", headers)[0], 403)
            self.assertEqual(self.request("POST", "/api/save", headers,
                                          {"filename": "intruder", "project": example(),
                                           "expectedSha256": None})[0], 403)
        self.assertFalse(self.store.path("intruder").exists())

    def test_no_origin_form_cannot_write_and_duplicate_origin_is_rejected(self):
        payload = json.dumps({"filename": "intruder", "project": example(),
                              "expectedSha256": None}).encode("utf-8")
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port,
                                                timeout=5)
        connection.putrequest("POST", "/api/save", skip_host=True)
        connection.putheader("Host", self.host)
        connection.putheader("Content-Type", "text/plain")
        connection.putheader("Content-Length", str(len(payload)))
        connection.endheaders(payload)
        response = connection.getresponse()
        self.assertEqual(response.status, 415)
        response.read()
        connection.close()
        headers = (("Host", self.host), ("Origin", self.origin),
                   ("Origin", self.origin))
        self.assertEqual(self.request("POST", "/api/save", headers,
                                      {"filename": "intruder", "project": example(),
                                       "expectedSha256": None})[0], 403)
        self.assertFalse(self.store.path("intruder").exists())

    def test_preflight_does_not_enable_cors(self):
        headers = (("Host", self.host), ("Origin", "http://evil.example"),
                   ("Access-Control-Request-Method", "POST"))
        status, response_headers, _ = self.request("OPTIONS", "/api/save", headers)
        self.assertEqual(status, 403)
        self.assertNotIn("Access-Control-Allow-Origin", response_headers)


class ProtectedLocalAPITests(unittest.TestCase):
    """Private loopback project APIs require a per-process capability."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = ProjectStore(Path(self.temp.name))
        self.key = "Z" * 43  # Only a fake test key; CLI uses a CSPRNG.
        self.server = LabHTTPServer(("127.0.0.1", 0), self.store, auth_token=self.key)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.host = f"127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=4)
        self.temp.cleanup()

    def request(self, method, path, extra=(), data=None):
        payload = None if data is None else json.dumps(data).encode()
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        conn.putrequest(method, path, skip_host=True)
        conn.putheader("Host", self.host)
        for key, value in extra:
            conn.putheader(key, value)
        if payload is not None:
            conn.putheader("Content-Type", "application/json")
            conn.putheader("Content-Length", str(len(payload)))
        conn.endheaders(payload)
        response = conn.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        conn.close()
        return result

    def test_another_local_process_cannot_read_write_or_infer_project(self):
        original = self.store.save("private", example())
        for path in ("/api/projects", "/api/projects/private",
                     "/api/diagnostics/arp", "/api/save", "/api/%70rojects/private"):
            with self.subTest(path=path):
                status, _, raw = self.request("GET", path)
                self.assertEqual(status, 401)
                self.assertEqual(json.loads(raw)["error"], "AUTH_REQUIRED")
                self.assertNotIn(b"PC A", raw)
                self.assertNotIn(self.key.encode(), raw)
        payload = {"filename": "intruder", "project": example(), "expectedSha256": None}
        self.assertEqual(self.request("POST", "/api/save", data=payload)[0], 401)
        self.assertFalse(self.store.path("intruder").exists())
        self.assertEqual(self.store.read("private")["sha256"], original["sha256"])

    def test_bad_duplicate_or_wrong_scheme_authorization_is_denied(self):
        for extra in ((("Authorization", "Bearer " + "A" * 43),),
                      (("Authorization", "Basic abc"),),
                      (("Authorization", "Bearer é"),),
                      (("Authorization", "Bearer " + self.key),
                       ("Authorization", "Bearer " + self.key))):
            with self.subTest(extra=extra):
                self.assertEqual(self.request("GET", "/api/projects", extra)[0], 401)

    def test_owner_can_save_and_reopen_with_key_but_not_bypass_origin(self):
        header = (("Authorization", "Bearer " + self.key),)
        self.assertEqual(self.request("GET", "/api/projects", header)[0], 200)
        payload = {"filename": "explicit", "project": example(), "expectedSha256": None}
        status, _, response = self.request("POST", "/api/save", header, payload)
        self.assertEqual(status, 200)
        saved = json.loads(response)
        status, _, response = self.request("GET", "/api/projects/explicit", header)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(response)["project"], example())
        self.assertEqual(self.store.read("explicit")["sha256"], saved["sha256"])
        bad_origin = header + (("Origin", "http://other.example"),)
        self.assertEqual(self.request("GET", "/api/projects", bad_origin)[0], 403)

    def test_health_static_shell_and_only_synthetic_templates_are_public(self):
        for path in ("/api/health", "/", "/index.html", "/app.js",
                     "/services/api.js", "/api/templates/xlsx", "/api/templates/ods"):
            with self.subTest(path=path):
                status, _, raw = self.request("GET", path)
                self.assertEqual(status, 200)
                self.assertNotIn(self.key.encode(), raw)
        self.assertEqual(self.request("POST", "/api/validate", data=example())[0], 401)

    def test_short_invalid_or_nonstring_capabilities_rejected_before_bind(self):
        for value in ("", "weak", True, 3, " " * 43, "a" * 43 + "\n"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                LabHTTPServer(("127.0.0.1", 0), self.store, auth_token=value)
