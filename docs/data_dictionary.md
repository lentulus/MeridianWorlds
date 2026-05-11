# Data Dictionary

*2026-05-07. Covers world.db tables. For spaceship tables see `docs/spaceships/spaceship_schema.md`.*

DDL source: `docs/schema.md`. Three subject areas: **Settlements**, **Species**, **Spaceships**.

---

# Settlements

Settlement data describes what a body is like politically and industrially.
Physical body data (gravity, atmosphere, temperature) is owned by Meridian and
accessed via `meridian/api.py` — it is not stored here.

## Code tables

### `settlement_type`

| Field | Purpose |
|---|---|
| `code` | Primary key used as FK in `world_settlement` |
| `label` | Display name for queries and Obsidian frontmatter |
| `sort_order` | Source-book order (Step 33, pp. 121–122) |

Four values covering the GURPS Space settlement ladder: UNINHABITED → OUTPOST
→ COLONY → HOMEWORLD. A code table rather than CHECK because settlement type
is the most common filter a GM runs (`WHERE settlement_type = 'COLONY'`) and
the label is needed for display without joining to species or bodies.

### `government_type`

| Field | Purpose |
|---|---|
| `code` | Primary key |
| `label` | Full government name |
| `sort_order` | Step 35 table order (GURPS Space p. 122) |

Thirteen values from GURPS Space Step 35. Code table chosen because: (a) a GM
extends or renames government types during campaign design; (b) the label
(e.g. "Representative Oligarchy" vs raw "SENATE") is needed in Obsidian notes
without a JOIN. The `label` column absorbs what would otherwise be a verbose
CHECK string.

### `starport_class`

| Field | Purpose |
|---|---|
| `code` | Single letter A–X, primary key |
| `label` | Display name |
| `description` | Industrial capability summary |
| `sort_order` | A=1 (best) to X=6 (none) |

Starport class is the primary input to the ship production scaling formula
(see `docs/spaceships/spacecraft_production_scaling.md`). A code table lets
the `description` carry the industrial capability summary used in that formula
without embedding it in application code.

### `campaign_role`

| Field | Purpose |
|---|---|
| `code` | Primary key; FK from `species.campaign_role` |
| `label` | Display name |
| `sort_order` | Narrative significance order |

Controls which Claude model generates the Obsidian note and which batch API
parameters apply. Code table because campaign role is filtered constantly
(`--roles PEOPLE,BEAST`) and the label appears in generated prose.

---

## `world_settlement`

One row per surveyed body. LEFT JOINed to Meridian body data at query time.
Captures everything GURPS Space Steps 31–38 produce that isn't a physical
body property.

| Field | Type | Function | Why |
|---|---|---|---|
| `body_id` | TEXT PK | Opaque Meridian key; joins all settlement queries to physical data | Meridian is the authority on bodies — this table adds only what Meridian doesn't own |
| `is_main_world` | INTEGER 0/1 | Flags the highest-affinity body in a system | GURPS Step 33: exactly one body per system is the main world; this flag makes the query trivial |
| `volcanic_activity` | TEXT | NONE / LIGHT / MODERATE / HEAVY / EXTREME | Step 31 (p. 119); affects RVM and atmosphere; CHECK used because these five values are a physical classification that will never grow |
| `tectonic_activity` | TEXT | Same five levels | Step 31 (p. 120); affects habitability modifier; same rationale as volcanic |
| `resource_value_mod` | INTEGER −5..+5 | Raw material abundance modifier | Step 32 (p. 121); direct input to ship production formula k_r factor |
| `habitability` | INTEGER 0..12 | How comfortable the environment is for humans | Step 32 (p. 121); drives settlement type and population decisions |
| `affinity_score` | INTEGER | habitability + modifiers; selects the main world | Step 32; derived field stored for query convenience rather than recomputed |
| `settlement_type` | TEXT FK | UNINHABITED / OUTPOST / COLONY / HOMEWORLD | Step 33 (pp. 121–122); top-level campaign classification; FK to code table for display and filtering |
| `population` | INTEGER | Absolute headcount | Step 34 (p. 122); raw figure for precise calculations |
| `population_log` | INTEGER 0..13 | log₁₀ of population | Step 34; Traveller-style shorthand used in production formula k_p factor; stored alongside absolute to avoid repeated `log10()` calls |
| `government_type` | TEXT FK | Political structure | Step 35 (p. 122); FK to code table because GMs name and extend government types |
| `control_rating` | INTEGER 0..6 | Civil liberties / authoritarianism index | Step 36 (p. 122); 0 = anarchy, 6 = totalitarian; used in scenario generation |
| `tech_level` | INTEGER | Baseline industrial TL | Step 37 (p. 122); primary production formula input; no upper bound because TL^ tech is assigned hard numeric TLs in a separate faction table |
| `starport_class` | TEXT FK | Industrial infrastructure grade | Step 38 (p. 123); FK to code table because the description (industrial capability) is needed by the production scaling formula |

