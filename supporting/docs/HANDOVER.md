# Worlds — Handover

Written 2026-05-26. If the Claude window closes mid-task, this is the
file the next assistant should read first. It is a pointer document — it
does not restate the design; it tells you what has been built, what is
known to be wrong, and what to do next.

## TL;DR for a fresh session

**Star List + Map MVP is in progress.** Slices 0–2 are complete (commits
`9e051d5`, `0e28314`, `230f399`). vitest is installed in all three workspaces;
25 unit tests are green. G-002, G-006, G-007 are closed. Next step: Slice 2b
(center-relative search) then Slice 3 (HTTP integration tests).

The first conversation in a new session should be:
1. Read this file.
2. `git log --oneline -10` — confirm what has changed.
3. Open [StarListMVP_Checklist.md](Design/Worlds/StarListMVP_Checklist.md)
   and find the first unchecked step.
4. Apply the double-approval gate before doing anything irreversible.

Apply the double-approval gate (see "Working-style rules") before doing
anything irreversible — including `npm install`, `pnpm add`, and
`git commit`.

---

## What the project is

Single-user desktop web app for GURPS-based worldbuilding. It has four
components:

| Component | What it does |
|---|---|
| **Star List** | Filterable, sortable table of named star systems drawn from Meridian parquet data |
| **Star Map** | Three.js 3D point cloud of the current list results |
| **System Orbit Display** | SVG 2D diagram of one system — stars at centre, bodies on orbital ellipses |
| **Ship Design Tool** | GURPS Spaceships slot-based design tool backed by `WORLDS_DB` SQLite |

Stack: TypeScript throughout. Server is Hono + `@hono/node-server` (port
3000). Client is Vite + Three.js, no framework. Shared types in
`packages/shared`. Data in DuckDB (Meridian parquet, read-only) and
`node:sqlite` (WORLDS_DB, read-write for ships). pnpm workspaces.

The design authority is
[client_server_design.md](Design/Worlds/client_server_design.md).

---

## What to read, in order

1. This file — orientation.
2. [Design/Worlds/client_server_design.md](Design/Worlds/client_server_design.md)
   — authoritative design spec. API shapes, query strategy, data sources,
   client layout. Dated 2026-05-22.
3. [Design/Worlds/functions.md](Design/Worlds/functions.md) — original
   one-page UI brief.
4. `CLAUDE.md` (project root) — data paths, Meridian API boundary rules,
   unit conventions.

---

## Decisions already made (do not re-litigate)

- **Stack:** TypeScript, Hono, DuckDB, `node:sqlite`, Vite, Three.js.
  No framework on the client (vanilla TS DOM).
- **No Python server.** The former Python FastAPI server is superseded.
  All server code is in `server/src/`.
- **Meridian is read-only.** Never write to `STARFIELD_DB` or the
  Meridian parquet files. Access only via `server/src/db/meridian.ts`.
- **Named-system startup index.** On server start, DuckDB scans all
  system parquet files and builds an in-memory `Map<name_lower, IndexEntry>`.
  System-by-name lookups (Star List search, `/api/stars/by-name`) are
  instant against this index. It is not persisted — rebuilt each start.
- **No real-time / WebSocket / multi-user** in this phase.
- **Unit conventions** (from CLAUDE.md): 1 yd = 1 m, 1 lb = 0.5 kg,
  1 atm = 1 bar, mps = miles/s so 1 mps = 1.6 km/s. These are not
  physical measurements — they are GURPS game quantities treated as if
  already in sensible SI units.
- **pnpm workspaces:** `client`, `server`, `packages/shared`. The root
  `package.json` has `dev` and `build` scripts via pnpm `--filter`.

---

## Current repo state

