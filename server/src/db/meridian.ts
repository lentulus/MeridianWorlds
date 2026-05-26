import duckdb from 'duckdb';
import { DatabaseSync } from 'node:sqlite';
import { join } from 'path';
import { Config } from '../config.js';
import type {
  StarListRow, StarListParams, SystemDetail, StarDetail, BodyDetail,
} from '@worlds/shared';

const DATA = Config.meridianData;

// ── DuckDB singleton ─────────────────────────────────────────────────────────

const duck = new duckdb.Database(':memory:');
const conn = duck.connect();

let sqliteLoaded = false;

function run(sql: string): Promise<void> {
  return new Promise((resolve, reject) =>
    conn.run(sql, (err: Error | null) => (err ? reject(err) : resolve())));
}

function query<T>(sql: string, ...params: unknown[]): Promise<T[]> {
  return new Promise((resolve, reject) =>
    conn.all(sql, ...params, (err: Error | null, rows: T[]) =>
      err ? reject(err) : resolve(rows)));
}

async function ensureSqlite(): Promise<void> {
  if (!sqliteLoaded) {
    await run('INSTALL sqlite; LOAD sqlite;');
    sqliteLoaded = true;
  }
}

// ── Manifest helper (node:sqlite — fast synchronous lookup) ─────────────────

const manifest = new DatabaseSync(join(DATA, 'manifest.db'), { open: true });
const getSector = manifest.prepare(
  `SELECT file_path FROM sectors
   WHERE table_type = ? AND x_min_mpc <= ? AND x_max_mpc > ?
     AND y_min_mpc <= ? AND y_max_mpc > ?
     AND z_min_mpc <= ? AND z_max_mpc > ?`
);

interface SectorRow { file_path: string }

function sectorFile(type: string, x: number, y: number, z: number): string {
  const row = getSector.get(type, x, x, y, y, z, z) as SectorRow | undefined;
  if (!row) throw new Error(`No ${type} sector at (${x},${y},${z})`);
  return row.file_path;
}

// ── Pure math helpers ────────────────────────────────────────────────────────

export function mpcToPc(mpc: number): number {
  return mpc / 1000;
}

// ── Named-system startup index ───────────────────────────────────────────────

export interface IndexEntry {
  system_id: string;
  name: string;
  dist_pc: number;
  x_mpc: number;
  y_mpc: number;
  z_mpc: number;
  sector_key: string;
}

// Lower-cased name → entry
const nameIndex = new Map<string, IndexEntry>();
let indexReady = false;

interface RawSystemRow {
  system_id: string;
  primary_name: string;
  dist_pc: number;
  x: string; y: string; z: string;
}

export async function buildIndex(): Promise<void> {
  console.log('Building named-system index…');
  const rows = await query<RawSystemRow>(
    `SELECT system_id::VARCHAR AS system_id, primary_name,
            dist_pc, x_mpc::VARCHAR AS x, y_mpc::VARCHAR AS y, z_mpc::VARCHAR AS z
     FROM read_parquet('${DATA}/systems/*.parquet')
     WHERE primary_name IS NOT NULL`
  );
  for (const r of rows) {
    const x = Number(r.x), y = Number(r.y), z = Number(r.z);
    const sector = sectorFile('bodies', x, y, z)
      .replace('bodies/', '').replace('.parquet', '');
    nameIndex.set(r.primary_name.toLowerCase(), {
      system_id: r.system_id,
      name: r.primary_name,
      dist_pc: r.dist_pc,
      x_mpc: x, y_mpc: y, z_mpc: z,
      sector_key: sector,
    });
  }
  indexReady = true;
  console.log(`Index built: ${nameIndex.size} named systems`);
}

// ── Star List ────────────────────────────────────────────────────────────────

interface StarRow {
  system_id: string; spectral: string; luminosity_sol: number; hz_eligible: boolean;
}
interface BodyCountRow { system_id: string; body_count: string; }

