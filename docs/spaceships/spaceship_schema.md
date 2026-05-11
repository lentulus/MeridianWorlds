# Spaceship Database Schema
## GURPS Spaceships 4e

All stats are decade-scale (dDR, dST/HP) as per GURPS Spaceships conventions.
Sources: Spaceships 1–8, worldbuild reference docs.

---

## Table Overview

| Table | Purpose |
|---|---|
| `hull_sizes` | Reference: SM → mass, dimensions, base stats |
| `ship_types` | Reference: vessel categories (Fighter, Freighter, etc.) |
| `ships` | Core vessel records — one row per named vessel |
| `ship_design_features` | Design features attached to a ship |
| `ship_system_catalog` | All possible systems available in the rules |
| `ship_system_slots` | Systems installed on a specific ship |
| `system_sm_stats` | Per-system, per-SM statistics (cost, workspaces, type-specific stats) |
| `armor_sm_stats` | Armor dDR by SM (US and SL) — separate due to density of values |
| `design_features` | Reference: all design features and switches |

---

## `hull_sizes`

Reference table. One row per Size Modifier. Static — derived from the Hull Size Table in SS1 p.9.

| Column | Type | Notes |
|---|---|---|
| `sm` | INTEGER PRIMARY KEY | Size Modifier: +5 to +15 |
| `mass_tons` | INTEGER | Loaded mass in short tons |
| `length_yards` | INTEGER | Typical length in yards |
| `dst_hp` | INTEGER | Decade-scale ST/HP |
| `handling` | INTEGER | Base Handling modifier (negative = sluggish) |
| `stability_rating` | INTEGER | Base Stability Rating |

---

## `design_bureaus`

Organizations that design and/or build ships. The first entry covers ships sourced directly from the GURPS Spaceships books.

| Column | Type | Notes |
|---|---|---|
| `bureau_id` | INTEGER PRIMARY KEY | |
| `name` | TEXT NOT NULL | e.g. "GURPS Spaceships Index", "Consolidated Aerospace", "Martian Naval Yards" |
| `short_code` | TEXT | Brief identifier e.g. "SS-INDEX", "CAI", "MNY" |
| `notes` | TEXT | Background, affiliation, specialisation |

---

## `ship_types`

Reference table. Role categories — what a ship is for.

| Column | Type | Notes |
|---|---|---|
| `type_id` | INTEGER PRIMARY KEY | |
| `name` | TEXT NOT NULL | e.g. "Tramp Freighter", "Fighter", "Battle Station" |
| `military` | INTEGER | Boolean: 1 if a combat type |

---

## `ships`

One row per named vessel or class variant. Multi-stage ships (e.g. Midnight Sun booster vs orbiter) get separate rows linked via `parent_ship_id`.

| Column | Type | Notes |
|---|---|---|
| `ship_id` | INTEGER PRIMARY KEY | |
| `hull_number` | TEXT | Hull designation e.g. "CVN-65", "NCC-1701"; unique identifier for a specific hull |
| `name` | TEXT | Proper name e.g. "Enterprise"; NULL for bulk-built hulls that have no individual name |
| `class_name` | TEXT | Class name e.g. "Star Flower"; ships of the same design share this |
| `type_id` | INTEGER | FK → ship_types |
| `bureau_id` | INTEGER | FK → design_bureaus |
| `parent_ship_id` | INTEGER | FK → ships; for upper stages / sub-variants |
| `tl` | INTEGER | Tech level number (7–12) |
| `is_superscience` | INTEGER | Boolean: 1 if TL marked ^ |
| `sm` | INTEGER | Size Modifier; FK → hull_sizes |
| `is_streamlined` | INTEGER | Boolean: 1 = streamlined hull |
| `dst_hp` | INTEGER | dST/HP (decade-scale) |
| `handling` | INTEGER | Handling modifier |
| `stability_rating` | INTEGER | Stability Rating |
| `ht` | INTEGER | Health |
| `move_accel_g` | REAL | Acceleration in G (NULL if no space performance) |
| `move_delta_v_mps` | REAL | Delta-V in miles per second (NULL if FTL/no drive) |
| `move_is_ftl` | INTEGER | Boolean: 1 if delta-V is c-fraction (stardrive) |
| `move_atm_only` | INTEGER | Boolean: 1 if atmospheric drive only |
| `lwt_tons` | REAL | Loaded weight in tons |
| `load_tons` | REAL | Max cargo/payload tons |
| `occ_crew` | INTEGER | Number of crew positions (workspaces) |
| `occ_passengers` | INTEGER | Passenger capacity |
| `occ_has_artificial_grav` | INTEGER | Boolean: 1 = ASV notation |
| `occ_is_short_voyage` | INTEGER | Boolean: 1 = SV (24h life support only) |
| `ddr_front` | INTEGER | Decade-scale DR, front hull |
| `ddr_central` | INTEGER | Decade-scale DR, central hull |
| `ddr_rear` | INTEGER | Decade-scale DR, rear hull |
| `range_ftl` | TEXT | FTL range rating (e.g. "2×"); NULL if no FTL |
| `cost_dollars` | REAL | Cost in dollars (e.g. 44500000 for $44.5M) |
| `date_laid_down` | INTEGER | Seconds from campaign epoch. NULL = not yet happened. 0 = pre-dates epoch / always true (use for book ships) |
| `date_commissioned` | INTEGER | Seconds from campaign epoch. NULL = not yet commissioned. 0 = pre-dates epoch |
| `date_removed` | INTEGER | Seconds from campaign epoch. NULL = still in service. 0 = pre-dates epoch (decommissioned before campaign start) |
| `fate_id` | INTEGER | FK → ship_fates; NULL if still active |
| `notes` | TEXT | Markdown. Free-form notes, history, footnotes |

