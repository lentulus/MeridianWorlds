# Species & Obsidian Generation — Project Plan

*Recorded: 2026-05-07. Planning phase.*

## Goal

Add alien species and world settlement data to the Starscape6/Meridian pipeline,
and use the Claude Batch API to initialise Obsidian vault notes for campaign-
significant species from the structured data.

---

## Deliverables already created (planning phase)

| File | Status | Notes |
|---|---|---|
| `docs/plans/species_schema.md` | Done | Parquet schema for species, settlement, traits |
| `tools/prompts/species_system_prompt.md` | Done | Cacheable system prompt for Claude |
| `tools/generate_species_md.py` | Done | Batch API script; not yet runnable (no data yet) |

---

## Phase 1 — Data model (prerequisite for everything)

### 1a. Define Python enums for GURPS Chapter 6 tables

- [ ] Create `src/generators/alien_enums.py`
  - One `enum.StrEnum` per trait column in `species.parquet`
  - Values must exactly match the strings used in the Parquet schema
  - Source: GURPS Space Tables I–IX (pp. 136–170)

- [ ] Create `src/generators/alien_tables.py`
  - Weighted probability tables as `dict[enum, int]` (weights from dice roll ranges)
  - `roll_species(rng, homeworld_body) -> dict` — returns a fully populated row
  - No database access; pure functions over the enum tables

### 1b. Validate schema against PDF

- [ ] Cross-check every `habitat_type`, `government_type`, `special_senses` bitmask
  value against the source pages (pp. 121–123, 134–170) before writing any data
- [ ] Resolve open question 3: settle whether `world_settlement` goes to Parquet
  or directly to `story.db`

---

## Phase 2 — Parquet writer

*Depends on Phase 1. Parquet files live in Meridian, not starscape6.*

- [ ] Create `meridian/writers/write_species.py` (or equivalent in the Meridian project)
  - Accepts a list of `dict` rows conforming to `species.parquet` schema
  - Writes `reference/species.parquet` using PyArrow with Zstd compression
  - Explicit schema (typed, no inference) with nullable columns marked nullable

- [ ] Create `meridian/writers/write_world_settlement.py`
  - Same pattern for `world_settlement.parquet`

- [ ] Write at least 2–3 hand-crafted species rows as test fixtures
  - One PEOPLE (sapient), one BEAST, one with non-water-carbon biochemistry
  - Used to smoke-test the generator before any real data exists

---

## Phase 3 — Obsidian generator (smoke test)

*Depends on Phase 2 test fixtures.*

- [ ] Install dependencies in the working venv:
  ```
  pip install anthropic duckdb pyarrow
  ```

- [ ] Run dry-run against test fixtures:
  ```
  python3 tools/generate_species_md.py \
      --parquet-dir ~/projects/meridian/reference \
      --dry-run
  ```
  Verify the JSON request objects look correct before spending API budget.

- [ ] Review the system prompt output quality
  - Run a single PEOPLE species manually (not via batch) to check prose quality
  - Iterate on `tools/prompts/species_system_prompt.md` as needed
  - Specifically check: does Claude invent facts that contradict the structured data?

- [ ] Confirm Obsidian frontmatter validates correctly
  - Open the output .md in Obsidian and check Dataview can query the frontmatter fields

---

## Phase 4 — Integration with the build pipeline

*After the tool is validated on test fixtures.*

- [ ] Add `alien_tables.py` to the body generation flow
  - Decision needed: generate species at body generation time, or as a separate pass?
  - Recommendation: separate pass, keyed on `life_complexity` field from `BodyLife`

- [ ] Decide what triggers species generation
  - Option A: any world with `life_complexity >= SIMPLE_ANIMALS` gets fauna candidates
  - Option B: explicit authored list only (no automatic generation)
  - This is a campaign design question, not a technical one

- [ ] Add `obsidian_slug` population to the species writer
  - Helper: `slugify(name: str) -> str` — lowercase, hyphens, UUID suffix on collision

---

## Phase 5 — Bulk generation run

*After pipeline integration and manual review of at least 5 species.*

- [ ] Run full batch for all PEOPLE (sapient) species first
  - Smaller set, highest value, use Opus 4.7
- [ ] Review outputs, tune system prompt if needed
- [ ] Run BEAST batch
- [ ] Add `--force` refresh workflow to CLAUDE.md or Makefile

---

## Deferred / out of scope for now

- **world_settlement data entry**: Manual for story-significant systems; automated
  generation at scale is low priority until the campaign needs it
- **species_traits.parquet**: Useful eventually for GURPS character gen; skip until
  species.parquet is stable
- **Obsidian Dataview queries**: The vault consumer will want dashboards over the
  frontmatter fields; out of scope for this plan
- **Re-generation workflow**: When a species row changes in Parquet, the .md file
  needs updating. The `--force` flag handles this manually; an automated watch is
  not planned

---

## Key design decisions recorded

| Decision | Choice | Reason |
|---|---|---|
| Parquet vs story.db for species | Parquet | Reference/canonical; read-only at runtime |
| Parquet vs story.db for settlement | TBD | Settlement changes over campaign time (see open Q3 in schema doc) |
| Generation tables storage | Python enums, not DB rows | Tables are grammar, not data |
| Claude model for sapients | Opus 4.7 | Highest coherence; sapients are few and high-value |
| Claude model for beasts | Sonnet 4.6 | Good prose at 3× lower cost |
| Prompt caching strategy | System prompt cached; user message varies | System prompt is ~1500 tokens, stable across all species in a batch |
| Batch vs streaming | Batch API | Async, 50% cost reduction; latency irrelevant for offline init |
