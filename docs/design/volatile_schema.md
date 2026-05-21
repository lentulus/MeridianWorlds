# colonybase.db — Volatile Schema

**File:** `meridian/VolatileData/colonybase.db`  
**Sources:** `colony-model.md`, `colony-sim-design.md` (WTH + GURPS RM + Turchin 2013)

---

## Parameter variation: species vs. culture

The colony model has a single aggregate population with uniform parameters. With multiple
cultures and species the parameters split into three tiers:

**Species-level (biological — same for all cultures of that species):**

| Parameter | Symbol | Rationale |
|-----------|--------|-----------|
| Base growth rate | r₀ | Reproductive biology |
| Working-age fraction | λ | Lifespan and maturation rate |
| Min rations per person | r_min | Metabolic requirement |
| Nutrition stress exponent | κ_N | Biological resilience to food scarcity |

**Culture-level (social — varies among cultures within a species):**

| Parameter | Symbol | Rationale |
|-----------|--------|-----------|
| Min living standard | l_min | Cultural consumption expectations |
| Social mobility rate | μ₀ | Caste vs. meritocracy |
| Max elite fraction | s_max | Degree of social stratification |
| Mobility-neutral welfare threshold | w₀ | What the culture considers "adequate" |
| Wage-stickiness lag | τ | Labor contract norms |
| Wage labor-market elasticity | β | Market vs. command economy orientation |
| Settlement fraction tendency | f_set | Nomadic vs. sedentary preference |
| Loyalty gain per PT step | α_PT | Political temperament |
| Loyalty erosion per PSI unit | α_Ψ | Political temperament |

**Colony-level (set by governance, applies to all residents):**

r_a, phi_min, p0, qm_mult — planet physics, unchanged.
Control Rating (CR), Education Rating (ER), capital allocation, housing — policy decisions
of the colonial administration, not cultural. ER in particular is an infrastructure
investment that all cultures draw on, though their effective productivity differs via β.

**Mixed:** A culture may override species defaults where technology or cultural practice
has shifted the biological baseline (e.g. advanced medicine raising effective r₀). Store
these as culture-level values; the species row provides the fallback.

---

## Key design constraints

**body_id is sector-local.** In Meridian, `body_id` is a sequential integer unique only
within a sector. The globally unique body reference is `(system_id, body_id)`. The `colony`
table enforces `UNIQUE(system_id, body_id)` and uses a local surrogate `colony_id` for
internal FKs so joins never rely on `body_id` alone.

**Time is seconds from a configurable epoch.** All `sim_time` columns are `INTEGER` (SQLite
stores this as 64-bit, equivalent to bigint). The epoch zero-point is stored in `epoch_config`
and resolved at application startup. Sim months are also stored as a convenience counter.

**Snapshots store derived outputs.** The colony simulation computes many derived quantities
(welfare, PSI, elite fraction, etc.) from raw state. Storing them avoids recomputation on
every query and preserves the exact values that drove the next step's stochastic events.

---

## Tables

### culture

Master registry of cultures. A culture belongs to at most one species (`species_id` is a
logical FK to `world.db species`; NULL for multi-species or survey/administrative entities
that name things but have no resident population). All parameter columns are NULL when the
model default applies; the application resolves via COALESCE(culture param, species default,
model default).

Species-level parameters (r₀, λ, r_min, κ_N) should be identical across all cultures of
the same species. They are stored on the culture row so that mixed-species cultures and
cultural overrides of biological baselines (e.g. advanced medicine) can be expressed
without a separate species-params table.

```sql
CREATE TABLE IF NOT EXISTS culture (
    culture_id   TEXT PRIMARY KEY,  -- short code, e.g. 'TERRAN', 'VILANI'
    name         TEXT NOT NULL,
    species_id   TEXT,              -- logical FK → world.db species.species_id; NULL = multi-species

    -- Species-level biological parameters (NULL = model default)
    r0_annual    REAL,   -- base pop growth rate y⁻¹; default 0.02
    lambda       REAL,   -- working-age fraction; default 0.55
    r_min        REAL,   -- min rations per person per month
    kappa_n      REAL,   -- nutrition stress exponent; default 2.0

    -- Culture-level social/economic parameters (NULL = model default)
    l_min_base   REAL,   -- min living standard cr/person/month
    mu0          REAL,   -- social mobility coefficient mo⁻¹; default 0.005
    s_max        REAL,   -- max elite fraction; default 0.05
    w0           REAL,   -- mobility-neutral welfare threshold; default 1.0
    tau_months   REAL,   -- wage-stickiness lag months; default 3–5
    beta         REAL,   -- wage labor-market elasticity; default 0.5
    f_set_base   REAL,   -- settlement fraction baseline tendency

    -- Political temperament (NULL = model default)
    alpha_pt     REAL,   -- loyalty gain per PT improvement step
    alpha_psi    REAL    -- loyalty erosion per PSI unit per month
);
```

