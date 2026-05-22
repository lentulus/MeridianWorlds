# Species & Settlement Data — Schema

*Updated: 2026-05-07. Parquet replaced with SQLite (world.db).*

All tables live in `world.db` (imported via `from config import WORLDS_DB`).
The `bodies` table is in `starfield.db`; FK references to it are **logical only**
(enforced at application level — SQLite cannot enforce cross-database foreign keys).

---

## Source material scope

| Pages | Content |
|---|---|
| pp. 119–120 | Steps 31: volcanic activity, tectonic activity |
| pp. 121 | Step 32: resource value modifier, habitability, affinity score |
| pp. 121–123 | Steps 33–39: settlement type, population, government, control rating, TL, starport |
| pp. 134–135 | Chapter 6 intro: alien creation philosophy, biochemistry basis |
| pp. 136–144 | Ecology tables I–V: habitat, trophic level, body plan, locomotion, size |
| pp. 144–155 | Body detail tables VI: skeleton, covering, breathing, metabolism, reproduction |
| pp. 155–163 | Senses & intelligence tables VII–VIII |
| pp. 163–170 | Social structure table IX; sapient finishing rules |

---

## 1. world_settlement

One row per inhabited (or surveyed) body. Separated from `bodies` because most
bodies are uninhabited; a LEFT JOIN keeps the starfield table lean.

Geologic activity (Steps 31–32) is stored here rather than in `bodies` because
it feeds directly into RVM and habitability, and `bodies` is read-only starfield
ground truth.

```sql
CREATE TABLE IF NOT EXISTS world_settlement (
    body_id              TEXT    NOT NULL PRIMARY KEY,
    -- logical FK → starfield.db bodies.body_id

    is_main_world        INTEGER NOT NULL DEFAULT 0
                                 CHECK (is_main_world IN (0, 1)),

    -- Step 31: Geologic Activity (pp. 119–120)
    volcanic_activity    TEXT    CHECK (volcanic_activity IN (
                                     'NONE', 'LIGHT', 'MODERATE', 'HEAVY', 'EXTREME')),
    tectonic_activity    TEXT    CHECK (tectonic_activity IN (
                                     'NONE', 'LIGHT', 'MODERATE', 'HEAVY', 'EXTREME')),

    -- Step 32: Resources & Habitability (p. 121)
    resource_value_mod   INTEGER CHECK (resource_value_mod BETWEEN -5 AND 5),
    habitability         INTEGER CHECK (habitability BETWEEN 0 AND 12),
    affinity_score       INTEGER,

    -- Step 33: Settlement Type (pp. 121–122)
    settlement_type      TEXT    NOT NULL DEFAULT 'UNINHABITED'
                                 CHECK (settlement_type IN (
                                     'UNINHABITED', 'OUTPOST', 'COLONY', 'HOMEWORLD')),

    -- Step 34: Population (p. 122)
    population           INTEGER CHECK (population >= 0),
    population_log       INTEGER CHECK (population_log BETWEEN 0 AND 13),

    -- Step 35: Government Type (p. 122)
    government_type      TEXT    CHECK (government_type IN (
                                     'NO_GOV', 'CORPORATION', 'PARTICIPATORY',
                                     'REPRESENTATIVE', 'TECHNOCRACY', 'FEUDAL',
                                     'OLIGARCHY', 'SENATE', 'DICTATORSHIP',
                                     'THEOCRACY', 'CLAN_TRIBAL', 'MILITARY',
                                     'COMMUNIST')),

    -- Step 36: Control Rating (p. 122)
    control_rating       INTEGER CHECK (control_rating BETWEEN 0 AND 6),

    -- Step 37: Tech Level (p. 122)
    -- Baseline TL only. Superscience (^) capabilities are itemised separately
    -- with a hard numeric TL and faction qualifier — not encoded in this column.
    -- Upper bound left open-ended; ^ tech in this setting has assigned hard TLs.
    tech_level           INTEGER CHECK (tech_level >= 0),

    -- Step 38: Starport Class (p. 123)
    starport_class       TEXT    CHECK (starport_class IN ('A','B','C','D','E','X'))
);
```

---

## 2. species

One row per named species. `body_id` is the homeworld (logical FK to
`starfield.db`). `obsidian_slug` bridges to the Obsidian vault narrative file.

