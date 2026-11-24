# Local automatic diagram layout – presentation contract

> **Status 2026-11-24:** Automatic first layout and coordinate-free strict CSV/XLSX/ODS import/export were delivered in ELK-06A–C (merged PR #94–#96). Earlier future-tense requirements below describe enforced behavior, not missing implementation. The Worker/ELK/SVG presentation layer must not change topology. Teaching architecture is documented separately in [PEDAGOGICAL_TROUBLESHOOTING_PLAN.md](PEDAGOGICAL_TROUBLESHOOTING_PLAN.md); no new motor is authorized.

## Purpose and boundaries

ELK calculates presentation geometry only; it never creates or changes network
facts, declared ports, physical cables, IP addresses, routes or import evidence.
After a user explicitly accepts a valid CSV/XLSX/ODS or flexible mapped
documentation import, the existing ELK Worker computes the **first** diagram
automatically (ELK-06B). This result affects only node X/Y and temporary edge
paths; Save remains an explicit separate action. Existing manually placed or
saved projects keep their positions until the user requests manual re-layout.

New external documentation exports and demo templates omit X/Y (ELK-06C).
Legacy strict inputs with both columns remain accepted for compatibility;
incomplete pairs are rejected. Canonical `.yadilab`/JSON project files
**still save X/Y** and remain the only layout-preserving project backup.
Document source cell addresses are factual provenance, not display geometry.

## Offline dependency

The browser uses the locally vendored, version-pinned `elkjs 0.13.0`
`elk-api.js` and `elk-worker.js`. No CDN and no npm installation are
required when starting the local app. See `web/vendor/NOTICE.md` and
`web/vendor/ELK-LICENSE.md` for upstream attribution and license text.

The layout is computed in a Web Worker. Worker errors, unsupported browsers,
timeouts, aborts, unknown graph objects, invalid coordinates and invalid
port/edge geometry reject the entire proposal. There is no silent
main-thread fallback.

## Current manual re-layout flow for existing diagrams

The following steps describe **already implemented** voluntary
Preview/Apply/Cancel. They are **not** the target flow after accepting a new
network-document import. ELK-06B already performs the first automatic layout
and display the result without an extra Preview/Apply click; it must still
require separate Save.

1. The user explicitly requests **Föreslå ELK-layout**.
2. A snapshot of the canonical project is supplied to a two-pass ELK
   computation. The result is a *read-only preview* that draws suggested node
   positions and ELK-routed cables without modifying the project or disk.
3. **Tillämpa placering** checks workspace revision, edit revision,
   filename and the complete canonical project snapshot immediately before
   mutating. Only already-declared nodes' X/Y values are replaced; no cable,
   port, zone, route, or historical import evidence is modified. This marks
   the project dirty. Only a later explicit **Spara projekt** writes to disk.
4. **Avbryt** restores the unmodified canonical view. Editing, dragging a
   node, opening/importing a project or starting a new workspace invalidates
   the preview and any previously accepted *transient* edge paths. An older
   Worker result is ignored.

### Persisted geometry policy

**Only node X/Y is persisted** using the existing canonical project schema.
ELK edge sections are *not* stored in project files or import receipts.
Immediately after Apply, the in-memory SVG can use validated ELK edge paths
for the exact applied project snapshot, so existing packet playback follows
those displayed paths. After Save/Open or full restart, the project renders
using the canonical canvas's ordinary cable router. The user can recompute
an ELK preview on demand. This distinction is intentional and must remain
visible to users.

An imported project with historical evidence can therefore correctly report
`CHANGED_SINCE_IMPORT` after accepted X/Y edits while its original source
replay and immutable receipt remain valid. The historical import
`node_layout()` function must not be changed in place.

## Large topology navigation

The old fixed 9,000-unit maximum viewBox width was only appropriate for small
projects. After **Anpassa** (Fit), the camera now bases its zoom-out limit on
the full current canvas extent, including an ELK preview. The first wheel step
must zoom smoothly without jumping to a much smaller viewport; the world point
under the cursor must stay fixed. The zoom-out limit is reset when Fit is used
for a smaller or newly opened project, so huge extents do not leak between
workspaces. This changes only camera geometry, never node coordinates or links.

## Layout rules and failure conditions

- ELK Layered, orthogonal routing, `MULTI_EDGE` wrapping and a pinned
  `aspectRatio` of 1.6.
- First pass: positions for a deterministic ordered graph. Port sides follow
  the current canvas rule: remote node X left of local node X means left;
  otherwise right.
- Second pass: `FIXED_POS` with zero-size virtual ELK ports at exactly the
  SVG port-circle centers. These are never canonical network ports.
- Exactly matching source/output node IDs, edge IDs and port identities;
  exactly one route section per declared cable; every path begins/ends at
  the corresponding visible port center.
- Round and translate coordinates; do not resize nodes, shorten cables or
  fabricate connections to force a valid layout.
- Entire rectangles must remain inside ±100000 model coordinates with no
  positive-area overlaps. Reject layouts that do not fit rather than
  truncating them. Fail closed if a port side flips between passes.
- The source project snapshot must remain untouched in all preview paths.

## Tests

`npm run check` includes mock-backed adapter invariants and negative
cases. `python3 tests/browser_elk_layout.py` exercises the actual vendored
ELK, local Python HTTP server, Chromium UI, cable endpoints, preview cancel,
stale response rejection, explicit Save/Open and ephemeral edge-path policy.

Large-topology performance, navigation and readability need a repeatable
test environment and measured results for the exact scenario being claimed.
An isolated historical stress result is not proof of general production
scalability; consult the current test suite and CI before any such claim.