---

## `ship_fates`

Controlled vocabulary for how a ship left service. Using a lookup table keeps queries consistent and allows adding detail per fate type.

| Column | Type | Notes |
|---|---|---|
| `fate_id` | INTEGER PRIMARY KEY | |
| `name` | TEXT NOT NULL | e.g. "Scrapped", "Lost in combat", "Lost — accident", "Converted", "Mothballed", "Captured", "Expended", "Unknown" |
| `notes` | TEXT | Any clarification |

---

## `design_features`

Reference table of all design features and switches from SS1 pp.29–31 and supplements.

| Column | Type | Notes |
|---|---|---|
| `feature_id` | INTEGER PRIMARY KEY | |
| `name` | TEXT NOT NULL | e.g. "Artificial Gravity", "Streamlined", "Winged" |
| `feature_type` | TEXT | "feature" or "switch" |
| `tl_min` | INTEGER | Minimum TL |
| `is_superscience` | INTEGER | Boolean |
| `description` | TEXT | Rules summary |

---

## `ship_design_features`

Junction table: which design features a ship has.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PRIMARY KEY | |
| `ship_id` | INTEGER | FK → ships |
| `feature_id` | INTEGER | FK → design_features |
| `notes` | TEXT | Any variant details |

---

## `ship_system_catalog`

Master list of all installable systems. One row per distinct system (or variant where stats differ — e.g. Fission Reactor and Fusion Reactor are separate rows).

| Column | Type | Notes |
|---|---|---|
| `system_id` | INTEGER PRIMARY KEY | |
| `name` | TEXT NOT NULL | e.g. "Armor, Metallic Laminate" |
| `category` | TEXT | "Armor", "Cargo", "Control", "Power", "Reaction Engine", "Reactionless Engine", "FTL", "Weapon", "Industrial", "Utility", "Superscience" |
| `tl_min` | INTEGER | First TL available (NULL if superscience-only) |
| `is_superscience` | INTEGER | Boolean: 1 if TL marked ^ |
| `location` | TEXT | "ANY", "HULL", "FRONT", "REAR", "SPECIAL" |
| `is_high_energy` | INTEGER | Boolean: 1 if requires a Power Point (marked !) |
| `repair_skill` | TEXT | e.g. "Armoury (Vehicle Armor)" |
| `notes` | TEXT | Rules notes, variants |

### System Categories and Key Entries