---

### epoch_config

Global time reference. Application reads this at startup.

```sql
CREATE TABLE IF NOT EXISTS epoch_config (
    key         TEXT    PRIMARY KEY,
    epoch_unix  INTEGER NOT NULL,
    -- Unix timestamp (seconds since 1970-01-01 UTC) of sim t=0
    description TEXT
);
INSERT OR IGNORE INTO epoch_config VALUES
    ('campaign', 0, 'Default — override with campaign start Unix timestamp');
```

---

### colony

One row per colony. Holds only what Meridian does not: the colony's name, its founding
time, and any GM overrides to the derived sim parameters. All planet physical data
(atmosphere, world type, habitability, RVM, etc.) is read from Meridian at query time
via `(system_id, body_id)`.

Sim parameter overrides are NULL when the Meridian-derived default applies. The
application resolves: `COALESCE(override, meridian_derived_value)`.

```sql
CREATE TABLE IF NOT EXISTS colony (
    colony_id       INTEGER PRIMARY KEY,

    -- Meridian reference — body_id alone is NOT unique; composite key is authoritative
    system_id       TEXT    NOT NULL,
    body_id         INTEGER NOT NULL,
    UNIQUE (system_id, body_id),

    name            TEXT    NOT NULL,
    founded_at      INTEGER NOT NULL,  -- sim_time (seconds from epoch)

    -- GM overrides for derived sim parameters; NULL = use Meridian-derived value
    -- Formulas for defaults are in colony-sim-design.md § Mapping formulas
    override_r_a             REAL,   -- agricultural richness (1.0–5.0)
    override_phi_min         REAL,   -- growing-season floor
    override_lmin_mult       REAL,   -- life-support cost multiplier
    override_p0              REAL,   -- base disruption probability / month
    override_qm_mult         REAL,   -- materials yield multiplier (RVM effect)
    override_season_months   REAL    -- season cycle length
);
```

---

### colony_snapshot

Time-series state. One row per simulation step per colony. The sim advances in monthly
steps; each step appends one row.

