# Ship Design Tool — MVP Plan

*2026-05-27. Companion to [ShipDesignMVP_Checklist.md](ShipDesignMVP_Checklist.md).*

---

## 1. MVP scope

**In scope — everything needed to call this component done:**

- Browse and filter the 195 imported ships by TL, SM, type, and military flag
- View any ship's full stats and slot layout
- Create a new ship design from scratch: pick SM, TL, streamlined flag, name
- Slot grid shows all 20 positions regardless of what is installed
- Assign a system to any slot by dragging from the system catalog
- Clear a slot by dragging an "empty" placeholder onto it
- Enter and edit detail text per slot (e.g. "50 tons capacity", "1G acceleration")
- Auto-derived stats updated whenever slots change (see derivation rules below):
  - `cost_dollars` — sum of slot costs at the ship's SM
  - `power_points_available` — sum of `power_points` from power plant slots
  - `power_points_consumed` — count of installed high-energy (`[!]`) slots
  - `occ_crew` — sum of `workspaces` from all installed systems
  - `ddr_front`, `ddr_central`, `ddr_rear` — sum of armor slot dDR per hull section
  - `move_accel_g` — sum of drive slot `acceleration_g` at ship's SM
  - `move_delta_v_mps` — drive's `delta_v_mps_per_tank` × fuel tank count (reaction drives); null for reactionless
  - `ht` — base 13 with engine room and automation adjustments
- Manual override for all derived stats: if the ship record holds a non-null value
  for any derived field, that value is used instead of the computed result; setting
  the field to null reverts to auto-derive. The stats panel shows derived and override
  values side by side.
- Power points displayed (available vs consumed); budget is informational only, not enforced
- Free-text description (markdown) in `ships.description` — narrative, design rationale, variants
- Optional image attachment stored as a file, path recorded in `ships.image_path`
- Delete a ship design

**Out of scope for this MVP:**

- Input validation on server POST/PUT bodies (G-005 — deferred)
- Delta-V derivation for ships with mixed reaction drive types (requires per-tank fuel assignment)
- Backfilling slot data for the 195 imported ships (data-entry work, not code)
- Design feature assignment UI (design features exist in DB; no UI planned at MVP)
- Multi-stage ships / upper stage links
- Ship fate and dates

---

## 2. Known gaps to resolve

| ID | Description | Where |
|---|---|---|
| **G-001** | `power_points_available` always returns 0 — placeholder reduce | `server/src/db/ships.ts:134–136` |
| **Schema-M01** | `ship_system_slots.system_id NOT NULL` — prevents representing empty slot positions | `supporting/sql/schema.sql` + live DB |
| **Schema-M02** | `ships` table missing `description TEXT` and `image_path TEXT` columns | `supporting/sql/schema.sql` + live DB |

G-005 (input validation) is deferred as noted above.

### G-001 fix strategy

In `getShip()`, replace the placeholder `reduce` with a SQL join to `system_sm_stats` on the slot query and sum `power_points` across power plant slots:

```typescript
const ppAvail = slots
  .filter(s => s.system_name?.toLowerCase().includes('power plant'))
  .reduce((sum, s) => sum + (s.power_points ?? 0), 0);
```

This requires `power_points` to be included in the `SlotDetail` type and fetched
in the `getShip` slot query via a join to `system_sm_stats`.

### Schema-M01 fix strategy

SQLite does not support `ALTER COLUMN`, so the migration recreates the table:

```sql
-- Migration 001
CREATE TABLE ship_system_slots_new (
    slot_id INTEGER PRIMARY KEY,
    ship_id INTEGER NOT NULL REFERENCES ships(ship_id),
    hull_section TEXT NOT NULL CHECK(hull_section IN ('front','central','rear')),
    slot_number INTEGER,
    slot_to INTEGER,
    is_core INTEGER NOT NULL DEFAULT 0,
    is_high_energy INTEGER NOT NULL DEFAULT 0,
    system_id INTEGER REFERENCES ship_system_catalog(system_id),
    detail TEXT
);
INSERT INTO ship_system_slots_new SELECT * FROM ship_system_slots;
DROP TABLE ship_system_slots;
ALTER TABLE ship_system_slots_new RENAME TO ship_system_slots;
```

Apply to the live DB and update `schema.sql`.

---

