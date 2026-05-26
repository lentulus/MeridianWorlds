import { describe, it, expect } from 'vitest';
import { filterAndPage } from './meridian.js';
import type { IndexEntry } from './meridian.js';

const entries: IndexEntry[] = [
  { system_id: '1', name: 'Alpha Centauri', dist_pc: 1.34, x_mpc: 100, y_mpc: 200, z_mpc: 300, sector_key: 'a' },
  { system_id: '2', name: 'Barnard',        dist_pc: 1.83, x_mpc: 110, y_mpc: 210, z_mpc: 310, sector_key: 'a' },
  { system_id: '3', name: 'Sirius',         dist_pc: 2.64, x_mpc: 120, y_mpc: 220, z_mpc: 320, sector_key: 'b' },
  { system_id: '4', name: 'Sol',            dist_pc: 0.00, x_mpc: 0,   y_mpc: 0,   z_mpc: 0,   sector_key: 'b' },
  { system_id: '5', name: 'Tau Ceti',       dist_pc: 3.65, x_mpc: 130, y_mpc: 230, z_mpc: 330, sector_key: 'c' },
];

describe('filterAndPage', () => {
  it('name filter: case-insensitive exact match', () => {
    const { total, page } = filterAndPage(entries, { name: 'sol' });
    expect(total).toBe(1);
    expect(page[0].name).toBe('Sol');
  });

  it('name filter: partial match counts all containing entries', () => {
    const { total } = filterAndPage(entries, { name: 'a' });
    expect(total).toBe(3); // Alpha Centauri, Barnard, Tau Ceti
  });

  it('distance max filter', () => {
    const { total } = filterAndPage(entries, { dist_max_pc: 2.0 });
    expect(total).toBe(3); // Sol (0), Alpha Centauri (1.34), Barnard (1.83)
  });

  it('distance min + max filter', () => {
    const { total, page } = filterAndPage(entries, { dist_min_pc: 1.5, dist_max_pc: 3.0 });
    expect(total).toBe(2);
    expect(page.map(e => e.name).sort()).toEqual(['Barnard', 'Sirius']);
  });

  it('sort by name ascending', () => {
    const { page } = filterAndPage(entries, { sort: 'name', dir: 'asc' });
    expect(page[0].name).toBe('Alpha Centauri');
    expect(page[4].name).toBe('Tau Ceti');
  });

  it('sort by dist_pc descending', () => {
    const { page } = filterAndPage(entries, { sort: 'dist_pc', dir: 'desc' });
    expect(page[0].name).toBe('Tau Ceti');
    expect(page[4].name).toBe('Sol');
  });

  it('pagination: limit respected', () => {
    const { page, total } = filterAndPage(entries, { limit: 2, offset: 0 });
    expect(page.length).toBe(2);
    expect(total).toBe(5);
  });

  it('pagination: offset near end returns remaining entries', () => {
    const { page } = filterAndPage(entries, { limit: 2, offset: 4 });
    expect(page.length).toBe(1);
  });

  it('empty result when no name matches', () => {
    const { total, page } = filterAndPage(entries, { name: 'zzz' });
    expect(total).toBe(0);
    expect(page).toHaveLength(0);
  });

  it('default sort is dist_pc ascending (Sol first)', () => {
    const { page } = filterAndPage(entries, {});
    expect(page[0].name).toBe('Sol');
    expect(page[1].name).toBe('Alpha Centauri');
  });

  // Sirius fixture coords: x_mpc=120, y_mpc=220, z_mpc=320 → (0.12, 0.22, 0.32) pc
  // Distance from Sirius to Sol (0,0,0): sqrt(0.12²+0.22²+0.32²) ≈ 0.406 pc

  it('center: star at centre has zero computed distance (Sirius as centre)', () => {
    const { page } = filterAndPage(entries, {
      center_x_pc: 0.12, center_y_pc: 0.22, center_z_pc: 0.32,
      dist_max_pc: 0.001,
    });
    expect(page.map(e => e.name)).toContain('Sirius');
  });

  it('center: Sol excluded when dist_max_pc < distance from Sirius to Sol', () => {
    const { page } = filterAndPage(entries, {
      center_x_pc: 0.12, center_y_pc: 0.22, center_z_pc: 0.32,
      dist_max_pc: 0.05,
    });
    expect(page.some(e => e.name === 'Sol')).toBe(false);
  });
});
