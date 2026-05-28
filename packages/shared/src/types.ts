// ── Star / System types ──────────────────────────────────────────────────────

export interface StarListRow {
  system_id: string;
  name: string;
  dist_pc: number;
  age_gyr: number | null;
  primary_spectral: string;
  luminosity_sol: number;
  hz_eligible: boolean;
  body_count: number;
  x_pc: number;
  y_pc: number;
  z_pc: number;
}

export interface StarListResponse {
  total: number;
  rows: StarListRow[];
}

export interface StarListParams {
  name?: string;
  dist_min_pc?: number;
  dist_max_pc?: number;
  spectral?: string;
  hz_eligible?: boolean;
  sort?: 'name' | 'dist_pc' | 'age_gyr';
  dir?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
  center_x_pc?: number;
  center_y_pc?: number;
  center_z_pc?: number;
}

export interface StarDetail {
  star_id: string;
  component: string;
  spectral: string;
  luminosity_sol: number;
  hz_eligible: boolean;
}

export interface BodyDetail {
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

export interface SystemDetail {
  system_id: string;
  name: string;
  dist_pc: number;
  age_gyr: number | null;
  stars: StarDetail[];
  bodies: BodyDetail[];
}

// ── Ship types ───────────────────────────────────────────────────────────────

export interface HullSize {
  sm: number;
  mass_tons: number;
  length_m: number;
  dst_hp: number;
  handling: number;
  stability_rating: number;
}

export interface SlotDetail {
  hull_section: 'front' | 'central' | 'rear';
  slot_number: number | null;
  slot_to: number | null;
  is_core: boolean;
  is_high_energy: boolean;
  system_id: number | null;
  system_name: string | null;
  category: string | null;
  detail: string | null;
  power_points: number | null;
}

export interface ShipListRow {
  ship_id: number;
  name: string | null;
  class_name: string | null;
  hull_number: string | null;
  type_name: string;
  tl: number;
  is_superscience: boolean;
  sm: number;
  move_accel_g: number | null;
  move_delta_v_mps: number | null;
  move_is_ftl: boolean;
  ddr_front: number;
  ddr_central: number;
  ddr_rear: number;
  occ_crew: number;
  occ_passengers: number;
  cost_dollars: number | null;
}

export interface ShipDesign extends ShipListRow {
  is_streamlined: boolean;
  dst_hp: number;
  handling: number;
  stability_rating: number;
  ht: number;
  lwt_tons: number;
  load_tons: number;
  move_is_ftl: boolean;
  range_ftl: string | null;
  notes: string | null;
  design_features: string[];
  power_points_available: number;
  power_points_consumed: number;
  slots: SlotDetail[];
}

export interface ShipListParams {
  tl?: number;
  tl_max?: number;
  type?: string;
  sm?: number;
  military?: boolean;
  superscience?: boolean;
  sort?: 'name' | 'sm' | 'cost_dollars' | 'tl';
  dir?: 'asc' | 'desc';
}

export interface CatalogEntry {
  system_id: number;
  name: string;
  category: string;
  tl_min: number | null;
  is_superscience: boolean;
  location: string;
  is_high_energy: boolean;
  cost_dollars: number | null;
  workspaces: number | null;
  power_points: number | null;
  acceleration_g: number | null;
  ddr_us: number | null;
  ddr_sl: number | null;
  stat_notes: string | null;
}

export interface CatalogResponse {
  tl: number;
  sm: number;
  systems: CatalogEntry[];
}

export interface CreateShipBody {
  class_name?: string;
  name?: string;
  hull_number?: string;
  type_id: number;
  tl: number;
  is_superscience?: boolean;
  sm: number;
  is_streamlined?: boolean;
  notes?: string;
}

export interface UpdateSlotsBody {
  slots: Array<{
    hull_section: 'front' | 'central' | 'rear';
    slot_number: number | null;
    slot_to?: number | null;
    is_core?: boolean;
    system_id: number | null;
    detail?: string | null;
  }>;
}