```sql
CREATE TABLE IF NOT EXISTS species (
    species_id              TEXT    NOT NULL PRIMARY KEY,
    body_id                 TEXT,
    -- logical FK → starfield.db bodies.body_id (homeworld); NULL for space-native species

    name                    TEXT    NOT NULL,
    campaign_role           TEXT    NOT NULL
                                    CHECK (campaign_role IN (
                                        'PEOPLE', 'BEAST', 'THING', 'MONSTER')),

    -- Biochemistry & habitat (Table I–II)
    biochem_basis           TEXT    CHECK (biochem_basis IN (
                                        'WATER_CARBON', 'AMMONIA_CARBON',
                                        'HYDROGEN_NEON', 'SULFUR', 'CHLORINE', 'METHANE')),
    habitat_medium          TEXT    CHECK (habitat_medium IN (
                                        'LAND', 'WATER', 'SPACE', 'ATMOSPHERIC')),
    habitat_type            TEXT    CHECK (habitat_type IN (
                                        'PLAINS', 'DESERT', 'ARCTIC', 'FOREST', 'JUNGLE',
                                        'MOUNTAINS', 'OCEAN_SURFACE', 'OCEAN_SHALLOW',
                                        'OCEAN_DEEP', 'SWAMP', 'CAVE', 'GAS_GIANT',
                                        'ORBITAL', 'ASTEROID', 'INTERIOR', 'VACUUM')),
    trophic_level           TEXT    CHECK (trophic_level IN (
                                        'AUTOTROPH_PHOTO', 'AUTOTROPH_CHEMO',
                                        'HERBIVORE', 'OMNIVORE', 'CARNIVORE',
                                        'SCAVENGER', 'DECOMPOSER', 'PARASITE', 'SYMBIONT')),

    -- Body plan (Table III)
    symmetry                TEXT    CHECK (symmetry IN (
                                        'BILATERAL', 'TRILATERAL', 'RADIAL',
                                        'SPHERICAL', 'ASYMMETRIC')),
    size_class              TEXT    CHECK (size_class IN (
                                        'TINY', 'SMALL', 'HUMAN_SCALE', 'LARGE', 'HUGE')),
    size_m                  REAL,   -- body length/height in metres (1 yd → 1 m)
    mass_kg                 REAL,   -- body mass in kilograms (1 lb → 0.5 kg)

    -- Locomotion (Table IV) — up to 3 modes
    locomotion_primary      TEXT    CHECK (locomotion_primary IN (
                                        'IMMOBILE', 'SLITHERING', 'WALKING', 'RUNNING',
                                        'CLIMBING', 'SWIMMING', 'FLYING', 'GLIDING',
                                        'BURROWING', 'SPACE')),
    locomotion_secondary    TEXT    CHECK (locomotion_secondary IN (
                                        'IMMOBILE', 'SLITHERING', 'WALKING', 'RUNNING',
                                        'CLIMBING', 'SWIMMING', 'FLYING', 'GLIDING',
                                        'BURROWING', 'SPACE')),
    locomotion_tertiary     TEXT    CHECK (locomotion_tertiary IN (
                                        'IMMOBILE', 'SLITHERING', 'WALKING', 'RUNNING',
                                        'CLIMBING', 'SWIMMING', 'FLYING', 'GLIDING',
                                        'BURROWING', 'SPACE')),

    -- Limbs & manipulators (Table VI)
    num_body_segments       INTEGER CHECK (num_body_segments > 0),
    limbs_per_segment       INTEGER CHECK (limbs_per_segment >= 0),
    has_tail                INTEGER NOT NULL DEFAULT 0 CHECK (has_tail IN (0, 1)),
    tail_type               TEXT    CHECK (tail_type IN (
                                        'BALANCE', 'PREHENSILE', 'WEAPON', 'SENSORY')),
    manipulator_sets        INTEGER CHECK (manipulator_sets >= 0),
    manipulator_quality     TEXT    CHECK (manipulator_quality IN (
                                        'NONE', 'BAD_GRIP', 'NORMAL', 'HIGH_DEX', 'TENTACLE')),

    -- Structure & covering (Table VI)
    skeleton_type           TEXT    CHECK (skeleton_type IN (
                                        'NONE', 'HYDROSTATIC', 'EXTERNAL',
                                        'INTERNAL', 'COMBINATION')),
    covering_type           TEXT    CHECK (covering_type IN (
                                        'SKIN', 'SCALES', 'FUR', 'FEATHERS', 'EXOSKELETON',
                                        'SHELL', 'BARK', 'CRYSTALLINE', 'OTHER')),
    covering_dr             INTEGER CHECK (covering_dr >= 0),

    -- Metabolism (Table VI)
    breathing               TEXT    CHECK (breathing IN (
                                        'GILLS', 'LUNGS', 'BOTH',
                                        'O2_ABSORPTION', 'DOESNT_BREATHE')),
    temp_regulation         TEXT    CHECK (temp_regulation IN (
                                        'COLD_BLOODED', 'WARM_BLOODED',
                                        'WARM_METAB_CONTROL', 'VARIABLE')),

    -- Reproduction (Table VI)
    sexual_arrangement      TEXT    CHECK (sexual_arrangement IN (
                                        'ASEXUAL', 'HERMAPHRODITE', 'TWO_SEX',
                                        'THREE_SEX', 'PARTHENOGENESIS')),
    gestation_method        TEXT    CHECK (gestation_method IN (
                                        'SPAWNING', 'EGG_LAYING', 'LIVE_BEARING',
                                        'POUCH', 'EXTERNAL_LARVAL')),
    special_gestation       TEXT    CHECK (special_gestation IN (
                                        'BROOD_PARASITE', 'SEQUENTIAL_HERMAPHRODITE')),
    repro_strategy          TEXT    CHECK (repro_strategy IN (
                                        'STRONG_K', 'MODERATE_K', 'MEDIAN',
                                        'MODERATE_R', 'STRONG_R')),
    offspring_per_litter    INTEGER CHECK (offspring_per_litter > 0),

    -- Senses (Tables VII–VIII)
    primary_sense           TEXT    CHECK (primary_sense IN (
                                        'HEARING', 'VISION', 'TOUCH_TASTE')),
    vision                  TEXT    CHECK (vision IN (
                                        'BLIND', 'DIM', 'NORMAL',
                                        'ACUTE', 'WIDE_ANGLE', 'TELESCOPIC')),
    hearing                 TEXT    CHECK (hearing IN (
                                        'DEAF', 'MUFFLED', 'NORMAL', 'ACUTE', 'SONAR')),
    touch                   TEXT    CHECK (touch IN (
                                        'NUMB', 'NORMAL', 'SENSITIVE', 'SENSITIVE_VIBRATION')),
    taste_smell             TEXT    CHECK (taste_smell IN (
                                        'NONE', 'WEAK', 'NORMAL', 'DISCRIMINATORY')),
    special_senses          INTEGER NOT NULL DEFAULT 0,
    -- bitmask: INFRARED=1, ULTRAVIOLET=2, MAGNETIC=4,
    --          ELECTRIC=8, PRESSURE=16, ECHOLOCATION=32

    -- Mind (Table VIII)
    intelligence            TEXT    CHECK (intelligence IN (
                                        'MINDLESS', 'REACTIVE', 'SELF_AWARE',
                                        'PRE_SAPIENT', 'SAPIENT')),
    iq_typical              INTEGER CHECK (iq_typical >= 1),
    -- NULL unless intelligence = 'SAPIENT'

    -- Social (Table IX)
    mating_behavior         TEXT    CHECK (mating_behavior IN (
                                        'NO_BOND', 'SEASONAL', 'PAIR_BOND',
                                        'HAREM', 'HIVE_DRONE', 'HIVE_QUEEN')),
    social_organization     TEXT    CHECK (social_organization IN (
                                        'SOLITARY', 'PAIR', 'FAMILY', 'BAND',
                                        'TRIBE', 'NATION', 'HIVE')),
    typical_group_size      INTEGER CHECK (typical_group_size > 0),

    -- Vault bridge
    notes                   TEXT,
    obsidian_slug           TEXT    UNIQUE
);
```

