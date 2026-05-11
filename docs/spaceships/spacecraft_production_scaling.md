# Spacecraft Production Scaling — Design Speculation

*2026-05-07. Speculative parameterisation — not yet implemented.*

Extends the industrial scaling framework in `warship_industrial_scaling_formulae.md`
to GURPS Spaceships hulls. All time is in **calendar days**. All mass is in
**metric tonnes**. Cost figures are GURPS $ used as a relative index only — they
are not mapped to a real economy.

---

## 1. The Core Formula

From the warship scaling doc:

```
C = k × M^α × T^β
```

Solving for build time:

```
T = ( C / (k × M^α) )^(1/β)
```

This gives T in whatever units the calibration anchor uses — here, **days**.

The linearised alternative (more physically intuitive) separates materials from
labour and overhead:

```
T = (C − k₁ × M) / (k₂ × M + k₃)
```

where k₁M is material cost, k₂ × M × T is labour (workforce scales with hull
mass), and k₃T is fixed overhead. The power-law form is used here because the
linearised form requires three separate empirical constants that are hard to
anchor from GURPS data alone.

---

## 2. GURPS Spaceships Adaptations

### 2.1 Size Modifier → hull mass

From GURPS Spaceships 1 Hull Size Table. Treated as metric tonnes per unit
convention (no conversion factor applied):

| SM | Hull mass (t) | Example (from spaceships-list.md) |
|:--:|:-------------:|:----------------------------------|
| +5 | 30 | Artemis-class Lander, Ahab-class |
| +6 | 100 | Nova fighter, Storm Bird |
| +7 | 300 | Pioneer-class Freighter, Anson-class Patrol |
| +8 | 1,000 | Deimos-class Frigate, Kilroy-class Scout |
| +9 | 3,000 | Battle-class Frigate, Odyssey-class Explorer |
| +10 | 10,000 | Trinity-class Heavy Cruiser, Victory-class |
| +11 | 30,000 | Ragnarok-class Battleship, Sword-class |
| +12 | 100,000 | Exodus-class Generation Ship |
| +13 | 300,000 | Overlord-class Assault Carrier, Palomar-class |
| +14 | 1,000,000 | Empire-class Battleship, Rock Snake |

Each SM step ≈ ×3 in mass (10^0.5 per step).

### 2.2 Tech Level → production capability

A colony can only build ships up to its own TL. Attempting a ship TL above
colony TL is not a cost/time modifier — it is an industrial impossibility
(missing supply chains, tooling, and expertise).

| Condition | Effect on k |
|---|---|
| Colony TL = ship TL | k × 1.0 (baseline) |
| Colony TL = ship TL + 1 | k × 2.0 (mature production base) |
| Colony TL = ship TL − 1 | k × 0.3 (significant industrial strain) |
| Colony TL < ship TL − 1 | not possible — cannot build |

Superscience systems (TL^) add complexity independent of TL: treat as +1 to the
effective TL requirement for that system only.

### 2.3 Delta-V units

GURPS Spaceships quotes delta-V in mps (miles per second). **1 mps = 1.6 km/s**
(1 mile = 1,609 m; round to 1,600 m). Do not treat mps as km/s — the 38%
underestimate produces significantly wrong travel times.

Thrust acceleration in G is already SI-compatible (1 G = 9.807 m/s²).

Delta-V is a context field on the ship record; it is **not** an input to the
production time formula.

---

## 3. Input Parameters

All inputs needed to compute build time for a single ship.

### 3.1 Ship parameters

| Parameter | Type | Unit | Source |
|---|---|---|---|
| `sm` | integer | — | GURPS SS1 Hull Size Table |
| `hull_mass_t` | float | metric tonnes | derived from `sm` |
| `ship_tl` | integer (or `^`) | — | ship record |
| `ship_class` | enum | — | see §4.1 |
| `gurps_cost` | float | GURPS $ (millions) | ship record |
| `is_prototype` | bool | — | first-of-class vs. production run |
| `production_run_n` | integer ≥ 1 | — | cumulative hulls built of this design |

### 3.2 Colony / industrial parameters

| Parameter | Type | Unit | Source |
|---|---|---|---|
| `colony_tl` | integer | — | `world_settlement.tech_level` |
| `pop_log` | integer 0–13 | log₁₀ persons | `world_settlement.population_log` |
| `starport_class` | enum A–X | — | `world_settlement.starport_class` |
| `rvm` | integer −5 to +5 | — | `world_settlement.resource_value_mod` |
| `construction_env` | enum | — | SURFACE \| ORBITAL \| DEEP_SPACE |

### 3.3 Programme parameters

