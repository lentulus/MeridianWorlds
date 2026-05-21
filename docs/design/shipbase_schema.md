# shipbase.db — Schema

**File:** `meridian/VolatileData/shipbase.db`  
**Source:** `docs/spaceships/spaceship_schema.md` (GURPS Spaceships 1–8)

---

## Structure

Three layers:

| Layer | Tables | Mutability |
|-------|--------|------------|
| Reference | `hull_sizes`, `ship_types`, `design_bureaus`, `ship_fates`, `design_features`, `ship_system_catalog`, `system_sm_stats`, `armor_sm_stats` | Immutable — from rulebooks |
| Class tombstone | `ship_class`, `class_system_slots`, `class_design_features` | Static per class once designed |
| Instance | `ship`, `ship_state` | `ship` mostly static (lifecycle); `ship_state` time-series |

The tombstone is a complete design record — SM, TL, systems, armor, performance. All ships
of the same class reference one tombstone. Individual hulls add hull number, name, builder,
and lifecycle dates. State tracks where a hull is and what condition it is in over sim time.

---

## Reference tables

Identical to `spaceship_schema.md`; reproduced here so shipbase.db is self-contained.

```sql
CREATE TABLE IF NOT EXISTS hull_sizes (
    sm               INTEGER PRIMARY KEY,  -- +5 to +15
    mass_tons        INTEGER NOT NULL,
    length_yards     INTEGER NOT NULL,
    dst_hp           INTEGER NOT NULL,
    handling         INTEGER NOT NULL,
    stability_rating INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS ship_types (
    type_id  INTEGER PRIMARY KEY,
    name     TEXT    NOT NULL,
    military INTEGER NOT NULL DEFAULT 0 CHECK (military IN (0, 1))
);

CREATE TABLE IF NOT EXISTS design_bureaus (
    bureau_id  INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    short_code TEXT,
    notes      TEXT
);

CREATE TABLE IF NOT EXISTS ship_fates (
    fate_id INTEGER PRIMARY KEY,
    name    TEXT NOT NULL,
    notes   TEXT
);
INSERT OR IGNORE INTO ship_fates (name) VALUES
    ('Scrapped'), ('Lost in combat'), ('Lost — accident'),
    ('Converted'), ('Mothballed'), ('Captured'), ('Expended'), ('Unknown');

CREATE TABLE IF NOT EXISTS design_features (
    feature_id     INTEGER PRIMARY KEY,
    name           TEXT    NOT NULL,
    feature_type   TEXT    NOT NULL CHECK (feature_type IN ('feature', 'switch')),
    tl_min         INTEGER,
    is_superscience INTEGER NOT NULL DEFAULT 0 CHECK (is_superscience IN (0, 1)),
    description    TEXT
);

CREATE TABLE IF NOT EXISTS ship_system_catalog (
    system_id      INTEGER PRIMARY KEY,
    name           TEXT    NOT NULL,
    category       TEXT    NOT NULL,
    tl_min         INTEGER,
    is_superscience INTEGER NOT NULL DEFAULT 0 CHECK (is_superscience IN (0, 1)),
    location       TEXT    NOT NULL DEFAULT 'ANY'
                           CHECK (location IN ('ANY','HULL','FRONT','REAR','SPECIAL')),
    is_high_energy INTEGER NOT NULL DEFAULT 0 CHECK (is_high_energy IN (0, 1)),
    repair_skill   TEXT,
    notes          TEXT
);

CREATE TABLE IF NOT EXISTS system_sm_stats (
    stat_id                    INTEGER PRIMARY KEY,
    system_id                  INTEGER NOT NULL REFERENCES ship_system_catalog(system_id),
    sm                         INTEGER NOT NULL,
    workspaces                 INTEGER,
    cost_dollars               REAL,
    capacity_tons              REAL,
    launch_rate_tons           REAL,
    fuel_tons                  REAL,
    seats                      INTEGER,
    cabins                     INTEGER,
    areas                      INTEGER,
    control_stations           INTEGER,
    computer_complexity        INTEGER,
    comm_sensor_level_offset   INTEGER,
    power_points               INTEGER,
    acceleration_g             REAL,
    delta_v_mps_per_tank       REAL,
    output_per_hour_dollars    REAL,
    output_per_hour_lbs        REAL,
    mining_tons_per_hour       REAL,
    refinery_tons_per_hour     REAL,
    max_tonnage                REAL,
    force_screen_ddr           INTEGER,
    cost_variant               TEXT,
    stat_notes                 TEXT
);

CREATE TABLE IF NOT EXISTS armor_sm_stats (
    stat_id    INTEGER PRIMARY KEY,
    system_id  INTEGER NOT NULL REFERENCES ship_system_catalog(system_id),
    sm         INTEGER NOT NULL,
    ddr_us     INTEGER NOT NULL,
    ddr_sl     INTEGER,
    cost_dollars REAL NOT NULL
);
```

