import { describe, it, expect } from 'vitest';
import { getShip } from './ships.js';

// Ship_id 1 = Star Flower, SM+8, TL11. Has a Fusion Reactor slot (2 PP at SM+8).
// All other ships in the seed have no power plants installed.
describe('getShip — G-001: power_points_available', () => {
  it('returns power_points_available > 0 for a ship with an installed power plant', () => {
    const ship = getShip(1);
    expect(ship).not.toBeNull();
    expect(ship!.power_points_available).toBeGreaterThan(0);
  });

  it('exposes power_points on each slot (null for non-power-plant systems)', () => {
    const ship = getShip(1);
    expect(ship).not.toBeNull();
    const ppSlots = ship!.slots.filter(s => s.power_points !== null && s.power_points > 0);
    expect(ppSlots.length).toBeGreaterThan(0);
  });
});
