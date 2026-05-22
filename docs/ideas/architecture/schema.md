# World Database Schema

*2026-05-07. Supersedes `lifeforms/species_schema.md`.*

All tables live in `world.db` (`from config import WORLDS_DB`).
`body_id` columns are logical FKs to the Meridian API — SQLite cannot enforce
cross-database foreign keys; integrity is enforced at application level.
Enum validation strategy: **code tables** (FK) for fields a GM queries or
extends; **CHECK** for GURPS biological trait enums (fixed vocabulary,
written only by generated code, Pydantic is primary guard).

---

## 0. Code / lookup tables

Created first; referenced by FK from main tables. Each carries a `sort_order`
so queries can return values in source-book order without sorting by code.

```sql
CREATE TABLE IF NOT EXISTS settlement_type (
    code       TEXT PRIMARY KEY,
    label      TEXT NOT NULL,
    sort_order INTEGER NOT NULL
);
INSERT OR IGNORE INTO settlement_type VALUES
    ('UNINHABITED', 'Uninhabited', 1),
    ('OUTPOST',     'Outpost',     2),
    ('COLONY',      'Colony',      3),
    ('HOMEWORLD',   'Homeworld',   4);


CREATE TABLE IF NOT EXISTS government_type (
    code       TEXT PRIMARY KEY,
    label      TEXT NOT NULL,
    sort_order INTEGER NOT NULL
);
INSERT OR IGNORE INTO government_type VALUES
    ('NO_GOV',         'No Government',            1),
    ('CORPORATION',    'Corporate',                2),
    ('PARTICIPATORY',  'Participatory Democracy',  3),
    ('REPRESENTATIVE', 'Representative Democracy', 4),
    ('TECHNOCRACY',    'Technocracy',              5),
    ('FEUDAL',         'Feudal',                   6),
    ('OLIGARCHY',      'Oligarchy',                7),
    ('SENATE',         'Representative Oligarchy', 8),
    ('DICTATORSHIP',   'Dictatorship',             9),
    ('THEOCRACY',      'Theocracy',               10),
    ('CLAN_TRIBAL',    'Clan / Tribal',           11),
    ('MILITARY',       'Military Dictatorship',   12),
    ('COMMUNIST',      'Communist / Collectivist',13);


CREATE TABLE IF NOT EXISTS starport_class (
    code        TEXT PRIMARY KEY,
    label       TEXT NOT NULL,
    description TEXT,
    sort_order  INTEGER NOT NULL
);
INSERT OR IGNORE INTO starport_class VALUES
    ('A', 'Class A', 'Full industrial — builds and overhauls any ship',   1),
    ('B', 'Class B', 'Major repairs — limited new construction to SM+10', 2),
    ('C', 'Class C', 'Routine repairs — up to SM+8',                      3),
    ('D', 'Class D', 'Limited repairs — up to SM+6',                      4),
    ('E', 'Class E', 'Minimal — emergency services only',                 5),
    ('X', 'Class X', 'No starport',                                        6);


CREATE TABLE IF NOT EXISTS campaign_role (
    code       TEXT PRIMARY KEY,
    label      TEXT NOT NULL,
    sort_order INTEGER NOT NULL
);
INSERT OR IGNORE INTO campaign_role VALUES
    ('PEOPLE',  'People (Sapient)', 1),
    ('BEAST',   'Beast',            2),
    ('THING',   'Thing',            3),
    ('MONSTER', 'Monster',          4);
```

---

## 1. world_settlement

One row per surveyed body. Separated from Meridian body data because most
bodies are uninhabited; settlement data is world.db territory.

```sql
CREATE TABLE IF NOT EXISTS world_settlement (
    body_id              TEXT    NOT NULL PRIMARY KEY,
    -- logical FK → Meridian API body_id

    is_main_world        INTEGER NOT NULL DEFAULT 0
                                 CHECK (is_main_world IN (0, 1)),

    -- Step 31: Geologic Activity (GURPS Space pp. 119–120)
    volcanic_activity    TEXT    CHECK (volcanic_activity IN (
                                     'NONE','LIGHT','MODERATE','HEAVY','EXTREME')),
    tectonic_activity    TEXT    CHECK (tectonic_activity IN (
                                     'NONE','LIGHT','MODERATE','HEAVY','EXTREME')),

    -- Step 32: Resources & Habitability (p. 121)
    resource_value_mod   INTEGER CHECK (resource_value_mod BETWEEN -5 AND 5),
    habitability         INTEGER CHECK (habitability BETWEEN 0 AND 12),
    affinity_score       INTEGER,

    -- Step 33: Settlement Type (pp. 121–122)
    settlement_type      TEXT    NOT NULL DEFAULT 'UNINHABITED'
                                 REFERENCES settlement_type(code),

    -- Step 34: Population (p. 122)
    population           INTEGER CHECK (population >= 0),
    population_log       INTEGER CHECK (population_log BETWEEN 0 AND 13),

    -- Step 35: Government Type (p. 122)
    government_type      TEXT    REFERENCES government_type(code),

    -- Step 36: Control Rating (p. 122)
    control_rating       INTEGER CHECK (control_rating BETWEEN 0 AND 6),

    -- Step 37: Tech Level (p. 122)
    -- Baseline TL only. Superscience (^) capabilities are itemised separately
    -- with a hard numeric TL and faction qualifier.
    tech_level           INTEGER CHECK (tech_level >= 0),

    -- Step 38: Starport Class (p. 123)
    starport_class       TEXT    REFERENCES starport_class(code)
);
```