---

## Class tombstone

### ship_class

One row per ship class (or sub-variant where stats differ — e.g. booster vs. orbiter of
the same design get separate rows linked via `parent_class_id`).

```sql
CREATE TABLE IF NOT EXISTS ship_class (
    class_id         INTEGER PRIMARY KEY,
    class_name       TEXT    NOT NULL,
    type_id          INTEGER REFERENCES ship_types(type_id),
    bureau_id        INTEGER REFERENCES design_bureaus(bureau_id),
    parent_class_id  INTEGER REFERENCES ship_class(class_id),
    -- ^ for multi-stage designs (booster → orbiter)

    tl               INTEGER NOT NULL,
    is_superscience  INTEGER NOT NULL DEFAULT 0 CHECK (is_superscience IN (0, 1)),
    sm               INTEGER NOT NULL REFERENCES hull_sizes(sm),
    is_streamlined   INTEGER NOT NULL DEFAULT 0 CHECK (is_streamlined IN (0, 1)),

    -- Hull stats
    dst_hp           INTEGER NOT NULL,
    handling         INTEGER NOT NULL,
    stability_rating INTEGER NOT NULL,
    ht               INTEGER,

    -- Performance
    move_accel_g     REAL,    -- NULL if no space drive
    move_delta_v_mps REAL,    -- NULL if FTL or no drive
    move_is_ftl      INTEGER  NOT NULL DEFAULT 0 CHECK (move_is_ftl IN (0, 1)),
    move_atm_only    INTEGER  NOT NULL DEFAULT 0 CHECK (move_atm_only IN (0, 1)),
    range_ftl        TEXT,    -- e.g. '2×'; NULL if no FTL

    -- Mass and capacity
    lwt_tons         REAL,
    load_tons        REAL,

    -- Occupancy
    occ_crew              INTEGER,
    occ_passengers        INTEGER,
    occ_has_artificial_grav INTEGER NOT NULL DEFAULT 0 CHECK (occ_has_artificial_grav IN (0, 1)),
    occ_is_short_voyage    INTEGER NOT NULL DEFAULT 0 CHECK (occ_is_short_voyage IN (0, 1)),

    -- Armor (derived from system slots but stored for fast query)
    ddr_front        INTEGER,
    ddr_central      INTEGER,
    ddr_rear         INTEGER,

    cost_dollars     REAL,
    notes            TEXT    -- Markdown; design history, source book reference, footnotes
);
```

### class_system_slots

The 20 installed systems for a class design.

```sql
CREATE TABLE IF NOT EXISTS class_system_slots (
    slot_id       INTEGER PRIMARY KEY,
    class_id      INTEGER NOT NULL REFERENCES ship_class(class_id) ON DELETE CASCADE,
    hull_section  TEXT    NOT NULL CHECK (hull_section IN ('front','central','rear')),
    slot_number   INTEGER,          -- 1–6; NULL if core slot
    slot_to       INTEGER,          -- for spans: slot_number–slot_to are identical
    is_core       INTEGER NOT NULL DEFAULT 0 CHECK (is_core IN (0, 1)),
    is_high_energy INTEGER NOT NULL DEFAULT 0 CHECK (is_high_energy IN (0, 1)),
    system_id     INTEGER NOT NULL REFERENCES ship_system_catalog(system_id),
    detail        TEXT              -- free text: capacity, level, complexity, etc.
);

CREATE INDEX IF NOT EXISTS idx_class_slots_class
    ON class_system_slots (class_id);
```

### class_design_features

```sql
CREATE TABLE IF NOT EXISTS class_design_features (
    id         INTEGER PRIMARY KEY,
    class_id   INTEGER NOT NULL REFERENCES ship_class(class_id) ON DELETE CASCADE,
    feature_id INTEGER NOT NULL REFERENCES design_features(feature_id),
    notes      TEXT
);
```

---

## Instance layer

### ship

