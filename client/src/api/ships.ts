import type {
  HullSize, CatalogResponse, ShipListRow, ShipDesign,
  CreateShipBody, UpdateSlotsBody,
} from '@worlds/shared';

export async function fetchHullSizes(): Promise<HullSize[]> {
  const res = await fetch('/api/ships/hull-sizes');
  if (!res.ok) throw new Error(`Hull sizes API error ${res.status}`);
  return res.json();
}

export async function fetchCatalog(tl: number, sm: number): Promise<CatalogResponse> {
  const res = await fetch(`/api/ships/catalog?tl=${tl}&sm=${sm}`);
  if (!res.ok) throw new Error(`Catalog API error ${res.status}`);
  return res.json();
}

export async function fetchShips(params: Record<string, string | number | boolean>): Promise<ShipListRow[]> {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v != null) qs.set(k, String(v));
  }
  const res = await fetch(`/api/ships?${qs}`);
  if (!res.ok) throw new Error(`Ships API error ${res.status}`);
  return res.json();
}

export async function fetchShip(id: number): Promise<ShipDesign> {
  const res = await fetch(`/api/ships/${id}`);
  if (!res.ok) throw new Error(`Ship API error ${res.status}`);
  return res.json();
}

export async function createShip(body: CreateShipBody): Promise<number> {
  const res = await fetch('/api/ships', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Create ship error ${res.status}`);
  const data = await res.json();
  return data.ship_id;
}

export async function patchShip(id: number, body: Partial<CreateShipBody>): Promise<void> {
  const res = await fetch(`/api/ships/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Patch ship error ${res.status}`);
}

export async function putSlots(id: number, body: UpdateSlotsBody): Promise<void> {
  const res = await fetch(`/api/ships/${id}/slots`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Slots API error ${res.status}`);
}

export async function deleteShip(id: number): Promise<void> {
  const res = await fetch(`/api/ships/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`Delete ship error ${res.status}`);
}