| Category | Examples |
|---|---|
| Armor | Ice, Stone, Steel, Light Alloy, Metallic Laminate, Advanced Metallic Laminate, Nanocomposite, Organic, Diamondoid, Exotic Laminate |
| Cargo | Cargo Hold, Passenger Seating, Habitat, Open Space, Hangar Bay |
| Control | Control Room, Engine Room, Comm/Sensor Array (Enhanced/Science/Tactical/Multipurpose), Defensive ECM, External Clamp, Robot Arm, Robot Leg, Cloaking Device |
| Power | Power Plant (Fuel Cell, MHD Turbine, Fission, Fusion, Antimatter, Super Fusion, Total Conversion), Solar Panel Array, Ramscoop |
| Reaction Engine | Chemical Rocket, HEDM, Ion Drive, Mass Driver, NTR, Nuclear Light Bulb, Orion Pulse, Fusion Pulse, Fusion Torch, Antimatter series, Total Conversion Torch |
| Reactionless Engine | Rotary Reactionless, Standard, Hot, Super, Subwarp |
| FTL | Stardrive Engine, Super Stardrive, Jump Gate |
| Weapon | Major Battery, Medium Battery, Secondary Battery, Tertiary Battery, Spinal Battery |
| Industrial | Factory (Fabricator, Robofac, Nanofactory, Replicator), Mining System, Chemical Refinery |
| Utility | Fuel Tank, Jet Engine, Soft-Landing System, Space Sails (Light/Mag), Upper Stage, Reconfigurable System |
| Superscience | Contragravity Lifter, Force Screen (Light/Heavy), Stasis Web |

---

## `ship_system_slots`

The 20 installed systems on a specific ship. Each row is one slot (or a span of identical adjacent slots).

| Column | Type | Notes |
|---|---|---|
| `slot_id` | INTEGER PRIMARY KEY | |
| `ship_id` | INTEGER | FK → ships |
| `hull_section` | TEXT | "front", "central", "rear" |
| `slot_number` | INTEGER | 1–6; NULL if core |
| `slot_to` | INTEGER | For spans: e.g. slot 2–4 → slot_number=2, slot_to=4 |
| `is_core` | INTEGER | Boolean: 1 = [core] slot |
| `is_high_energy` | INTEGER | Boolean: 1 = this slot requires a Power Point |
| `system_id` | INTEGER | FK → ship_system_catalog |
| `detail` | TEXT | Free-text description: "50 tons capacity", "1G acceleration", "Complexity 9", etc. |

### Example: Star Flower-class Freighter

| hull_section | slot_number | is_core | system | detail |
|---|---|---|---|---|
| front | 1 | 0 | Armor, Metallic Laminate | dDR 7 |
| front | 2 | 0 | Cargo Hold | 50 tons |
| front | 3 | 0 | Cargo Hold | 50 tons |
| front | 4 | 0 | Cargo Hold | 50 tons |
| front | 5 | 0 | Cargo Hold | 50 tons |
| front | 6 | 0 | Comm/Sensor Array, Enhanced | Level 10 |
| front | NULL | 1 | Control Room | 4 stations, Complexity 9 |
| central | 1 | 0 | Armor, Metallic Laminate | dDR 7 |
| central | 2 | 0 | Habitat | 6 cabins, passengers |
| central | 3 | 0 | Habitat | 4 cabins, 2-bed sickbay, crew |
| central | 4 | 0 | Cargo Hold | 50 tons |
| central | 5 | 0 | Cargo Hold | 50 tons |
| central | 6 | 1 | Tertiary Battery | 1 turret, 10 MJ laser, 43.5 tons cargo |
| rear | 1 | 0 | Armor, Metallic Laminate | dDR 7 |
| rear | 2 | 1 | Reaction Engine, Standard Reactionless | 1G |
| rear | 3 | 1 | Reaction Engine, Standard Reactionless | 1G |
| rear | 4 | 1 | Stardrive Engine | FTL-1 |
| rear | 5 | 1 | Stardrive Engine | FTL-1 |
| rear | 6 | 0 | Engine Room | 1 workspace |
| rear | NULL | 1 | Power Plant, Fusion Reactor | 2 Power Points |

---

## `system_sm_stats`

Per-system, per-SM statistics. Columns are nullable — only those relevant to each system type are populated. Covers all non-armor systems.

