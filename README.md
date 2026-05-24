# Worlds

A GURPS worldbuilding browser — explore star systems, planetary bodies, and ship designs via a web interface backed by the Meridian star database.

## Overview

Worlds is a TypeScript monorepo providing:

- **Star browser** — search and filter nearby stars by distance, spectral class, and habitability
- **System view** — orbital diagram with planetary body details (atmosphere, climate, habitability)
- **Ship design** — drag-and-drop GURPS Spaceships design tool

## Architecture

```
worlds/
├── server/          # Hono (Node.js) API server
├── client/          # Vite + Three.js browser client
├── packages/shared/ # Shared TypeScript types
└── supporting/
    ├── meridian/    # Read-only Python boundary layer to the star database
    ├── scripts/     # Database utility scripts
    ├── sql/         # Schemas, queries, migrations
    └── docs/        # Design notes and reference docs
```

The server reads star and system data from the Meridian star database (`STARFIELD_DB`) via [DuckDB](https://duckdb.org/). World-specific data (settlements, species, ships) goes into a separate project database (`WORLDS_DB`).

## Requirements

- Node.js 20+
- [pnpm](https://pnpm.io/) 9+
- Python 3.12+ (for utility scripts only)

## Setup

```sh
# Install dependencies
pnpm install

# Copy env config and set database paths
cp .env.example .env
```

Edit `.env` to point `STARFIELD_DB` and `WORLDS_DB` at your local database files (see `config.py` for the Python side).

## Development

```sh
# Run server and client together
pnpm dev

# Or separately
pnpm server   # API server on http://localhost:3000
pnpm client   # Vite dev server on http://localhost:5173
```

## Build

```sh
pnpm build
```

## API

| Route | Description |
|---|---|
| `GET /api/stars` | Search stars (filter by name, distance, spectral class, HZ eligibility) |
| `GET /api/stars/:id` | Star system detail with bodies |
| `GET /api/stars/by-name?name=` | Redirect to system by name |
| `GET /api/ships` | Ship catalogue |
| `GET /health` | Health check |

## License

MIT — see [LICENSE](LICENSE).
