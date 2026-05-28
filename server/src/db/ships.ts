import { DatabaseSync } from 'node:sqlite';
import { Config } from '../config.js';
import type {
  HullSize, ShipListRow, ShipDesign, SlotDetail,
  CatalogEntry, CatalogResponse, CreateShipBody, UpdateSlotsBody,
} from '@worlds/shared';

const db = new DatabaseSync(Config.worldsDb, { open: true });

// ── Hull sizes ───────────────────────────────────────────────────────────────

export function getHullSizes(): HullSize[] {
  return db.prepare(
    `SELECT sm, mass_tons, length_yards AS length_m, dst_hp, handling, stability_rating
     FROM hull_sizes ORDER BY sm`
  ).all() as HullSize[];
}

// ── Catalogue ────────────────────────────────────────────────────────────────

export function getCatalog(tl: number, sm: number): CatalogResponse {
  const systems = db.prepare(`
    SELECT c.system_id, c.name, c.category, c.tl_min, c.is_superscience,
           c.location, c.is_high_energy,
           CASE WHEN c.category = 'Armor'
                THEN a.cost_dollars
                ELSE s.cost_dollars END AS cost_dollars,
           s.workspaces, s.power_points, s.acceleration_g,
           a.ddr_us, a.ddr_sl,
           s.stat_notes
    FROM ship_system_catalog c
    LEFT JOIN system_sm_stats s ON s.system_id = c.system_id AND s.sm = ?
    LEFT JOIN armor_sm_stats  a ON a.system_id = c.system_id AND a.sm = ?
    WHERE (c.tl_min IS NULL OR c.tl_min <= ?)
    ORDER BY c.category, c.name
  `).all(sm, sm, tl) as CatalogEntry[];

  return { tl, sm, systems };
}

export function getCatalogSystemStats(systemId: number, sm: number): CatalogEntry | null {
  return db.prepare(`
    SELECT c.system_id, c.name, c.category, c.tl_min, c.is_superscience,
           c.location, c.is_high_energy,
           CASE WHEN c.category = 'Armor'
                THEN a.cost_dollars
                ELSE s.cost_dollars END AS cost_dollars,
           s.workspaces, s.power_points, s.acceleration_g,
           a.ddr_us, a.ddr_sl, s.stat_notes
    FROM ship_system_catalog c
    LEFT JOIN system_sm_stats s ON s.system_id = c.system_id AND s.sm = ?
    LEFT JOIN armor_sm_stats  a ON a.system_id = c.system_id AND a.sm = ?
    WHERE c.system_id = ?
  `).get(sm, sm, systemId) as CatalogEntry | null;
}

// ── Ship list ────────────────────────────────────────────────────────────────

export function listShips(params: {
  tl?: number; tl_max?: number; type?: string; sm?: number;
  military?: boolean; superscience?: boolean;
  sort?: string; dir?: string;
}): ShipListRow[] {
  const conditions: string[] = [];
  const args: unknown[] = [];

  if (params.tl     != null) { conditions.push('s.tl = ?');          args.push(params.tl); }
  if (params.tl_max != null) { conditions.push('s.tl <= ?');         args.push(params.tl_max); }
  if (params.sm     != null) { conditions.push('s.sm = ?');          args.push(params.sm); }
  if (params.type)           { conditions.push('t.name LIKE ?');     args.push(`%${params.type}%`); }
  if (params.military  != null) { conditions.push('t.military = ?'); args.push(params.military ? 1 : 0); }
  if (params.superscience === false) { conditions.push('s.is_superscience = 0'); }

  const allowed_sorts: Record<string, string> = {
    name: 's.class_name', sm: 's.sm', cost_dollars: 's.cost_dollars', tl: 's.tl',
  };
  const orderCol = allowed_sorts[params.sort ?? ''] ?? 's.sm';
  const orderDir = params.dir === 'desc' ? 'DESC' : 'ASC';

  const where = conditions.length ? `WHERE ${conditions.join(' AND ')}` : '';
  return db.prepare(`
    SELECT s.ship_id, s.name, s.class_name, s.hull_number,
           t.name AS type_name, s.tl, s.is_superscience, s.sm,
           s.move_accel_g, s.move_delta_v_mps, s.move_is_ftl,
           s.ddr_front, s.ddr_central, s.ddr_rear,
           s.occ_crew, s.occ_passengers, s.cost_dollars
    FROM ships s
    LEFT JOIN ship_types t ON t.type_id = s.type_id
    ${where}
    ORDER BY ${orderCol} ${orderDir}
  `).all(...args) as ShipListRow[];
}

// ── Ship detail ──────────────────────────────────────────────────────────────

