"""Deterministic concurrent HTTP session-boundary regression tests.

Four explicit reference outcomes are asserted below. Earlier review history
is available from Git; no retired Markdown report is required to run tests.
All saved project bytes and the server live exclusively in TemporaryDirectory.
Only in-test wrappers pause operations; original registry methods still run.
"""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from network_core.server import LabHTTPServer
from network_core.simulation import MAX_SESSIONS
from network_core.storage import ProjectStore
from test_dhcp_registry import clients
from test_vlan_persistence import persisted_topology


class ConcurrentRealHttpOracles(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.server = LabHTTPServer(("127.0.0.1", 0), ProjectStore(self.root))
        self.worker = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.worker.start()
        self.addCleanup(self.close_server)
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.baseline = None

    def close_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.worker.join(timeout=5)
        self.assertFalse(self.worker.is_alive())
        self.assertFalse(self.server._cleanup_thread.is_alive())

    def post(self, path, payload):
        request = Request(self.base + path, data=json.dumps(payload).encode("utf-8"),
                          headers={"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=10) as result:
                return result.status, json.loads(result.read())
        except HTTPError as error:
            return error.code, json.loads(error.read())

    def stored_snapshot(self, project):
        source = copy.deepcopy(project)
        result = self.server.store.save("baseline", project)
        file_path = self.root / "baseline.yadilab"
        raw = file_path.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), result["sha256"])
        self.assertEqual(json.loads(raw), source)
        self.baseline = (file_path, raw, result["sha256"], source)

    def assert_baseline_unchanged(self):
        path, raw, sha, project = self.baseline
        self.assertEqual(path.read_bytes(), raw)
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), sha)
        self.assertEqual(self.server.store.read("baseline")["project"], project)
        self.assertEqual(sorted(p.name for p in self.root.glob("*.yadilab")),
                         ["baseline.yadilab"])

    @staticmethod
    def sim_run_payload(project, sid):
        return {"sessionId": sid, "project": project, "operation": "arp",
                "sourceNode": "a", "sourcePort": "eth0", "target": "192.0.2.20"}

    def held_simulation_run(self, sid):
        entered = threading.Event()
        release = threading.Event()
        session = self.server.simulations._sessions[sid]
        real_run = session.run

        def held(*args, **kwargs):
            entered.set()
            if not release.wait(timeout=8):
                raise RuntimeError("test operation release not signalled")
            return real_run(*args, **kwargs)

        session.run = held
        return entered, release

    def test_real_http_run_completes_before_waiting_stop_and_retired_id_rejected(self):
        project = persisted_topology()
        self.stored_snapshot(project)
        code, initial = self.post("/api/simulation/start", {"project": project})
        self.assertEqual(code, 200)
        sid = initial["sessionId"]
        entered, release = self.held_simulation_run(sid)
        stop_entered = threading.Event()
        registry = self.server.simulations
        real_stop = registry.stop

        def observed_stop(session_id):
            stop_entered.set()
            return real_stop(session_id)

        registry.stop = observed_stop
        with ThreadPoolExecutor(max_workers=2) as pool:
            try:
                running = pool.submit(
                    self.post, "/api/simulation/run", self.sim_run_payload(project, sid))
                self.assertTrue(entered.wait(timeout=5), "Run did not enter session")
                stopping = pool.submit(self.post, "/api/simulation/stop", {"sessionId": sid})
                self.assertTrue(stop_entered.wait(timeout=5), "Stop did not enter HTTP registry")
                self.assertFalse(stopping.done(), "Stop bypassed held session lock")
            finally:
                release.set()
            run_status, run = running.result(timeout=10)
            stop_status, stopped = stopping.result(timeout=10)
        self.assertEqual(run_status, 200)
        self.assertEqual(run["operationCount"], 1)
        self.assertEqual(run["result"]["status"], "RESOLVED")
        self.assertEqual(stop_status, 200)
        self.assertEqual(stopped, {"status": "STOPPED"})
        self.assertNotIn(sid, registry._sessions)
        code, error = self.post("/api/simulation/run", self.sim_run_payload(project, sid))
        self.assertEqual(code, 422)
        self.assertEqual(error["error"], "INVALID_PROJECT")
        self.assertIn("unknown or expired", error["message"])
        self.assert_baseline_unchanged()

    def test_real_http_reset_serializes_after_held_run_and_clears_learning(self):
        project = persisted_topology()
        self.stored_snapshot(project)
        code, initial = self.post("/api/simulation/start", {"project": project})
        self.assertEqual(code, 200)
        sid = initial["sessionId"]
        entered, release = self.held_simulation_run(sid)
        reset_entered = threading.Event()
        registry = self.server.simulations
        real_reset = registry.reset

        def observed_reset(session_id, document):
            reset_entered.set()
            return real_reset(session_id, document)

        registry.reset = observed_reset
        with ThreadPoolExecutor(max_workers=2) as pool:
            try:
                running = pool.submit(
                    self.post, "/api/simulation/run", self.sim_run_payload(project, sid))
                self.assertTrue(entered.wait(timeout=5), "Run did not enter session")
                resetting = pool.submit(
                    self.post, "/api/simulation/reset", {"sessionId": sid, "project": project})
                self.assertTrue(reset_entered.wait(timeout=5), "Reset did not enter HTTP registry")
                self.assertFalse(resetting.done(), "Reset bypassed held session lock")
            finally:
                release.set()
            run_status, run = running.result(timeout=10)
            reset_status, reset = resetting.result(timeout=10)
        self.assertEqual(run_status, 200)
        self.assertEqual(run["operationCount"], 1)
        self.assertEqual(run["result"]["status"], "RESOLVED")
        self.assertEqual(reset_status, 200)
        self.assertEqual(reset["operationCount"], 0)
        self.assertEqual(reset["macTables"], [])
        self.assertEqual(registry._sessions[sid].state()["operationCount"], 0)
        after_status, after = self.post(
            "/api/simulation/run", self.sim_run_payload(project, sid))
        self.assertEqual(after_status, 200)
        self.assertEqual(after["operationCount"], 1)
        self.assertEqual(after["result"]["status"], "RESOLVED")
        self.assert_baseline_unchanged()

    def test_parallel_http_dhcp_requests_allocate_two_unique_leases_only(self):
        project = clients()
        self.stored_snapshot(project)
        code, state = self.post("/api/dhcp/session/start", {
            "project": project, "serverNode": "server", "serverPort": "eth0",
            "poolStart": "192.0.2.70", "poolEnd": "192.0.2.71"})
        self.assertEqual(code, 200)
        sid = state["sessionId"]
        gate = threading.Barrier(4)

        def allocate(client, xid):
            gate.wait(timeout=5)
            return self.post("/api/dhcp/session/run", {
                "sessionId": sid, "project": project,
                "clientNode": client, "clientPort": "eth0",
                "transactionId": xid, "leaseSeconds": 80})

        with ThreadPoolExecutor(max_workers=3) as pool:
            tasks = [pool.submit(allocate, client, idx) for idx, client in
                     enumerate(("client", "client-2", "client-3"), start=101)]
            gate.wait(timeout=5)
            responses = [task.result(timeout=10) for task in tasks]
        successes = [body for status, body in responses if status == 200]
        denied = [body for status, body in responses if status == 422]
        self.assertEqual(len(successes), 2)
        self.assertEqual(len(denied), 1)
        self.assertEqual({value["result"]["status"] for value in successes},
                         {"ACK_RECEIVED"})
        self.assertEqual({value["result"]["lease"]["ipv4"] for value in successes},
                         {"192.0.2.70", "192.0.2.71"})
        self.assertEqual(denied[0]["error"], "INVALID_PROJECT")
        self.assertIn("pool exhausted", denied[0]["message"])
        session = self.server.dhcp_sessions._sessions[sid]
        lease_state = session.state()
        self.assertEqual(lease_state["leaseCount"], 2)
        self.assertEqual(lease_state["operationCount"], 2)
        self.assertEqual({entry["ipv4"] for entry in lease_state["leases"]},
                         {"192.0.2.70", "192.0.2.71"})
        self.assert_baseline_unchanged()

    def test_parallel_http_start_cannot_exceed_capacity_and_reuses_freed_slot(self):
        project = persisted_topology()
        self.stored_snapshot(project)
        n = MAX_SESSIONS + 4
        # This burst must be accepted by the local listener so the application
        # registry, not the TCP accept backlog, returns the four explicit 422s.
        self.assertGreaterEqual(self.server.request_queue_size, n)
        gate = threading.Barrier(n + 1)

        def start():
            gate.wait(timeout=8)
            return self.post("/api/simulation/start", {"project": project})

        with ThreadPoolExecutor(max_workers=n) as pool:
            tasks = [pool.submit(start) for _ in range(n)]
            gate.wait(timeout=8)
            results = [task.result(timeout=15) for task in tasks]
        successful = [body for status, body in results if status == 200]
        rejected = [body for status, body in results if status == 422]
        self.assertEqual(len(successful), MAX_SESSIONS)
        self.assertEqual(len(rejected), 4)
        self.assertEqual(len({item["sessionId"] for item in successful}), MAX_SESSIONS)
        self.assertTrue(all(item["error"] == "INVALID_PROJECT"
                            and "too many active" in item["message"] for item in rejected))
        self.assertEqual(len(self.server.simulations._sessions), MAX_SESSIONS)
        old = successful[0]["sessionId"]
        code, stop = self.post("/api/simulation/stop", {"sessionId": old})
        self.assertEqual((code, stop), (200, {"status": "STOPPED"}))
        code, fresh = self.post("/api/simulation/start", {"project": project})
        self.assertEqual(code, 200)
        self.assertNotEqual(fresh["sessionId"], old)
        self.assertEqual(len(self.server.simulations._sessions), MAX_SESSIONS)
        self.assert_baseline_unchanged()


if __name__ == "__main__":
    unittest.main()
