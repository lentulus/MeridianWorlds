import type { CatalogEntry } from '@worlds/shared';

export function renderCatalogPanel(el: HTMLElement, entries: CatalogEntry[]) {
  el.innerHTML = '';

  const byCategory = new Map<string, CatalogEntry[]>();
  for (const e of entries) {
    const list = byCategory.get(e.category) ?? [];
    list.push(e);
    byCategory.set(e.category, list);
  }

  for (const [cat, items] of byCategory) {
    const section = document.createElement('details');
    section.open = true;
    section.innerHTML = `<summary>${cat} (${items.length})</summary>`;

    const ul = document.createElement('ul');
    ul.className = 'catalog-list';

    for (const item of items) {
      const li = document.createElement('li');
      li.className = 'catalog-item';
      li.draggable = true;
      li.dataset.id = String(item.system_id);

      const cost = item.cost_dollars != null
        ? `$${(item.cost_dollars / 1000).toFixed(0)}k`
        : '';
      const pp = item.power_points != null ? ` ${item.power_points > 0 ? '+' : ''}${item.power_points}PP` : '';

      li.innerHTML = `<span class="ci-name">${item.name}</span><span class="ci-stats">${cost}${pp}</span>`;
      li.title = item.stat_notes ?? '';

      li.addEventListener('dragstart', (e) => {
        e.dataTransfer?.setData('application/json', JSON.stringify(item));
      });

      ul.appendChild(li);
    }
    section.appendChild(ul);
    el.appendChild(section);
  }
}
