# QUALITY-005/5A–5B — Save-integrity error-boundary oracles (first test slice)

**Date:** 2026-11-23 (ISO)  
**Source baseline:** `main@0a1d51d81250e5b87372b2ec9bc35bda657c0960`  
**Status:** **PRE-REGISTERED / NOT_VERIFIED UNTIL EXACT-HEAD CI**. QUALITY-004 final main CI for the preceding audit may still be running; this independent test work does not claim QUALITY-004 acceptance.  
**Scope:** Linux-only local application, `network_core/storage.py`, `ProjectStore` API; test data exclusively under `tempfile.TemporaryDirectory()`. No user files, real network or global settings. This does **not** implement or test any other operating system.

## Why this slice is necessary

Existing `tests/test_storage_concurrency.py` already tests thread/process/HTTP optimistic locking, concurrent 200-vs-409, and a failed `os.replace`. `tests/test_storage_http.py` already covers success, corrupted read, create-only and basic validation. These are kept unchanged. The remaining narrow edge is **failure before vs after the atomic rename** at the two different `fsync` calls in `ProjectStore.save`.

This document specifies the expected behavior *before running the newly added test file* `tests/test_quality_005_storage_faults.py`. It is derived from explicit code control flow and Linux/POSIX file operation ordering, **not** from expected output computed by the implementation. Not a claim about actual power-loss durability on physical hardware.

## Pre-registered invariants

| Test | Exact fault and initial state | Required independent result |
|---|---|---|
| **5B-1 create failure** | Fresh isolated directory; `os.fsync` raises during temporary file synchronization **before** `os.replace` | Raise the OSError; no `lab.yadilab` created; no `.pending-*` left; lock released; ordinary retry must succeed with SHA-256 matching file bytes |
| **5B-2 overwrite failure** | Existing valid `lab.yadilab` and matching old SHA; `os.fsync` raises before replacement | Old file bytes and hash unchanged; no `.pending-*`; a normal retry using the same expected old SHA succeeds and writes exactly the new document |
| **5B-3 post-rename directory fsync failure** | Existing valid project, matching old SHA; first (file) fsync is **real and successful**, `os.replace` completes, injected error only on second (directory) fsync | Save raises OSError but file now contains the **new** complete bytes, hash of on-disk bytes is consistent; no partial file or temporary file. A retry using **old** SHA is rejected with a conflict reporting the actual on-disk SHA; a retry using that actual SHA can succeed. **Do not assume durability was guaranteed after failed directory fsync** |
| **5A-1 invalid in-memory project overwrite** | Existing valid file; submitted document contains a declared link referencing a nonexistent port | `ProjectValidationError`; existing bytes and SHA unchanged; no silent removal of bad link, no write, no source object mutation |
| **5B-4 corrupt existing file overwrite** | Existing `lab.yadilab` contains invalid JSON bytes (written only by test setup) | Create-only `expected_sha256=None` refuses overwrite by `ProjectConflictError`, reports actual hash of corrupt bytes, and leaves bytes unchanged. No silent repair or data loss |

## Test command and CI requirements

```bash
python3 -m unittest discover -s tests -p 'test_quality_005_storage_faults.py' -v
```

All tests must pass along with the complete GitHub Actions `unit-tests` workflow (Python, JavaScript, real Chromium Save/Open and Linux X11 regressions) **on exact final PR HEAD**. A green test is evidence of these synthetic fault boundaries, *not* of power-failure guarantees or simultaneous production writes to real user files.

**Further QUALITY-005 work stays NOT_VERIFIED:** 5A schema/identity fuzzing beyond the existing validator cases; 5B crash/power loss and rename/permission failures not simulated here; 5C late HTTP UI responses/overlapping Builder/New/Open/Import; 5D session-registry API races and shutdown; 5E parser/ZIP/ODS/XLSX resource exhaustion. No engine, schema, test workflow, timeouts, OS policy or production files should be modified simply to make tests green.
