import type { BodyDetail, StarDetail } from '@worlds/shared';

const W = 700, H = 500, CX = W / 2, CY = H / 2;

export function renderOrbitDiagram(
  svg: SVGSVGElement,
  stars: StarDetail[],
  bodies: BodyDetail[],
  onSelectBody: (b: BodyDetail) => void,
) {
  svg.innerHTML = '';
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);

  // Scale: fit all orbits
  const maxAu = Math.max(0.1, ...bodies.map(b => b.orbit_au ?? 0));
  const scale = (W / 2 - 30) / maxAu;

  // Background
  rect(svg, 0, 0, W, H, '#050510');

  // Stars at centre
  for (const s of stars) {
    const r = Math.min(12, Math.max(4, (s.luminosity_sol ?? 1) * 5));
    circle(svg, CX, CY, r, spectralFill(s.spectral));
  }

  // Orbits and bodies
  for (const b of bodies) {
    const au = b.orbit_au ?? 0;
    const rx  = au * scale;
    const ecc = b.eccentricity ?? 0;
    const ry  = rx * Math.sqrt(1 - ecc * ecc);

    ellipse(svg, CX, CY, rx, ry, '#1a2a3a');

    const angle = Math.random() * 2 * Math.PI;
    const bx = CX + rx * Math.cos(angle);
    const by = CY + ry * Math.sin(angle);
    const br = bodyRadius(b.body_type);
    const fill = bodyFill(b.body_type, b.in_hz);

    const dot = circle(svg, bx, by, br, fill);
    dot.style.cursor = 'pointer';
    dot.addEventListener('click', () => onSelectBody(b));

    const tip = document.createElementNS('http://www.w3.org/2000/svg', 'title');
    tip.textContent = `${b.body_type} — ${au.toFixed(2)} AU`;
    dot.appendChild(tip);
  }
}

function rect(svg: SVGSVGElement, x: number, y: number, w: number, h: number, fill: string) {
  const el = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
  el.setAttribute('x', String(x)); el.setAttribute('y', String(y));
  el.setAttribute('width', String(w)); el.setAttribute('height', String(h));
  el.setAttribute('fill', fill);
  svg.appendChild(el);
  return el;
}

function circle(svg: SVGElement, cx: number, cy: number, r: number, fill: string) {
  const el = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  el.setAttribute('cx', String(cx)); el.setAttribute('cy', String(cy));
  el.setAttribute('r', String(r)); el.setAttribute('fill', fill);
  svg.appendChild(el);
  return el;
}

function ellipse(svg: SVGSVGElement, cx: number, cy: number, rx: number, ry: number, stroke: string) {
  const el = document.createElementNS('http://www.w3.org/2000/svg', 'ellipse');
  el.setAttribute('cx', String(cx)); el.setAttribute('cy', String(cy));
  el.setAttribute('rx', String(rx)); el.setAttribute('ry', String(ry));
  el.setAttribute('fill', 'none'); el.setAttribute('stroke', stroke);
  svg.appendChild(el);
}

function bodyRadius(type: string): number {
  if (type?.includes('Giant')) return 7;
  if (type?.includes('Dwarf')) return 2;
  return 4;
}

function bodyFill(type: string, inHz: boolean): string {
  if (type?.includes('Gas')) return '#6080c0';
  if (inHz) return '#40b060';
  return '#708090';
}

function spectralFill(spectral: string): string {
  switch (spectral?.[0]?.toUpperCase()) {
    case 'O': return '#aabbff';
    case 'B': return '#ccddff';
    case 'A': return '#eeeeff';
    case 'F': return '#ffffcc';
    case 'G': return '#ffee88';
    case 'K': return '#ffaa44';
    case 'M': return '#ff6622';
    default:  return '#aaaaaa';
  }
}