```sql
CREATE TABLE IF NOT EXISTS colony_snapshot (
    snapshot_id     INTEGER PRIMARY KEY,
    colony_id       INTEGER NOT NULL REFERENCES colony(colony_id) ON DELETE CASCADE,
    sim_time        INTEGER NOT NULL,   -- seconds from epoch
    sim_month       INTEGER NOT NULL,   -- months from founding (convenience counter)

    -- ── Raw state (from advanceState) ────────────────────────────────────────
    -- Population
    population      INTEGER NOT NULL CHECK (population >= 0),  -- N
    elite_pop       INTEGER NOT NULL CHECK (elite_pop >= 0),   -- E
    housing         REAL    NOT NULL CHECK (housing >= 0),     -- H [berths]

    -- Capital deployed [capital-units]
    capital_agri    REAL    NOT NULL CHECK (capital_agri >= 0),      -- AC
    capital_indus   REAL    NOT NULL CHECK (capital_indus >= 0),     -- IC
    capital_materials REAL  NOT NULL CHECK (capital_materials >= 0), -- MC
    power_capacity  REAL    NOT NULL CHECK (power_capacity >= 0),    -- PC [MW]

    -- Labor assigned [persons]
    labor_agri      REAL    NOT NULL CHECK (labor_agri >= 0),        -- AL
    labor_indus     REAL    NOT NULL CHECK (labor_indus >= 0),       -- IL
    labor_materials REAL    NOT NULL CHECK (labor_materials >= 0),   -- ML

    -- Fiscal
    debt            REAL    NOT NULL,    -- Y [credits]; can be negative (surplus)
    citizen_loyalty REAL    NOT NULL CHECK (citizen_loyalty BETWEEN 0.0 AND 1.0),  -- CL
    political_track INTEGER NOT NULL CHECK (political_track BETWEEN -3 AND 3),     -- PT

    -- Slow-changing governance (can be updated between steps by GM policy)
    control_rating  INTEGER NOT NULL CHECK (control_rating BETWEEN 2 AND 6),  -- CR
    education_rating INTEGER NOT NULL CHECK (education_rating BETWEEN 0 AND 6), -- ER

    -- ── Derived outputs (from computeSnapshot) ───────────────────────────────
    -- Economic outputs (per month)
    output_rations  REAL,   -- Q_A [rations/mo]
    output_credits  REAL,   -- Q_I [cr/mo]
    output_materials REAL,  -- Q_M [tonnes/mo]
    gdp_annual      REAL,   -- G [cr/year]

    -- Satisfaction indices [dimensionless; 1.0 = adequate]
    std_nutrition   REAL,   -- S_N
    std_shelter     REAL,   -- S_S
    std_living      REAL,   -- S_L
    welfare         REAL,   -- w = (S_N + S_S + S_L) / 3

    -- Elite dynamics
    elite_fraction  REAL,   -- e = E/N
    elite_income    REAL,   -- ε = (1 − w·λ) / e

    -- Political Stress Indicator components
    mmp             REAL,   -- Mass Mobilization Potential
    emp             REAL,   -- Elite Mobilization Potential
    sfd             REAL,   -- State Fiscal Distress
    psi             REAL,   -- Ψ = MMP × EMP × SFD

    -- Fiscal
    debt_to_gdp     REAL,   -- Y/G (months of GDP)
    trade_revenue   REAL,   -- T_rev received this step [cr/mo]
    export_tonnage  REAL,   -- X(t) shipped this step [dt/mo]
    realm_value     REAL,   -- V [cr]

    -- Disruption risk
    disruption_prob REAL    -- p_dis = p0 · Ψ^κ [probability/month]
);

CREATE INDEX IF NOT EXISTS idx_snapshot_colony_time
    ON colony_snapshot (colony_id, sim_time);
```

---

### colony_culture_state

Per-culture population breakdown, one row per culture present in a colony per sim step.
Rows sum to the aggregate totals in `colony_snapshot`. The sim computes culture states
first, then aggregates; the snapshot is the authoritative colony-level record.

`citizen_loyalty` here is the loyalty of this cultural group to the colonial
administration — it may differ sharply from the colony aggregate (a suppressed minority
culture will have low loyalty even in an otherwise stable colony).

```sql
CREATE TABLE IF NOT EXISTS colony_culture_state (
    id              INTEGER PRIMARY KEY,
    colony_id       INTEGER NOT NULL REFERENCES colony(colony_id) ON DELETE CASCADE,
    culture_id      TEXT    NOT NULL REFERENCES culture(culture_id),
    sim_time        INTEGER NOT NULL,
    sim_month       INTEGER NOT NULL,

    -- Raw state
    population      INTEGER NOT NULL CHECK (population >= 0),   -- N_c
    elite_pop       INTEGER NOT NULL CHECK (elite_pop >= 0),    -- E_c

    -- This culture's labor contribution to the colony pool
    labor_agri      REAL    NOT NULL DEFAULT 0 CHECK (labor_agri >= 0),
    labor_indus     REAL    NOT NULL DEFAULT 0 CHECK (labor_indus >= 0),
    labor_materials REAL    NOT NULL DEFAULT 0 CHECK (labor_materials >= 0),

    -- Political state
    citizen_loyalty REAL    CHECK (citizen_loyalty BETWEEN 0.0 AND 1.0),  -- CL_c

    -- Derived (culture-specific, using this culture's parameter set)
    welfare         REAL,   -- w_c
    elite_fraction  REAL,   -- e_c = E_c / N_c
    elite_income    REAL,   -- ε_c
    psi             REAL    -- Ψ_c
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_culture_state_key
    ON colony_culture_state (colony_id, culture_id, sim_time);
CREATE INDEX IF NOT EXISTS idx_culture_state_colony_time
    ON colony_culture_state (colony_id, sim_time);
```

---

### colony_event

Log of disruption events fired during the simulation. Each row is one event instance.

