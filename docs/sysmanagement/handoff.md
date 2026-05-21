# Session Handoff — 2026-05-07

---

## What this session covered

A full data-architecture session. No data was generated and no SQL was executed.
All output is documentation and Python source.

---

## Decisions made

| Decision | Choice | Rationale |
|---|---|---|
| Storage format for species & settlement | SQLite (`world.db`), not Parquet | Dozens–hundreds of rows; Parquet's columnar advantages don't materialise at this scale; SQLite handles FKs and JOINs natively |
| world.db vs story.db split | Deferred — single database | Only one campaign; cross-database JOIN cost not justified until a second campaign actually exists |
| `starfield.db` dependency | Removed | Physical body data is owned by Meridian; `starfield.db` retained in config.py only if a local cache is ever needed |
| Enum validation — settlement / government / starport / campaign_role | Code tables (FK + seed data) | GMs filter and extend these; labels needed for display without JOIN |
| Enum validation — species biological traits | CHECK constraints | Fixed GURPS vocabulary; written only by generated code through Pydantic; CHECKs are readable and self-documenting |
| Meridian API boundary | JSON in → Pydantic out, translated once at boundary | Loose coupling to Meridian internals; typed objects inside the worlds codebase |
| TL^ (superscience) tech | Itemised with hard numeric TLs, faction-qualified | Standard TL-cap production rule applies unchanged; no schema special case needed |
| Delta-V unit | 1 mps = 1.6 km/s | mps = miles per second; 1:1 treatment is 38% error, too large for travel time calculations |

---

## Unit conventions (established this session — also in memory)

| Source unit | Store as | Factor |
|---|---|---|
| pound (lb) | kilogram (kg) | 1 lb = 0.5 kg |
| yard (yd) | metre (m) | 1 yd = 1 m |
| atmosphere (atm) | bar | 1 atm = 1 bar |
| miles/second (mps) | km/s | 1 mps = 1.6 km/s |
| Fahrenheit | kelvin | K = (°F + 459.67) × 5/9 |

Temperature scale: kelvin for planetary/astronomical contexts; Celsius for
human-scale (habitability, biology, weather). Round to nearest even °C unless
the value is a physical constant used in a calculation (melting points etc.).

All of the above are also saved in project memory.

---

## Files created this session

| File | Purpose |
|---|---|
| `meridian/__init__.py` | Package marker |
| `meridian/models.py` | Pydantic models: `Body`, `System` — typed boundary for Meridian API responses |
| `meridian/api.py` | Stub functions: `get_body()`, `get_system()`, `list_bodies()` — all raise `NotImplementedError` until Meridian API is wired |
| `docs/schema.md` | Combined DDL for all world.db tables: code tables, `world_settlement`, `species`, `species_traits` |
| `docs/data_dictionary.md` | Field-by-field documentation split by Settlements / Species / Spaceships |
| `docs/architecture.md` | Pipeline architecture: data stores, Meridian boundary, generation grammar, Obsidian vault, unit conventions |
| `docs/spaceships/spacecraft_production_scaling.md` | Speculative production scaling formula for spacecraft; inputs/outputs in SI units; calibration anchor defined |

---

## Files modified this session

| File | Change |
|---|---|
| `lifeforms/scripts/generate_species_md.py` | Replaced DuckDB/Parquet with SQLite (`world.db`) + `meridian.api.get_body()`; removed `--parquet-dir` argument |
| `CLAUDE.md` | Updated schema paths; corrected `starfield.db` note; added species schema and data dictionary references |
| `lifeforms/species_schema.md` | **Superseded** by `docs/schema.md` — safe to delete |

---

## Open questions / next actions

1. **`special_gestation` completeness** — CHECK constraint lists only two values
   (`BROOD_PARASITE`, `SEQUENTIAL_HERMAPHRODITE`). Cross-check Table VI
   (pp. 144–155) for the full set before populating species data.

2. **`faction_tech` table** — TL^ capabilities need a table: `body_id`,
   `faction`, `capability`, `hard_tl`. Schema not yet designed.

3. **`shipyard` table** — `construction_env` (SURFACE / ORBITAL / DEEP_SPACE)
   and `concurrent_slipways` are shipyard properties, not world properties.
   Needed before the production scaling formula can be implemented.

4. **Production scaling calibration** — `k_base` must be solved numerically
   from the 600-day anchor once α and β are fixed. See
   `docs/spaceships/spacecraft_production_scaling.md` §6.

5. **SQL migration files** — DDL lives in `docs/schema.md` but the `sql/`
   directory is still empty. Split into executable files before first DB write:
   `sql/create_codes.sql`, `sql/create_world_settlement.sql`,
   `sql/create_species.sql`.

6. **Meridian API implementation** — all three stubs raise `NotImplementedError`.
   The contract is defined in `meridian/api.py`; implementation waits on
   Meridian delivering the API. Ship position will need `get_ship_position()`
   added to the same file when that work begins.

7. **Delete `lifeforms/species_schema.md`** — superseded, no longer maintained.

---

## Meridian cross-reference

There is a counterpart document in the Meridian project believed to be named
`worlds-something.md` (exact name not recalled). It likely covers the Meridian
side of the API contract defined here in `meridian/api.py`. Locate and review
it before implementing the API — there may be field name or type mismatches
between what Meridian plans to return and what `meridian/models.py` currently
expects.

---

## Demo produced

A sapient species (the **Vreth**) was generated end-to-end using the GURPS
Space Chapter 6 tables as a live test of the schema. The species record and
narrative description are in the session transcript. The Vreth are a radially
symmetric, cave-dwelling, exoskeletal, cold-blooded echolocating omnivore with
tribal social structure. They have spaceflight and don't like it.
