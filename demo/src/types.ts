export interface StarInfo {
  star_id: string;
  component: string;
  spectral: string;
  luminosity_sol: number;
  hz_eligible: boolean;
}

export interface BodyInfo {
  body_id: string;
  star_id: string;
  body_type: string;
  in_hz: boolean;
  mass_kg: number;
  size_km: number;
  orbit_au: number;
  eccentricity: number;
  moonlet_count: number;
  // from physical table (null if no entry)
  world_type: string | null;
  atmosphere: string | null;
  temp_k: number | null;
  climate: string | null;
  habitability: string | null;
  affinity: string | null;
}

export interface SystemResult {
  system_id: string;
  name: string;
  dist_ly: number;
  age_gyr: number | null;
  stars: StarInfo[];
  bodies: BodyInfo[];
}

export interface ApiError {
  error: string;
}
