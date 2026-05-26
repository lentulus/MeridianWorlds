# Star List + Map — MVP Checklist

Execution record for the Star List + Map MVP.
Design authority: [StarListMVP_Plan.md](StarListMVP_Plan.md).
Working-style rules (double-approval gate, test-first, etc.): [HANDOVER.md](../../HANDOVER.md).

**Legend.** `[AI]` = Claude does it. `[HUMAN]` = user does it.

**Double-approval gate** — at every `[HUMAN]` approval step, Claude echoes
the specific next action ("Confirming: about to X — proceed?") and waits for
a second explicit yes before acting. This applies without exception, including
to `pnpm add`, `pnpm install`, and `git commit`.

**Commit convention.** `red:` prefix for commits with intentionally failing
tests. `green:` prefix for commits that turn them green. Plain descriptive
messages for structural changes that contain no tests.

---

## Slice 0 — Test harness

Goal: `pnpm test` runs in all three workspaces, finds no test files, exits
cleanly. No application code changes.

- [x] **0.1 [AI]** Post a one-screen harness plan: packages to install, where
      `vitest.config.ts` files go, root `pnpm test` script, `app.ts` / `main.ts`
      split rationale. This is a proposal only — do not run any installs.
      *Result:* Plan posted 2026-05-26 in chat.

- [x] **0.2 [HUMAN]** Review the harness plan. Redirect if needed.
      *Result:* Approved.

- [x] **0.3 [HUMAN]** **Approve install** *(double-approval gate).*
      *Result:* Approved.

- [x] **0.4 [AI]** Install dependencies:
      `vitest` + `@vitest/coverage-v8` in `server`, `client`, `packages/shared`.
      `fast-check` in `client`.
      No supertest — Hono uses `app.request()` for handler tests.
      Report exact versions installed.
      *Result:* vitest@4.1.7, @vitest/coverage-v8@4.1.7, fast-check@4.8.0. All clean.

- [x] **0.5 [AI]** Add `vitest.config.ts` to `server/`, `client/`, `packages/shared/`.
      Add `"test": "vitest run"` and `"test:watch": "vitest"` to each workspace
      `package.json`. Add `"test": "pnpm -r run test"` to root `package.json`.
      Added `passWithNoTests: true` to all three configs (vitest exits 1 with no
      files otherwise, aborting the recursive run).
      *Result:* Done.

- [x] **0.6 [AI]** Refactor `server/src/main.ts` → split into:
      - `server/src/app.ts` — exports `const app` with all middleware and routes
      - `server/src/main.ts` — imports `app`, calls `buildIndex()`, calls `serve()`
      *Result:* Done. Server behaviour unchanged.

- [x] **0.7 [AI]** Run `pnpm test` from root. Confirm all three workspaces run
      vitest, report "No test files found", and exit without error.
      *Result:* All three workspaces: "No test files found, exiting with code 0". Exit 0.

- [x] **0.8 [HUMAN]** Confirm the clean run looks right.
      *Result:* Approved.

- [x] **0.9 [AI]** Pre-commit triage: list every changed file; propose commit message.
      *Result:* 10 files listed; message proposed in chat.

- [x] **0.10 [HUMAN]** **Approve commit** *(double-approval gate).*
      *Result:* Approved.

- [x] **0.11 [AI]** Commit. Report hash.
      *Result:* `9e051d5` — "chore: Slice 0 — test harness + app/main split"

---

## Slice 1 — Math and filter anchors (red)

Goal: write all math and filter tests. Every test fails for the right reason
(missing import, wrong value, or function does not exist yet). No production
code changes except extracting the functions being tested.

- [x] **1.1 [AI]** Extract `spectralColour` from `client/src/components/StarMap.ts` as
      an **exported** function. No other logic changes in that file.
      *Result:* Done. Added `export` keyword to existing function.

- [x] **1.2 [AI]** Add `mpcToPc(mpc: number): number` as an **exported** pure function
      in `server/src/db/meridian.ts`. Not yet applied to row building (G-007 fix
      is Slice 2 step 2.1).
      *Result:* Done. Added under "Pure math helpers" section.

- [x] **1.3 [AI]** Extract `filterAndPage(entries: IndexEntry[], params: StarListParams)`
      as an **exported** pure function from `searchStars` in `server/src/db/meridian.ts`.
      The name/distance filter, sort, and pagination logic move into this function.
      `searchStars` calls it. No behaviour change.
      *Result:* Done. `searchStars` now calls `filterAndPage([...nameIndex.values()], params)`.