---

## 3. species_traits

Optional join table for GURPS racial advantages and disadvantages. Keeps the
main table free of a wide sparse bitmask.

```sql
CREATE TABLE IF NOT EXISTS species_traits (
    id          INTEGER PRIMARY KEY,
    species_id  TEXT    NOT NULL REFERENCES species(species_id) ON DELETE CASCADE,
    trait_name  TEXT    NOT NULL,
    level       INTEGER
    -- NULL for binary traits; populated for levelled traits (e.g. "Night Vision 5")
);

CREATE INDEX IF NOT EXISTS idx_species_traits_species
    ON species_traits(species_id);
```

---

## Migration file

DDL above belongs in `sql/create_species.sql`. Apply with:

```
sqlite3 ~/databases/world.db < sql/create_species.sql
```

---

## Obsidian vault structure

```
worldbuild/
  species/
    <obsidian_slug>.md   ← generated by tools/generate_species_md.py
```

Each file: YAML frontmatter (all mechanical fields) + narrative sections written
by Claude. Frontmatter is the authoritative copy for Obsidian/Dataview queries.
The `species` row is the authoritative copy for the pipeline.

---

## Generation grammar (Python, not persisted)

GURPS Chapter 6 Tables I–IX define probability distributions over traits.
These are encoded as Python enums + weighted choice tables in the build pipeline,
not stored as database rows. Location: `src/generators/alien_tables.py`.

---

## Open questions

1. **story.db for campaign instances**: The `species` table holds canonical
   reference species. Per-campaign mutations or encountered individuals need a
   `campaign_species` table in a separate `story.db` with a soft FK to
   `species_id`. Not in scope yet.

2. **world_settlement over campaign time**: The table captures canonical
   time-0 state. A `SystemEvents` table (also in `world.db` or `story.db`)
   should record changes — population shifts, government collapse, etc.

3. **obsidian_slug naming convention**: `{name_lower_snake_case}` with a
   UUID suffix on collision. Needs a `slugify()` helper in the generator.

4. **special_gestation completeness**: The CHECK constraint currently lists
   only two values. Cross-check Table VI (p. 144–155) for the full set before
   populating data.
