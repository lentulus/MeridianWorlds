## Reference material
- GURPS rulebooks (PDF): `/Users/lentulus/projects/reference/rules/` — read directly
- Worldbuild tech notes (Markdown): `/Users/lentulus/projects/reference/worldbuild/tech/` — spaceships systems catalogue, ship lists, tech levels, tech tree, mass combat rules
- World DB schema (settlements, species): `supporting/docs/schema.md`
- Data dictionary: `supporting/docs/data_dictionary.md`
- Spaceship DB schema: `supporting/docs/spaceships/spaceship_schema.md`

## Data sources
Database paths are defined in `config.py` — update them there, not in individual scripts.

- `STARFIELD_DB`: path to the immutable star/system database created and owned by the Meridian project. Worlds reads it read-only via `supporting/meridian/api.py`. Do not write to it.
- `WORLDS_DB`: `/Users/lentulus/databases/world.db` — project database for new tables and data.

Import in scripts with: `from config import STARFIELD_DB, WORLDS_DB`

## Project structure

Core implementation:
- `server/` — TypeScript/Hono server (replaces former Python FastAPI server)
- `client/` — TypeScript/Three.js browser client
- `packages/shared/` — shared TypeScript types (server and client both import from here)
- `config.py` — Database paths (single source of truth for Python scripts)

Supporting material:
- `supporting/scripts/` — Python utility scripts
- `supporting/sql/` — SQL files (schemas, queries, migrations)
- `supporting/docs/` — Documentation and design notes
- `supporting/demo/` — TypeScript demo app (star system browser proof of concept)
- `supporting/meridian/` — Read-only Python boundary layer to starfield.db; never redefine its models elsewhere

## Meridian API (Python)
- Import from `supporting/meridian/api.py` and `supporting/meridian/models.py` — never copy or redefine these models.
- To request an API change: append to `supporting/meridian/API_REQUESTS.md` using the template in `supporting/docs/meridian_contract.md`.

## Other
- always ask permission before asking
