# Star List + Map — MVP Plan

*2026-05-26. Companion to [StarListMVP_Checklist.md](StarListMVP_Checklist.md).*

---

## 1. MVP scope

**In scope — everything needed to call this component done:**

- `GET /api/stars` — filtering, sorting, pagination all correct (including G-006 fix)
- `GET /api/stars/by-name?name=X` — redirect to system_id form
- `GET /api/stars/:id` — full `SystemDetail` response (tested, used by Orbit Display later)
- `StarListRow` coordinates correct on the wire (G-007 fix — see §3)
- Client Star List — search toolbar, table render, row-click navigation
- Client Star Map — Three.js point cloud, orbit controls, spectral colouring
- Test harness (vitest in all three workspaces) wired to `pnpm test`
- All mathematical operations covered by automated tests (see §5)

**Out of scope for this MVP:**

- Map raycasting / hover tooltips / click-to-navigate from map point (deferred)
- Bi-directional selection sync (map click highlights list row)
- Pagination UI controls in the client (the search already caps at 500)
- Age column (always null from Meridian — leave the field, do not remove it)
- Input validation / zod on the server star routes (G-004 — deferred to hardening phase)
- System Orbit Display rendering (navigation to `#system` hash is already wired; display is Orbit MVP)
- Ship Design, settlement overlays, species data

---

## 2. Known gaps to resolve in this MVP

From the HANDOVER gap register:

| ID | Description | Where |
|---|---|---|
| **G-006** | `searchStars` calculates `total` before applying spectral/hz filters — inflated count | `server/src/db/meridian.ts` |
| **G-007** | `StarListRow.x_pc/y_pc/z_pc` hold mpc values; `StarMap.ts` compensates silently with `/ 1000` | `meridian.ts:207`, `types.ts:14`, `StarMap.ts:50` |

G-002 (`mass_km` typo in `getSystem`) is in scope to fix as it is in the same file — one-line change, no test required.

G-004 (input validation) is deferred.

### G-006 fix strategy

The current flow computes `total = candidates.length` after the name/distance filter but
before the spectral/hz filter, which is applied only after DuckDB star data is fetched
for the paginated page. This means `total` can over-count when spectral or hz filters
are active.

**Fix:** when neither `spectral` nor `hz_eligible` is set, `total` is exact (no
change). When either is set, return `total = rows.length` (the true count for the
returned page) and cap the query at `limit` rows. This is honest: the client cannot
know the cross-page total without a full scan, and the search UI does not need it.
Document the behaviour in a comment.

### G-007 fix strategy

`meridian.ts:207` currently does `x_pc: e.x_mpc`. Fix: `x_pc: e.x_mpc / 1000`.
Same for `y_pc` and `z_pc`. Remove the compensating `/ 1000` in `StarMap.ts:50-52`.
The comment there becomes obsolete — delete it.

After this fix: `StarListRow.x_pc` in parsecs, matching its name. External consumers
can use the field without a hidden conversion factor.

---

## 3. Integration seams — do not break these

These are the contracts that System Orbit Display, Ship Design, and external
projects depend on. Every item in this list must survive the MVP unchanged or
must be explicitly tested to confirm it was preserved.

### Shared types (`packages/shared/src/types.ts`)

| Type | Fields that must not change |
|---|---|
| `StarListRow` | `system_id: string`, `name`, `dist_pc`, `x_pc`, `y_pc`, `z_pc`, `hz_eligible`, `body_count` |
| `StarListResponse` | `total: number`, `rows: StarListRow[]` |
| `SystemDetail` | `system_id`, `name`, `dist_pc`, `stars: StarDetail[]`, `bodies: BodyDetail[]` |
| `StarDetail` | entire shape (consumed by OrbitDiagram) |
| `BodyDetail` | entire shape (consumed by BodyPanel) |

Adding fields to any type is safe. Removing or renaming fields is not.

### Server API endpoints

| Endpoint | Contract |
|---|---|
| `GET /api/stars` | JSON `{ total: number, rows: StarListRow[] }` |
| `GET /api/stars/by-name?name=X` | HTTP 302 → `/api/stars/:id` |
| `GET /api/stars/:id` | JSON `SystemDetail` or 404 |
| `GET /health` | JSON `{ ok: true }` |
| All `/api/ships/*` | Unchanged — out of scope |

Port 3000 is the default (set in `config.ts`); do not change it.
The `/api` proxy in `vite.config.ts` points there; do not change the proxy target.
CORS middleware (`cors()` in `main.ts`) must remain — external projects may call the API.

