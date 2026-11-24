# QUALITY-005/5D — Parallel local HTTP session-state oracles

**Date:** 2026-11-23 (ISO)  
**Base:** `main@cad82c5b68eb0451f59ddb7d2f3e5a0c8355875b` following merged #108.  
**Statuskorrigering 2026-11-24:** Ursprunglig PRE-REGISTERED / NOT_VERIFIED-status gällde före CI. Testerna och den begränsade Linux-loopback-backlog-fixen mergades i PR #109 (final PR HEAD `3955199a79011806cf84d66f63842d2425980d2e`, båda obligatoriska `unit-tests` SUCCESS; squash-mergad till `main@b1c6fb0323fc93085084128e3ff4382f2b3a9576`). Detta bevisar inte alla möjliga produktionsraces eller full QUALITY-005-acceptans.  
**Scope:** Linux-only local `LabHTTPServer`, `SimulationRegistry` and `DhcpSessionRegistry`, real HTTP requests to a loopback test server and files strictly within `tempfile.TemporaryDirectory()`. No live NICs, user home directories or external services.

## Existing coverage and reason to add tests

`tests/test_session_idle.py` already checks registry-level cleanup versus held operations and Stop, bounded capacity, idle expiration, and worker shutdown. `tests/test_dhcp_registry.py` already checks registry-level concurrent two-client allocations and sequential real HTTP DORA. `tests/test_simulation_sessions.py` tests sequential HTTP lifecycle. These tests must remain unchanged. New tests focus on **real parallel HTTP dispatch**, exercising the handler and registry lock together rather than re-testing only direct registry methods. A held operation is paused with a deterministic `threading.Event` directly before its original implementation, then released; the real operation, response serialization and HTTP request path still execute.

## Predetermined independent outcomes

| Case | Ordered concurrent operations | Required result |
|---|---|---|
| **5D-1: HTTP Run vs Stop** | Start an actual L2 session. Enter and deliberately hold its real `run`. While held, send a genuine HTTP Stop. Release Run. | Run completes successfully with exactly **one** counted operation and genuine ARP success; Stop returns HTTP **200 / STOPPED** after the operation. A later Run with the retired ID is **422**, not an invented new session or success. Saved project bytes and SHA remain exact. |
| **5D-2: HTTP Run vs Reset** | Start, hold actual L2 Run under the registry lock. Submit Reset via another HTTP client and release. | Held Run returns HTTP **200** with count **1**; subsequent Reset returns **200** with count **0** and empty MAC tables. A later Run is a new successful first operation, not a stale continuation. No file bytes change. |
| **5D-3: Concurrent DHCP pool exhaustion** | Start one DHCP session on an explicitly wired three-client topology; pool contains only **two addresses** `192.0.2.70` and `.71`. Three independent HTTP clients concurrently request unique leases. | Exactly **two** HTTP 200 with **ACK_RECEIVED** and unique IPs `.70, .71`; exactly **one** HTTP 422 `INVALID_PROJECT` with `pool exhausted`. No silent duplicate lease, lease committed for rejected client or file write. |
| **5D-4: Concurrent simulation capacity** | Submit **20** simultaneous real HTTP Start requests for the same valid declared project; registry limit is **16**. | Exactly **16** HTTP 200 and distinct session IDs; exactly **4** HTTP 422 `INVALID_PROJECT` with `too many active sessions`. After one explicit HTTP Stop, a new Start returns HTTP 200 with a fresh ID and exactly 16 active sessions. No saved project mutation. |

The real HTTP server is created in `setUp`, bound only to `127.0.0.1` on an OS-assigned port, and stopped in `tearDown`. All concurrency tests use finite timeouts and unblock barriers in `finally`; never hold a lock indefinitely. No fake success is supplied by mocks. A method wrapper only schedules one known real session operation, then delegates to its unmodified implementation. Expected statuses come from the explicit session, pool, and locking contracts and are fixed *before test execution*.

## Limits and exit gate

This is **not** a claim of arbitrary race-freedom, real packet transmission or protocol-complete DHCP. No real user data, actual filesystem crash/restart, or cross-process server sharing is exercised. Uncovered QUALITY-005 work includes browser-level New/Open/Import late responses and other 5C races, parser/resource 5E, and additional 5A model fuzz boundaries.

Test command: `python3 -m unittest discover -s tests -p 'test_quality_005_http_races.py' -v`. Required GitHub `unit-tests` on exact PR HEAD must also complete SUCCESS (full Python, Node, Chromium, X11, ELK). Any failing pre-registered outcome must be diagnosed, not weakened merely to obtain PASS. Only then may a squash merge be considered. **No production code or OS policy changes** in this slice.

## Observed CI failure and minimal correction (2026-11-23)

**First exact PR HEAD:** `5107a7c6d65366e05bf8954f85df310a4ebad7b7`. The push workflow run 45251936506 completed **FAILURE** in the Python step after **687 tests**; the 5D-4 burst surfaced `ConnectionResetError: [Errno 104] Connection reset by peer` while reading the response from the real `ThreadingHTTPServer`. This is **not** a successful `HTTP 422` application-limit rejection. The three other added 5D test cases completed without a test failure in that run.

**Cause and scope of fix:** `LabHTTPServer` inherited Python `TCPServer`'s default pending TCP accept backlog of **5** despite allowing **16** active simulated sessions. Twenty simultaneous real loopback clients can overload the accept backlog before the application-level registry gets a chance to return a deterministic error. In this PR only, the existing Linux local listener's `request_queue_size` is set to **32**, enough to queue the specifically tested burst without increasing `MAX_SESSIONS`, changing protocol engines, or relaxing the four expected **422** results. The new negative test also asserts that the listener's advertised backlog is at least `MAX_SESSIONS + 4`. **The original 5D-4 oracle and 20-simultaneous-request load remain unchanged.**

This finding is a real **test-observed transport robustness issue**, not evidence of lost project files. The scoped correction later passed both mandatory `unit-tests` check runs on final PR #109 HEAD before squash merge; the observed tests do not prove every possible transport race. If it fails, retain the same application-level expectation and diagnose the specific transport error again. No production server is contacted: only a temporary loopback server is used in the test.
