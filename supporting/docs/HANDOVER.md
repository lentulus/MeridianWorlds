# Worlds — Handover

Updated 2026-05-27. If the Claude window closes mid-task, read this file
first. It is a pointer document — it tells you what has been built, what
is wrong, and what to do next.

## TL;DR for a fresh session

**Star List + Map is complete. Ship Design Tool planning is complete;
implementation starts at Slice 0.**

First actions in a new session:
1. Read this file.
2. `git log --oneline -10` and `git status` — confirm current state.
3. Open [ShipDesignMVP_Checklist.md](supporting/docs/Design/Worlds/ShipDesignMVP_Checklist.md)
   and find the first unchecked step.
4. Read [ShipDesignMVP_Plan.md](supporting/docs/Design/Worlds/ShipDesignMVP_Plan.md)
   for derivation rules and architecture decisions before writing any code.
5. Apply the double-approval gate before doing anything irreversible.

---

## What the project is

Single-user desktop web app for GURPS-based worldbuilding.

| Component | What it does |
|---|---|
| **Star List** | Filterable table of star systems drawn from Meridian parquet data |
| **Star Map** | Three.js 3D point cloud of the current list results |
| **System Orbit Display** | SVG 2D diagram — stars at centre, bodies on orbital ellipses |
| **Ship Design Tool** | GURPS Spaceships slot-based design backed by `WORLDS_DB` SQLite |

Stack: TypeScript throughout. Server is Hono + `@hono/node-server` (port
3000). Client is Vite + Three.js, no framework. Shared types in
`packages/shared`. Data in DuckDB (Meridian parquet, read-only) and
`node:sqlite` (WORLDS_DB, read-write for ships). pnpm workspaces.

The design authority is
[client_server_design.md](supporting/docs/Design/Worlds/client_server_design.md).

---

## What to read, in order

1. This file — orientation.
2. [ShipDesignMVP_Checklist.md](supporting/docs/Design/Worlds/ShipDesignMVP_Checklist.md)
   — running execution record for the active component; find the first unchecked step.
3. [ShipDesignMVP_Plan.md](supporting/docs/Design/Worlds/ShipDesignMVP_Plan.md)
   — scope, derivation rules, architecture decisions, data model.
4. [ShipDesignMVP_UI.md](supporting/docs/Design/Worlds/ShipDesignMVP_UI.md)
   — approved UI skeleton. Prototype: [ShipDesignMVP_Prototype.html](supporting/docs/Design/Worlds/ShipDesignMVP_Prototype.html).
5. [client_server_design.md](supporting/docs/Design/Worlds/client_server_design.md)
   — authoritative design spec for the overall app.
6. `CLAUDE.md` (project root) — data paths, Meridian API boundary rules.

---

## Architecture decisions (do not re-litigate)

- **No in-memory star index.** We previously loaded all named systems
  into JS Maps on startup. Removed: caused OOM at 3.7 GB for 198 k
  named stars. `buildIndex()` is now a no-op flag setter. All star
  queries hit DuckDB directly, bounded by the user's distance filter.
- **Name = navigation target, not text filter.** When the Name field
  contains a star name, the server resolves it to coordinates via
  `findByName()` and uses those as the search centre. The name is NOT
  used as a LIKE filter on results. The client's Centre field still
  accepts a separate centre-star name.
- **Default distance: 10 pc.** Applied server-side whenever
  `dist_max_pc` is absent. Prevents unbounded full-catalog scans.
- **All stars in scope (named + unnamed).** Named stars show their name;
  unnamed stars show `(x, y, z) pc` coordinate labels.
- **Spectral/HZ filter total = page count.** Cross-sector totals for
  spectral/hz filters are not feasible; `total` equals `rows.length`
  when either filter is active (G-006 design decision).
- **Stack:** TypeScript, Hono, DuckDB, `node:sqlite`, Vite, Three.js.
  No Python server. No framework on client.
- **Meridian is read-only.** Never write to `STARFIELD_DB` or parquet.

---

## Current repo state

```
worlds/
├── packages/shared/src/types.ts    All API request/response types (incl. centre params)
├── server/src/
│   ├── app.ts                      Hono app: middleware + routes (no port binding)
│   ├── main.ts                     Startup: buildIndex() (no-op) then serve()
│   ├── config.ts                   Reads MERIDIAN_DATA, WORLDS_DB, PORT from .env
│   ├── db/
│   │   ├── meridian.ts             DuckDB queries: searchStars(), getSystem(),
│   │   │                           findByName(), filterAndPage() (test utility)
│   │   ├── meridian.math.test.ts   5 tests: mpcToPc exact values + round-trip
│   │   ├── meridian.filter.test.ts 19 tests: name/dist/centre/unnamed filter,
│   │   │                           sort, pagination (in-memory filterAndPage)
│   │   └── ships.ts                node:sqlite CRUD for all ship tables
│   └── routes/
│       ├── stars.ts                GET /api/stars (name→centre resolution),
│       │                           /api/stars/by-name, /api/stars/:id
│       ├── stars.http.test.ts      9 HTTP integration tests via app.request()
│       └── ships.ts                Full CRUD for /api/ships + hull-sizes + catalog
└── client/src/
    ├── main.ts                     Hash router, global CSS, view lifecycle
    ├── api/stars.ts                Typed fetch wrappers
    ├── state/selection.ts          Shared signal: selectedSystemId
    ├── views/
    │   ├── StarList.ts             Name field = navigate; Centre field = explicit centre
    │   │                           Display button toggles table ↔ Three.js map
    │   ├── SystemView.ts           Fetches system, drives OrbitDiagram + BodyPanel
    │   └── ShipDesign.ts           Ship CRUD, slot drag-assign, catalog load (partial)
    └── components/
        ├── StarMap.ts              Three.js WebGL renderer; setCentre() shifts camera
        ├── OrbitDiagram.ts         SVG ellipse renderer
        ├── BodyPanel.ts            Physical data sidebar; breakable() for long strings
        ├── SlotGrid.ts             Slot grid render (partial — target layout in UI doc)
        └── CatalogPanel.ts         Catalog grouped render (partial)
```