### Client state signals (`client/src/state/selection.ts`)

`selectedSystemId: signal<string | null>` — written by StarList row click, read by
SystemView. Must remain type `string | null`. Do not rename; do not remove.

`selectedShipId: signal<number | null>` — not touched in this MVP. Leave it.

### Hash routing

`#stars` → `StarListView`, `#system` → `SystemView`, `#ships` → `ShipDesignView`.
StarList row click does `selectedSystemId.set(id); location.hash = '#system'`.
This navigation must continue to work after any refactor.

---

## 4. Test harness plan

Install in **Slice 0**, before writing any tests.

| Package | Workspace | Purpose |
|---|---|---|
| `vitest` | `server`, `client`, `packages/shared` | Test runner |
| `@vitest/coverage-v8` | `server`, `client` | Coverage (optional, but install now) |
| `fast-check` | `client` | Property-based tests for math |

No supertest. Hono provides `app.request(url)` for handler testing — cleaner than
supertest for fetch-based frameworks, no extra dependency.

Each workspace gets `vitest.config.ts`:

```typescript
import { defineConfig } from 'vitest/config';
export default defineConfig({
  test: { environment: 'node', include: ['src/**/*.test.ts'] },
});
```

The `client` workspace may need `environment: 'happy-dom'` if any test exercises DOM
APIs. Decide at test-write time; default to `node`.

Root `package.json` gets:
```json
"test": "pnpm --filter '*' run test"
```

Each workspace `package.json` gets:
```json
"test":       "vitest run",
"test:watch": "vitest"
```

`pnpm test` from the root runs all workspaces sequentially. A "No test files found"
result in all three workspaces is the success condition for Slice 0.

### Server test prerequisite: split `main.ts`

The server's `main.ts` currently both defines the Hono app and starts the server.
Tests need to import the app without binding to a port. Refactor before writing
server tests:

- **`server/src/app.ts`** — export `const app = new Hono()` with all middleware and
  routes wired.
- **`server/src/main.ts`** — import `app`, call `buildIndex()`, call `serve()`.

Tests import from `app.ts` and call `buildIndex()` in `beforeAll`. Nothing else
about the server changes.

### Integration test data dependency

The server tests that exercise `searchStars` and `getSystem` require:
- Meridian volume mounted at `MERIDIAN_DATA` (default `/Volumes/Lexar/MeridianData`)
- `buildIndex()` to have completed

Tests must call `await buildIndex()` in `beforeAll`. The call is idempotent — if the
index is already built it will rebuild (acceptable in tests). If the volume is not
mounted, `buildIndex()` throws; the test suite fails with a clear message rather than
silently skipping.

Do not add skip guards. These tests are integration tests and must run locally.
If the volume is unmounted, the developer knows why they failed.

---

## 5. Math tests — Claude's responsibility

Extract each mathematical operation into an importable pure function before writing
the test. Tests assert against analytic expected values, not empirical observations.

### 5.1 Coordinate scaling

**Extract:** `mpcToPc(mpc: number): number` — pure function in `server/src/db/meridian.ts`
(or a shared math module).

**Tests:**

```
mpcToPc(0)      === 0
mpcToPc(1000)   === 1         // 1000 mpc = 1 pc
mpcToPc(-500)   === -0.5
mpcToPc(308.5)  === 0.3085    // representative star distance
```

**Property (fast-check):** `Math.abs(mpcToPc(x) * 1000 - x) < 1e-9` for all finite `x`.

### 5.2 Distance invariant

After the G-007 fix, `StarListRow.dist_pc` should equal
`√(x_pc² + y_pc² + z_pc²)` within floating-point tolerance for any row whose
coordinates are non-zero. Test this against at least three real rows from the
`buildIndex()` result, verifying:

```
Math.abs(dist_pc - Math.sqrt(x_pc**2 + y_pc**2 + z_pc**2)) < 0.01
```

(0.01 pc tolerance — DuckDB may round coordinates differently from `dist_pc`.)

If this invariant does not hold, file a note in the HANDOVER — it means Meridian
stores `dist_pc` and coordinates from independent calculations.

### 5.3 Spectral colour mapping

**Extract:** `spectralColour(spectral: string): { r: number; g: number; b: number }` —
already a private function in `StarMap.ts`; make it an exported named function.

**Tests — exhaustive (all seven classes + default):**

