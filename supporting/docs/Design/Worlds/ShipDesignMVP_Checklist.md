# Ship Design Tool — MVP Checklist

Execution record for the Ship Design Tool MVP.
Design authority: [ShipDesignMVP_Plan.md](ShipDesignMVP_Plan.md).
Working-style rules (double-approval gate, test-first, etc.): [HANDOVER.md](../../HANDOVER.md).

**Legend.** `[AI]` = Claude does it. `[HUMAN]` = user does it.

**Double-approval gate** — at every `[HUMAN]` approval step, Claude echoes
the specific next action and waits for a second explicit yes before acting.
Applies to `pnpm add`, `git commit`, DB mutations, and structural refactors.

**Commit convention.** `red:` prefix for commits with intentionally failing
tests. `green:` prefix for commits that turn them green.

---

## Slice 0 — Schema migrations + SQL files

Goal: Both migrations applied to the live DB and reflected in `schema.sql`.
`seed.sql` regenerated. All three files committed.

**Migration 001** — `ship_system_slots.system_id` nullable (table recreation).
**Migration 002** — `ships.description` and `ships.image_path` columns added (ADD COLUMN).

- [ ] **0.1 [AI]** Write `supporting/sql/migrations/001_nullable_slot_system_id.sql`.
      Write `supporting/sql/migrations/002_ships_description_image.sql`.
      Post both for review — do not apply yet.

- [ ] **0.2 [HUMAN]** Review both migration files.

- [ ] **0.3 [HUMAN]** Approve applying both migrations to live DB *(double-approval gate).*

- [ ] **0.4 [AI]** Apply migration 001 then 002 to `/Users/lentulus/databases/world.db`
      via `sqlite3`. Verify row counts unchanged after each.

- [ ] **0.5 [AI]** Update `supporting/sql/schema.sql` to reflect both changes.
      Regenerate `supporting/sql/seed.sql` from the live DB.

- [ ] **0.6 [HUMAN]** Approve commit *(double-approval gate).*

- [ ] **0.7 [AI]** Commit: `schema: nullable slot system_id + ships description/image (migrations 001–002)`.

---

## Slice 1 — G-001 fix: power points derived correctly

Goal: `ShipDesign.power_points_available` reflects the actual PP from
installed power plants. Test-first.

- [ ] **1.1 [AI]** Add `power_points: number | null` to `SlotDetail` in `packages/shared/src/types.ts`.

- [ ] **1.2 [AI]** Write a red test in a new `server/src/db/ships.test.ts`:
      - Load the *Midnight Sun* orbital shuttle (ship_id 3, has a fusion reactor slot).
      - Assert `power_points_available > 0`.
      Report the red result.

- [ ] **1.3 [HUMAN]** Review red test.

- [ ] **1.4 [AI]** Fix `getShip()` in `server/src/db/ships.ts`:
      - Join `system_sm_stats` on the slot query to fetch `power_points` per slot.
      - Sum `power_points` across power plant slots for `power_points_available`.

- [ ] **1.5 [AI]** Run `pnpm test`. Confirm new test green, all 28 existing tests still green.

- [ ] **1.6 [HUMAN]** Approve commit *(double-approval gate).*

- [ ] **1.7 [AI]** Commit: `green: fix G-001 — derive power_points_available from installed power plants`.

---

## Slice 2 — Slot grid shows all 20 positions

Goal: The slot grid always renders 20 positions (front [1–6]+[core],
central [1–6]+[core], rear [1–6]), populated where the ship has installed
systems and blank otherwise. No DB changes.

- [ ] **2.1 [AI]** Update `client/src/components/SlotGrid.ts`:
      - Generate the 20 canonical positions for any SM hull.
      - Overlay `ship.slots` data onto the matching position.
      - Empty positions render as unoccupied drop targets.

- [ ] **2.2 [HUMAN]** Review the updated slot grid in the browser.