- [x] **1.4 [AI]** Write `client/src/components/StarMap.math.test.ts`:
      10 tests: 7 spectral class mappings + empty + unknown + fast-check property.
      *Result:* Written. Tests were red (TypeError) before export; green after.

- [x] **1.5 [AI]** Write `server/src/db/meridian.math.test.ts`:
      5 tests: mpcToPc exact values + round-trip table.
      *Result:* Written. Round-trip uses 9 representative values (no fast-check in server).

- [x] **1.6 [AI]** Write `server/src/db/meridian.filter.test.ts`:
      10 tests covering all 9 plan cases + one extra (sort desc last entry).
      *Result:* Written. Five-entry synthetic IndexEntry fixture; no DuckDB.

- [x] **1.7 [AI]** Run `pnpm test`. Capture output. Every new test must fail.
      *Result:* 25/25 tests red before extractions (all "TypeError: X is not a
      function"). 25/25 green after extractions. Confirmed correct failure mode.

- [x] **1.8 [AI]** Post **red-review summary**.
      *Result:* Posted in chat. Noted that G-006/G-007 anchors are deferred to
      Slice 3 HTTP tests; all unit-level math and filter tests turn green on extraction.

- [x] **1.9 [HUMAN]** **Red review.**
      *Result:* Approved.

- [x] **1.10 [HUMAN]** **Approve red commit** *(double-approval gate).*
      *Result:* Approved.

- [x] **1.11 [AI]** Commit `red:`. Report hash.
      *Result:* `0e28314` — "red: Slice 1 — math and filter test anchors"

---

## Slice 2 — Fix gaps; turn Slice 1 green

Goal: implement the extracted functions correctly; fix G-002, G-006, G-007.
All Slice 1 tests go green.

- [x] **2.1 [AI]** Fix G-007: confirm `mpcToPc` is now applied in `searchStars`
      row-building (`x_pc: mpcToPc(e.x_mpc)` etc.). Remove the compensating
      `/ 1000` in `StarMap.ts:50-52` and the comment that documented it.
      *Result:* Done. `x_pc: mpcToPc(e.x_mpc)` etc. applied; `/1000` and comment removed from StarMap.ts.

- [x] **2.2 [AI]** Fix G-002: remove the `mass_km` duplicate field in `getSystem`
      (`server/src/db/meridian.ts:276`).
      *Result:* Done. `mass_km` field removed; only `mass_kg` remains.

- [x] **2.3 [AI]** Fix G-006: in `searchStars`, when `params.spectral` or
      `params.hz_eligible` is set, compute `total` as `rows.length` (filtered count
      for the returned page, not the pre-filter candidate count). Add an inline
      comment explaining the limitation. See Plan §2 for rationale.
      *Result:* Done. `filteredTotal` logic added with inline comment.

- [x] **2.4 [AI]** Run `pnpm test`. All Slice 1 tests must be green. Report output.
      *Result:* 25/25 green across all workspaces.

- [x] **2.5 [AI]** Post **ready-for-review summary**: changed files, what each change
      does, test output (pass count + any remaining failures).
      *Result:* Posted in chat.

- [x] **2.6 [HUMAN]** Read the diff.
      *Result:* Approved.

- [x] **2.7 [HUMAN]** Run `pnpm dev`, load the star list, search within 30 pc.
      Confirm the table populates and the map renders correctly.
      *Result:* Approved. Display confirmed good for MVP.

- [x] **2.8 [AI]** Update the HANDOVER gap register: close G-002, G-006, G-007;
      note what was done and which commit.
      *Result:* Done. See HANDOVER.md gap register.

- [x] **2.9 [HUMAN]** **Green sign-off for Slice 2** *(double-approval gate).*
      *Result:* Approved ("Commit. slice 2" / "go").

- [x] **2.10 [AI]** Pre-commit triage: list changed files; propose `green:` commit message.
      *Result:* 2 files listed; message proposed in chat.

- [x] **2.11 [HUMAN]** **Approve commit** *(double-approval gate).*
      *Result:* Approved ("go").

- [x] **2.12 [AI]** Commit `green:`. Report hash.
      *Result:* `230f399` — "green: Slice 2 — fix G-002 G-006 G-007 coordinate and filter bugs"

---

## Slice 2b — Center-relative search (MVP scope addition)

Goal: star list distance filter and display works relative to a user-selected
center star, not always from Sol. User enters a name in a "Center" field; the
search re-fires with that star's coordinates as origin.

- [ ] **2b.1 [AI]** Update `StarListParams` in `packages/shared/src/types.ts`:
      add `center_x_pc?: number; center_y_pc?: number; center_z_pc?: number`.
      *Result:* —

- [ ] **2b.2 [AI]** Write red tests in `server/src/db/meridian.filter.test.ts`:
      - When center = Sirius coords, Sol's computed dist ≈ 2.64 pc (not 0)
      - When center = Sol (default 0,0,0), all existing tests still pass
      *Result:* —

- [ ] **2b.3 [HUMAN]** Red review.
      *Result:* —

- [ ] **2b.4 [AI]** Update `filterAndPage` to compute distance from center when
      provided; update `searchStars` to pass center through and use computed dist
      in the returned `dist_pc` field.
      *Result:* —

- [ ] **2b.5 [AI]** Add "Center" name input to `client/src/views/StarList.ts`:
      on search, resolve center name → coordinates via a `/api/stars/by-name`
      call, then pass `center_x_pc/y_pc/z_pc` in the search params.
      *Result:* —

- [ ] **2b.6 [AI]** Shift the Three.js scene origin in `StarMap.ts` to the center
      star's position so the map renders centred on the chosen star.
      *Result:* —

- [ ] **2b.7 [AI]** Run `pnpm test`. All tests green. Report output.
      *Result:* —

- [ ] **2b.8 [AI]** Post ready-for-review summary.
      *Result:* —

- [ ] **2b.9 [HUMAN]** Read diff + run `pnpm dev` to confirm centre behaviour.
      *Result:* —

- [ ] **2b.10 [HUMAN]** **Approve commit** *(double-approval gate).*
      *Result:* —

- [ ] **2b.11 [AI]** Pre-commit triage + commit `green:`. Report hash.
      *Result:* —

---

## Slice 3 — HTTP integration tests

Goal: test the three star endpoints via `app.request()` against real Meridian data.
Confirm the G-006 regression is covered at the HTTP level.

- [ ] **3.1 [AI]** Write `server/src/routes/stars.http.test.ts`.
      `beforeAll`: import and call `buildIndex()`.

      Tests to include:

      | Test | Request | Assert |
      |---|---|---|
      | Shape: star list | `GET /api/stars?limit=5` | `{ total: number, rows: StarListRow[] }` shape; `rows.length ≤ 5` |
      | Name filter | `GET /api/stars?name=Sol&limit=10` | at least one row with `name` containing "Sol" |
      | Distance filter | `GET /api/stars?dist_max_pc=2&limit=100` | all returned rows have `dist_pc ≤ 2` |
      | Coordinate units (G-007) | `GET /api/stars?name=Sol&limit=1` | `x_pc`, `y_pc`, `z_pc` all `≈ 0` (Sol at origin); none are in the thousands |
      | **G-006 regression** | `GET /api/stars?spectral=G&dist_max_pc=30&limit=100` | `total === rows.length`; all `primary_spectral` start with `"G"` |
      | By-name redirect | `GET /api/stars/by-name?name=Sol` | status 302; `Location` header contains `/api/stars/` |
      | System detail shape | `GET /api/stars/by-name?name=Sol` then follow redirect | `SystemDetail` shape with `stars` and `bodies` arrays |
      | System not found | `GET /api/stars/AAAAAAAA-0000-0000-0000-000000000000` | status 404 |
      | Missing name param | `GET /api/stars/by-name` | status 400 |

      *Result:* —

- [ ] **3.2 [AI]** Run `pnpm test`. Confirm Slice 3 tests fail (expected — functions
      exist but tests may expose integration issues). Post failure summary.
      *Result:* —

- [ ] **3.3 [AI]** Fix any failures that are bugs (not test-setup issues). If a fix
      requires a new failing-test-first cycle, do so and note it.
      *Result:* —

- [ ] **3.4 [AI]** Run `pnpm test`. All tests green. Post output.
      *Result:* —

- [ ] **3.5 [AI]** Post ready-for-review summary for Slice 3.
      *Result:* —

- [ ] **3.6 [HUMAN]** Read the diff and test output.
      *Result:* —

- [ ] **3.7 [HUMAN]** **Approve commit** *(double-approval gate).*
      *Result:* —

- [ ] **3.8 [AI]** Commit `green:`. Report hash.
      *Result:* —

---

## Slice 4 — Manual smoke test

Goal: a human walks the golden path and two edge cases in the running app.

- [ ] **4.1 [AI]** Post the smoke-test procedure (see below). Do not proceed to 4.2
      until the user confirms they are ready.
      *Result:* —

```
Smoke-test procedure

Setup: pnpm server (port 3000) + pnpm client (port 5173) both running.

Golden path:
  1. Load http://localhost:5173  — app appears, #stars view active.
  2. Default search fires (30 pc max dist). Table populates with named systems.
     Status shows "N systems" for some N > 0.
  3. Click "Display". Map appears — point cloud visible, Sol crosshair at origin.
     Rotate and zoom: controls work.
  4. Click "List". Table returns; "Display" button visible again.
  5. Click any row in the table. Hash changes to #system; system view loads
     (may show "Loading…" then orbit diagram or an error — either is acceptable
     at this stage; orbit MVP is separate). Back button returns to #stars.

Spectral filter (G-006 regression):
  6. Enter "G" in the Spectral field. Click Search.
     Status count appears. All rows in the table show a spectral class starting
     with G. Spot-check 5 rows.

Edge cases:
  7. Search for a name that does not exist ("zzzzz"). Status shows "0 systems".
     Table is empty. No error in console.
  8. Search with max dist = 0. Status shows "0 systems" or "1 system" (Sol at 0).
     No crash.
```

- [ ] **4.2 [HUMAN]** Walk the smoke-test. Record each step's result inline above
      (pass / fail / unexpected behaviour). Report any regressions.
      *Result:* —

- [ ] **4.3 [AI]** Triage any failures reported in 4.2: is each a bug requiring a
      red test first, or polish? Post triage list.
      *Result:* —

- [ ] **4.4 [HUMAN]** Approve the triage (or redirect).
      *Result:* —

- [ ] **4.5 [AI]** If bugs: write red tests, get approval, fix, turn green, commit
      `green:`. If polish only: apply and commit with a plain message.
      *Result:* —

---

## Slice 5 — Sign-off

Goal: confirm all DoD items, verify integration seams, update HANDOVER, write retro.

- [ ] **5.1 [AI]** Run `pnpm test` from root. Report: pass count per workspace,
      total time, any failures.
      *Result:* —

- [ ] **5.2 [AI]** Integration seam verification — confirm each item unchanged.
      Post a table with status (✓ / ✗) for every item in Plan §3:

      | Seam | Status |
      |---|---|
      | `StarListRow.system_id` type is `string` | — |
      | `StarListRow.x_pc/y_pc/z_pc` are parsecs (not mpc) | — |
      | `StarListResponse` shape `{ total, rows }` | — |
      | `SystemDetail` shape with `stars[]` and `bodies[]` | — |
      | `GET /api/stars` endpoint at this path | — |
      | `GET /api/stars/by-name` → 302 | — |
      | `GET /api/stars/:id` → `SystemDetail` or 404 | — |
      | `GET /health` → `{ ok: true }` | — |
      | `selectedSystemId` signal type `string \| null` | — |
      | Row click → `selectedSystemId.set` → `#system` hash | — |
      | Server port default 3000 | — |
      | CORS middleware present | — |

      *Result:* —

- [ ] **5.3 [AI]** DoD checklist sweep (from Plan §7). Mark each item green or note
      the explicit waiver with reason.
      *Result:* —

- [ ] **5.4 [AI]** Draft slice retro: what surprised me / what worked / what I'd
      change. Keep it to one paragraph per item; three items maximum.
      *Result:* —

- [ ] **5.5 [AI]** Update [HANDOVER.md](../../HANDOVER.md):
      - Close G-002, G-006, G-007 in the gap register (commit hash, date)
      - Add a "Star List + Map — MVP complete" section noting what is tested
        and what seams are guaranteed stable
      *Result:* —

- [ ] **5.6 [HUMAN]** Review DoD checklist, seam table, retro, and HANDOVER update.
      Approve or call out anything that needs more work.
      *Result:* —

- [ ] **5.7 [HUMAN]** **MVP sign-off** *(double-approval gate).*
      *Result:* —

- [ ] **5.8 [AI]** Pre-commit triage for final state.
      *Result:* —

- [ ] **5.9 [HUMAN]** **Approve final commit** *(double-approval gate).*
      *Result:* —

- [ ] **5.10 [AI]** Commit. Report hash. Star List + Map MVP complete.
      *Result:* —

---

## Deferred / carry-overs

*Record anything decided not to do here (with one-line reason) so the next phase
can pick it up.*

- G-004 (input validation, star routes) — deferred; no parsing bugs in practice,
  lower priority than other components.
- Map raycasting / click-to-navigate — deferred; requires Three.js raycaster wiring
  and a dependency on `SystemView`; belongs in Orbit Display MVP.
- `age_gyr` always null — not a bug, blocked on Meridian data; leave field.
- Pagination UI in client — deferred; 500-row cap is sufficient for MVP usage.
