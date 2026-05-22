import type { BodyDetail } from '@worlds/shared';

export function renderBodyPanel(el: HTMLElement, body: BodyDetail | null) {
  if (!body) { el.innerHTML = '<p class="dim">Select a body</p>'; return; }

  const rows: [string, string][] = [
    ['Type',         body.body_type],
    ['Orbit',        body.orbit_au != null ? `${body.orbit_au.toFixed(3)} AU` : '—'],
    ['Mass',         body.mass_kg  != null ? `${(body.mass_kg / 5.972e24).toFixed(3)} M⊕` : '—'],
    ['Diameter',     body.size_km  != null ? `${body.size_km.toFixed(0)} km` : '—'],
    ['In HZ',        body.in_hz    ? 'Yes' : 'No'],
    ['World type',   body.world_type  ?? '—'],
    ['Atmosphere',   body.atmosphere  ?? '—'],
    ['Temp',         body.temp_k  != null ? `${body.temp_k.toFixed(0)} K` : '—'],
    ['Climate',      body.climate    ?? '—'],
    ['Habitability', body.habitability != null ? String(body.habitability) : '—'],
    ['Affinity',     body.affinity    != null ? String(body.affinity)      : '—'],
    ['Moonlets',     String(body.moonlet_count ?? 0)],
  ];

  el.innerHTML = `
    <table class="kv-table">
      ${rows.map(([k, v]) => `<tr><th>${k}</th><td>${v}</td></tr>`).join('')}
    </table>`;
}
