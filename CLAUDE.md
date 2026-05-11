## Reference material
- GURPS rulebooks (PDF): `/Users/lentulus/projects/reference/rules/` — read directly
- Worldbuild tech notes (Markdown): `/Users/lentulus/projects/reference/worldbuild/tech/` — spaceships systems catalogue, ship lists, tech levels, tech tree, mass combat rules
- World DB schema (settlements, species): `docs/schema.md`
- Data dictionary: `docs/data_dictionary.md`
- Spaceship DB schema: `docs/spaceships/spaceship_schema.md`

## Data sources
Database paths are defined in `config.py` — update them there, not in individual scripts.

- `STARFIELD_DB`: path to the immutable star/system database created and owned by the Meridian project. Worlds reads it read-only via `meridian/api.py`. Do not write to it.
- `WORLDS_DB`: `/Users/lentulus/databases/world.db` — project database for new tables and data.

Import in scripts with: `from config import STARFIELD_DB, WORLDS_DB`

## Project structure
- `scripts/` — Python scripts
- `sql/` — SQL files (schemas, queries, migrations)
- `docs/` — Documentation
- `config.py` — Database paths (single source of truth)
- `meridian/` — Read-only boundary layer to starfield.db; never redefine its models elsewhere
- `server/` — FastAPI visualization server; exposes starfield and worlds data over HTTP/WebSocket
  - `server/routes/` — one file per data domain (systems, bodies, ships)
  - `server/main.py` — app entry point; run with `uvicorn server.main:app --reload`
- `client/` — Three.js browser visualization (not yet implemented)
  - `client/src/` — JavaScript source

## Meridian API
- Import from `meridian/api.py` and `meridian/models.py` — never copy or redefine these models.
- To request an API change: append to `meridian/API_REQUESTS.md` using the template in `docs/meridian_contract.md`.
- Contract governance design: `docs/meridian_contract.md`

## Other
- always ask permission before asking