---

# Species

Species data covers the GURPS Space Chapter 6 alien creation pipeline
(pp. 134–170). All enum columns use CHECK constraints: the vocabulary is fixed
by the source tables, these fields are written only by generated code that goes
through Pydantic validation, and the number of values (5–16 per column) makes
CHECK readable. `campaign_role` is the exception — it is filtered, displayed,
and extended by GMs, so it gets a code table.

## `species`

### Identity

| Field | Type | Function | Why |
|---|---|---|---|
| `species_id` | TEXT PK | UUID; stable key across pipeline | UUIDs survive renames; used as `custom_id` in Claude Batch API requests |
| `body_id` | TEXT | Meridian key for homeworld; NULL for space-native species | Logical FK; physical homeworld context (gravity, atmosphere) fetched from Meridian at generation time |
| `name` | TEXT | Common name | Free-form; no constraint — exotic names are expected |
| `campaign_role` | TEXT FK | PEOPLE / BEAST / THING / MONSTER | Controls Claude model, max_tokens, and generation prompt; FK to code table for filtering |

### Biochemistry & habitat (Tables I–II)

| Field | Type | Function | Why |
|---|---|---|---|
| `biochem_basis` | TEXT | Chemical foundation of life | Determines what atmospheres are breathable and what environments are survivable; 6 values from Table I |
| `habitat_medium` | TEXT | Gross medium: LAND / WATER / SPACE / ATMOSPHERIC | Top-level filter for encounter and scenario generation |
| `habitat_type` | TEXT | Specific environment within the medium | 16 values from Table II; used for Obsidian note prose and encounter table generation |
| `trophic_level` | TEXT | Ecological role in food web | 9 values from Table II; affects behaviour, aggression, and encounter context |

### Body plan (Table III)

| Field | Type | Function | Why |
|---|---|---|---|
| `symmetry` | TEXT | Body symmetry type | Determines visual appearance and GURPS trait availability |
| `size_class` | TEXT | Narrative size band | Quick filter; 5 values |
| `size_m` | REAL | Body length / height in metres | Concrete measurement; GURPS source uses yards — stored as metres (1 yd → 1 m) |
| `mass_kg` | REAL | Body mass in kilograms | GURPS source uses pounds — stored as kg (1 lb → 0.5 kg) |

### Locomotion (Table IV)

| Field | Type | Function | Why |
|---|---|---|---|
| `locomotion_primary` | TEXT | Main movement mode | Determines terrain, encounter context, and GURPS Move stat |
| `locomotion_secondary` | TEXT | Optional second mode | NULL if not applicable; up to 3 modes to cover amphibious / gliding combinations |
| `locomotion_tertiary` | TEXT | Optional third mode | As above |

Three columns rather than a join table because the number of modes is small
and fixed (0–3); a join table would add a query for a very common field.

### Limbs & manipulators (Table VI)

| Field | Type | Function | Why |
|---|---|---|---|
| `num_body_segments` | INTEGER | Segment count | Drives limb count calculation; CHECK > 0 |
| `limbs_per_segment` | INTEGER | Limbs per segment | Combined with segments gives total limb count |
| `has_tail` | INTEGER 0/1 | Boolean tail presence | Simpler than nullable tail_type alone |
| `tail_type` | TEXT | Function of tail if present | NULL when has_tail = 0 |
| `manipulator_sets` | INTEGER | Count of independent hand-equivalents | Key for sapient species; 0 = no manipulation |
| `manipulator_quality` | TEXT | Dexterity and grip type | Determines which GURPS skills are available at full level |

### Structure & covering (Table VI)

| Field | Type | Function | Why |
|---|---|---|---|
| `skeleton_type` | TEXT | Internal support structure | Affects DR, flexibility, and damage effects |
| `covering_type` | TEXT | Outer surface material | Visual description and passive DR source |
| `covering_dr` | INTEGER | Passive damage resistance from covering | Direct GURPS game stat; CHECK ≥ 0 |

### Metabolism (Table VI)

| Field | Type | Function | Why |
|---|---|---|---|
| `breathing` | TEXT | Respiratory method | Determines atmosphere compatibility with biochem_basis |
| `temp_regulation` | TEXT | Thermal regulation strategy | Affects behaviour in cold/hot environments and activity levels |

### Reproduction (Table VI)

| Field | Type | Function | Why |
|---|---|---|---|
| `sexual_arrangement` | TEXT | Mating system structure | Affects social organisation and encounter behaviour |
| `gestation_method` | TEXT | How offspring are produced | Background flavour and encounter context (e.g. egg nests) |
| `special_gestation` | TEXT | Unusual reproductive strategy | Nullable; only two values confirmed — CHECK list pending full Table VI audit |
| `repro_strategy` | TEXT | r/K selection spectrum | STRONG_K = few, well-invested offspring; STRONG_R = many, expendable; affects encounter numbers |
| `offspring_per_litter` | INTEGER | Typical litter size | Feeds into encounter table generation |