**Test count: 28 green (5 math + 19 filter + 4 HTTP GET /stars + 5 HTTP
other).** `pnpm test` from root runs all three workspaces.

**Ship Design planning artifacts** (not yet implemented):

```
supporting/docs/Design/Worlds/
├── ShipDesignMVP_Plan.md       Scope, derivation rules, architecture decisions, data model
├── ShipDesignMVP_Checklist.md  Step-by-step execution record (Slices 0–7)
├── ShipDesignMVP_UI.md         Approved UI skeleton with wireframes
└── ShipDesignMVP_Prototype.html  Interactive layout prototype (open in browser to view)

supporting/sql/
├── schema.sql                  Current live DB schema (pre-migration)
├── seed.sql                    Full INSERT dump for disaster recovery
└── migrations/                 (directory to be created in Slice 0)
```

---

## Known gaps

| ID | File | Issue |
|---|---|---|
| ~~P0-D01~~ | ~~`server/src/routes/stars.ts`~~ | **CLOSED** — negative-coordinate ORDER BY used `--` which DuckDB parsed as a line comment; fixed by parenthesising interpolated coords. |
| G-001 | `server/src/db/ships.ts:136` | PP budget is placeholder — always returns 0. Fixed in Ship Design Slice 1. |
| G-003 | `client/src/components/OrbitDiagram.ts:36` | Body angular position uses `Math.random()` — non-deterministic. Deferred. |
| G-004 | `server/src/routes/stars.ts` | No input validation on query params. Deferred. |
| G-005 | `server/src/routes/ships.ts` | No input validation on POST/PUT bodies. Deferred. |
| Schema-M01 | `ship_system_slots` | `system_id NOT NULL` prevents empty slot positions. Migration 001 in Slice 0. |
| Schema-M02 | `ships` | Missing `description TEXT` and `image_path TEXT`. Migration 002 in Slice 0. |
| ~~G-002, G-006, G-007~~ | — | **CLOSED** — see git log `230f399`. |

---

## Sequencing — what to build next

**Active component: Ship Design Tool.** Star List + Map is signed off.

| Slice | Goal | Status |
|---|---|---|
| 0 | Schema migrations (M01 + M02) + SQL files | Not started |
| 1 | G-001 fix — PP derivation, test-first | Not started |
| 2 | Slot grid — all 20 positions | Not started |
| 3 | Slot assignment + detail text | Not started |
| 4 | All derived stats (dDR, accel, delta-V, HT, cost, crew) | Not started |
| 5 | Override inputs + description + image attachment | Not started |
| 6 | Ship list filters | Not started |
| 7 | Smoke test + sign-off | Not started |

After Ship Design Tool: System Orbit Display (fix G-003 first).

---

## Working-style rules (non-negotiable)

- **Double-approval gate on every `[HUMAN]` step:**
  1. User gives first approval.
  2. Claude echoes the specific next action.
  3. User gives second explicit confirmation.
  4. Only then Claude acts.
  Applies to: `pnpm add`, `git commit`, `git push`, destructive DB ops,
  structural refactors.

- **No unprompted commits.** Always pre-commit triage + double-approval.

- **Test-first.** No production code without a failing red test first.

- **Math tests are Claude's responsibility.** Claude identifies invariants,
  extracts pure functions, writes tests against analytic results.

---

## Working-style preferences (durable)

- No web-programming background — explain HTTP, routing, JS ecosystem
  from first principles when relevant.
- Strong preference for explicit terse documentation with the *why*.
- Design pinned before code. Surface decisions explicitly; reach
  agreement before implementing.
- Conversation continuity is fragile. Write durable artifacts; do not
  rely on chat history.

---

## Ship Design — key decisions (do not re-litigate)

- **All derivable stats computed server-side.** dDR, acceleration, delta-V, HT,
  cost, PP, and crew are all computed in `getShip()` from slot contents. Formulas
  are in the plan document section 3.
- **Override beats derived.** Null in a stat column = auto-derive. Non-null =
  use stored value, show derived alongside as reference.
- **Images as files, not blobs.** `ships.image_path` stores a filename; server
  serves from `server/data/ship-images/`. Keeps SQLite small.
- **Three-panel layout approved.** List left, slot grid + catalog centre, stats right.
  See prototype HTML for exact look and feel.
- **HT base is 13** (SS1 p.35), not 12. −1 for SM+5–9 without engine room; −1 for
  high/total automation at TL7–9; +1 for robofac/nanofactory/fabricator/replicator.

---

## Open seams (do NOT build now)

- `age_gyr` is always `null` — Meridian parquet does not expose it yet.
- `BodyPanel.ts` is a stub. Full detail panel deferred.
- `SlotGrid.ts` and `CatalogPanel.ts` have partial implementations.
- Settlement and species overlays (WORLDS_DB) not wired to any UI.
- Delta-V for mixed reaction drive types requires per-tank fuel assignment — deferred.