| Input | Expected r | Expected g | Expected b |
|---|---|---|---|
| `'O'` | 0.6 | 0.7 | 1.0 |
| `'B2'` | 0.7 | 0.8 | 1.0 |
| `'A0'` | 0.9 | 0.95 | 1.0 |
| `'F5'` | 1.0 | 1.0 | 0.9 |
| `'G2'` | 1.0 | 0.95 | 0.7 |
| `'K3'` | 1.0 | 0.75 | 0.4 |
| `'M8'` | 1.0 | 0.4 | 0.2 |
| `''` | 0.5 | 0.5 | 0.5 |
| `'XYZ'` | 0.5 | 0.5 | 0.5 |

**Property:** all returned r/g/b values are in `[0, 1]` for any non-null string input.

### 5.4 Filter / sort / pagination (pure logic)

**Extract:** `filterAndPage(entries: IndexEntry[], params: StarListParams): { total: number; page: IndexEntry[] }` — the name/distance filter, sort, and paginate logic
currently embedded in `searchStars`. This function must not call DuckDB; it operates
only on the in-memory `IndexEntry[]`.

**Tests using a synthetic five-entry index:**

```
entries = [
  { name: 'Alpha Centauri', dist_pc: 1.34, x_mpc: ..., y_mpc: ..., z_mpc: ... },
  { name: 'Barnard',        dist_pc: 1.83 },
  { name: 'Sirius',         dist_pc: 2.64 },
  { name: 'Sol',            dist_pc: 0.00 },
  { name: 'Tau Ceti',       dist_pc: 3.65 },
]
```

| Test | Input | Expected output |
|---|---|---|
| Name filter (exact substring) | `{ name: 'sol' }` | `total=1`, `page=[Sol]` |
| Name filter (partial) | `{ name: 'a' }` | `total=3` (Alpha Cen, Barnard, Tau Ceti) |
| Distance max filter | `{ dist_max_pc: 2.0 }` | `total=3` (Sol, Alpha Cen, Barnard) |
| Distance min+max | `{ dist_min_pc: 1.5, dist_max_pc: 3.0 }` | `total=2` (Barnard, Sirius) |
| Sort by name asc | `{ sort: 'name', dir: 'asc' }` | page[0].name = 'Alpha Centauri' |
| Sort by dist desc | `{ sort: 'dist_pc', dir: 'desc' }` | page[0].name = 'Tau Ceti' |
| Pagination limit | `{ limit: 2, offset: 0 }` | `page.length=2`, `total=5` |
| Pagination offset | `{ limit: 2, offset: 4 }` | `page.length=1` |
| Empty result | `{ name: 'zzz' }` | `total=0`, `page=[]` |
| Default sort | `{}` | sorted by dist_pc asc (Sol first) |

### 5.5 G-006 regression (HTTP level)

After fixing G-006, write one HTTP-level regression test:

```
GET /api/stars?spectral=G&dist_max_pc=30&limit=100
→ result.rows.every(r => r.primary_spectral.startsWith('G'))
→ result.total === result.rows.length   // no inflation
```

This runs against real data and does not require a synthetic fixture.

---

## 6. Slice overview

| Slice | Goal | Tests state at end |
|---|---|---|
| 0 | Harness installed; `pnpm test` runs clean ("no test files") | — |
| 1 | Math + filter anchors written; all red for right reason | Red |
| 2 | G-006, G-007, G-002 fixed; extracted pure functions implemented | Green |
| 3 | HTTP integration tests; `app.ts` split; G-006 regression | Green |
| 4 | Manual smoke test by user | — |
| 5 | Sign-off; integration seams verified; HANDOVER updated | Full green |

---

## 7. Definition of Done (MVP)

All of the following must be true before this component is declared MVP-complete:

- [ ] `pnpm test` exits 0, all tests green
- [ ] G-006 fixed and covered by an HTTP regression test
- [ ] G-007 fixed: `StarListRow.x_pc/y_pc/z_pc` are true parsecs
- [ ] G-002 fixed: `mass_km` typo removed from `getSystem`
- [ ] All mathematical operations in §5 covered by automated tests
- [ ] `app.ts` / `main.ts` split complete
- [ ] Every integration seam in §3 verified (see Slice 5 checklist)
- [ ] Manual smoke test passed (golden path + spectral filter)
- [ ] Slice retro written and approved
- [ ] HANDOVER gap register updated (G-002, G-006, G-007 closed)