```sql
CREATE TABLE IF NOT EXISTS colony_event (
    event_id        INTEGER PRIMARY KEY,
    colony_id       INTEGER NOT NULL REFERENCES colony(colony_id) ON DELETE CASCADE,
    sim_time        INTEGER NOT NULL,   -- seconds from epoch when event fired
    sim_month       INTEGER NOT NULL,

    event_type      TEXT    NOT NULL CHECK (event_type IN (
                        'PLAGUE','FAMINE','CORRUPTION','SCHISM',
                        'FAUNA','POLLUTION','EMBARGO','OTHER')),
    description     TEXT,
    severity        REAL    -- magnitude drawn at event time; interpretation is type-specific
);

CREATE INDEX IF NOT EXISTS idx_event_colony_time
    ON colony_event (colony_id, sim_time);
```

---

### celestial_name

Any star, planet, moon, or star system can carry any number of names — one per culture
per assignment event. All historical assignments are kept; the application selects the
current name by querying the most recent `assigned_at` for a given object and culture.

`body_id` NULL means the name applies to the **system** as a whole. `body_id` set means
it applies to the specific body within that system. The same `(system_id, body_id)`
composite key rules apply as everywhere else.

```sql
CREATE TABLE IF NOT EXISTS celestial_name (
    name_id     INTEGER PRIMARY KEY,
    system_id   TEXT    NOT NULL,
    body_id     INTEGER,            -- NULL = system-level name
    culture     TEXT    NOT NULL,   -- matches culture.culture_id where possible; free text for survey agencies / historical empires with no resident population
    name        TEXT    NOT NULL,
    assigned_at INTEGER NOT NULL    -- sim_time (seconds from epoch)
);

CREATE INDEX IF NOT EXISTS idx_name_object
    ON celestial_name (system_id, body_id);
CREATE INDEX IF NOT EXISTS idx_name_culture
    ON celestial_name (culture, system_id, body_id);
```

---

### immigration_wave and trade_shipment — deferred

**Not defined here.** The base colony-sim model treats immigration and trade as simple
fixed-lag queues (12 months in, 24 months round-trip). At thousands of colonies these
become a multi-colony flow network — transit times vary by distance, convoys serve
multiple destinations, colonies trade with each other not just with Earth, and capacity
constraints are shared across routes.

That model requires its own design pass. Until then:

- The snapshot columns `trade_revenue` and `export_tonnage` record what the sim
  computed each step; they are the durable record of economic flow.
- Pending-convoy state can be carried in a JSON blob in `colony_snapshot` or in a
  separate scratch table outside this schema, whichever suits the sim implementation.

---

## Creation order

```sql
PRAGMA foreign_keys = ON;
-- 1. culture
-- 2. epoch_config
-- 3. colony
-- 4. celestial_name
-- 5. colony_snapshot
-- 6. colony_culture_state
-- 7. colony_event
```

---

## Notes

**Class structure.** The Turchin model is two-class: elites (E) hold positional slots
(S_pos = s_max × N); everyone else is a commoner. This is intentional for the initial
build. Planned extension: either a Gini-index scalar derived from the elite/commoner
income split (ε vs. w·λ), or a Marxist multi-class breakdown (capital owners, skilled
workers, labor, marginal). Either approach adds columns to `colony_culture_state` without
restructuring it.

**Scale.** At thousands of colonies the `colony_snapshot` table will be the largest
by far (colonies × months × row size). The index on `(colony_id, sim_time)` covers
the primary access pattern (one colony's history). Cross-colony queries at a fixed
`sim_time` (e.g., "all colonies with Ψ > 2 this step") need a separate index on
`(sim_time, psi)` — add it when that query pattern is confirmed, not speculatively.
SQLite handles tables of this size comfortably; if write throughput becomes a
bottleneck when advancing thousands of colonies in bulk, batch inserts in a single
transaction are the first lever.

**Meridian path.** `colony_export.py` has a `MERIDIAN` constant that must point to
`/Volumes/Lexar/MeridianData` (see transfer checklist in `colony-sim-design.md`).
`config.py` now exposes this as `MERIDIAN_DATA_PATHS[0]`.

**Sector key warning.** Any query joining against Meridian data must use
`(system_id, body_id)` together. Filtering on `body_id` alone will silently match
bodies from different sectors.

**Derived columns.** The derived output columns in `colony_snapshot` are nullable.
A row written by a partial import (e.g., restoring raw state only) will have NULLs
there. The application must tolerate this and recompute on demand.

**Month length.** The model uses calendar months as its step unit. When converting
to seconds, use 30 × 24 × 3600 = 2 592 000 s/month throughout for consistency.
Do not use variable-length months.