## 3. Derivation rules (from GURPS Spaceships 1, pp. 34–35)

These rules govern what the server computes from slot contents. All lookups
are at the ship's SM using `system_sm_stats` or `armor_sm_stats`.

### dDR

> "Add up the cumulative dDR from the spaceship's armor systems protecting each
> hull section. Record front dDR, central dDR, and rear dDR, separated by slashes."

- **Streamlined hull**: use `armor_sm_stats.ddr_sl`
- **Unstreamlined hull**: use `armor_sm_stats.ddr_us`
- Multiple armor systems in the same section: dDR values add
- A section with no armor slots: dDR = 0
- Fully derivable from slot contents with no judgment required.

### Acceleration (move_accel_g)

- Each drive slot contributes its `system_sm_stats.acceleration_g` at the ship's SM.
- Total acceleration = sum of all drive slots' `acceleration_g`.
- Fully derivable for any ship with a single drive category (reactionless or reaction).
- For mixed drive categories, derived values are shown per-category in notes; override
  field holds the figure the designer chooses for the primary operating mode.

### Delta-V (move_delta_v_mps)

For **reaction drives**:
- Each drive type has `system_sm_stats.delta_v_mps_per_tank`.
- Count the number of Fuel Tank slots installed.
- Total delta-V = `delta_v_mps_per_tank × fuel_tank_count`.
- Derivable for ships with one reaction drive type and no mixed-propellant complexity.

For **reactionless drives**:
- No fuel is consumed; delta-V is effectively unlimited.
- Record as null in `move_delta_v_mps`; display as "unlimited (/c)" in the UI.

For **FTL / stardrive** systems:
- FTL range is stored in `ships.range_ftl` (text); not derived from slots.

### HT

> "This starts at HT 13. Reduce HT by 1 for the following: if the vessel has
> SM +5–9 with no engine room; if using high or total automation at TL7–9.
> Add +1 to HT if it has at least one robofac, nanofactory, fabricator, or
> replicator system aboard."

Derivation:
- Base = 13
- −1 if `ship.sm` in [5..9] AND no engine room system slot is installed
- −1 if the ship has a High Automation or Total Automation design feature AND `ship.tl` ≤ 9
- +1 if any slot contains a robofac, nanofactory, fabricator, or replicator system

The engine room check and the industrial system check are fully resolvable from
slot contents. The automation check requires `ship_design_features` (already in
the DB). Derivable, but lower priority than dDR/move; HT changes rarely.

### Cost

> "Total up the cost of all systems, design features, and switches."

- Sum `system_sm_stats.cost_dollars` for all non-armor slots at ship's SM
- Sum `armor_sm_stats.cost_dollars` for all armor slots at ship's SM
- Fully derivable.

### Crew (occ_crew)

- Sum `system_sm_stats.workspaces` for all installed slots at ship's SM.
- Fully derivable.

---

## 4. Architecture decisions (do not re-litigate)

- **Slot positions are client-generated, not stored.** The server stores only
  installed systems (`ship_system_slots` rows). The client generates all 20
  positions from the hull shape and overlays installed systems on top. Empty
  positions are never written to the DB.
- **All derivable stats are computed server-side.** `getShip()` performs the
  cost, PP, crew, dDR, acceleration, delta-V, and HT computations. The client
  displays what the server returns.
- **Override beats derived.** If a ship record holds a non-null value in any
  of the derived stat columns, that value is used as-is; the derived value is
  shown alongside it as a reference. Setting a field to null reinstates
  auto-derivation. This makes every imported ship editable without forcing a
  full slot backfill first.
- **Catalog drag-and-drop is the primary assignment interaction.** The catalog
  panel groups systems by category. The user drags a catalog entry onto a slot.
  A detail-text prompt follows immediately.
- **Description is `ships.description TEXT`.** New column added via migration
  002. Markdown-capable free-text for narrative, design rationale, variants.
  Distinct from `ships.notes` (operational notes, already exists).
- **Images are stored as files, not blobs.** `ships.image_path TEXT` records a
  filename relative to `server/data/ship-images/`. The server exposes three
  endpoints: `GET /api/ships/:id/image` (serve), `POST /api/ships/:id/image`
  (multipart upload), `DELETE /api/ships/:id/image` (remove and clear path).
  Keeping binaries out of SQLite avoids DB bloat and simplifies backup.
