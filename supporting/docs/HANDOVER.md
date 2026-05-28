# Worlds — Handover

Updated 2026-05-27. If the Claude window closes mid-task, read this file
first. It is a pointer document — it tells you what has been built, what
is wrong, and what to do next.

## TL;DR for a fresh session

**Star List + Map is complete. Ship Design Tool Slices 0–3 are complete.
Next action: begin Slice 4 (all derived stats).**

First actions in a new session:
1. Read this file.
2. `git log --oneline -10` and `git status` — confirm current state.
3. Open [ShipDesignMVP_Checklist.md](Design/Worlds/ShipDesignMVP_Checklist.md)
   and find the first unchecked step (currently **4.0**).
4. Read [ShipDesignMVP_Plan.md](Design/Worlds/ShipDesignMVP_Plan.md)
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
[client_server_design.md](Design/Worlds/client_server_design.md).

---

## What to read, in order

1. This file — orientation.
2. [ShipDesignMVP_Checklist.md](Design/Worlds/ShipDesignMVP_Checklist.md)
   — running execution record; find the first unchecked step.
3. [ShipDesignMVP_Plan.md](Design/Worlds/ShipDesignMVP_Plan.md)
   — scope, derivation rules, architecture decisions, data model.
4. [ShipDesignMVP_UI.md](Design/Worlds/ShipDesignMVP_UI.md)
   — approved UI skeleton. Prototype: [ShipDesignMVP_Prototype.html](Design/Worlds/ShipDesignMVP_Prototype.html).
5. [client_server_design.md](Design/Worlds/client_server_design.md)
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
- **Slot detail is a short display label**, not a structured field. User types it
  in a `window.prompt()` pre-filled with a stat-derived default (dDR, G, PP, etc.).
  Improvement to the prompt's guidance text is tracked as step 4.0.
- **Empty positions are not stored in the DB.** `ship_system_slots` only has rows
  for installed systems. The client grid renders all 20 canonical positions by
  generating them from the layout rules and overlaying DB rows.

---

## Current repo state

```
worlds/
├── packages/shared/src/types.ts    All API types; SlotDetail now includes power_points
├── server/src/
│   ├── app.ts                      Hono app: middleware + routes
│   ├── main.ts                     Startup: serve() on port 3000
│   ├── config.ts                   Reads MERIDIAN_DATA, WORLDS_DB, PORT from .env
│   ├── db/
│   │   ├── meridian.ts             DuckDB queries: searchStars(), getSystem(), findByName()
│   │   ├── meridian.math.test.ts   5 tests: mpcToPc
│   │   ├── meridian.filter.test.ts 15 tests: name/dist/centre/unnamed filter, sort, pagination
│   │   ├── ships.ts                node:sqlite CRUD; getShip() derives power_points_available
│   │   └── ships.test.ts           2 tests: G-001 power_points_available (ship_id 1, Star Flower)
│   └── routes/
│       ├── stars.ts                GET /api/stars, /api/stars/by-name, /api/stars/:id
│       ├── stars.http.test.ts      9 HTTP integration tests
│       └── ships.ts                Full CRUD: /api/ships, /hull-sizes, /catalog, /:id/slots
└── client/src/
    ├── main.ts                     Hash router, global CSS (all shared styles live here)
    ├── api/ships.ts                Typed fetch wrappers for all ship endpoints
    ├── state/selection.ts          Shared signal: selectedShipId
    ├── views/
    │   ├── StarList.ts             Name field = navigate; Centre field = explicit centre
    │   ├── SystemView.ts           Fetches system, drives OrbitDiagram + BodyPanel
    │   └── ShipDesign.ts           Ship CRUD; slot drag-assign; detail prompt; catalog load
    └── components/
        ├── StarMap.ts              Three.js WebGL renderer
        ├── OrbitDiagram.ts         SVG ellipse renderer
        ├── BodyPanel.ts            Physical data sidebar
        ├── SlotGrid.ts             Renders all 20 canonical positions; drag-drop targets;
        │                           spanning slot support; absorbedUpTo tracking
        └── CatalogPanel.ts         Catalog grouped by category; clear-slot dragger at top

supporting/sql/
├── schema.sql                  Live DB schema (reflects migrations 001 + 002)
├── seed.sql                    Full INSERT dump for disaster recovery
└── migrations/
    ├── 001_nullable_slot_system_id.sql   system_id nullable (table recreation)
    └── 002_ships_description_image.sql   ADD COLUMN description + image_path

supporting/docs/Design/Worlds/
├── ShipDesignMVP_Plan.md       Scope, derivation rules, architecture decisions, data model
├── ShipDesignMVP_Checklist.md  Step-by-step execution record (Slices 0–7)
├── ShipDesignMVP_UI.md         Approved UI skeleton with wireframes
└── ShipDesignMVP_Prototype.html  Interactive layout prototype
```

**Test count: 40 green** (10 client + 5 math + 15 filter + 2 ships + 9 HTTP).
`pnpm test` from root runs all three workspaces.

---

## Known gaps

| ID | File | Issue |
|---|---|---|
| ~~G-001~~ | — | **CLOSED** — PP budget derived from power plant slots; correlated subquery in `getShip()`. |
| G-003 | `client/src/components/OrbitDiagram.ts:36` | Body angular position uses `Math.random()` — non-deterministic. Deferred. |
| G-004 | `server/src/routes/stars.ts` | No input validation on query params. Deferred. |
| G-005 | `server/src/routes/ships.ts` | No input validation on POST/PUT bodies. Deferred. |
| ~~Schema-M01~~ | — | **CLOSED** — `system_id` nullable via migration 001. |
| ~~Schema-M02~~ | — | **CLOSED** — `description` and `image_path` added via migration 002. |
| ~~G-002, G-006, G-007~~ | — | **CLOSED** — see git log `230f399`. |
| ~~P0-D01~~ | — | **CLOSED** — negative-coordinate ORDER BY fix. |

---

## Sequencing — what to build next

**Active component: Ship Design Tool.** Star List + Map is signed off.

| Slice | Goal | Status |
|---|---|---|
| 0 | Schema migrations (M01 + M02) + SQL files | **Done** `80e415a` |
| 1 | G-001 fix — PP derivation, test-first | **Done** `cf3d0a7` |
| 2 | Slot grid — all 20 positions | **Done** `79a8992` |
| 3 | Slot assignment + detail text | **Done** `d472899` |
| **4** | **All derived stats (dDR, accel, delta-V, HT, cost, crew)** | **Next** |
| 5 | Override inputs + description + image attachment | Not started |
| 6 | Ship list filters | Not started |
| 7 | Smoke test + sign-off | Not started |

**First step of Slice 4 is 4.0** — improve the detail-prompt guidance text
(section + slot position, field purpose, format hint by category) before
moving on to derived-stat derivation.

After Ship Design Tool: fix G-003 (deterministic orbit positions) in System Orbit Display.

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

## Open seams (do NOT build now)

- `age_gyr` is always `null` — Meridian parquet does not expose it yet.
- `BodyPanel.ts` is a stub. Full detail panel deferred.
- Settlement and species overlays (WORLDS_DB) not wired to any UI.
- Delta-V for mixed reaction drive types requires per-tank fuel assignment — deferred.
