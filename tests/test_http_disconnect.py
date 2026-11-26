"""A2 real loopback peer-disconnect and preserved HTTP/Save contract oracles."""
from __future__ import annotations

import errno
import hashlib
import http.client
import json
import socket
import struct
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from network_core import server as server_module
from network_core.server import Handler, LabHTTPServer
from network_core.storage import ProjectStore
from test_model import example


class ObservedServer(LabHTTPServer):
    """Record uncaught request exceptions instead of hiding printed tracebacks."""

    def __init__(self, *args, **kwargs):
        self.unhandled = []
        self.logged_errors = []
        self.response_errors = []
        self.json_sends = 0
        self.paused = False
        self.break_headers_once = False
        self.headers_ready = threading.Event()
        self.resume_body = threading.Event()
        self.response_completed = threading.Event()
        self.handler_finished = threading.Event()
        super().__init__(*args, **kwargs)

    def handle_error(self, request, client_address):
        self.unhandled.append(sys.exc_info()[1])


class RecordedHandler(Handler):
    def log_message(self, format, *args):
        # Keep expected client test traffic out of CI stderr.
        pass

    def log_error(self, format, *args):
        self.server.logged_errors.append(format % args)

    def handle_one_request(self):
        try:
            return super().handle_one_request()
        finally:
            self.server.handler_finished.set()

    def _json(self, code, data):
        self.server.json_sends += 1
        return super()._json(code, data)

    def _respond_error(self, error):
        self.server.response_errors.append(error)
        try:
            return super()._respond_error(error)
        finally:
            self.server.response_completed.set()


class PauseAfterHeadersHandler(RecordedHandler):
    def end_headers(self):
        super().end_headers()
        if self.server.paused:
            self.server.paused = False
            self.server.headers_ready.set()
            if not self.server.resume_body.wait(5):
                raise RuntimeError("HTTP disconnect test response barrier timed out")


class BrokenHeaderHandler(RecordedHandler):
    def end_headers(self):
        if self.server.break_headers_once:
            self.server.break_headers_once = False
            raise BrokenPipeError(errno.EPIPE, "client disconnected during headers")
        super().end_headers()


