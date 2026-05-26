import { describe, it, expect, beforeAll } from 'vitest';
import { app } from '../app.js';
import { buildIndex } from '../db/meridian.js';
import type { StarListRow, SystemDetail } from '@worlds/shared';

beforeAll(async () => {
  await buildIndex();
}, 60_000);

describe('GET /api/stars', () => {
  it('returns correct shape with limit=5', async () => {
    const res = await app.request('/api/stars?limit=5');
    expect(res.status).toBe(200);
    const body = await res.json() as { total: number; rows: StarListRow[] };
    expect(typeof body.total).toBe('number');
    expect(Array.isArray(body.rows)).toBe(true);
    expect(body.rows.length).toBeLessThanOrEqual(5);
  });

  it('name filter returns rows containing the search term', async () => {
    const res = await app.request('/api/stars?name=Sol&limit=10');
    expect(res.status).toBe(200);
    const { rows } = await res.json() as { total: number; rows: StarListRow[] };
    expect(rows.length).toBeGreaterThan(0);
    expect(rows.some((r: StarListRow) => r.name.includes('Sol'))).toBe(true);
  });

  it('distance filter: all rows have dist_pc ≤ max', async () => {
    const res = await app.request('/api/stars?dist_max_pc=2&limit=100');
    expect(res.status).toBe(200);
    const { rows } = await res.json() as { total: number; rows: StarListRow[] };
    expect(rows.length).toBeGreaterThan(0);
    for (const r of rows) {
      expect(r.dist_pc).toBeLessThanOrEqual(2);
    }
  });

  it('G-007: Sol coordinates are ≈ 0 pc, not thousands (mpc scale)', async () => {
    const res = await app.request('/api/stars?name=Sol&limit=1');
    expect(res.status).toBe(200);
    const { rows } = await res.json() as { total: number; rows: StarListRow[] };
    const sol = rows.find((r: StarListRow) => r.name === 'Sol');
    expect(sol).toBeDefined();
    expect(Math.abs(sol!.x_pc)).toBeLessThan(1);
    expect(Math.abs(sol!.y_pc)).toBeLessThan(1);
    expect(Math.abs(sol!.z_pc)).toBeLessThan(1);
  });

  it('G-006 regression: spectral filter total === rows.length', async () => {
    const res = await app.request('/api/stars?spectral=G&dist_max_pc=30&limit=100');
    expect(res.status).toBe(200);
    const body = await res.json() as { total: number; rows: StarListRow[] };
    expect(body.total).toBe(body.rows.length);
    for (const r of body.rows) {
      expect(r.primary_spectral.startsWith('G')).toBe(true);
    }
  });
});

describe('GET /api/stars/by-name', () => {
  it('known name returns 302 with Location pointing to system endpoint', async () => {
    const res = await app.request('/api/stars/by-name?name=Sol');
    expect(res.status).toBe(302);
    const location = res.headers.get('Location');
    expect(location).toContain('/api/stars/');
  });

  it('following redirect returns SystemDetail shape', async () => {
    const redirect = await app.request('/api/stars/by-name?name=Sol');
    const location = redirect.headers.get('Location')!;
    const res = await app.request(location);
    expect(res.status).toBe(200);
    const body = await res.json() as SystemDetail;
    expect(typeof body.system_id).toBe('string');
    expect(typeof body.name).toBe('string');
    expect(Array.isArray(body.stars)).toBe(true);
    expect(Array.isArray(body.bodies)).toBe(true);
  });

  it('missing name param returns 400', async () => {
    const res = await app.request('/api/stars/by-name');
    expect(res.status).toBe(400);
  });
});

describe('GET /api/stars/:id', () => {
  it('unknown uuid returns 404', async () => {
    const res = await app.request('/api/stars/AAAAAAAA-0000-0000-0000-000000000000');
    expect(res.status).toBe(404);
  });
});
