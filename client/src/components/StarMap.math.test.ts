import { describe, it, expect } from 'vitest';
import fc from 'fast-check';
import { spectralColour } from './StarMap.js';

describe('spectralColour', () => {
  it('O → blue-violet',    () => expect(spectralColour('O')).toEqual({ r: 0.6,  g: 0.7,  b: 1.0 }));
  it('B2 → blue-white',   () => expect(spectralColour('B2')).toEqual({ r: 0.7,  g: 0.8,  b: 1.0 }));
  it('A0 → white',        () => expect(spectralColour('A0')).toEqual({ r: 0.9,  g: 0.95, b: 1.0 }));
  it('F5 → yellow-white', () => expect(spectralColour('F5')).toEqual({ r: 1.0,  g: 1.0,  b: 0.9 }));
  it('G2 → yellow',       () => expect(spectralColour('G2')).toEqual({ r: 1.0,  g: 0.95, b: 0.7 }));
  it('K3 → orange',       () => expect(spectralColour('K3')).toEqual({ r: 1.0,  g: 0.75, b: 0.4 }));
  it('M8 → red',          () => expect(spectralColour('M8')).toEqual({ r: 1.0,  g: 0.4,  b: 0.2 }));
  it('empty → grey',      () => expect(spectralColour('')).toEqual({ r: 0.5,  g: 0.5,  b: 0.5 }));
  it('unknown → grey',    () => expect(spectralColour('XYZ')).toEqual({ r: 0.5, g: 0.5,  b: 0.5 }));

  it('property: all channels in [0, 1] for any string', () => {
    fc.assert(
      fc.property(fc.string(), (s) => {
        const { r, g, b } = spectralColour(s);
        return r >= 0 && r <= 1 && g >= 0 && g <= 1 && b >= 0 && b <= 1;
      }),
    );
  });
});
