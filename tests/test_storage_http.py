import errno
import hashlib
import io
import json
import socket
import tempfile
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from network_core import config
from network_core.model import ProjectValidationError
from network_core.server import LabHTTPServer, main
from network_core.storage import ProjectConflictError, ProjectStore
from test_model import example


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self.tmp.name)
        self.store = ProjectStore(self.directory)

    def tearDown(self):
        self.tmp.cleanup()

    def test_save_real_bytes_and_reload_new_store_instance(self):
        document = example()
        result = self.store.save('office-a', document)
        path = self.directory / 'office-a.yadilab'
        self.assertTrue(path.is_file())
        raw = path.read_bytes()
        self.assertEqual(result['bytes'], len(raw))
        self.assertEqual(result['sha256'], hashlib.sha256(raw).hexdigest())
        new_instance = ProjectStore(self.directory)
        self.assertEqual(new_instance.read('office-a')['project'], document)

    def test_atomic_update_and_explicit_hash(self):
        original = self.store.save('office-a', example())
        edited = example()
        edited['nodes'][0]['label'] = 'Changed client'
        new_version = self.store.save('office-a', edited, original['sha256'])
        self.assertNotEqual(original['sha256'], new_version['sha256'])
        self.assertEqual(self.store.read('office-a')['project']['nodes'][0]['label'], 'Changed client')
        self.assertEqual(list(self.directory.glob('.pending-*')), [])

    def test_refuse_unintentional_overwrite(self):
        original = self.store.save('office-a', example())
        with self.assertRaises(ProjectConflictError):
            self.store.save('office-a', example())
        with self.assertRaises(ProjectConflictError):
            self.store.save('office-a', example(), '0' * 64)
        self.assertEqual(self.store.read('office-a')['sha256'], original['sha256'])

    def test_reject_invalid_name_and_invalid_document_without_write(self):
        with self.assertRaises(ProjectValidationError):
            self.store.save('../escaped', example())
        document = example(); document['links'][0]['a']['port'] = 'does-not-exist'
        with self.assertRaises(ProjectValidationError):
            self.store.save('not-saved', document)
        self.assertEqual(self.store.list(), [])

    def test_listing_and_corrupted_saved_file(self):
        self.store.save('b-project', example())
        self.store.save('a-project', example())
        self.assertEqual([item['filename'] for item in self.store.list()], ['a-project','b-project'])
        (self.directory / 'bad.yadilab').write_text('{ invalid json')
        with self.assertRaisesRegex(ProjectValidationError,'invalid JSON'):
            self.store.read('bad')


class APIIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.server = LabHTTPServer(('127.0.0.1', 0), ProjectStore(Path(self.tmp.name)))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=4)
        self.tmp.cleanup()

    def request(self, path, payload=None):
        body = None if payload is None else json.dumps(payload).encode()
        req = Request(self.base + path, data=body,
                      headers={'Content-Type': 'application/json'} if body else {})
        try:
            with urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read()) if path.startswith('/api/') else resp.read()
        except HTTPError as error:
            return error.code, json.loads(error.read())

    def test_real_save_open_and_graph_trace(self):
        code, data = self.request('/api/save', {'filename':'lab','project':example(),'expectedSha256':None})
        self.assertEqual(code, 200)
        self.assertRegex(data['sha256'], '^[0-9a-f]{64}$')
        code, loaded = self.request('/api/projects/lab')
        self.assertEqual(code, 200)
        self.assertEqual(loaded['project'],example())
        code, traced = self.request('/api/trace', {'project':loaded['project'],'source':'pc-a','target':'pc-b'})
        self.assertEqual(code,200)
        self.assertEqual(traced['status'], 'PATH_PRESENT')
        self.assertEqual(len(traced['hops']),2)

    def test_invalid_import_and_no_silent_loss(self):
        bad = example(); bad['links'].append({'id':'fake', 'a':{'node':'pc-a','port':'eth0'},
                                              'b':{'node':'pc-b','port':'eth0'}, 'enabled':True})
        code, data = self.request('/api/validate', bad)
        self.assertEqual(code, 422)
        self.assertEqual(data['error'], 'INVALID_PROJECT')
        code, listing = self.request('/api/projects')
        self.assertEqual(code,200)
        self.assertEqual(listing['projects'],[])

    def test_explicit_csv_tables_import_without_writing_or_inference(self):
        from test_csv_import import source, LINKS
        code, result = self.request('/api/import/csv', source())
        self.assertEqual(code, 200)
        self.assertEqual([node['id'] for node in result['project']['nodes']], ['pc-a', 'sw-a'])
        self.assertEqual(result['project']['links'][0]['id'], 'cable-1')
        self.assertEqual(self.request('/api/projects')[1]['projects'], [])
        broken = source(**{'Links.csv': LINKS.replace('sw-a,gi1', 'unknown,gi1')})
        code, error = self.request('/api/import/csv', broken)
        self.assertEqual(code, 422)
        self.assertEqual(error['error'], 'INVALID_PROJECT')
        self.assertEqual(self.request('/api/projects')[1]['projects'], [])

    def test_conflict_is_explicit_in_http(self):
        payload = {'filename':'lab','project':example(),'expectedSha256':None}
        self.assertEqual(self.request('/api/save',payload)[0],200)
        code, conflict = self.request('/api/save',payload)
        self.assertEqual(code,409)
        self.assertEqual(conflict['error'],'CONFLICT')
        self.assertEqual(len(conflict['currentSha256']),64)

    def test_single_declarative_name_updates_every_user_visible_surface(self):
        from unittest.mock import patch
        candidate = "Example Name & <Laboratory>"
        with patch.object(config, "APP_NAME", candidate):
            code, health = self.request('/api/health')
            self.assertEqual(code, 200)
            self.assertEqual(health['app'], candidate)
            with urlopen(self.base + '/', timeout=5) as response:
                document = response.read().decode('utf-8')
            self.assertIn('<title>Example Name &amp; &lt;Laboratory&gt; · Nätverkslabb</title>', document)
            self.assertIn('aria-label="Example Name &amp; &lt;Laboratory&gt;"', document)
            self.assertIn('<strong>Example Name &amp; &lt;Laboratory&gt;</strong>', document)
            self.assertIn('Example Name &amp; &lt;Laboratory&gt; · Lokal version', document)
            self.assertNotIn('{{APP_NAME}}', document)

    def test_static_application_and_health(self):
        code, health = self.request('/api/health')
        self.assertEqual(code,200)
        self.assertEqual(health['app'],config.APP_NAME)
        with urlopen(self.base + '/',timeout=5) as response:
            self.assertIn(config.APP_NAME.encode('utf-8'), response.read())
        with urlopen(self.base + '/app.js',timeout=5) as response:
            self.assertIn(b'function render()',response.read())