### Senses (Tables VII–VIII)

| Field | Type | Function | Why |
|---|---|---|---|
| `primary_sense` | TEXT | Dominant sensory channel | Affects how the species detects threats and prey |
| `vision` | TEXT | Visual acuity / type | BLIND through TELESCOPIC; used for night encounter modifiers |
| `hearing` | TEXT | Auditory acuity | DEAF through SONAR |
| `touch` | TEXT | Tactile sensitivity | Affects search and perception rolls |
| `taste_smell` | TEXT | Chemical sense quality | NONE through DISCRIMINATORY |
| `special_senses` | INTEGER | Bitmask for additional senses | INFRARED=1, UV=2, MAGNETIC=4, ELECTRIC=8, PRESSURE=16, ECHOLOCATION=32; bitmask chosen over join table because these combine freely and are tested with bitwise AND |

### Mind (Table VIII)

| Field | Type | Function | Why |
|---|---|---|---|
| `intelligence` | TEXT | Sapience level | Five-step scale; primary filter for whether Claude writes a PEOPLE entry |
| `iq_typical` | INTEGER | GURPS IQ stat | NULL unless SAPIENT; meaningful only for player-race context |

### Social (Table IX)

| Field | Type | Function | Why |
|---|---|---|---|
| `mating_behavior` | TEXT | Pair bond / hive structure | Affects social encounter dynamics |
| `social_organization` | TEXT | Group structure at population scale | SOLITARY through HIVE; drives typical_group_size |
| `typical_group_size` | INTEGER | Expected encounter group size | Direct input to encounter table generation |

### Vault bridge

| Field | Type | Function | Why |
|---|---|---|---|
| `notes` | TEXT | Free-text design notes | Not sent to Claude; for the worldbuilder's own reference |
| `obsidian_slug` | TEXT UNIQUE | Filename stem for vault .md file | Bridge between world.db and Obsidian; UNIQUE enforces one file per species |

---

## `species_traits`

GURPS racial advantage / disadvantage list per species. Separate table to avoid
a wide sparse bitmask or unbounded column count on `species`.

| Field | Type | Function | Why |
|---|---|---|---|
| `id` | INTEGER PK | Rowid alias | Required for ON DELETE CASCADE to work cleanly |
| `species_id` | TEXT FK | Parent species | CASCADE delete keeps the table clean if a species is removed |
| `trait_name` | TEXT | GURPS advantage or disadvantage name | Free-form; matches GURPS book text exactly (e.g. "Night Vision 5", "Fragile (Unnatural)") |
| `level` | INTEGER | Level for levelled traits | NULL for binary traits; avoids encoding level into the name string |

---

# Spaceships

Spaceship data is managed in two layers: the GURPS Spaceships rules catalogue
(reference, static) and the campaign ship register (named vessels).

Full DDL: `docs/spaceships/spaceship_schema.md`.
Production scaling model: `docs/spaceships/spacecraft_production_scaling.md`.

## Table summary

| Table | Subject | Function |
|---|---|---|
| `hull_sizes` | Reference | SM → mass (t), dimensions, base dST/HP, handling |
| `ship_types` | Reference | Vessel role categories (Fighter, Freighter, etc.) |
| `design_bureaus` | Reference | Who designed / built the ship |
| `ship_system_catalog` | Reference | Every installable system from SS1–SS8 |
| `system_sm_stats` | Reference | Per-system per-SM cost, workspaces, type stats |
| `armor_sm_stats` | Reference | Armor dDR by SM — split out due to value density |
| `design_features` | Reference | All design features and switches from SS1 |
| `ships` | Campaign | One row per named vessel |
| `ship_design_features` | Campaign | Design features on a specific ship |
| `ship_system_slots` | Campaign | Systems installed in specific hull slots |

## Key design decisions

**Decade-scale stats throughout.** All dDR, dST/HP, and d-Damage values are
stored decade-scale as GURPS Spaceships defines them (1 point = 10 normal
GURPS points). No conversion applied.

**Delta-V in km/s.** GURPS Spaceships quotes delta-V in mps (miles per
second). Stored as km/s: 1 mps = 1.6 km/s. The 38% ratio error from treating
mps as km/s is too large for travel time calculations.

**Thrust in standard gravities (g).** Already SI-compatible; no conversion.

**Cost in GURPS $.** Not mapped to a real economy. Used as a relative index
in the production scaling formula.

**Body position via Meridian.** Ship position and current system are dynamic
world-state owned by Meridian. The `ships` table stores design and identity;
position is fetched via `meridian.api.get_ship_position()` when needed.
