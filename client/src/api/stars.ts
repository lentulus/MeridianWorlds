import type { StarListParams, StarListResponse, SystemDetail } from '@worlds/shared';

export async function fetchStars(params: Partial<StarListParams>): Promise<StarListResponse> {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v != null) qs.set(k, String(v));
  }
  const res = await fetch(`/api/stars?${qs}`);
  if (!res.ok) throw new Error(`Stars API error ${res.status}`);
  return res.json();
}

export async function fetchSystem(id: string): Promise<SystemDetail> {
  const res = await fetch(`/api/stars/${id}`);
  if (!res.ok) throw new Error(`System API error ${res.status}`);
  return res.json();
}