export function filterAndPage(
  entries: IndexEntry[],
  params: StarListParams,
): { total: number; page: IndexEntry[] } {
  let candidates = [...entries];

  if (params.name) {
    const q = params.name.toLowerCase();
    candidates = candidates.filter(e => e.name.toLowerCase().includes(q));
  }
  if (params.dist_min_pc != null) {
    candidates = candidates.filter(e => e.dist_pc >= params.dist_min_pc!);
  }
  if (params.dist_max_pc != null) {
    candidates = candidates.filter(e => e.dist_pc <= params.dist_max_pc!);
  }

  const total = candidates.length;

  const sort = params.sort ?? 'dist_pc';
  const dir  = params.dir  ?? 'asc';
  candidates.sort((a, b) => {
    const va = sort === 'name' ? a.name    : a.dist_pc;
    const vb = sort === 'name' ? b.name    : b.dist_pc;
    if (va < vb) return dir === 'asc' ? -1 : 1;
    if (va > vb) return dir === 'asc' ?  1 : -1;
    return 0;
  });

  const limit  = Math.min(params.limit  ?? 100, 500);
  const offset = params.offset ?? 0;
  const page   = candidates.slice(offset, offset + limit);

  return { total, page };
}

export async function searchStars(params: StarListParams): Promise<{ total: number; rows: StarListRow[] }> {
  const { total, page } = filterAndPage([...nameIndex.values()], params);

  if (page.length === 0) return { total, rows: [] };

  // Collect the unique sector files needed for this page.
  const bySector = new Map<string, IndexEntry[]>();
  for (const e of page) {
    const list = bySector.get(e.sector_key) ?? [];
    list.push(e);
    bySector.set(e.sector_key, list);
  }

  // For each sector, fetch star data and body counts.
  const starMap  = new Map<string, StarRow>();
  const countMap = new Map<string, number>();

  await Promise.all([...bySector.entries()].map(async ([sk, entries]) => {
    const ids = entries.map(e => `'${e.system_id}'`).join(',');
    const starsFile = `stars/${sk}.parquet`;
    const bodiesFile = `bodies/${sk}.parquet`;

    const [stars, counts] = await Promise.all([
      query<StarRow>(
        `SELECT system_id::VARCHAR AS system_id, spectral, luminosity_sol, hz_eligible
         FROM read_parquet('${DATA}/${starsFile}')
         WHERE system_id::VARCHAR IN (${ids})
         ORDER BY luminosity_sol DESC`
      ),
      query<BodyCountRow>(
        `SELECT system_id::VARCHAR AS system_id, COUNT(*)::VARCHAR AS body_count
         FROM read_parquet('${DATA}/${bodiesFile}')
         WHERE system_id::VARCHAR IN (${ids})
         GROUP BY system_id`
      ),
    ]);

    // Keep only the primary (brightest) star per system.
    const seen = new Set<string>();
    for (const s of stars) {
      if (!seen.has(s.system_id)) { starMap.set(s.system_id, s); seen.add(s.system_id); }
    }
    for (const c of counts) countMap.set(c.system_id, Number(c.body_count));
  }));

  // Apply spectral / hz_eligible filters now that we have star data.
  let filtered = page;
  if (params.spectral) {
    const prefix = params.spectral.toUpperCase();
    filtered = filtered.filter(e => {
      const s = starMap.get(e.system_id);
      return s && s.spectral.startsWith(prefix);
    });
  }
  if (params.hz_eligible != null) {
    filtered = filtered.filter(e => {
      const s = starMap.get(e.system_id);
      return s && s.hz_eligible === params.hz_eligible;
    });
  }

  const rows: StarListRow[] = filtered.map(e => {
    const star = starMap.get(e.system_id);
    return {
      system_id:       e.system_id,
      name:            e.name,
      dist_pc:         Math.round(e.dist_pc * 100) / 100,
      age_gyr:         null,
      primary_spectral: star?.spectral  ?? '?',
      luminosity_sol:  star?.luminosity_sol ?? 0,
      hz_eligible:     star?.hz_eligible    ?? false,
      body_count:      countMap.get(e.system_id) ?? 0,
      x_pc:            mpcToPc(e.x_mpc),
      y_pc:            mpcToPc(e.y_mpc),
      z_pc:            mpcToPc(e.z_mpc),
    };
  });

  // G-006: when spectral/hz filters are active, total reflects the filtered
  // page count — a full cross-page scan would require querying all sectors.
  const filteredTotal = (params.spectral != null || params.hz_eligible != null)
    ? rows.length
    : total;

  return { total: filteredTotal, rows };
}

