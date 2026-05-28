import type { ShipDesign, CatalogEntry, SlotDetail, HullSize } from '@worlds/shared';
import { fetchHullSizes, fetchCatalog, fetchShip, fetchShips, createShip, putSlots, deleteShip } from '../api/ships.js';
import { selectedShipId } from '../state/selection.js';
import { renderSlotGrid } from '../components/SlotGrid.js';
import { renderCatalogPanel } from '../components/CatalogPanel.js';

export function ShipDesignView(container: HTMLElement) {
  let ship: ShipDesign | null = null;
  let hullSizes: HullSize[] = [];
  let catalog: CatalogEntry[] = [];

  container.innerHTML = `
    <div class="toolbar">
      <select id="sd-ship-select"><option value="">— select ship —</option></select>
      <button id="sd-new">New ship</button>
      <button id="sd-delete" disabled>Delete</button>
      <span class="sep">|</span>
      <label>TL <input id="sd-tl" type="number" min="0" max="12" value="10" style="width:3em"></label>
      <label>SM <input id="sd-sm" type="number" min="3" max="12" value="5" style="width:3em"></label>
      <button id="sd-load-cat">Load catalogue</button>
    </div>
    <div class="sd-layout">
      <div class="sd-left">
        <div id="sd-stats" class="stats-box"></div>
        <div id="sd-slots" class="slot-grid"></div>
      </div>
      <aside id="sd-catalog" class="catalog-panel"><p class="dim">Load catalogue to begin</p></aside>
    </div>`;

  const shipSelect = container.querySelector<HTMLSelectElement>('#sd-ship-select')!;
  const newBtn     = container.querySelector<HTMLButtonElement>('#sd-new')!;
  const deleteBtn  = container.querySelector<HTMLButtonElement>('#sd-delete')!;
  const tlEl       = container.querySelector<HTMLInputElement>('#sd-tl')!;
  const smEl       = container.querySelector<HTMLInputElement>('#sd-sm')!;
  const loadCatBtn = container.querySelector<HTMLButtonElement>('#sd-load-cat')!;
  const statsEl    = container.querySelector<HTMLElement>('#sd-stats')!;
  const slotsEl    = container.querySelector<HTMLElement>('#sd-slots')!;
  const catalogEl  = container.querySelector<HTMLElement>('#sd-catalog')!;

  async function loadShipList() {
    const ships = await fetchShips({});
    shipSelect.innerHTML = '<option value="">— select ship —</option>'
      + ships.map(s => `<option value="${s.ship_id}">${s.class_name ?? s.name} (SM ${s.sm}, TL ${s.tl})</option>`).join('');
  }

  async function loadShip(id: number) {
    ship = await fetchShip(id);
    selectedShipId.set(id);
    deleteBtn.disabled = false;
    tlEl.value = String(ship.tl);
    smEl.value = String(ship.sm);
    renderStats();
    renderSlots();
  }

  function renderStats() {
    if (!ship) { statsEl.innerHTML = ''; return; }
    statsEl.innerHTML = `
      <table class="kv-table">
        <tr><th>Class</th><td>${ship.class_name ?? '—'}</td></tr>
        <tr><th>Name</th><td>${ship.name ?? '—'}</td></tr>
        <tr><th>TL</th><td>${ship.tl}</td></tr>
        <tr><th>SM</th><td>${ship.sm}</td></tr>
        <tr><th>Accel</th><td>${ship.move_accel_g ?? '—'} g</td></tr>
        <tr><th>DST HP</th><td>${ship.dst_hp ?? '—'}</td></tr>
        <tr><th>Cost</th><td>${ship.cost_dollars != null ? `$${ship.cost_dollars.toLocaleString()}` : '—'}</td></tr>
        <tr><th>Crew</th><td>${ship.occ_crew ?? '—'}</td></tr>
      </table>`;
  }

  function defaultDetail(e: CatalogEntry): string {
    if (e.ddr_us        != null) return `dDR ${e.ddr_us}`;
    if (e.acceleration_g != null) return `${e.acceleration_g}G`;
    if (e.power_points  != null && e.power_points > 0) return `${e.power_points} PP`;
    if (e.workspaces    != null) return `${e.workspaces} ws`;
    return '';
  }

  function renderSlots() {
    if (!ship) { slotsEl.innerHTML = ''; return; }
    renderSlotGrid(slotsEl, ship.slots, ship.sm, async (slot, entry) => {
      if (!ship) return;

      // Remove any existing DB slot that covers this position
      const filtered = ship.slots.filter(s => {
        if (s.hull_section !== slot.hull_section) return true;
        if (slot.is_core) return !s.is_core;
        const from = s.slot_number ?? 99;
        const to   = s.slot_to   ?? from;
        const pos  = slot.slot_number ?? 99;
        return !(from <= pos && pos <= to);
      });

      if (entry === null) {
        await putSlots(ship.ship_id, { slots: filtered as any });
      } else {
        const detail = prompt(`Detail for "${entry.name}":`, defaultDetail(entry));
        if (detail === null) return; // cancelled
        filtered.push({
          hull_section: slot.hull_section,
          slot_number:  slot.slot_number,
          slot_to:      slot.slot_to ?? null,
          is_core:      slot.is_core,
          is_high_energy: entry.is_high_energy,
          system_id:    entry.system_id,
          system_name:  entry.name,
          category:     entry.category,
          detail:       detail || null,
          power_points: entry.power_points,
        } as any);
        await putSlots(ship.ship_id, { slots: filtered as any });
      }

      ship = await fetchShip(ship!.ship_id);
      renderSlots();
    });
  }

  shipSelect.addEventListener('change', () => {
    const id = Number(shipSelect.value);
    if (id) loadShip(id);
  });

  newBtn.addEventListener('click', async () => {
    const name = prompt('Ship class name:');
    if (!name) return;
    const id = await createShip({
      class_name: name, name, tl: Number(tlEl.value),
      sm: Number(smEl.value), type_id: 1, is_superscience: false, is_streamlined: false,
    });
    await loadShipList();
    await loadShip(id);
    shipSelect.value = String(id);
  });

  deleteBtn.addEventListener('click', async () => {
    if (!ship) return;
    if (!confirm(`Delete ${ship.class_name ?? ship.name}?`)) return;
    await deleteShip(ship.ship_id);
    ship = null;
    deleteBtn.disabled = true;
    statsEl.innerHTML = '';
    slotsEl.innerHTML = '';
    selectedShipId.set(null);
    await loadShipList();
  });

  loadCatBtn.addEventListener('click', async () => {
    catalog = (await fetchCatalog(Number(tlEl.value), Number(smEl.value))).systems;
    renderCatalogPanel(catalogEl, catalog);
  });

  loadShipList().then(() => {
    const id = selectedShipId.get();
    if (id) { shipSelect.value = String(id); loadShip(id); }
  });
}
