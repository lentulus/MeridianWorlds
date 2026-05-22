# Worlds UI — Client/Server Design

*2026-05-22*

Source: `supporting/docs/design/Worlds/functions.md`

---

## Overview

Four distinct UI functions, two data domains:

| UI function | Primary data source |
|---|---|
| Star List + Map | Meridian parquet (systems, stars) |
| System Orbit Display | Meridian parquet (bodies — orbit + physical) |
| Ship Design tool | `SHIP_DB` SQLite (ships, hull_sizes, system_catalog, slots) |

The server is the single access point for all data. The client never touches
a database directly.

---

## Data sources the server must expose

| Source | Format | Access pattern |
|---|---|---|
| Meridian `/Volumes/Lexar/MeridianData/` | Parquet (ZSTD, sector files) | DuckDB glob + manifest sector lookup |
| `WORLDS_DB` `/Users/lentulus/databases/world.db` | SQLite | Settlement and species overlays (future) |
| `SHIP_DB` (path from `config.py`) | SQLite | Full ship design data |

The manifest SQLite at `MeridianData/manifest.db` maps spatial coordinates to
sector files (see `demo/` implementation for the proven pattern).

---

## Server

### Language: TypeScript / Hono

The server is TypeScript throughout. The client is also TypeScript. Shared type
definitions live in a `packages/shared/` workspace imported by both — no code
generation step, no OpenAPI artefact to keep in sync.

Stack:
- **Hono** with `@hono/node-server` — HTTP framework
- **DuckDB** (`duckdb` npm) — reads Meridian parquet and SQLite via the built-in
  sqlite extension (see demo for the proven sector-lookup pattern)
- **pnpm workspaces** — monorepo linking `packages/shared`, `server`, `client`

The existing Python code in `server/` is superseded. The DuckDB approach
demonstrated in `demo/` transfers directly to the new server.

### Project layout

```
worlds/
  package.json              pnpm workspace root
  config.py                 Database paths — single source of truth for Python scripts
  packages/
    shared/
      src/
        types.ts            All API request/response types — single source of truth
  server/
    src/
      main.ts               Hono app entry point
      db/
        meridian.ts         DuckDB + manifest sector lookup (from demo)
        ships.ts            SHIP_DB queries via DuckDB sqlite extension
      routes/
        stars.ts            /api/stars/* handlers
        ships.ts            /api/ships/* handlers
    package.json
  client/
    src/
      main.ts               Entry point — router, layout shell
      views/
        StarList.ts         Filterable table + Display button
        SystemView.ts       SVG orbit diagram + body panel
        ShipDesign.ts       Slot grid + catalogue picker + live stats
      api/
        stars.ts            Typed fetch wrappers for /api/stars/*
        ships.ts            Typed fetch wrappers for /api/ships/*
      state/
        selection.ts        Shared selection signal (list row ↔ map point)
      components/
        StarMap.ts          Three.js point cloud — receives StarListRow[], no fetch
        OrbitDiagram.ts     SVG orbital ellipse renderer (2D)
        BodyPanel.ts        Body physical data sidebar
        SlotGrid.ts         20-slot hull layout — drag-and-drop system assignment
        CatalogPanel.ts     System catalogue with category grouping + filter
    package.json
  supporting/
    docs/                   Design documents and reference notes
    demo/                   TypeScript proof-of-concept (star system browser)
    meridian/               Python read-only boundary layer to Meridian parquet data
    scripts/                Python utility scripts (db init, seeding)
    sql/                    SQL schemas, queries, migrations
```

### Base URL structure

```
/api/stars/...        Star and system data (Meridian parquet)
/api/ships/...        Ship design data (SHIP_DB)
/                     Serves client/dist/ in production
```

### Named-system startup cache

On server start, DuckDB scans all 729 system sector files once and builds a
lightweight in-memory index:

```typescript
interface NamedSystemIndex {
  [name_lower: string]: {
    system_id: string;
    primary_name: string;
    dist_pc: number;
    x_mpc: number; y_mpc: number; z_mpc: number;
    sector_key: string;   // derived from parquet file path
  }
}
```

This index is used for system-by-name lookups (Star List search,
`/api/stars/by-name`) so those return instantly. It is not persisted to disk —
rebuilt on each server start (~0.2 s for the glob scan).

---

## 1. Star List

A filterable, sortable table of named star systems. A **Display** button renders
the current results in the Star Map (see §2). There is no separate map endpoint —
the map is a view of whatever the list has already fetched.

### API endpoint

```
GET /api/stars
```