class ServerStartupTests(unittest.TestCase):
    """A port collision is neither a cleanup failure nor silent port substitution."""

    def test_failed_bind_preserves_eaddrinuse_and_does_not_start_worker(self):
        with tempfile.TemporaryDirectory() as directory:
            before = {id(t) for t in threading.enumerate()
                      if t.name == "session-idle-cleanup"}
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
                occupied.bind(("127.0.0.1", 0))
                occupied.listen()
                port = occupied.getsockname()[1]
                with self.assertRaises(OSError) as caught:
                    LabHTTPServer(("127.0.0.1", port), ProjectStore(directory))
                self.assertEqual(caught.exception.errno, errno.EADDRINUSE)
            after = {id(t) for t in threading.enumerate()
                     if t.name == "session-idle-cleanup"}
            self.assertEqual(after, before)
            with LabHTTPServer(("127.0.0.1", port), ProjectStore(directory)) as server:
                self.assertEqual(server.server_port, port)
                self.assertTrue(server._cleanup_thread.is_alive())

    def test_explicit_occupied_port_exits_cleanly_without_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
                occupied.bind(("127.0.0.1", 0))
                occupied.listen()
                port = occupied.getsockname()[1]
                stderr = io.StringIO()
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as stopped:
                    main(["--port", str(port), "--no-browser", "--data-dir", directory])
                self.assertEqual(stopped.exception.code, 2)
                self.assertIn(f"Port {port} is already in use", stderr.getvalue())
                self.assertIn("--port", stderr.getvalue())
                self.assertNotIn("Traceback", stderr.getvalue())

    def test_occupied_default_port_uses_free_loopback_fallback_and_prints_real_url(self):
        with tempfile.TemporaryDirectory() as directory:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
                occupied.bind(("127.0.0.1", 0))
                occupied.listen()
                port = occupied.getsockname()[1]
                stdout, stderr = io.StringIO(), io.StringIO()
                selected_ports = []

                def verify_running(server, *, poll_interval):
                    selected_ports.append(server.server_port)
                    self.assertEqual(server.server_address[0], "127.0.0.1")
                    self.assertGreater(server.server_port, port)
                    self.assertLessEqual(server.server_port, port + 9)
                    self.assertTrue(server._cleanup_thread.is_alive())

                with patch("network_core.server.DEFAULT_PORT", port), \
                     patch.object(LabHTTPServer, "serve_forever", verify_running), \
                     redirect_stdout(stdout), redirect_stderr(stderr):
                    main(["--no-browser", "--data-dir", directory])
                self.assertEqual(len(selected_ports), 1)
                self.assertIn(f"at http://127.0.0.1:{selected_ports[0]}/",
                              stdout.getvalue())
                self.assertIn(f"Port {port} is busy; using port {selected_ports[0]}",
                              stderr.getvalue())

    def test_default_port_range_exhausted_exits_with_actionable_message(self):
        with tempfile.TemporaryDirectory() as directory:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
                occupied.bind(("127.0.0.1", 0))
                occupied.listen()
                port = occupied.getsockname()[1]
                stderr = io.StringIO()
                with patch("network_core.server.DEFAULT_PORT", port), \
                     patch("network_core.server.DEFAULT_PORT_CANDIDATES", 1), \
                     redirect_stderr(stderr), self.assertRaises(SystemExit) as stopped:
                    main(["--no-browser", "--data-dir", directory])
                self.assertEqual(stopped.exception.code, 2)
                self.assertIn("default range are busy", stderr.getvalue())
                self.assertIn("--port PORT", stderr.getvalue())


if __name__ == '__main__':
    unittest.main()
