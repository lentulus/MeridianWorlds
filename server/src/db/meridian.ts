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
    conn.all(sql, ...params, (err: Error | null, rows: any) => {
      if (err) {
        const e = err as Error & { code?: string; errorType?: string };
        if (e.code === 'DUCKDB_NODEJS_ERROR' && e.errorType === 'Parser') {
          console.error('[DuckDB Parser Error] Query:\n', sql);
        }
        return reject(err);
      }
      resolve(rows as T[]);
    }));
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

function entryDist(e: IndexEntry, cx: number, cy: number, cz: number): number {
  const dx = mpcToPc(e.x_mpc) - cx;
  const dy = mpcToPc(e.y_mpc) - cy;
  const dz = mpcToPc(e.z_mpc) - cz;
  return Math.sqrt(dx * dx + dy * dy + dz * dz);
}

// ── Types ─────────────────────────────────────────────────────────────────────

// Used by filterAndPage (utility / tests) and findByName return value.
export interface IndexEntry {
  system_id: string;
  name: string | null;
  dist_pc: number;
  x_mpc: number;
  y_mpc: number;
  z_mpc: number;
  sector_key: string;
}

interface RawSystemRow {
  system_id: string;
  primary_name: string | null;
  dist_pc: number;
  x: string; y: string; z: string;
}

let indexReady = false;

