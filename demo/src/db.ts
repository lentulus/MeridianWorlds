import duckdb from 'duckdb';
import path from 'path';
import type { SystemResult, StarInfo, BodyInfo } from './types.js';

const MERIDIAN_DATA = process.env.MERIDIAN_DATA ?? '/Volumes/Lexar/MeridianData';
const MANIFEST      = path.join(MERIDIAN_DATA, 'manifest.db');
const PC_TO_LY      = 3.26156;

// Singleton DuckDB in-memory instance.
const duck = new duckdb.Database(':memory:');
const conn = duck.connect();

function run(sql: string): Promise<void> {
  return new Promise((resolve, reject) => {
    conn.run(sql, (err: Error | null) => (err ? reject(err) : resolve()));
  });
}

function query<T>(sql: string, ...params: unknown[]): Promise<T[]> {
  return new Promise((resolve, reject) => {
    conn.all(sql, ...params, (err: Error | null, rows: T[]) => {
      if (err) reject(err);
      else resolve(rows);
    });
  });
}

// Load the SQLite extension once so we can read manifest.db.
let ready: Promise<void> | null = null;
function ensureReady(): Promise<void> {
  if (!ready) ready = run('INSTALL sqlite; LOAD sqlite;');
  return ready;
}

// ── Raw row shapes ──────────────────────────────────────────────────────────

interface SystemRow {
  system_id: string;
  primary_name: string;
  dist_pc: number;
  system_age_gyr: number | null;
  x: string;
  y: string;
  z: string;
}

interface SectorRow { file_path: string }

interface StarRow {
  star_id: string;
  component: string;
  spectral: string;
  luminosity_sol: number;
  hz_eligible: boolean;
}

interface BodyRow {
  body_id: string;
  star_id: string;
  body_type: string;
  in_hz: boolean;
  mass_kg: number;
  size_km: number;
  orbit_primary_au: number;
  eccentricity: number;
  moonlet_count: string;
  world_type: string | null;
  atmosphere_code: string | null;
  avg_surface_temp_k: number | null;
  climate_type: string | null;
  habitability: string | null;
  affinity: string | null;
}

// ── Public API ──────────────────────────────────────────────────────────────

export async function searchSystem(name: string): Promise<SystemResult | null> {
  await ensureReady();

  // 1. Locate the system with a case-insensitive partial match.
  const systemRows = await query<SystemRow>(
    `SELECT system_id::VARCHAR AS system_id, primary_name, dist_pc, system_age_gyr,
            x_mpc::VARCHAR AS x, y_mpc::VARCHAR AS y, z_mpc::VARCHAR AS z
     FROM read_parquet('${MERIDIAN_DATA}/systems/*.parquet')
     WHERE primary_name ILIKE ?
     LIMIT 1`,
    `%${name}%`
  );

  if (systemRows.length === 0) return null;
  const sys = systemRows[0];

  // 2. Find which sector files hold this system's data via manifest.db.
  const x = Number(sys.x), y = Number(sys.y), z = Number(sys.z);

  const sectorSql = `
    SELECT file_path FROM sqlite_scan('${MANIFEST}', 'sectors')
    WHERE table_type = ?
      AND x_min_mpc <= ? AND x_max_mpc > ?
      AND y_min_mpc <= ? AND y_max_mpc > ?
      AND z_min_mpc <= ? AND z_max_mpc > ?
    LIMIT 1`;

  const [bSectors, pSectors] = await Promise.all([
    query<SectorRow>(sectorSql, 'bodies',   x, x, y, y, z, z),
    query<SectorRow>(sectorSql, 'physical', x, x, y, y, z, z),
  ]);

  if (!bSectors.length || !pSectors.length) {
    throw new Error(`No sector found for system "${sys.primary_name}" at (${x}, ${y}, ${z})`);
  }

  const bodiesFile = bSectors[0].file_path;
  const physFile   = pSectors[0].file_path;

  // Stars are not registered in the manifest — derive from the bodies sector key.
  const sectorKey = bodiesFile.replace('bodies/', '').replace('.parquet', '');
  const starsFile = `stars/${sectorKey}.parquet`;

  const systemId = sys.system_id;

  // 3. Parallel queries within the single sector.
  const [starRows, bodyRows] = await Promise.all([
    query<StarRow>(
      `SELECT star_id::VARCHAR AS star_id, component, spectral, luminosity_sol, hz_eligible
       FROM read_parquet('${MERIDIAN_DATA}/${starsFile}')
       WHERE system_id::VARCHAR = ?`,
      systemId
    ),
    query<BodyRow>(
      `SELECT b.body_id::VARCHAR       AS body_id,
              b.star_id::VARCHAR       AS star_id,
              b.body_type,             b.in_hz,
              b.mass_kg,               b.size_km,
              b.orbit_primary_au,      b.eccentricity,
              b.moonlet_count::VARCHAR AS moonlet_count,
              p.world_type,            p.atmosphere_code,
              p.avg_surface_temp_k,    p.climate_type,
              p.habitability::VARCHAR  AS habitability,
              p.affinity::VARCHAR      AS affinity
       FROM   read_parquet('${MERIDIAN_DATA}/${bodiesFile}') b
       LEFT JOIN read_parquet('${MERIDIAN_DATA}/${physFile}') p
              ON p.body_id = b.body_id
       WHERE  b.system_id::VARCHAR = ?
       ORDER BY b.orbit_primary_au`,
      systemId
    ),
  ]);

  const stars: StarInfo[] = starRows.map(s => ({
    star_id:        s.star_id,
    component:      s.component,
    spectral:       s.spectral,
    luminosity_sol: s.luminosity_sol,
    hz_eligible:    s.hz_eligible,
  }));

  const bodies: BodyInfo[] = bodyRows.map(b => ({
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
    climate:      b.climate_type  ?? null,
    habitability: b.habitability  ?? null,
    affinity:     b.affinity      ?? null,
  }));

  return {
    system_id: sys.system_id,
    name:      sys.primary_name,
    dist_ly:   Math.round(sys.dist_pc * PC_TO_LY * 100) / 100,
    age_gyr:   sys.system_age_gyr ?? null,
    stars,
    bodies,
  };
}
