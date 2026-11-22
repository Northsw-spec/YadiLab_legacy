# Local automatic diagram layout – presentation contract

## Purpose and boundaries

Automatic **manual re-layout of an existing diagram** is opt-in. The **initial**
ELK placement after an explicitly accepted, validated network-document import
is mandatory and automatic (ELK-06 target, **not yet implemented on this baseline**).
External CSV/XLSX/ODS network documents must not be required to contain node
X/Y columns. Source cell coordinates identify original facts, not SVG geometry.
The legacy strict four-table importer currently requires those columns, as do
its schema-1.0/1.3 workbook paths. ELK-06A must fix that input requirement.
ELK-06B must then automatically produce the first validated layout after
accepted document import, and ELK-06C must remove X/Y from new documentary
XLSX/ODS exports and templates (preserving canonical project Save/Open).
These are planned code deliverables, not claims that today's code already works.
ELK is never a network import engine or an
authority for cables, ports, IP addresses, routing, simulation, or topology.
The layout engine receives only already-declared `project.links` with both
canonical node/port endpoints. It can position existing nodes and suggest
visual cable paths; it cannot invent physical links or rewrite historical
import receipts.

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
network-document import. ELK-06 must automatically perform the first layout
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

The experiment proving a successful 2,000-node/5,000-link coordinate
candidate remains reproducible under the isolated research branch.
Production readability and navigation for other large topologies must not
be considered accepted from those isolated results.