// No pre-loading: all star queries hit DuckDB directly.
export async function buildIndex(): Promise<void> {
  indexReady = true;
  console.log(`Meridian ready. Data: ${DATA}`);
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

  const cx = params.center_x_pc;
  const cy = params.center_y_pc;
  const cz = params.center_z_pc;
  const hasCentre = cx != null && cy != null && cz != null;
  const dist = (e: IndexEntry) => hasCentre ? entryDist(e, cx!, cy!, cz!) : e.dist_pc;

  if (params.name) {
    const q = params.name.toLowerCase();
    // Unnamed entries (name === null) are excluded when a name filter is active.
    candidates = candidates.filter(e => e.name != null && e.name.toLowerCase().includes(q));
  }
  if (params.dist_min_pc != null) {
    candidates = candidates.filter(e => dist(e) >= params.dist_min_pc!);
  }
  if (params.dist_max_pc != null) {
    candidates = candidates.filter(e => dist(e) <= params.dist_max_pc!);
  }

  const total = candidates.length;

  const sort = params.sort ?? 'dist_pc';
  const dir  = params.dir  ?? 'asc';
  candidates.sort((a, b) => {
    // Null names sort last regardless of direction.
    const va = sort === 'name' ? (a.name ?? '￿') : dist(a);
    const vb = sort === 'name' ? (b.name ?? '￿') : dist(b);
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
  const cx = params.center_x_pc;
  const cy = params.center_y_pc;
  const cz = params.center_z_pc;
  const hasCentre = cx != null && cy != null && cz != null;

  // Build WHERE clause dynamically
  const conditions: string[] = [];
  const qp: (string | number)[] = [];

  if (hasCentre) {
    const d = `SQRT(POW(x_mpc/1000.0-?,2)+POW(y_mpc/1000.0-?,2)+POW(z_mpc/1000.0-?,2))`;
    if (params.dist_max_pc != null) { conditions.push(`${d}<=?`); qp.push(cx!, cy!, cz!, params.dist_max_pc); }
    if (params.dist_min_pc != null) { conditions.push(`${d}>=?`); qp.push(cx!, cy!, cz!, params.dist_min_pc); }
  } else {
    if (params.dist_max_pc != null) { conditions.push('dist_pc<=?'); qp.push(params.dist_max_pc); }
    if (params.dist_min_pc != null) { conditions.push('dist_pc>=?'); qp.push(params.dist_min_pc); }
  }
  if (params.name) {
    conditions.push('LOWER(primary_name) LIKE ?');
    qp.push(`%${params.name.toLowerCase()}%`);
  }

  const WHERE = conditions.length ? `WHERE ${conditions.join(' AND ')}` : '';
  const FROM  = `FROM read_parquet('${DATA}/systems/*.parquet')`;

  // ORDER BY: centre-relative distance when centre given, otherwise dist_pc or name
  let orderExpr: string;
  if (params.sort === 'name') {
    orderExpr = 'primary_name';
  } else if (hasCentre) {
    // cx/cy/cz are TypeScript numbers — safe to interpolate
    orderExpr = `SQRT(POW(x_mpc/1000.0-(${cx}),2)+POW(y_mpc/1000.0-(${cy}),2)+POW(z_mpc/1000.0-(${cz}),2))`;
  } else {
    orderExpr = 'dist_pc';
  }
  const orderDir = params.dir === 'desc' ? 'DESC' : 'ASC';
  const limit  = Math.min(params.limit  ?? 100, 500);
  const offset = params.offset ?? 0;

  // Single DuckDB query returns page rows + window count
  interface PageRow {
    system_id: string; primary_name: string | null; dist_pc: number;
    x: string; y: string; z: string; total_count: string;
  }
  const pageRows = await query<PageRow>(
    `SELECT system_id::VARCHAR AS system_id, primary_name, dist_pc,
            x_mpc::VARCHAR AS x, y_mpc::VARCHAR AS y, z_mpc::VARCHAR AS z,
            COUNT(*) OVER () AS total_count
     ${FROM} ${WHERE}
     ORDER BY ${orderExpr} ${orderDir} NULLS LAST
     LIMIT ${limit} OFFSET ${offset}`,
    ...qp
  );

  const total = pageRows.length > 0 ? Number(pageRows[0].total_count) : 0;
  if (pageRows.length === 0) return { total: 0, rows: [] };

  // Group by sector (synchronous manifest lookup per row — fast SQLite)
  const bySector = new Map<string, PageRow[]>();
  for (const r of pageRows) {
    const x = Number(r.x), y = Number(r.y), z = Number(r.z);
    const sk = sectorFile('bodies', x, y, z).replace('bodies/', '').replace('.parquet', '');
    const list = bySector.get(sk) ?? [];
    list.push(r);
    bySector.set(sk, list);
  }

  const starMap  = new Map<string, StarRow>();
  const countMap = new Map<string, number>();

  await Promise.all([...bySector.entries()].map(async ([sk, sRows]) => {
    const ids = sRows.map(r => `'${r.system_id}'`).join(',');
    const [stars, counts] = await Promise.all([
      query<StarRow>(
        `SELECT system_id::VARCHAR AS system_id, spectral, luminosity_sol, hz_eligible
         FROM read_parquet('${DATA}/stars/${sk}.parquet')
         WHERE system_id::VARCHAR IN (${ids})
         ORDER BY luminosity_sol DESC`
      ),
      query<BodyCountRow>(
        `SELECT system_id::VARCHAR AS system_id, COUNT(*)::VARCHAR AS body_count
         FROM read_parquet('${DATA}/bodies/${sk}.parquet')
         WHERE system_id::VARCHAR IN (${ids})
         GROUP BY system_id`
      ),
    ]);
    const seen = new Set<string>();
    for (const s of stars) {
      if (!seen.has(s.system_id)) { starMap.set(s.system_id, s); seen.add(s.system_id); }
    }
    for (const c of counts) countMap.set(c.system_id, Number(c.body_count));
  }));

  // Spectral / hz_eligible post-filters (applied after fetching star data)
  let filtered = pageRows;
  if (params.spectral) {
    const prefix = params.spectral.toUpperCase();
    filtered = filtered.filter(r => { const s = starMap.get(r.system_id); return s && s.spectral.startsWith(prefix); });
  }
  if (params.hz_eligible != null) {
    filtered = filtered.filter(r => { const s = starMap.get(r.system_id); return s && s.hz_eligible === params.hz_eligible; });
  }

  const rows: StarListRow[] = filtered.map(r => {
    const star = starMap.get(r.system_id);
    const xMpc = Number(r.x), yMpc = Number(r.y), zMpc = Number(r.z);
    const rawDist = hasCentre
      ? Math.sqrt(Math.pow(mpcToPc(xMpc) - cx!, 2) + Math.pow(mpcToPc(yMpc) - cy!, 2) + Math.pow(mpcToPc(zMpc) - cz!, 2))
      : r.dist_pc;
    return {
      system_id:        r.system_id,
      name:             r.primary_name ?? `(${mpcToPc(xMpc).toFixed(2)}, ${mpcToPc(yMpc).toFixed(2)}, ${mpcToPc(zMpc).toFixed(2)}) pc`,
      dist_pc:          Math.round(rawDist * 100) / 100,
      age_gyr:          null,
      primary_spectral: star?.spectral       ?? '?',
      luminosity_sol:   star?.luminosity_sol ?? 0,
      hz_eligible:      star?.hz_eligible    ?? false,
      body_count:       countMap.get(r.system_id) ?? 0,
      x_pc:             mpcToPc(xMpc),
      y_pc:             mpcToPc(yMpc),
      z_pc:             mpcToPc(zMpc),
    };
  });

  // G-006: spectral/hz total is page count — full cross-sector scan not feasible
  const filteredTotal = (params.spectral != null || params.hz_eligible != null) ? rows.length : total;
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
  const sysRows = await query<RawSystemRow>(
    `SELECT system_id::VARCHAR AS system_id, primary_name, dist_pc,
            x_mpc::VARCHAR AS x, y_mpc::VARCHAR AS y, z_mpc::VARCHAR AS z
     FROM read_parquet('${DATA}/systems/*.parquet')
     WHERE system_id::VARCHAR = ?
     LIMIT 1`,
    systemId
  );
  if (!sysRows.length) return null;
  const sr = sysRows[0];
  const x = Number(sr.x), y = Number(sr.y), z = Number(sr.z);
  const sector_key = sectorFile('bodies', x, y, z).replace('bodies/', '').replace('.parquet', '');
  const displayName = sr.primary_name ??
    `(${mpcToPc(x).toFixed(2)}, ${mpcToPc(y).toFixed(2)}, ${mpcToPc(z).toFixed(2)}) pc`;

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
    system_id: sr.system_id,
    name:      displayName,
    dist_pc:   Math.round(sr.dist_pc * 100) / 100,
    age_gyr:   null,
    stars,
    bodies,
  };
}

export async function findByName(name: string): Promise<IndexEntry | undefined> {
  const rows = await query<RawSystemRow>(
    `SELECT system_id::VARCHAR AS system_id, primary_name, dist_pc,
            x_mpc::VARCHAR AS x, y_mpc::VARCHAR AS y, z_mpc::VARCHAR AS z
     FROM read_parquet('${DATA}/systems/*.parquet')
     WHERE LOWER(primary_name) = ?
     LIMIT 1`,
    name.toLowerCase()
  );
  if (!rows.length) return undefined;
  const r = rows[0];
  const x = Number(r.x), y = Number(r.y), z = Number(r.z);
  const sector_key = sectorFile('bodies', x, y, z).replace('bodies/', '').replace('.parquet', '');
  return { system_id: r.system_id, name: r.primary_name ?? null, dist_pc: r.dist_pc, x_mpc: x, y_mpc: y, z_mpc: z, sector_key };
}

export { indexReady };