class A2HTTPDisconnectTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = ProjectStore(Path(self.tmp.name))
        self.server = None
        self.thread = None

    def start(self, handler_class=RecordedHandler, *, protected=False):
        if self.server is not None:
            raise AssertionError("start only once per test")
        token = "A" * 40 if protected else None
        # The HTTP server binds its request-handler class at construction.
        with patch.object(server_module, "Handler", handler_class):
            self.server = ObservedServer(("127.0.0.1", 0), self.store, auth_token=token)
        self.addCleanup(self.stop)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self.server

    def stop(self):
        if self.server is not None:
            self.server.resume_body.set()
            self.server.shutdown()
            self.server.server_close()
            self.thread.join(timeout=4)

    @property
    def host(self):
        return f"127.0.0.1:{self.server.server_port}"

    def request(self, method, path, *, raw=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            fields = {"Host": self.host}
            if headers:
                fields.update(headers)
            if raw is not None:
                fields["Content-Type"] = "application/json"
            conn.request(method, path, body=raw, headers=fields)
            res = conn.getresponse()
            return res.status, dict(res.getheaders()), res.read()
        finally:
            conn.close()

    def rst_after_headers(self, request_bytes, *, expect_response_error=True):
        """One real loopback TCP client aborts only after headers were written."""
        sock = socket.create_connection(("127.0.0.1", self.server.server_port), timeout=5)
        try:
            self.server.paused = True
            sock.sendall(request_bytes)
            self.assertTrue(self.server.headers_ready.wait(5),
                            "HTTP reply did not reach end_headers")
            # Linux SO_LINGER(1, 0) sends a TCP RST rather than FIN.
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
        finally:
            sock.close()
        # Let the peer reset arrive before releasing the actual body write.
        time.sleep(0.05)
        self.server.resume_body.set()
        self.assertTrue(self.server.handler_finished.wait(5), "request did not finish")
        if expect_response_error:
            self.assertTrue(self.server.response_completed.wait(5),
                            "disconnect did not enter response exception handler")
            self.assertTrue(any(isinstance(e, server_module.ClientDisconnected)
                                for e in self.server.response_errors),
                            f"expected disconnect, got: {self.server.response_errors}")
        self.assertEqual(self.server.unhandled, [],
                         "client abort caused uncaught server exception or traceback")
        self.assertEqual(self.server.logged_errors, [],
                         "expected client abort misreported as server failure")

    def test_real_tcp_reset_during_json_reply_does_not_send_second_json(self):
        self.start(PauseAfterHeadersHandler)
        raw = (f"GET /api/health HTTP/1.1\r\nHost: {self.host}\r\n"
               "Connection: close\r\n\r\n").encode("ascii")
        self.rst_after_headers(raw)
        self.assertEqual(self.server.json_sends, 1,
                         "aborted JSON reply must not trigger an INTERNAL retry")
        status, headers, body = self.request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(json.loads(body)["storage"], "local")

    def test_real_tcp_reset_during_static_file_does_not_send_error_json(self):
        self.start(PauseAfterHeadersHandler)
        raw = (f"GET /app.js HTTP/1.1\r\nHost: {self.host}\r\n"
               "Connection: close\r\n\r\n").encode("ascii")
        self.rst_after_headers(raw)
        self.assertEqual(self.server.json_sends, 0,
                         "aborted static file must not produce a second JSON response")
        status, _, body = self.request("GET", "/app.js")
        self.assertEqual(status, 200)
        self.assertIn(b"import ", body)

    def test_real_tcp_reset_during_binary_template_does_not_send_error_json(self):
        self.start(PauseAfterHeadersHandler)
        raw = (f"GET /api/templates/xlsx HTTP/1.1\r\nHost: {self.host}\r\n"
               "Connection: close\r\n\r\n").encode("ascii")
        self.rst_after_headers(raw)
        self.assertEqual(self.server.json_sends, 0)
        status, headers, body = self.request("GET", "/api/templates/xlsx")
        self.assertEqual(status, 200)
        self.assertIn("spreadsheetml.sheet", headers["Content-Type"])
        self.assertTrue(body.startswith(b"PK"))

    def test_real_tcp_reset_after_save_commits_exactly_once_with_stable_sha(self):
        self.start(PauseAfterHeadersHandler)
        original_save = self.store.save
        self.store.save = Mock(wraps=original_save)
        document = {"filename": "once", "project": example(), "expectedSha256": None}
        payload = json.dumps(document, separators=(",", ":")).encode("utf-8")
        raw = (f"POST /api/save HTTP/1.1\r\nHost: {self.host}\r\n"
               f"Content-Type: application/json\r\nContent-Length: {len(payload)}\r\n"
               "Connection: close\r\n\r\n").encode("ascii") + payload
        self.rst_after_headers(raw)
        self.assertEqual(self.store.save.call_count, 1,
                         "response loss must never cause an automatic second Save")
        self.assertEqual(self.server.json_sends, 1)
        saved = self.store.read("once")
        actual_bytes = self.store.path("once").read_bytes()
        self.assertEqual(hashlib.sha256(actual_bytes).hexdigest(), saved["sha256"])
        self.assertEqual(saved["project"], example())
        # A disconnected client may not know Save committed: recovery is an
        # explicit read, never an implicit duplicate store mutation.
        status, _, body = self.request("GET", "/api/projects/once")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["sha256"], saved["sha256"])
        self.assertEqual(self.store.save.call_count, 1)

    def test_early_unauthorized_reply_disconnect_has_no_server_traceback(self):
        self.start(PauseAfterHeadersHandler, protected=True)
        raw = (f"GET /api/projects HTTP/1.1\r\nHost: {self.host}\r\n"
               "Connection: close\r\n\r\n").encode("ascii")
        # Trust-boundary errors are written before do_GET's normal try block;
        # the outer HTTP request boundary must absorb the expected transport
        # disconnect without attempting an unauthorized/internal second reply.
        self.rst_after_headers(raw, expect_response_error=False)
        self.assertEqual(self.server.json_sends, 1)
        status, _, body = self.request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["storage"], "local")

    def test_broken_pipe_at_end_headers_is_handled_without_double_response(self):
        self.start(BrokenHeaderHandler)
        self.server.break_headers_once = True
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            conn.request("GET", "/api/health", headers={"Host": self.host})
            with self.assertRaises((http.client.RemoteDisconnected,
                                    ConnectionResetError, BrokenPipeError)):
                conn.getresponse()
        finally:
            conn.close()
        self.assertTrue(self.server.handler_finished.wait(5))
        self.assertEqual(self.server.unhandled, [])
        self.assertEqual(self.server.logged_errors, [])
        self.assertEqual(self.server.json_sends, 1,
                         "end_headers failure must not start a second error response")
        status, _, body = self.request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["storage"], "local")

    def test_invalid_json_keeps_4xx_and_valid_responses_unchanged(self):
        self.start()
        status, headers, body = self.request("POST", "/api/validate", raw=b'{"broken":')
        self.assertEqual(status, 422)
        self.assertEqual(headers["Content-Type"], "application/json; charset=utf-8")
        self.assertEqual(json.loads(body)["error"], "INVALID_PROJECT")
        status, headers, body = self.request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(json.loads(body)["app"], server_module.config.APP_NAME)
        self.assertEqual(self.store.list(), [])
        self.assertEqual(self.server.unhandled, [])

    def test_unexpected_server_exception_is_visible_as_500_not_swallowed(self):
        self.start()
        self.store.list = Mock(side_effect=RuntimeError("unexpected sentinel"))
        status, headers, body = self.request("GET", "/api/projects")
        self.assertEqual(status, 500)
        self.assertEqual(headers["Content-Type"], "application/json; charset=utf-8")
        self.assertEqual(json.loads(body),
                         {"error": "INTERNAL", "message": "Local operation failed"})
        self.assertTrue(any("unexpected server exception" in e
                            and "unexpected sentinel" in e
                            for e in self.server.logged_errors))
        self.assertEqual(self.server.unhandled, [])

    def test_unknown_os_error_is_not_classified_as_client_disconnect(self):
        self.assertFalse(Handler._expected_peer_disconnect(OSError(errno.EIO, "disk error")))
        for error in (BrokenPipeError(errno.EPIPE, "broken"),
                      ConnectionResetError(errno.ECONNRESET, "reset"),
                      ConnectionAbortedError(errno.ECONNABORTED, "aborted")):
            self.assertTrue(Handler._expected_peer_disconnect(error))
        self.start()
        self.store.list = Mock(side_effect=OSError(errno.EIO, "disk error sentinel"))
        status, _, body = self.request("GET", "/api/projects")
        self.assertEqual(status, 500)
        self.assertEqual(json.loads(body)["error"], "INTERNAL")
        self.assertTrue(any("disk error sentinel" in e
                            for e in self.server.logged_errors))


if __name__ == "__main__":
    unittest.main()