- **Three-panel layout.** Approved and prototyped. Ship list + filters left;
  slot grid + catalog centre; stats + overrides + description + image right.
  See [ShipDesignMVP_Prototype.html](ShipDesignMVP_Prototype.html) and
  [ShipDesignMVP_UI.md](ShipDesignMVP_UI.md).

---

## 5. Data model additions

### DB schema (migrations)

**Migration 001** — `ship_system_slots.system_id` nullable (table recreation required):

```sql
CREATE TABLE ship_system_slots_new ( ... system_id INTEGER REFERENCES ... );
INSERT INTO ship_system_slots_new SELECT * FROM ship_system_slots;
DROP TABLE ship_system_slots;
ALTER TABLE ship_system_slots_new RENAME TO ship_system_slots;
```

**Migration 002** — description and image columns on `ships` (simple ADD COLUMN; SQLite supports this for nullable columns):

```sql
ALTER TABLE ships ADD COLUMN description TEXT;
ALTER TABLE ships ADD COLUMN image_path  TEXT;
```

`image_path` stores a bare filename (e.g. `42.jpg`); the server resolves it to
`server/data/ship-images/<filename>` and exposes it via `/api/ships/:id/image`.

### Shared types

`SlotDetail` gains fields needed for server-side derivation:

```typescript
interface SlotDetail {
  // existing fields ...
  power_points: number | null;         // from system_sm_stats
  acceleration_g: number | null;       // from system_sm_stats; null for non-drives
  delta_v_mps_per_tank: number | null; // from system_sm_stats; null for non-reaction drives
  ddr_us: number | null;               // from armor_sm_stats; null for non-armor
  ddr_sl: number | null;               // from armor_sm_stats; null for non-armor
  category: string;                    // from ship_system_catalog
}
```

`ShipDesign` gains derived fields and new ship-level fields:

```typescript
interface ShipDesign {
  // existing DB columns (used as overrides when non-null):
  //   move_accel_g, move_delta_v_mps, ddr_front, ddr_central, ddr_rear,
  //   ht, cost_dollars, occ_crew

  // new DB columns (migration 002):
  description: string | null;
  image_path: string | null;

  // computed by server on every getShip() call, never stored:
  accel_derived: number | null;
  delta_v_derived: number | null;
  ddr_front_derived: number | null;
  ddr_central_derived: number | null;
  ddr_rear_derived: number | null;
  ht_derived: number | null;
  cost_derived: number | null;
  crew_derived: number | null;
  pp_available: number | null;
  pp_consumed: number | null;
}
```

The client always displays the `_derived` field; if the corresponding override
column is non-null it is shown in the override input alongside the derived reference.

---

## 6. Implementation slices

| Slice | Goal | Key deliverables |
|---|---|---|
| **0** | Schema migration + SQL files committed | `schema.sql` updated, migration applied to live DB, `seed.sql` regenerated |
| **1** | G-001 fix — power points derived correctly | Red test → green; `SlotDetail.power_points` added |
| **2** | Slot grid shows all 20 positions | Client generates positions; installed systems overlay; empty slots visible |
| **3** | Slot assignment + detail text | Drop to assign; prompt for detail; drag empty marker to clear |
| **4** | All derived stats | Server computes cost, crew, PP, dDR, acceleration, delta-V, HT from slots; stats panel shows derived values and override inputs |
| **5** | Override inputs | Stats panel override fields: clear to revert to derived; save persists to DB columns |
| **6** | Ship list filters | TL, SM, type, military filter controls wired to existing server params |
| **7** | Smoke test + sign-off | All `[HUMAN]` checklist steps |

---

## 7. Definition of done

All of the following must be true before the Ship Design Tool is called MVP-complete:

- [ ] 28 existing tests still green; new tests written for derived stat math
- [ ] Any imported ship can be selected and its stats and slots displayed
- [ ] A new ship can be created, all 20 slots assigned, and a detail saved per slot
- [ ] Cost, PP budget, dDR, acceleration, delta-V, and crew count display correctly
  for a known design (verified against the *Star Flower*-class Tramp Freighter from SS1 p.6)
- [ ] Override values persist and suppress auto-derivation; clearing restores it
- [ ] Ship can be deleted without orphaned slot rows
- [ ] `schema.sql` and `seed.sql` match the live database exactly