| Parameter | Type | Unit | Source |
|---|---|---|---|
| `concurrent_builds` | integer ≥ 1 | — | how many slipways simultaneously |
| `schedule_pressure` | enum | — | EMERGENCY \| NORMAL \| EXTENDED |

---

## 4. Parameter Tables

### 4.1 α — displacement exponent by ship class

α > 1: larger ships become disproportionately expensive (complexity explosion).
α < 1: economies of scale dominate.

| `ship_class` | α range | Rationale |
|---|---|---|
| FREIGHTER | 0.75 – 0.90 | Standardised hulls, bulk fabrication; large ships gain scale |
| EXPLORATION | 0.90 – 1.05 | Moderate systems integration; sensor fit adds non-linear cost |
| PATROL / CORVETTE | 1.00 – 1.15 | Weapon and sensor integration begins to dominate |
| CRUISER | 1.10 – 1.30 | Fire-control, crew systems, armour interact non-linearly |
| CAPITAL (battleship, carrier) | 1.25 – 1.50 | Full coordination burden; no two ships identical |
| SUPERSCIENCE-PRIMARY | add +0.20 | Exotic systems integration on top of base class |

Use the midpoint of each range as default; shift toward the upper bound for
prototype or novel designs, lower bound for serial production.

### 4.2 β — schedule exponent by production context

β > 1: delay multiplies cost faster than it extends time (modern procurement
pathology). β < 0.5: industrial throughput is robust and schedule-insensitive.

| Context | β | Notes |
|---|---|---|
| Emergency war production, frozen design | 0.30 – 0.45 | WWII Liberty-ship analogue |
| Mature serial production, stable design | 0.45 – 0.60 | Established shipyard, 3rd+ unit of class |
| Normal peacetime procurement | 0.55 – 0.75 | First or second unit, but no schedule crisis |
| First-of-class prototype | 0.70 – 0.90 | Design changes during build are common |
| Bureaucratically complex programme | 0.90 – 1.40 | Multiple contractors, political intervention |

### 4.3 k — industrial efficiency multiplier (composite)

k is the product of four independent factors. Each factor is dimensionless.

#### Starport factor k_s

| Starport class | k_s | Max SM buildable |
|---|---|---|
| A | 2.0 | unlimited |
| B | 1.0 | +10 |
| C | 0.4 | +8 |
| D | 0.15 | +6 |
| E | 0.04 | +5 |
| X | 0 | not possible |

#### Population factor k_p

Workforce constraint. Below the threshold the limiting factor is finding enough
qualified workers; above it the colony is not workforce-constrained.

| `pop_log` | k_p | Effective max SM |
|---|---|---|
| ≥ 10 | 1.0 | unlimited |
| 9 | 0.9 | +13 |
| 8 | 0.75 | +11 |
| 7 | 0.55 | +9 |
| 6 | 0.35 | +7 |
| < 6 | 0.15 | +6 |

#### Resource factor k_r (from RVM)

| RVM | k_r |
|---|---|
| +4 to +5 | 1.30 |
| +1 to +3 | 1.10 |
| 0 | 1.00 |
| −1 to −3 | 0.75 |
| −4 to −5 | 0.45 |

#### Construction environment factor k_e

| `construction_env` | k_e | Rationale |
|---|---|---|
| ORBITAL | 1.40 | Full hull access simultaneously; microgravity aids large structures |
| SURFACE | 1.00 | Baseline; gravity overhead but mature tooling |
| DEEP_SPACE | 0.60 | Remote logistics; no fixed infrastructure |

#### Composite k

```
k = k_base × k_s × k_p × k_r × k_e
```

`k_base` is set by the calibration anchor below. All other factors are
multipliers relative to that anchor.

### 4.4 Learning curve

For production-run ships, each doubling of cumulative hulls built reduces build
time by a factor L (the learning ratio):

| Ship class | L (time ratio per production doubling) |
|---|---|
| FREIGHTER | 0.82 |
| EXPLORATION / PATROL | 0.87 |
| CRUISER | 0.90 |
| CAPITAL | 0.93 |

```
T_adjusted = T_base × L^( log₂(production_run_n) )
```

First-of-class (n=1): no reduction. Tenth unit of a frigate class: multiply
by 0.87^3.32 ≈ 0.62 — roughly one-third less time than the prototype.

---

## 5. Outputs

| Output | Unit | Meaning |
|---|---|---|
| `build_time_days` | calendar days | keel-laying to commissioning |
| `build_time_display` | human string | days / months / years as appropriate |
| `peak_workforce` | persons | maximum workers simultaneously employed |
| `steady_workforce` | persons | average workers over the full build |

