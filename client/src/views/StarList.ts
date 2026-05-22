import type { StarListRow } from '@worlds/shared';
import { fetchStars } from '../api/stars.js';
import { selectedSystemId } from '../state/selection.js';
import { StarMap } from '../components/StarMap.js';

export function StarListView(container: HTMLElement) {
  let rows: StarListRow[] = [];
  let mapMode = false;
  let starMap: StarMap | null = null;

  container.innerHTML = `
    <div class="toolbar">
      <label>Name <input id="sl-name" type="text" placeholder="Sol…"></label>
      <label>Max dist (ly) <input id="sl-dist" type="number" min="0" step="1" value="100"></label>
      <label>Spectral <input id="sl-spectral" type="text" placeholder="G…" style="width:4em"></label>
      <label>HZ <select id="sl-hz"><option value="">Any</option><option value="true">Yes</option><option value="false">No</option></select></label>
      <button id="sl-search">Search</button>
      <button id="sl-display" disabled>Display</button>
      <span id="sl-status" class="dim"></span>
    </div>
    <div id="sl-body" class="list-body">
      <table id="sl-table" class="data-table">
        <thead>
          <tr>
            <th>Name</th><th>Dist (ly)</th><th>Spectral</th>
            <th>Luminosity</th><th>HZ</th><th>Bodies</th>
          </tr>
        </thead>
        <tbody id="sl-tbody"></tbody>
      </table>
    </div>
    <div id="sl-map" style="display:none;flex:1"></div>`;

  const nameEl     = container.querySelector<HTMLInputElement>('#sl-name')!;
  const distEl     = container.querySelector<HTMLInputElement>('#sl-dist')!;
  const spectralEl = container.querySelector<HTMLInputElement>('#sl-spectral')!;
  const hzEl       = container.querySelector<HTMLSelectElement>('#sl-hz')!;
  const searchBtn  = container.querySelector<HTMLButtonElement>('#sl-search')!;
  const displayBtn = container.querySelector<HTMLButtonElement>('#sl-display')!;
  const statusEl   = container.querySelector<HTMLSpanElement>('#sl-status')!;
  const tbody      = container.querySelector<HTMLElement>('#sl-tbody')!;
  const tableDiv   = container.querySelector<HTMLElement>('#sl-body')!;
  const mapDiv     = container.querySelector<HTMLElement>('#sl-map')!;

  async function doSearch() {
    statusEl.textContent = 'Searching…';
    searchBtn.disabled = true;
    try {
      const params: Record<string, string | number> = { limit: 500 };
      if (nameEl.value)     params.name = nameEl.value;
      if (distEl.value)     params.dist_max_ly = Number(distEl.value);
      if (spectralEl.value) params.spectral = spectralEl.value;
      if (hzEl.value)       params.hz_eligible = hzEl.value;

      const data = await fetchStars(params as any);
      rows = data.rows;
      statusEl.textContent = `${data.total} systems`;
      displayBtn.disabled = rows.length === 0;
      renderTable();
      if (mapMode && starMap) starMap.setStars(rows);
    } catch (err: any) {
      statusEl.textContent = `Error: ${err.message}`;
    } finally {
      searchBtn.disabled = false;
    }
  }

  function renderTable() {
    tbody.innerHTML = rows.map(r => `
      <tr data-id="${r.system_id}" style="cursor:pointer">
        <td>${r.name}</td>
        <td>${r.dist_ly.toFixed(2)}</td>
        <td>${r.primary_spectral}</td>
        <td>${r.luminosity_sol.toFixed(3)}</td>
        <td>${r.hz_eligible ? '✓' : ''}</td>
        <td>${r.body_count}</td>
      </tr>`).join('');

    tbody.querySelectorAll('tr[data-id]').forEach(row => {
      row.addEventListener('click', () => {
        selectedSystemId.set(row.getAttribute('data-id'));
        location.hash = '#system';
      });
    });
  }

  displayBtn.addEventListener('click', () => {
    mapMode = !mapMode;
    if (mapMode) {
      tableDiv.style.display = 'none';
      mapDiv.style.display = 'flex';
      displayBtn.textContent = 'List';
      if (!starMap) starMap = new StarMap(mapDiv);
      starMap.setStars(rows);
    } else {
      mapDiv.style.display = 'none';
      tableDiv.style.display = '';
      displayBtn.textContent = 'Display';
    }
  });

  searchBtn.addEventListener('click', doSearch);
  nameEl.addEventListener('keydown', (e) => { if (e.key === 'Enter') doSearch(); });

  doSearch();

  return {
    destroy() { starMap?.destroy(); },
  };
}
