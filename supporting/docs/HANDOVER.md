# Worlds — Handover

Updated 2026-05-27. If the Claude window closes mid-task, read this file
first. It is a pointer document — it tells you what has been built, what
is wrong, and what to do next.

## TL;DR for a fresh session

**Star List + Map minimum viable build is complete.** All known defects
are closed. Next: Slice 4 (manual smoke test in browser) and Slice 5
(sign-off).

First actions in a new session:
1. Read this file.
2. `git log --oneline -10` and `git status` — confirm current state.
3. Open [StarListMVP_Checklist.md](Design/Worlds/StarListMVP_Checklist.md)
   and find the first unchecked step.
4. Apply the double-approval gate before doing anything irreversible.

**Test to write (red first):**
```typescript
it('name search for distant star (>700 pc) returns 200 not 500', async () => {
  const res = await app.request('/api/stars?name=HD+77164&limit=5');
  expect(res.status).toBe(200);
  const body = await res.json();
  expect(typeof body.total).toBe('number');
});
```

**Note on DuckDB LIMIT:** DuckDB fully supports `LIMIT`/`OFFSET`. The
user could not find it in docs — this is not related to the 500. The
existing `COUNT(*) OVER ()` window function is evaluated before `LIMIT`
is applied, so `total_count` reflects all matching rows correctly.

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
2. [Design/Worlds/StarListMVP_Checklist.md](Design/Worlds/StarListMVP_Checklist.md)
   — running execution record; find the first unchecked step.
3. [Design/Worlds/client_server_design.md](Design/Worlds/client_server_design.md)
   — authoritative design spec.
4. `CLAUDE.md` (project root) — data paths, Meridian API boundary rules.

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
    │   └── ShipDesign.ts           Ship CRUD, slot drag-assign, catalog load
    └── components/
        ├── StarMap.ts              Three.js WebGL renderer; setCentre() shifts camera
        ├── OrbitDiagram.ts         SVG ellipse renderer
        ├── BodyPanel.ts            Physical data sidebar; breakable() for long strings
        ├── SlotGrid.ts             Slot grid render (partial)
        └── CatalogPanel.ts         Catalog grouped render (partial)
```

**Test count: 28 green (5 math + 19 filter + 4 HTTP GET /stars + 5 HTTP
other).** `pnpm test` from root runs all three workspaces.

---

## Known gaps

| ID | File | Issue |
|---|---|---|
| ~~P0-D01~~ | ~~`server/src/routes/stars.ts`~~ | **CLOSED** — negative-coordinate ORDER BY used `--` which DuckDB parsed as a line comment; fixed by parenthesising interpolated coords. |
| G-001 | `server/src/db/ships.ts:136` | PP budget is placeholder — always returns 0. |
| G-003 | `client/src/components/OrbitDiagram.ts:36` | Body angular position uses `Math.random()` — non-deterministic. |
| G-004 | `server/src/routes/stars.ts` | No input validation on query params. |
| G-005 | `server/src/routes/ships.ts` | No input validation on POST/PUT bodies. |
| G-002, G-006, G-007 | — | **CLOSED** — see git log `230f399`. |

---

## Sequencing — what to build next

- **Slice 4:** Manual smoke test (golden path + edge cases in browser).
  All `[HUMAN]` steps in checklist.
- **Slice 5:** Sign-off — definition-of-done checklist, seam table, retro, final commit.

After Star List + Map MVP is signed off, choose next component:
1. System Orbit Display (fix G-003 first)
2. Ship Design Tool (fix G-001 first)

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
- `SlotGrid.ts` and `CatalogPanel.ts` have partial implementations.
- Settlement and species overlays (WORLDS_DB) not wired to any UI.
