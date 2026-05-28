import type { SlotDetail, CatalogEntry } from '@worlds/shared';

type Section = 'front' | 'central' | 'rear';

const SECTIONS: Section[] = ['front', 'central', 'rear'];

// Canonical hull layout: front and central have [1–6] + [core]; rear has [1–6] only.
const SECTION_HAS_CORE: Record<Section, boolean> = {
  front: true, central: true, rear: false,
};

type DropTarget = Pick<SlotDetail,
  'hull_section' | 'slot_number' | 'slot_to' | 'is_core' | 'is_high_energy' | 'system_id' | 'detail'
>;

export function renderSlotGrid(
  el: HTMLElement,
  slots: SlotDetail[],
  sm: number,
  onDropSystem: (slot: DropTarget, entry: CatalogEntry | null) => void,
) {
  el.innerHTML = '';

  for (const section of SECTIONS) {
    const sectionInstalled = slots.filter(s => s.hull_section === section);

    const wrapper = document.createElement('div');
    wrapper.className = 'slot-section';
    wrapper.innerHTML = `<div class="slot-section-label">${section[0].toUpperCase() + section.slice(1)} Hull</div>`;

    // Numbered slots [1]–[6].
    // Track which position a spanning system ends at so we skip absorbed positions.
    let absorbedUpTo = 0;

    for (let pos = 1; pos <= 6; pos++) {
      if (pos <= absorbedUpTo) continue; // absorbed by a spanning system

      // Find an installed system whose range covers this position.
      const installed = sectionInstalled.find(s =>
        !s.is_core &&
        s.slot_number !== null &&
        s.slot_number <= pos &&
        (s.slot_to ?? s.slot_number) >= pos
      ) ?? null;

      if (installed && (installed.slot_number ?? pos) < pos) {
        // Mid-span: position covered by a system that started earlier. Skip.
        continue;
      }

      if (installed && (installed.slot_to ?? pos) > pos) {
        absorbedUpTo = installed.slot_to!;
      }

      const target: DropTarget = installed
        ? { ...installed }
        : {
            hull_section: section,
            slot_number: pos,
            slot_to: null,
            is_core: false,
            is_high_energy: false,
            system_id: null,
            detail: null,
          };

      wrapper.appendChild(makeSlotRow(pos, null, installed, target, onDropSystem));
    }

    // Core slot (front and central only).
    if (SECTION_HAS_CORE[section]) {
      const core = sectionInstalled.find(s => s.is_core) ?? null;
      const coreTarget: DropTarget = core
        ? { ...core }
        : {
            hull_section: section,
            slot_number: null,
            slot_to: null,
            is_core: true,
            is_high_energy: false,
            system_id: null,
            detail: null,
          };
      wrapper.appendChild(makeSlotRow(null, '●', core, coreTarget, onDropSystem));
    }

    el.appendChild(wrapper);
  }
}

function makeSlotRow(
  pos: number | null,
  label: string | null,
  installed: SlotDetail | null,
  target: DropTarget,
  onDropSystem: (slot: DropTarget, entry: CatalogEntry | null) => void,
): HTMLElement {
  const row = document.createElement('div');

  const isEmpty = !installed;
  const isCore  = target.is_core;
  const isHE    = installed?.is_high_energy ?? false;

  row.className = [
    'slot-row',
    isEmpty  ? 'slot-empty'  : '',
    isCore   ? 'slot-core'   : '',
    isHE     ? 'slot-he'     : '',
  ].filter(Boolean).join(' ');

  // Slot number label.
  const numStr = label ?? (
    installed?.slot_to && installed.slot_to !== installed.slot_number
      ? `${installed.slot_number}–${installed.slot_to}`
      : String(pos ?? '')
  );

  const numEl = document.createElement('span');
  numEl.className = 'slot-num';
  numEl.textContent = `[${numStr}]`;

  // System name.
  const nameEl = document.createElement('span');
  nameEl.className = 'slot-name';

  if (isEmpty) {
    nameEl.textContent = 'empty';
  } else {
    nameEl.textContent = installed!.system_name ?? '—';
    if (isHE) {
      const he = document.createElement('span');
      he.className = 'slot-he-marker';
      he.textContent = ' [!]';
      nameEl.appendChild(he);
    }
  }

  // Detail text.
  const detailEl = document.createElement('span');
  detailEl.className = 'slot-detail';
  detailEl.textContent = installed?.detail ?? '';

  row.appendChild(numEl);
  row.appendChild(nameEl);
  row.appendChild(detailEl);

  // Drop target handling.
  row.addEventListener('dragover', (e) => {
    e.preventDefault();
    row.classList.add('drag-over');
  });
  row.addEventListener('dragleave', () => row.classList.remove('drag-over'));
  row.addEventListener('drop', (e) => {
    e.preventDefault();
    row.classList.remove('drag-over');
    const raw = e.dataTransfer?.getData('application/json');
    if (!raw) return;
    try {
      const entry: CatalogEntry = JSON.parse(raw);
      // Null system_id signals "clear this slot".
      const isEmpty = (entry as any).system_id == null;
      onDropSystem(target, isEmpty ? null : entry);
    } catch { /* malformed drag data — ignore */ }
  });

  return row;
}