### Display conventions for build time

| `build_time_days` | Display as |
|---|---|
| < 90 | "N days" |
| 90 – 730 | "N months" (round to nearest month) |
| > 730 | "N years" (round to nearest half-year) |

### Workforce estimate

Workforce is not yet derived from the formula — it requires the linearised
model (§1). As a first approximation:

```
peak_workforce ≈ hull_mass_t / build_time_days × workforce_density
```

where `workforce_density` is persons per (tonne/day). Calibration needed;
placeholder range is 0.5–5.0 persons per tonne/day depending on ship class
and TL. This is the most uncertain figure in the model.

---

## 6. Calibration Anchor

One concrete anchor is needed to set `k_base`. Proposed anchor:

> A **TL9 Battle-class Frigate** (SM+9, ~3,000 t, GURPS cost $387M) built at a
> Class A starport, orbital construction, RVM 0, pop_log 9, normal peacetime
> procurement, first-of-class — should take approximately **600 days** (20 months).

This is informed by:
- WWII fleet destroyer construction: 12–18 months (simpler, lower TL)
- Modern destroyer: 3–5 years (more complex, larger, bureaucratically slower)
- 600 days reflects TL9 automation compressing the WWII timeline somewhat, but
  the ship is far more capable than a WWII destroyer

From this anchor and the selected α, β:
- α = 1.20 (CRUISER, midpoint)
- β = 0.65 (normal peacetime, first-of-class)
- k_s = 2.0, k_p = 0.9, k_r = 1.0, k_e = 1.40 → composite factor = 2.52

Solve for k_base from T = 600:

```
600 = (387 / (k_base × 2.52 × 3000^1.20))^(1/0.65)
```

This yields k_base — computed when the model is implemented. All other build
times then derive from this anchor consistently.

---

## 7. Worked Examples (qualitative, pending calibration)

| Ship | SM | Mass (t) | Ship class | Colony | Expected T |
|---|---|---|---|---|---|
| Anson-class Patrol | +7 | 300 | PATROL | TL9, Class A | ~60 days |
| Deimos-class Frigate | +8 | 1,000 | PATROL | TL9, Class A | ~180 days |
| Battle-class Frigate | +9 | 3,000 | CRUISER | TL9, Class A | **600 days** ← anchor |
| Trinity-class Heavy Cruiser | +10 | 10,000 | CRUISER | TL9, Class A | ~1,800 days (5 years) |
| Ragnarok-class Battleship | +11 | 30,000 | CAPITAL | TL8, Class A | ~5,500 days (15 years) |
| Overlord-class Assault Carrier | +13 | 300,000 | CAPITAL | TL10, Class A | ~12,000 days (33 years) |

The carrier number is sobering but defensible — modern supercarriers take 5–7
years and are far smaller. A 300,000-tonne vessel is qualitatively different.

---

## 8. Settlement Data as Production Inputs

The `world_settlement` table in `world.db` provides all colonial parameters
directly. The mapping is:

| Production input | `world_settlement` column |
|---|---|
| `colony_tl` | `tech_level` |
| `pop_log` | `population_log` |
| `starport_class` | `starport_class` |
| `rvm` | `resource_value_mod` |

Construction environment (`construction_env`) is not in `world_settlement` —
it is a property of the shipyard itself, not the world. It belongs on a
`shipyard` table (not yet designed) keyed by `body_id`.

---

## 9. Open Questions

1. **k_base calibration**: The anchor must be computed numerically once α and β
   are fixed. The 600-day anchor is defensible but could be argued either way.
   GURPS gives no canonical build times for spacecraft.

2. **Workforce formula**: The power-law model gives T and C but not Nw directly.
   The linearised model is needed for workforce. Decide which model is primary.

3. **Concurrent builds**: Two hulls built simultaneously at the same yard do not
   take 2× the workforce — there are economies in shared infrastructure. A
   concurrency factor is needed.

4. **TL^ (superscience) ships**: Resolved. Within this setting, ^ tech is
   itemised and assigned a hard numeric TL, faction-qualified. The `^` marker
   becomes a label/provenance flag, not a schema-breaking exception. The
   standard TL-cap rule applies: a colony with faction access to a given ^
   technology at its assigned hard TL can build ships using that technology
   normally. No special production rule is needed beyond tracking which factions
   hold which ^ capabilities.

5. **Repair and refit**: The same formula likely applies with M replaced by
   damaged mass and C replaced by repair cost, but this has not been worked out.

6. **Shipyard table**: `construction_env` and `concurrent_slipways` need a
   `shipyard` table with `body_id` FK. Design deferred.