#### Query parameters

| Parameter | Type | Description |
|---|---|---|
| `name` | string | Partial match on system name (index lookup) |
| `dist_max_ly` | float | Maximum distance from Sol in light-years |
| `dist_min_ly` | float | Minimum distance |
| `spectral` | string | Spectral class prefix (e.g. `G`, `M`, `K`) |
| `hz_eligible` | bool | Only systems with at least one HZ-eligible star |
| `sort` | string | Column to sort by (`name`, `dist_ly`, `age_gyr`) |
| `dir` | `asc`/`desc` | Sort direction |
| `limit` | int | Max rows (default 100, max 500) |
| `offset` | int | Pagination offset |

#### Response shape

Coordinates are always included so the map can render without a second request.

```typescript
interface StarListResponse {
  total: number;
  rows: StarListRow[];
}

interface StarListRow {
  system_id: string;
  name: string;
  dist_ly: number;
  age_gyr: number | null;
  primary_spectral: string;
  luminosity_sol: number;
  hz_eligible: boolean;
  body_count: number;
  x_mpc: number;
  y_mpc: number;
  z_mpc: number;
}
```

#### Server query strategy

Name and distance filters are resolved against the startup index (instant).
`spectral` and `hz_eligible` require a DuckDB join against the stars parquet
for the matching sectors.

---

## 2. Star Map

A Three.js 3D display of the current Star List results. The user sets filters
and paginates in the Star List, then presses **Display** to see those rows
plotted in 3D space. There is no separate API call — the map receives the
`StarListRow[]` already in memory.

The map and list are two views of the same dataset. Clicking a point in the map
highlights the corresponding row in the list (and vice versa) via the shared
`selection.ts` signal. Clicking a point also opens the System Orbit view.

### No separate API endpoint

The map is a pure client-side rendering of the list data. `x_mpc`, `y_mpc`,
`z_mpc` on `StarListRow` supply the 3D coordinates.

### Three.js rendering

- Each `StarListRow` becomes a point, coloured by `primary_spectral`:
  O=blue, B=blue-white, A=white, F=yellow-white, G=yellow, K=orange, M=red
- Scale: 1 mpc = 1 scene unit; Sol sits at (0, 0, 0)
- Orbit controls for pan, zoom, and rotate
- Hover tooltip: system name + distance
- Raycasting on click → sets `selection.ts` → highlights list row → opens
  System view on double-click

---

## 3. System Orbit Display

A 2D graphical view of one system — star(s) at the centre, bodies on orbital
ellipses drawn in SVG. Physical detail shown in a side panel on click/hover.
Designed for upgrade to Three.js 3D later without changing the data model.

### API endpoints

```
GET /api/stars/{system_id}
GET /api/stars/by-name?name=Sol
```

`by-name` resolves via the startup index and redirects to the `system_id` form,
so the client URL always uses the opaque ID after the first lookup.

#### Response shape

```typescript
interface SystemDetail {
  system_id: string;
  name: string;
  dist_ly: number;
  age_gyr: number | null;
  stars: StarDetail[];
  bodies: BodyDetail[];
}

interface StarDetail {
  star_id: string;
  component: string;
  spectral: string;
  luminosity_sol: number;
  hz_eligible: boolean;
}

interface BodyDetail {
  body_id: string;
  star_id: string;
  body_type: string;
  in_hz: boolean;
  size_km: number;
  mass_kg: number;
  orbit_au: number;
  eccentricity: number;
  moonlet_count: number;
  world_type: string | null;
  atmosphere: string | null;
  temp_k: number | null;
  climate: string | null;
  habitability: number | null;
  affinity: number | null;
}
```

#### Orbit rendering (SVG, 2D)

```
semi-major axis  a = orbit_au
semi-minor axis  b = a × √(1 − eccentricity²)
focus offset     c = a × eccentricity   (star sits at one focus)
```

Bodies are rendered as coloured circles on the ellipse path — not to scale,
but sized relationally (gas giants larger than rocks). Colour by `world_type`:
green for Garden, blue for ocean worlds, grey for rock, orange for Infernal,
white for ice. HZ bodies get a subtle ring highlight.

---

## 4. Ship Design Tool

A full interactive design tool. The user selects a hull size and TL, then
assembles a ship by assigning systems from a categorised catalogue into the
20 available slots. Stats and cost are derived and displayed live.

A ship design can be saved to `SHIP_DB`. Existing designs can be loaded and
edited. Read-only catalogue access (hull sizes, system stats) is unauthenticated;
save/edit requires no authentication in this single-user context.