| Column | Type | Notes |
|---|---|---|
| `stat_id` | INTEGER PRIMARY KEY | |
| `system_id` | INTEGER | FK → ship_system_catalog |
| `sm` | INTEGER | Size Modifier (+5 to +15) |
| `workspaces` | INTEGER | Number of crew workspaces (NULL = 0 implied) |
| `cost_dollars` | REAL | Cost in dollars at this SM |
| `capacity_tons` | REAL | Cargo/hangar capacity in tons |
| `launch_rate_tons` | REAL | Hangar Bay: max tons launched/recovered per minute |
| `fuel_tons` | REAL | Fuel Tank: tons of reaction mass stored |
| `seats` | INTEGER | Passenger Seating: number of seats |
| `cabins` | INTEGER | Habitat: number of cabins |
| `areas` | INTEGER | Open Space: number of open areas |
| `control_stations` | INTEGER | Control Room: number of control stations |
| `computer_complexity` | INTEGER | Control Room: network Complexity (numeric, e.g. 9 for C9) |
| `comm_sensor_level_offset` | INTEGER | Comm/Sensor Array: level offset from TL (e.g. -2 = TL-2) |
| `power_points` | INTEGER | Power Plant: Power Points provided |
| `acceleration_g` | REAL | Drive: acceleration in G per system |
| `delta_v_mps_per_tank` | REAL | Reaction drive: delta-V per fuel tank in mps |
| `output_per_hour_dollars` | REAL | Factory: production value $/hr |
| `output_per_hour_lbs` | REAL | Replicator: lbs of goods per hour |
| `mining_tons_per_hour` | REAL | Mining System |
| `refinery_tons_per_hour` | REAL | Chemical Refinery |
| `max_tonnage` | REAL | Jump Gate: max tons through at once |
| `force_screen_ddr` | INTEGER | Force Screen: dDR provided |
| `cost_variant` | TEXT | For systems with multiple cost tiers at same SM (e.g. "fusion", "antimatter") |
| `stat_notes` | TEXT | Any footnotes or conditions |

---

## `armor_sm_stats`

Armor systems have two dDR values per SM (unstreamlined and streamlined) plus cost. Kept separate from `system_sm_stats` to avoid sparse rows.

| Column | Type | Notes |
|---|---|---|
| `stat_id` | INTEGER PRIMARY KEY | |
| `system_id` | INTEGER | FK → ship_system_catalog |
| `sm` | INTEGER | Size Modifier (+5 to +15; some armor unavailable at low SM) |
| `ddr_us` | INTEGER | Unstreamlined dDR |
| `ddr_sl` | INTEGER | Streamlined dDR (NULL if unavailable at this SM) |
| `cost_dollars` | REAL | Cost at this SM |

### Armor Values Summary

| Armor Type | TL | SM+5 US dDR | SM+8 US dDR | SM+12 US dDR |
|---|---|---|---|---|
| Ice | 0 | — | 2 | 5 |
| Stone | 0 | — | 2 | 5 |
| Steel | 7 | 1 | 5 | 20 |
| Light Alloy | 7 | 2 | 7 | 30 |
| Metallic Laminate | 8 | 3 | 10 | 50 |
| Advanced Metallic Laminate | 9 | 5 | 15 | 70 |
| Nanocomposite | 10 | 7 | 20 | 100 |
| Organic | 10 | 2 | 7 | 30 |
| Diamondoid | 11 | 10 | 30 | 150 |
| Exotic Laminate | 12 | 15 | 50 | 200 |

---

## Key Relationships

```
hull_sizes (sm)
    ↑
ships ──────────────────────── ship_types
    │   ├───────────────────── design_bureaus
    │   └───────────────────── ship_fates
    │
    ├── ship_design_features ── design_features
    │
    └── ship_system_slots ───── ship_system_catalog
                                    │
                                    ├── system_sm_stats
                                    └── armor_sm_stats
```

---

## Notes on Special Cases

### Occupancy parsing
The `occ` field in source material encodes multiple values in one string (e.g. `"2+12SV"` = 2 crew + 12 passengers, short voyage). The schema stores these as separate integer columns (`occ_crew`, `occ_passengers`, `occ_is_short_voyage`, `occ_has_artificial_grav`).

### Move field parsing
The `move` field in source material (e.g. `"3G/2.6 mps"`, `"100G/c"`, `"–/–"`) is split into `move_accel_g`, `move_delta_v_mps`, `move_is_ftl`, and `move_atm_only`.

### dDR parsing
Single-value dDR (e.g. `7`) means all three sections are equal. Three-value dDR (e.g. `45/15/60`) maps to `ddr_front`/`ddr_central`/`ddr_rear`.

### Multi-stage vessels
Upper stages and booster stacks are linked via `parent_ship_id`. The booster row points to the upper stage as its parent (or vice versa depending on convention — recommend booster points to orbiter as parent).

### Power Points
Power Points are not stored on the ship directly; they are derived by summing `power_points` from the ship's power plant entries in `ship_system_slots` joined to `system_sm_stats`. High-energy systems (is_high_energy = 1) each consume one PP when active.

### Superscience TL
Systems and ships marked `^` store `is_superscience = 1` with `tl_min` set to the associated numeric TL where one exists, or NULL for purely undefined-TL superscience.
