import { describe, it, expect } from 'vitest';
import { mpcToPc } from './meridian.js';

describe('mpcToPc', () => {
  it('0 mpc → 0 pc',       () => expect(mpcToPc(0)).toBe(0));
  it('1000 mpc → 1 pc',    () => expect(mpcToPc(1000)).toBe(1));
  it('-500 mpc → -0.5 pc', () => expect(mpcToPc(-500)).toBe(-0.5));
  it('308.5 mpc → 0.3085 pc', () => expect(mpcToPc(308.5)).toBeCloseTo(0.3085, 10));

  it('round-trip: mpcToPc(x) * 1000 ≈ x', () => {
    for (const x of [-1e6, -1, 0, 0.001, 1, 42, 308.5, 1000, 1e6]) {
      expect(mpcToPc(x) * 1000).toBeCloseTo(x, 9);
    }
  });
});
