import type { SlotDetail, CatalogEntry } from '@worlds/shared';

const SECTIONS = ['front', 'central', 'rear'] as const;

export function renderSlotGrid(
  el: HTMLElement,
  slots: SlotDetail[],
  sm: number,
  onDropSystem: (slot: Omit<SlotDetail, 'system_name' | 'category'>, entry: CatalogEntry | null) => void,
) {
  el.innerHTML = '';

  for (const section of SECTIONS) {
    const sectionSlots = slots.filter(s => s.hull_section === section);
    const div = document.createElement('div');
    div.className = 'slot-section';
    div.innerHTML = `<h4>${section[0].toUpperCase() + section.slice(1)}</h4>`;

    for (const slot of sectionSlots) {
      const cell = document.createElement('div');
      cell.className = `slot-cell${slot.is_core ? ' core' : ''}${slot.is_high_energy ? ' high-energy' : ''}`;
      cell.draggable = true;

      const label = slot.system_name ?? '—';
      const span = slot.slot_to && slot.slot_to !== slot.slot_number
        ? `${slot.slot_number}–${slot.slot_to}`
        : `${slot.slot_number ?? ''}`;
      cell.innerHTML = `<span class="slot-num">${span}</span><span class="slot-name">${label}</span>`;

      cell.addEventListener('dragover', (e) => e.preventDefault());
      cell.addEventListener('drop', (e) => {
        e.preventDefault();
        const raw = e.dataTransfer?.getData('application/json');
        if (!raw) return;
        const entry: CatalogEntry = JSON.parse(raw);
        onDropSystem({ ...slot, system_id: entry.system_id }, entry);
      });

      div.appendChild(cell);
    }
    el.appendChild(div);
  }
}