- [ ] **2.3 [HUMAN]** Approve commit *(double-approval gate).*

- [ ] **2.4 [AI]** Commit: `feat: slot grid renders all 20 hull positions`.

---

## Slice 3 — Slot assignment and detail text

Goal: Dragging a catalog entry onto a slot assigns the system and prompts
for a detail string. An "empty" marker clears the slot. Changes persist
via the existing `PUT /api/ships/:id/slots` endpoint.

- [ ] **3.1 [AI]** Add an empty-slot marker to the catalog panel (or a clear button on
      occupied slots) so the user can remove a system.

- [ ] **3.2 [AI]** On drop: show an inline text input pre-filled with a sensible default
      from the system's stats (e.g. cargo tons, acceleration, cabin count). User
      confirms or edits, then the full slot list is PUT to the server.

- [ ] **3.3 [AI]** Update `server/src/db/ships.ts` — `updateSlots` must accept
      `system_id: null` for empty slots (now that the column is nullable).

- [ ] **3.4 [HUMAN]** Test in browser: assign systems to all 20 slots of a new ship,
      enter details, reload the page, confirm persistence.

- [ ] **3.5 [HUMAN]** Approve commit *(double-approval gate).*

- [ ] **3.6 [AI]** Commit: `feat: slot assignment with detail text entry`.

---

## Slice 4 — All derived stats

Goal: Whenever slots change, the server recomputes all derivable stats and
returns them with `getShip()`. The stats panel shows derived values. Derivation
rules from SS1 pp. 34–35; see plan for full formulas.

Stats to derive:

| Stat | Source |
|---|---|
| `cost_derived` | Sum `system_sm_stats.cost_dollars` + `armor_sm_stats.cost_dollars` per slot |
| `crew_derived` | Sum `system_sm_stats.workspaces` per slot |
| `pp_available` | Sum `system_sm_stats.power_points` from power plant slots |
| `pp_consumed` | Count `is_high_energy = 1` slots |
| `ddr_front_derived` | Sum `armor_sm_stats.ddr_us/sl` for front-section armor slots |
| `ddr_central_derived` | Sum for central-section armor slots |
| `ddr_rear_derived` | Sum for rear-section armor slots |
| `accel_derived` | Sum `system_sm_stats.acceleration_g` from drive slots |
| `delta_v_derived` | Drive's `delta_v_mps_per_tank` × fuel tank count (reaction); null (reactionless) |
| `ht_derived` | 13 − engine room check − automation check + industrial system check |

- [ ] **4.1 [AI]** Extend `SlotDetail` shared type with `acceleration_g`, `delta_v_mps_per_tank`,
      `ddr_us`, `ddr_sl`, `category` fields. Extend `ShipDesign` shared type with all
      `*_derived` fields listed above.

- [ ] **4.2 [AI]** Write red tests in `server/src/db/ships.test.ts`:
      - For a ship with known steel armor slots: assert `ddr_front_derived` matches table value.
      - For a ship with a known drive + fuel tanks: assert `accel_derived` and
        `delta_v_derived` match expected values.
      - For a known SM+5–9 ship without engine room: assert `ht_derived = 12`.
      Report the red results.

- [ ] **4.3 [HUMAN]** Review red tests.

- [ ] **4.4 [AI]** Extend `getShip()` slot query to fetch all required stat columns from
      `system_sm_stats` and `armor_sm_stats`. Compute all derived fields in
      `getShip()`. Return them in the `ShipDesign` response.

- [ ] **4.5 [AI]** Update the stats panel in `client/src/views/ShipDesign.ts` to display
      all derived values (replacing any placeholder zeros).

- [ ] **4.6 [AI]** Run `pnpm test`. Confirm all new tests green, all prior tests green.

- [ ] **4.7 [HUMAN]** Approve commit *(double-approval gate).*

- [ ] **4.8 [AI]** Commit: `green: Slice 4 — derive all stats from installed systems`.

---