export function getShip(shipId: number): ShipDesign | null {
  const ship = db.prepare(`
    SELECT s.*, t.name AS type_name, b.name AS bureau_name
    FROM ships s
    LEFT JOIN ship_types t ON t.type_id = s.type_id
    LEFT JOIN design_bureaus b ON b.bureau_id = s.bureau_id
    WHERE s.ship_id = ?
  `).get(shipId) as any;

  if (!ship) return null;

  const features: Array<{ name: string }> = db.prepare(`
    SELECT f.name FROM ship_design_features sdf
    JOIN design_features f ON f.feature_id = sdf.feature_id
    WHERE sdf.ship_id = ?
  `).all(shipId) as any;

  const slots: SlotDetail[] = (db.prepare(`
    SELECT ss.hull_section, ss.slot_number, ss.slot_to, ss.is_core,
           ss.is_high_energy, ss.system_id, c.name AS system_name,
           c.category, ss.detail,
           (SELECT st.power_points FROM system_sm_stats st
            WHERE st.system_id = ss.system_id AND st.sm = ?
            LIMIT 1) AS power_points
    FROM ship_system_slots ss
    LEFT JOIN ship_system_catalog c ON c.system_id = ss.system_id
    WHERE ss.ship_id = ?
    ORDER BY ss.hull_section, COALESCE(ss.slot_number, 99)
  `).all(ship.sm, shipId) as any).map((r: any) => ({
    hull_section:   r.hull_section,
    slot_number:    r.slot_number,
    slot_to:        r.slot_to,
    is_core:        Boolean(r.is_core),
    is_high_energy: Boolean(r.is_high_energy),
    system_id:      r.system_id,
    system_name:    r.system_name,
    category:       r.category,
    detail:         r.detail,
    power_points:   r.power_points ?? null,
  }));

  const ppAvail = slots
    .filter(s => s.category === 'Power')
    .reduce((sum, s) => sum + (s.power_points ?? 0), 0);

  return {
    ship_id:          ship.ship_id,
    name:             ship.name,
    class_name:       ship.class_name,
    hull_number:      ship.hull_number,
    type_name:        ship.type_name,
    bureau_name:      ship.bureau_name,
    tl:               ship.tl,
    is_superscience:  Boolean(ship.is_superscience),
    sm:               ship.sm,
    is_streamlined:   Boolean(ship.is_streamlined),
    dst_hp:           ship.dst_hp,
    handling:         ship.handling,
    stability_rating: ship.stability_rating,
    ht:               ship.ht,
    lwt_tons:         ship.lwt_tons,
    load_tons:        ship.load_tons,
    move_accel_g:     ship.move_accel_g,
    move_delta_v_mps: ship.move_delta_v_mps,
    move_is_ftl:      Boolean(ship.move_is_ftl),
    ddr_front:        ship.ddr_front,
    ddr_central:      ship.ddr_central,
    ddr_rear:         ship.ddr_rear,
    range_ftl:        ship.range_ftl,
    cost_dollars:     ship.cost_dollars,
    occ_crew:         ship.occ_crew,
    occ_passengers:   ship.occ_passengers,
    notes:            ship.notes,
    design_features:  features.map(f => f.name),
    power_points_available: ppAvail,
    power_points_consumed:  slots.filter(s => s.is_high_energy).length,
    slots,
  };
}

// ── Mutations ────────────────────────────────────────────────────────────────

export function createShip(body: CreateShipBody): number {
  const result = db.prepare(`
    INSERT INTO ships (class_name, name, hull_number, type_id, tl, is_superscience,
                       sm, is_streamlined, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).run(
    body.class_name ?? null, body.name ?? null, body.hull_number ?? null,
    body.type_id, body.tl, body.is_superscience ? 1 : 0,
    body.sm, body.is_streamlined ? 1 : 0, body.notes ?? null
  );
  return Number(result.lastInsertRowid);
}

export function updateShip(shipId: number, body: Partial<CreateShipBody>): void {
  const sets: string[] = [];
  const args: unknown[] = [];
  const allowed = ['class_name','name','hull_number','tl','sm','is_streamlined','notes'] as const;
  for (const key of allowed) {
    if (key in body) { sets.push(`${key} = ?`); args.push((body as any)[key]); }
  }
  if (!sets.length) return;
  args.push(shipId);
  db.prepare(`UPDATE ships SET ${sets.join(', ')} WHERE ship_id = ?`).run(...args);
}

export function updateSlots(shipId: number, body: UpdateSlotsBody): void {
  db.prepare('DELETE FROM ship_system_slots WHERE ship_id = ?').run(shipId);
  const insert = db.prepare(`
    INSERT INTO ship_system_slots
      (ship_id, hull_section, slot_number, slot_to, is_core, is_high_energy, system_id, detail)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `);
  for (const slot of body.slots) {
    const isHighEnergy = slot.system_id
      ? (db.prepare('SELECT is_high_energy FROM ship_system_catalog WHERE system_id = ?')
           .get(slot.system_id) as any)?.is_high_energy ?? 0
      : 0;
    insert.run(
      shipId, slot.hull_section, slot.slot_number ?? null,
      slot.slot_to ?? null, slot.is_core ? 1 : 0,
      isHighEnergy, slot.system_id, slot.detail ?? null
    );
  }
}

export function deleteShip(shipId: number): void {
  db.prepare('DELETE FROM ship_system_slots WHERE ship_id = ?').run(shipId);
  db.prepare('DELETE FROM ship_design_features WHERE ship_id = ?').run(shipId);
  db.prepare('DELETE FROM ships WHERE ship_id = ?').run(shipId);
}