### API endpoints

```
GET  /api/ships/hull-sizes                Hull SM reference table
GET  /api/ships/catalog?tl=8&sm=8        Systems available at a TL/SM
GET  /api/ships/catalog/{id}/stats?sm=8  Per-SM stats for one system
GET  /api/ships                           List saved designs (with filters)
GET  /api/ships/{ship_id}                 Full design with slots
POST /api/ships                           Create new design
PUT  /api/ships/{ship_id}                 Update design header fields
PUT  /api/ships/{ship_id}/slots           Replace all slot assignments
DELETE /api/ships/{ship_id}              Delete design
```

#### Hull sizes response

```typescript
interface HullSize {
  sm: number;
  mass_tons: number;
  length_m: number;       // stored as yards, displayed as metres (1 yd = 1 m)
  dst_hp: number;
  handling: number;
  stability_rating: number;
}
```

#### Catalogue response

Returns all systems the user can install given the chosen TL. Grouped by
category for the picker UI.

```typescript
interface CatalogResponse {
  tl: number;
  sm: number;
  systems: CatalogEntry[];
}

interface CatalogEntry {
  system_id: number;
  name: string;
  category: string;
  tl_min: number | null;
  is_superscience: boolean;
  location: string;           // "ANY", "HULL", "FRONT", "REAR", "SPECIAL"
  is_high_energy: boolean;
  // stats at the requested SM (from system_sm_stats or armor_sm_stats)
  cost_dollars: number | null;
  workspaces: number | null;
  power_points: number | null;    // provided (power plants)
  acceleration_g: number | null;  // drives
  ddr_us: number | null;
  ddr_sl: number | null;
  stat_notes: string | null;
}
```

#### Ship design response

```typescript
interface ShipDesign {
  ship_id: number;
  name: string | null;
  class_name: string | null;
  hull_number: string | null;
  type_name: string;
  bureau_name: string | null;
  tl: number;
  is_superscience: boolean;
  sm: number;
  is_streamlined: boolean;
  // derived totals
  cost_dollars: number;
  power_points_available: number;
  power_points_consumed: number;
  // header stats
  dst_hp: number;
  handling: number;
  stability_rating: number;
  ht: number;
  occ_crew: number;
  occ_passengers: number;
  move_acceleration_g: number | null;
  move_delta_v_mps: number | null;
  move_is_ftl: boolean;
  ddr_front: number;
  ddr_central: number;
  ddr_rear: number;
  design_features: string[];
  notes: string | null;
  slots: SlotDetail[];
}

interface SlotDetail {
  hull_section: 'front' | 'central' | 'rear';
  slot_number: number | null;   // null = core slot
  slot_to: number | null;       // non-null for multi-slot spans
  is_core: boolean;
  is_high_energy: boolean;
  system_id: number | null;     // null = empty slot
  system_name: string | null;
  category: string | null;
  detail: string | null;        // free text: "50 tons", "1G acceleration"
}
```

#### Slot grid UI

The design tool shows three columns (front / central / rear), each with 6
numbered slots plus one core slot. Empty slots are drop targets. The system
catalogue panel sits to one side, grouped by category, filtered by TL.

Dragging a catalogue entry onto a slot assigns it; right-click removes it.
The `location` field on each system restricts where it can land (`FRONT` only
goes in the front section, etc.). High-energy systems show a ⚡ badge; the
running PP budget is displayed at the top.

Cost and derived stats (acceleration, delta-V, crew, cargo) update live as slots
change, computed on the client from the catalogue stats already fetched.

---

## Client structure

```
client/
  src/
    main.ts              Router, layout shell
    views/
      StarList.ts        Filterable table + Display button
      SystemView.ts      SVG orbit diagram + body panel
      ShipDesign.ts      Slot grid + catalogue picker + live stats
    api/
      stars.ts           Typed fetch wrappers for /api/stars/*
      ships.ts           Typed fetch wrappers for /api/ships/*
    state/
      selection.ts       Shared selection signal (list row ↔ map point)
    components/
      StarMap.ts         Three.js point cloud — receives StarListRow[], no fetch
      OrbitDiagram.ts    SVG orbital ellipses
      BodyPanel.ts       Body physical data sidebar
      SlotGrid.ts        3-column 20-slot hull layout
      CatalogPanel.ts    System catalogue with category grouping + filter
```

Single-page app with hash routing. In production the server serves
`client/dist/index.html` at `/`. In development Vite runs on a separate port
with `/api` proxied to the server.
