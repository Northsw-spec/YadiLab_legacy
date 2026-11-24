# QUALITY-005/5C — Frontend stale-HTTP and session recovery oracles

**Date:** 2026-11-23 (ISO)  
**Baseline:** `main@6c8fe916a3c5c0f43a9d73993e9a49520e665d9c`.  
**Statuskorrigering 2026-11-24:** Ursprungligen förregistrerat som NOT_VERIFIED före CI. Avgränsade controller-tester för 5C mergades i PR #108 (final PR HEAD `633b17de7e6324cdf2e8516c3c49f20e6a18e5ad`, två `unit-tests` SUCCESS). Det innebär inte att ytterligare Builder/New/Open/Import-races eller all asynkron UI-kod är verifierad. Tidigare framtidstext om att lägga till testfilen är historisk.  
**Scope:** the existing `createSimulationSessionController` and `createDoraSessionController` in `web/features/sessions`. This slice does not modify the controllers, canonical project, API contracts or schema. Linux-only application; Windows/macOS UNSUPPORTED.

## Model and evidence boundary

These outcomes are derived from the **already implemented controller contract**: `generation`, `workspaceRevision`, `editRevision`, `projectSnapshot`, `id`, `busy`, `inFlight`, and `pendingStops`. The actual HTTP adapter `web/services/api.js` processes JSON and 422 errors. For deterministic ordering, newly added Node tests temporarily replace `fetch` with an explicitly controlled deferred-response transport and restore it after each case. **This is a unit test of the live controller code, not a replacement for the existing real Chromium/X11 test suite**. The original `tests/browser_smoke.py` remains an unmodified mandatory CI gate.

## Pre-registered expected behaviors

| Case | Controlled ordering | Required response |
|---|---|---|
| **5C-S1 stale successful Start** | Session START sent against workspace A; workspace switched to B and controller invalidated; late HTTP 200 contains old session ID | Never attach old ID/state to B; dispatch explicit Stop for the obsolete server ID; no false active session |
| **5C-S2 stale 422 after edit** | Successful Start; run pending; project revision changes; controller invalidated; delayed HTTP 422 from obsolete request | No new diagnostic or active ID in new workspace; old session Stop requested; no stale error shown |
| **5C-S3 changed diagnostic inputs** | Successful Start; Run requests target A; user changes query input to B before HTTP 200 | Keep actual server operationCount/state (the server may have processed the operation); **do not display** an A-result, A-highlight, or pretend it belongs to B |
| **5C-S4 reset supersedes Run** | Successful Start; Run pending; Reset starts and returns HTTP 200 **before** the old Run reply | Reset state wins in UI; delayed old Run must not restore stale diagnostic, link highlight or operation count |
| **5C-S5 failed Stop and retry** | Active session; Stop HTTP 500; later Stop HTTP 200 | First failure retains visible active session and shows error, not a false STOPPED; second confirmed Stop clears active session |
| **5C-D1 late DORA Start** | DORA START pending; project switches/invalidates; old 200 delivers an ID | Ignore old Start state, send explicit Stop for old server session, no BOUND or active session in new workspace |
| **5C-D2 changed DHCP selection** | DORA operation pending; selected client/parameter changes; late HTTP 200 arrives | Server-owned session state may advance, but obsolete trace must not be shown for the newly selected client |
| **5C-D3 expired DORA session** | Active DORA session; API returns 422 with the *known explicit* expired-session error | Clear the stale session ID, retain an actionable error in controller view, do **not** report a successful lease/renewal |

## Risk limits and follow-up

- A green result is evidence **only of these eight scheduled HTTP orderings** and their frontend guards; it does not prove arbitrary races, server-side operation ordering, true browser rendering, real network behavior, or physical disk safety.
- No timers, sleeps or real network requests; each test explicitly controls responses, avoids test flakiness and runs entirely in Node. Restore `globalThis.fetch` after each test.
- Independent 5C follow-up remains for **Builder/New/Open/Import late 200/422 with actual Chromium DOM and project Save**, and any cross-server-session reordering not covered here. 5D fick separata, avgränsade parallella HTTP-tester i PR #109; full shutdown-/race-täckning är inte därmed bevisad. 5E covers parser and resource boundaries. No production changes, exception swallowing or reduced CI gates authorized.
- The new test file **must be added** to the existing `npm run check` `node --test` list alongside (not instead of) every current test. Required `unit-tests` on exact PR HEAD must run Python, JavaScript, Chromium, X11 and ELK. Unchanged `main` base, reviews and branch rules still apply before any squash merge.