```
worlds/
├── packages/shared/src/types.ts    All API request/response types
├── server/src/
│   ├── app.ts                      Hono app: middleware + routes (no port binding)
│   ├── main.ts                     Startup only: buildIndex() then serve()
│   ├── config.ts                   Reads MERIDIAN_DATA, WORLDS_DB, PORT from .env
│   ├── db/
│   │   ├── meridian.ts             DuckDB index + filterAndPage() + searchStars() + getSystem()
│   │   ├── meridian.math.test.ts   5 tests: mpcToPc exact values + round-trip
│   │   ├── meridian.filter.test.ts 10 tests: name/dist filter, sort, pagination
│   │   └── ships.ts                node:sqlite CRUD for all ship tables
│   └── routes/
│       ├── stars.ts                GET /api/stars, /api/stars/by-name, /api/stars/:id
│       └── ships.ts                Full CRUD for /api/ships + hull-sizes + catalog
└── client/src/
    ├── main.ts                     Hash router, global CSS, view lifecycle
    ├── api/stars.ts + api/ships.ts Typed fetch wrappers
    ├── state/selection.ts          Shared signal: selectedSystemId, selectedShipId
    ├── views/
    │   ├── StarList.ts             Filterable table + Display ↔ List toggle
    │   ├── SystemView.ts           Fetches system, drives OrbitDiagram + BodyPanel
    │   └── ShipDesign.ts           Ship CRUD, slot drag-assign, catalog load
    └── components/
        ├── StarMap.ts              Three.js WebGL renderer, orbit controls
        ├── StarMap.math.test.ts    10 tests: spectral colours + fast-check property
        ├── OrbitDiagram.ts         SVG ellipse renderer (100 lines)
        ├── BodyPanel.ts            Physical data sidebar (25 lines — complete)
        ├── SlotGrid.ts             Slot grid render (43 lines — partial)
        └── CatalogPanel.ts         Catalog grouped render (44 lines — partial)
```

**Test infrastructure installed.** vitest 4.1.7 in all three workspaces;
`pnpm test` from root runs all. 25 tests green (Slices 1–2). `app.ts`/`main.ts`
split enables handler tests without port binding.

---

## Known gaps (filed, not yet fixed)

These are correctness problems in the existing code:

| ID | File | Line | Issue |
|---|---|---|---|
| G-001 | `server/src/db/ships.ts` | 136 | Power-plant PP budget is a placeholder — `reduce(sum, 0)` always returns 0. PP available is always 0. |
| G-002 | ~~`server/src/db/meridian.ts:276`~~ | **CLOSED** `230f399` 2026-05-26 — `mass_km` duplicate field removed; only `mass_kg` remains. |
| G-003 | `client/src/components/OrbitDiagram.ts` | 36 | Body angular position uses `Math.random()` — not from orbital geometry. Diagram is non-deterministic; correct formula is mean anomaly or a fixed epoch angle. |
| G-004 | `server/src/routes/stars.ts` | — | No input validation — malformed query params are silently coerced. |
| G-005 | `server/src/routes/ships.ts` | — | No input validation — malformed POST/PUT bodies reach the DB layer unchecked. |
| G-006 | ~~`server/src/db/meridian.ts:162`~~ | **CLOSED** `230f399` 2026-05-26 — `filteredTotal` now equals `rows.length` when spectral/hz filters are active; comment explains the page-scope limitation. |
| G-007 | ~~`server/src/db/meridian.ts:207`~~ | **CLOSED** `230f399` 2026-05-26 — `x_pc/y_pc/z_pc` now use `mpcToPc()`; silent `/1000` compensation removed from `StarMap.ts`. |

G-001 and G-003 are the highest-priority correctness gaps for the Ship
Design and System Orbit components respectively. G-006 is a correctness
bug in Star List pagination. All must be addressed before a component
is declared MVP-complete.

---

## Math under test — Claude's responsibility

**This project does not use human math-review gates.** Instead, Claude
is responsible for identifying every mathematical operation in the
codebase, writing automated tests that verify it against known analytic
results, and ensuring those tests run in CI before any component is
signed off.

### Mathematical operations by component