## Slice 5 — Override inputs, description, and image

Goal: The stats panel exposes override fields for all derived stats, a description
textarea, and an image attachment area. All three persist to the DB/filesystem.

- [ ] **5.1 [AI]** Add override input fields to the stats panel for:
      `move_accel_g`, `move_delta_v_mps`, `ddr_front`, `ddr_central`, `ddr_rear`, `ht`.
      Each field shows the current override value (or blank if auto-derived).
      A "Save overrides" button calls the existing ship update endpoint.
      Derived value shown as `← N` beside each input so the user knows the
      auto-derived result.

- [ ] **5.2 [AI]** Add a Description textarea below the override section.
      Saves to `ships.description` on the same update endpoint.

- [ ] **5.3 [AI]** Add image endpoints to the server:
      `GET /api/ships/:id/image` — serves the file from `server/data/ship-images/`.
      `POST /api/ships/:id/image` — accepts `multipart/form-data`, writes file,
      updates `ships.image_path`.
      `DELETE /api/ships/:id/image` — removes file, clears `ships.image_path`.
      Create `server/data/ship-images/` directory (git-ignored for binaries;
      add a `.gitkeep`).

- [ ] **5.4 [AI]** Add the image drop/upload zone to the stats panel below Description.
      On file select: POST to image endpoint; display preview on success.
      "Remove image" link: DELETE to image endpoint; revert to placeholder.
      On load: if `ship.image_path` is set, show `<img src="/api/ships/:id/image">`.

- [ ] **5.5 [HUMAN]** Test in browser:
      - Enter a dDR override; save; reload — override persists; clear it — auto value returns.
      - Type a description; save; reload — description persists.
      - Upload an image; reload — image shows. Remove it — placeholder returns.

- [ ] **5.6 [HUMAN]** Approve commit *(double-approval gate).*

- [ ] **5.7 [AI]** Commit: `feat: override inputs, description, and image attachment`.

---

## Slice 6 — Ship list filters

Goal: The ship list toolbar exposes TL range, SM, type, and military filters.
All filter params already exist on the server.

- [ ] **6.1 [AI]** Add filter controls to `client/src/views/ShipDesign.ts`:
      TL (min/max), SM, type (text), military (checkbox).
      Wire to `fetchShips()`.

- [ ] **6.2 [HUMAN]** Test in browser: filter to TL 11 military ships, confirm results.

- [ ] **6.3 [HUMAN]** Approve commit *(double-approval gate).*

- [ ] **6.4 [AI]** Commit: `feat: ship list filter controls`.

---

## Slice 7 — Smoke test and sign-off

Goal: Golden-path walkthrough confirms all MVP features work end-to-end.

- [ ] **7.1 [HUMAN]** Start server and client. Open Ship Design view.

- [ ] **7.2 [HUMAN]** Browse imported ships: filter to TL 9 civilian ships. Select the
      *Midnight Sun* orbiter. Confirm stats and slots display correctly.

- [ ] **7.3 [HUMAN]** Create a new SM+8 TL11 ship. Assign all 20 slots to match the
      *Star Flower*-class layout from SS1 p.6. Enter slot details.
      Confirm cost, PP budget, dDR, acceleration, and crew auto-update correctly.

- [ ] **7.4 [HUMAN]** Enter an acceleration override (e.g. 2G). Save. Reload. Confirm override
      persists and the auto-derived value is shown for reference. Clear override, confirm
      auto-derived value reinstates.

- [ ] **7.5 [HUMAN]** Delete the test ship. Confirm it disappears from the list.

- [ ] **7.6 [HUMAN]** Sign-off: Ship Design Tool MVP is complete.

- [ ] **7.7 [HUMAN]** Approve final commit *(double-approval gate).*

- [ ] **7.8 [AI]** Update `HANDOVER.md` to mark Ship Design Tool MVP complete.
      Commit: `green: Ship Design Tool MVP complete`.