One row per individual hull. `class_id` is NULL only for one-of-a-kind vessels with no
class tombstone (experimental ships, prizes, etc.) — in that case the class data is
duplicated on the ship row via an override mechanism to be defined when needed.

```sql
CREATE TABLE IF NOT EXISTS ship (
    ship_id       INTEGER PRIMARY KEY,
    class_id      INTEGER REFERENCES ship_class(class_id),
    hull_number   TEXT,    -- official designation e.g. 'CVN-65'; UNIQUE when not NULL
    name          TEXT,    -- proper name e.g. 'Enterprise'; NULL for unnamed bulk hulls
    builder_id    INTEGER REFERENCES design_bureaus(bureau_id),
    -- builder may differ from class designer

    -- Lifecycle (sim_time seconds from epoch; 0 = predates campaign)
    date_laid_down    INTEGER,
    date_commissioned INTEGER,
    date_removed      INTEGER,
    fate_id           INTEGER REFERENCES ship_fates(fate_id),

    notes         TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_ship_hull_number
    ON ship (hull_number) WHERE hull_number IS NOT NULL;
```

### ship_state

Time-series state per hull. One row per sim step in which the ship's state changes.
The application reads the most recent row at or before a given `sim_time`.

Location encodes three cases:
- **In system, not orbiting a specific body:** `system_id` set, `body_id` NULL
- **Orbiting a body:** both set (same composite key rules as everywhere else)
- **In transit:** `in_transit = 1`, `dest_system_id` set, `arrive_at` set

```sql
CREATE TABLE IF NOT EXISTS ship_state (
    state_id        INTEGER PRIMARY KEY,
    ship_id         INTEGER NOT NULL REFERENCES ship(ship_id) ON DELETE CASCADE,
    sim_time        INTEGER NOT NULL,

    -- Location
    system_id       TEXT,       -- current or last-known system; NULL = unknown
    body_id         INTEGER,    -- NULL = not in specific orbit
    in_transit      INTEGER NOT NULL DEFAULT 0 CHECK (in_transit IN (0, 1)),
    dest_system_id  TEXT,       -- set when in_transit = 1
    arrive_at       INTEGER,    -- sim_time of arrival; set when in_transit = 1

    -- Condition [0.0–1.0 fraction of full dST/HP remaining]
    condition       REAL NOT NULL DEFAULT 1.0 CHECK (condition BETWEEN 0.0 AND 1.0),
    status          TEXT NOT NULL DEFAULT 'ACTIVE'
                         CHECK (status IN (
                             'ACTIVE','DAMAGED','DISABLED','UNDER_REPAIR',
                             'MOTHBALLED','CAPTURED','DESTROYED')),

    -- Assignment
    owner_faction   TEXT,       -- faction/polity that owns the hull
    task_force_id   INTEGER,    -- FK → task_force when that table exists
    commanding_officer TEXT     -- free text for now
);

CREATE INDEX IF NOT EXISTS idx_ship_state_ship_time
    ON ship_state (ship_id, sim_time);
```

---

## Creation order

```sql
PRAGMA foreign_keys = ON;
-- Reference (no FKs between them)
-- 1. hull_sizes
-- 2. ship_types
-- 3. design_bureaus
-- 4. ship_fates
-- 5. design_features
-- 6. ship_system_catalog
-- 7. system_sm_stats
-- 8. armor_sm_stats
-- Class tombstone
-- 9.  ship_class
-- 10. class_system_slots
-- 11. class_design_features
-- Instance
-- 12. ship
-- 13. ship_state
```

---

## Notes

**Tombstone is immutable.** Once a class is entered it should not be edited. If a
variant is produced (refit, stretched hull, export version) create a new `ship_class`
row, optionally linking back to the original via `parent_class_id`.

**Condition vs. damage.** `ship_state.condition` is a scalar summary (fraction of HP
remaining). Detailed damage by hull section belongs in a future `ship_damage` table
when combat resolution requires it.

**Transit model.** `in_transit` / `arrive_at` on `ship_state` is a minimal placeholder.
Like trade and immigration in colonybase.db, realistic multi-hop routing with convoy
grouping requires a separate design pass.

**Sector key.** `system_id` + `body_id` composite applies here as everywhere — do not
filter on `body_id` alone.

**Power Points.** Not stored on the class directly; derived by summing `power_points`
from `class_system_slots` joined to `system_sm_stats`. High-energy slots consume one PP
each when active.