// ── System detail ────────────────────────────────────────────────────────────

interface RawBody {
  body_id: string; star_id: string; body_type: string; in_hz: boolean;
  mass_kg: number; size_km: number; orbit_primary_au: number; eccentricity: number;
  moonlet_count: string;
  world_type: string | null; atmosphere_code: string | null;
  avg_surface_temp_k: number | null; climate_type: string | null;
  habitability: string | null; affinity: string | null;
}

export async function getSystem(systemId: string): Promise<SystemDetail | null> {
  // Find in index.
  const entry = [...nameIndex.values()].find(e => e.system_id === systemId);
  if (!entry) return null;

  const { x_mpc: x, y_mpc: y, z_mpc: z, sector_key } = entry;
  const starsFile  = `stars/${sector_key}.parquet`;
  const bodiesFile = `bodies/${sector_key}.parquet`;
  const physFile   = sectorFile('physical', x, y, z);

  const [starRows, bodyRows] = await Promise.all([
    query<StarRow>(
      `SELECT star_id::VARCHAR AS system_id, component, spectral, luminosity_sol, hz_eligible
       FROM read_parquet('${DATA}/${starsFile}')
       WHERE system_id::VARCHAR = ?`, systemId
    ),
    query<RawBody>(
      `SELECT b.body_id::VARCHAR AS body_id, b.star_id::VARCHAR AS star_id,
              b.body_type, b.in_hz, b.mass_kg, b.size_km,
              b.orbit_primary_au, b.eccentricity,
              b.moonlet_count::VARCHAR AS moonlet_count,
              p.world_type, p.atmosphere_code, p.avg_surface_temp_k,
              p.climate_type,
              p.habitability::VARCHAR AS habitability,
              p.affinity::VARCHAR     AS affinity
       FROM read_parquet('${DATA}/${bodiesFile}') b
       LEFT JOIN read_parquet('${DATA}/${physFile}') p ON p.body_id = b.body_id
       WHERE b.system_id::VARCHAR = ?
       ORDER BY b.orbit_primary_au`, systemId
    ),
  ]);

  const stars: StarDetail[] = starRows.map((s: any) => ({
    star_id:        s.system_id,   // aliased in the query
    component:      s.component,
    spectral:       s.spectral,
    luminosity_sol: s.luminosity_sol,
    hz_eligible:    s.hz_eligible,
  }));

  const bodies: BodyDetail[] = bodyRows.map(b => ({
    body_id:      b.body_id,
    star_id:      b.star_id,
    body_type:    b.body_type,
    in_hz:        b.in_hz,
    mass_kg:      b.mass_kg,
    size_km:      b.size_km,
    orbit_au:     b.orbit_primary_au,
    eccentricity: b.eccentricity,
    moonlet_count: Number(b.moonlet_count ?? 0),
    world_type:   b.world_type   ?? null,
    atmosphere:   b.atmosphere_code ?? null,
    temp_k:       b.avg_surface_temp_k ?? null,
    climate:      b.climate_type ?? null,
    habitability: b.habitability != null ? Number(b.habitability) : null,
    affinity:     b.affinity     != null ? Number(b.affinity)     : null,
  }));

  return {
    system_id: entry.system_id,
    name:      entry.name,
    dist_pc:   Math.round(entry.dist_pc * 100) / 100,
    age_gyr:   null,
    stars,
    bodies,
  };
}

export function findByName(name: string): IndexEntry | undefined {
  return nameIndex.get(name.toLowerCase());
}

export { indexReady };
