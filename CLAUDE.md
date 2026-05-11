## Reference material
- GURPS rulebooks (PDF): `/Users/lentulus/projects/reference/rules/` — read directly
- Worldbuild tech notes (Markdown): `/Users/lentulus/projects/reference/worldbuild/tech/` — spaceships systems catalogue, ship lists, tech levels, tech tree, mass combat rules
- World DB schema (settlements, species): `docs/schema.md`
- Data dictionary: `docs/data_dictionary.md`
- Spaceship DB schema: `docs/spaceships/spaceship_schema.md`

## Data sources
Database paths are defined in `config.py` — update them there, not in individual scripts.

- `STARFIELD_DB`: not a direct file dependency. Physical body and system data comes from the Meridian API (`meridian/api.py`). `STARFIELD_DB` in config.py is retained only if a local cache is ever needed.
- `WORLDS_DB`: `/Users/lentulus/databases/world.db` — project database for new tables and data.

Import in scripts with: `from config import STARFIELD_DB, WORLDS_DB`

## Project structure
- `scripts/` — Python scripts
- `sql/` — SQL files (schemas, queries, migrations)
- `docs/` — Documentation
- `config.py` — Database paths (single source of truth)

## Meridian API
- Import from `meridian/api.py` and `meridian/models.py` — never copy or redefine these models.
- To request an API change: append to `meridian/API_REQUESTS.md` using the template in `docs/meridian_contract.md`.
- Contract governance design: `docs/meridian_contract.md`

## Other
- always ask permission before asking