---

## 2. species

One row per named species. `body_id` is the homeworld. `obsidian_slug` is the
bridge to the Obsidian vault narrative file.

```sql
CREATE TABLE IF NOT EXISTS species (
    species_id              TEXT    NOT NULL PRIMARY KEY,
    body_id                 TEXT,
    -- logical FK → Meridian API body_id (homeworld); NULL for space-native

    name                    TEXT    NOT NULL,
    campaign_role           TEXT    NOT NULL
                                    REFERENCES campaign_role(code),

    -- Biochemistry & habitat (Tables I–II)
    biochem_basis           TEXT    CHECK (biochem_basis IN (
                                        'WATER_CARBON','AMMONIA_CARBON',
                                        'HYDROGEN_NEON','SULFUR','CHLORINE','METHANE')),
    habitat_medium          TEXT    CHECK (habitat_medium IN (
                                        'LAND','WATER','SPACE','ATMOSPHERIC')),
    habitat_type            TEXT    CHECK (habitat_type IN (
                                        'PLAINS','DESERT','ARCTIC','FOREST','JUNGLE',
                                        'MOUNTAINS','OCEAN_SURFACE','OCEAN_SHALLOW',
                                        'OCEAN_DEEP','SWAMP','CAVE','GAS_GIANT',
                                        'ORBITAL','ASTEROID','INTERIOR','VACUUM')),
    trophic_level           TEXT    CHECK (trophic_level IN (
                                        'AUTOTROPH_PHOTO','AUTOTROPH_CHEMO',
                                        'HERBIVORE','OMNIVORE','CARNIVORE',
                                        'SCAVENGER','DECOMPOSER','PARASITE','SYMBIONT')),

    -- Body plan (Table III)
    symmetry                TEXT    CHECK (symmetry IN (
                                        'BILATERAL','TRILATERAL','RADIAL',
                                        'SPHERICAL','ASYMMETRIC')),
    size_class              TEXT    CHECK (size_class IN (
                                        'TINY','SMALL','HUMAN_SCALE','LARGE','HUGE')),
    size_m                  REAL,
    mass_kg                 REAL,

    -- Locomotion (Table IV) — up to 3 modes
    locomotion_primary      TEXT    CHECK (locomotion_primary IN (
                                        'IMMOBILE','SLITHERING','WALKING','RUNNING',
                                        'CLIMBING','SWIMMING','FLYING','GLIDING',
                                        'BURROWING','SPACE')),
    locomotion_secondary    TEXT    CHECK (locomotion_secondary IN (
                                        'IMMOBILE','SLITHERING','WALKING','RUNNING',
                                        'CLIMBING','SWIMMING','FLYING','GLIDING',
                                        'BURROWING','SPACE')),
    locomotion_tertiary     TEXT    CHECK (locomotion_tertiary IN (
                                        'IMMOBILE','SLITHERING','WALKING','RUNNING',
                                        'CLIMBING','SWIMMING','FLYING','GLIDING',
                                        'BURROWING','SPACE')),

    -- Limbs & manipulators (Table VI)
    num_body_segments       INTEGER CHECK (num_body_segments > 0),
    limbs_per_segment       INTEGER CHECK (limbs_per_segment >= 0),
    has_tail                INTEGER NOT NULL DEFAULT 0
                                    CHECK (has_tail IN (0, 1)),
    tail_type               TEXT    CHECK (tail_type IN (
                                        'BALANCE','PREHENSILE','WEAPON','SENSORY')),
    manipulator_sets        INTEGER CHECK (manipulator_sets >= 0),
    manipulator_quality     TEXT    CHECK (manipulator_quality IN (
                                        'NONE','BAD_GRIP','NORMAL','HIGH_DEX','TENTACLE')),

    -- Structure & covering (Table VI)
    skeleton_type           TEXT    CHECK (skeleton_type IN (
                                        'NONE','HYDROSTATIC','EXTERNAL',
                                        'INTERNAL','COMBINATION')),
    covering_type           TEXT    CHECK (covering_type IN (
                                        'SKIN','SCALES','FUR','FEATHERS','EXOSKELETON',
                                        'SHELL','BARK','CRYSTALLINE','OTHER')),
    covering_dr             INTEGER CHECK (covering_dr >= 0),

    -- Metabolism (Table VI)
    breathing               TEXT    CHECK (breathing IN (
                                        'GILLS','LUNGS','BOTH',
                                        'O2_ABSORPTION','DOESNT_BREATHE')),
    temp_regulation         TEXT    CHECK (temp_regulation IN (
                                        'COLD_BLOODED','WARM_BLOODED',
                                        'WARM_METAB_CONTROL','VARIABLE')),

    -- Reproduction (Table VI)
    sexual_arrangement      TEXT    CHECK (sexual_arrangement IN (
                                        'ASEXUAL','HERMAPHRODITE','TWO_SEX',
                                        'THREE_SEX','PARTHENOGENESIS')),
    gestation_method        TEXT    CHECK (gestation_method IN (
                                        'SPAWNING','EGG_LAYING','LIVE_BEARING',
                                        'POUCH','EXTERNAL_LARVAL')),
    special_gestation       TEXT    CHECK (special_gestation IN (
                                        'BROOD_PARASITE','SEQUENTIAL_HERMAPHRODITE')),
    repro_strategy          TEXT    CHECK (repro_strategy IN (
                                        'STRONG_K','MODERATE_K','MEDIAN',
                                        'MODERATE_R','STRONG_R')),
    offspring_per_litter    INTEGER CHECK (offspring_per_litter > 0),

    -- Senses (Tables VII–VIII)
    primary_sense           TEXT    CHECK (primary_sense IN (
                                        'HEARING','VISION','TOUCH_TASTE')),
    vision                  TEXT    CHECK (vision IN (
                                        'BLIND','DIM','NORMAL',
                                        'ACUTE','WIDE_ANGLE','TELESCOPIC')),
    hearing                 TEXT    CHECK (hearing IN (
                                        'DEAF','MUFFLED','NORMAL','ACUTE','SONAR')),
    touch                   TEXT    CHECK (touch IN (
                                        'NUMB','NORMAL','SENSITIVE','SENSITIVE_VIBRATION')),
    taste_smell             TEXT    CHECK (taste_smell IN (
                                        'NONE','WEAK','NORMAL','DISCRIMINATORY')),
    special_senses          INTEGER NOT NULL DEFAULT 0,
    -- bitmask: INFRARED=1, ULTRAVIOLET=2, MAGNETIC=4,
    --          ELECTRIC=8, PRESSURE=16, ECHOLOCATION=32

    -- Mind (Table VIII)
    intelligence            TEXT    CHECK (intelligence IN (
                                        'MINDLESS','REACTIVE','SELF_AWARE',
                                        'PRE_SAPIENT','SAPIENT')),
    iq_typical              INTEGER CHECK (iq_typical >= 1),
    -- NULL unless intelligence = 'SAPIENT'

    -- Social (Table IX)
    mating_behavior         TEXT    CHECK (mating_behavior IN (
                                        'NO_BOND','SEASONAL','PAIR_BOND',
                                        'HAREM','HIVE_DRONE','HIVE_QUEEN')),
    social_organization     TEXT    CHECK (social_organization IN (
                                        'SOLITARY','PAIR','FAMILY','BAND',
                                        'TRIBE','NATION','HIVE')),
    typical_group_size      INTEGER CHECK (typical_group_size > 0),

    -- Vault bridge
    notes                   TEXT,
    obsidian_slug           TEXT    UNIQUE
);
```

---

## 3. species_traits

Join table for GURPS racial advantages and disadvantages. Avoids a wide sparse
column set on the main species table.

```sql
CREATE TABLE IF NOT EXISTS species_traits (
    id          INTEGER PRIMARY KEY,
    species_id  TEXT    NOT NULL
                        REFERENCES species(species_id) ON DELETE CASCADE,
    trait_name  TEXT    NOT NULL,
    level       INTEGER
    -- NULL for binary traits; set for levelled traits e.g. "Night Vision 5"
);

CREATE INDEX IF NOT EXISTS idx_species_traits_species
    ON species_traits(species_id);
```

---

## Migration

```
PRAGMA foreign_keys = ON;
sqlite3 ~/databases/world.db < sql/create_world.sql
```

DDL execution order: code tables → world_settlement → species → species_traits.