#### System Orbit Display

| Operation | Location | Test approach |
|---|---|---|
| Semi-minor axis `b = a √(1 − e²)` | `OrbitDiagram.ts:32` | Pure function test: for `a=1, e=0` → `b=1`; for `a=1, e=0.5` → `b=0.866…`; for `a=2, e=0.8` → `b=1.2` |
| Focus offset `c = a × e` | implicit in centre placement | Test that star sits at focus, not at ellipse centre: `cx + c` should equal `cx + rx * e` |
| Scale factor `scale = (W/2 - 30) / maxAu` | `OrbitDiagram.ts:16` | Test that the outermost orbit fits in the viewport with the 30px margin |
| Body position epoch angle | G-003 fix | After fixing to a deterministic formula, test round-trip: encode angle, decode back |

#### Star List / Star Map

| Operation | Location | Test approach |
|---|---|---|
| Coordinate scaling `x_pc = x_mpc / 1000` | `StarMap.ts:50-52` | Known Meridian entry (Sol at origin): `x_pc = 0`, `y_pc = 0`, `z_pc = 0` |
| Distance from coordinates `d = √(x²+y²+z²) × 1000` (mpc→pc) | sanity check on `dist_pc` | For a known system, verify `dist_pc` ≈ `√(x_mpc²+y_mpc²+z_mpc²) / 1000` |
| Pagination total vs filtered total | G-006 fix | searchStars with `spectral='G'` must return `total` equal to the count of G systems in the test index, not the pre-filter count |

#### Ship Design Tool

| Operation | Location | Test approach |
|---|---|---|
| Power points available (G-001 fix) | `ships.ts:136` | Build a ship with one power plant; assert `power_points_available > 0` |
| Power points consumed | `ships.ts:168` | Count high-energy systems in slots; assert equals `power_points_consumed` |
| GURPS unit conversions | `ships.ts:14` | `length_yards` returned as `length_m` — 1:1 conversion per CLAUDE.md conventions; assert `length_m === raw_yards_value` |
| Delta-V unit (mps → km/s) | display layer | If ever displayed, 1 mps must appear as 1.6 km/s, not 1 km/s |

### How to approach math tests

1. Extract the computation into a pure, importable function if it is
   currently embedded in DOM/render code (e.g., extract `semiMinorAxis`
   from `OrbitDiagram`).
2. Write the test first (red phase) against the analytic result.
3. If a gap (G-001 to G-006) must be fixed to make the test meaningful,
   fix the gap in the implementation phase and verify the test turns green.
4. Property-based testing (`fast-check`) is appropriate for the ellipse
   formulas: for any `(a > 0, 0 ≤ e < 1)`, assert `b = a √(1 − e²) ≤ a`.

---

## Sequencing — what to build next

**First: agree on which component is the MVP target.** The recommended
order (easiest to hardest, given known gaps):

1. **Star List + Map** — most advanced; G-006 and G-007 are the only
   correctness gaps; client table and 3D map both render. **MVP target
   chosen — plan and checklist written.**
2. **System Orbit Display** — requires fixing G-003 (random positions)
   before the math tests can be written. Medium effort.
3. **Ship Design Tool** — requires fixing G-001 (PP budget) and G-005
   (input validation). Highest complexity but most standalone.

**Star List + Map MVP documents:**
- [StarListMVP_Plan.md](Design/Worlds/StarListMVP_Plan.md) — scope, gaps,
  integration seams, math test spec, slice overview, DoD
- [StarListMVP_Checklist.md](Design/Worlds/StarListMVP_Checklist.md) — step-by-step
  execution record with `[AI]` / `[HUMAN]` tags

The checklist is the running record of execution. Open it to find the next step.

---

## Test harness plan (Slice 0 detail)

- **vitest** in `server`, `client`, `packages/shared` (per-workspace
  `vitest.config.ts`; `environment: "node"` everywhere; client may
  switch to `"happy-dom"` if DOM testing is needed).
- **fast-check** in `client` for property-based tests on ellipse and
  coordinate formulas.
- **supertest** in `server` for HTTP route integration tests.
- Root `package.json` gets `"test": "pnpm --filter '*' run test"`.
- Each workspace gets `"test": "vitest run"` and `"test:watch": "vitest"`.
- Commit prefix convention: `red:` for commits with intentionally failing
  tests; `green:` for commits that turn them green.

---

## Working-style rules (non-negotiable)

- **Claude implements; the user supervises and reviews.** Claude writes
  all code and test files. The user reads diffs, runs the app, and signs
  off at each review gate.

- **Double-approval gate on every `[HUMAN]` step.** At every approval
  point in the execution checklist:
  1. User gives first approval ("proceed", "yes", etc.).
  2. Claude echoes the specific next action: *"Confirming: about to X —
     proceed?"*
  3. User gives a second explicit confirmation.
  4. Only then does Claude act.
  This applies without exception, even when the first approval looks
  unambiguous. The echo is what lets the user catch a typo or slip. If
  it feels like friction, that is it working as intended.
  The gate applies to: `pnpm add` / `npm install`, `git commit`,
  `git push`, destructive DB operations, and any structural refactor.

- **No unprompted commits.** Claude never runs `git commit` without
  going through pre-commit triage (list what would land, propose the
  commit message) and the double-approval gate.

- **Test-first.** No production code — including gap fixes — without a
  failing test that is red for the right reason. The red review is
  mandatory before implementation starts.

- **Claude writes math tests autonomously.** There is no human
  math-review gate. Claude identifies the mathematical invariants,
  extracts testable pure functions, writes tests against analytic
  results, and flags any discrepancy as a blocking issue. The user
  reviews the tests as code (red review) but is not responsible for
  deriving the expected values.

- **Green review = Definition of Done.** Every green review gate
  includes: full `pnpm test` green, all Known Gaps for the target
  component resolved, a slice retro drafted by Claude and approved by
  the user.

- **Slice retro at every green review.** Claude drafts a retro entry
  covering *what surprised me / what worked / what I'd change*. Past
  retros are immutable once approved.

---

## Working-style preferences (durable)

- The user has no web-programming background. Explain HTTP, routing,
  JS ecosystem concepts from first principles when they are relevant.
  Do not assume knowledge of terms like "middleware", "hydration", or
  "hot reload" without a one-line gloss.
- Strong preference for explicit terse documentation with the *why*
  alongside the *what*.
- Design pinned before code. If a design decision surfaces mid-slice,
  surface it explicitly and reach agreement before implementing.
- Conversation continuity is fragile. Write durable artifacts; do not
  rely on chat history.

---

## Open seams (do NOT build now)

- `age_gyr` is always `null` in `SystemDetail` and `StarListRow` — the
  Meridian parquet does not yet expose stellar age. Leave the field;
  populate when Meridian adds it.
- `BodyPanel.ts` is a stub (25 lines). Full physical detail panel is
  deferred until System Orbit is the MVP target.
- `SlotGrid.ts` and `CatalogPanel.ts` have partial drag-and-drop
  implementations. Full drag-and-drop interaction deferred until Ship
  Design is the MVP target.
- Settlement and species overlays (WORLDS_DB tables) are not yet wired
  to any UI. Deferred to a later phase.

---

## First steps in a new session

1. Read this file.
2. `git log --oneline -10` and `git status` — confirm what has changed
   since this handover was written.
3. Ask the user which component is the MVP target (Star List + Map /
   System Orbit / Ship Design). Apply the double-approval gate before
   proceeding.
4. Compare `server/src/` and `client/src/` against the file list above.
   If unexpected files exist, ask before proceeding.
5. Proceed to Slice 0: propose the vitest configuration and where it
   goes (per-workspace configs), post a one-screen plan, wait for
   double-approval before running any installs.
