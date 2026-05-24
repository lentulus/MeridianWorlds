import type { BodyDetail, SystemDetail } from '@worlds/shared';
import { fetchSystem } from '../api/stars.js';
import { selectedSystemId } from '../state/selection.js';
import { renderOrbitDiagram } from '../components/OrbitDiagram.js';
import { renderBodyPanel } from '../components/BodyPanel.js';

export function SystemView(container: HTMLElement) {
  container.innerHTML = `
    <div class="toolbar">
      <button id="sv-back">← Star List</button>
      <span id="sv-title" class="view-title"></span>
    </div>
    <div class="system-layout">
      <svg id="sv-orbit" class="orbit-svg" width="100%" height="100%" preserveAspectRatio="xMidYMid meet"></svg>
      <aside id="sv-body-panel" class="body-panel"><p class="dim">Select a body</p></aside>
    </div>`;

  const backBtn  = container.querySelector<HTMLButtonElement>('#sv-back')!;
  const titleEl  = container.querySelector<HTMLSpanElement>('#sv-title')!;
  const orbitSvg = container.querySelector<SVGSVGElement>('#sv-orbit')!;
  const bodyPanel = container.querySelector<HTMLElement>('#sv-body-panel')!;

  backBtn.addEventListener('click', () => { location.hash = '#stars'; });

  async function load() {
    const id = selectedSystemId.get();
    if (!id) { location.hash = '#stars'; return; }

    titleEl.textContent = 'Loading…';
    try {
      const system: SystemDetail = await fetchSystem(id);
      titleEl.textContent = `${system.name}  —  ${system.dist_pc} pc`;

      renderOrbitDiagram(orbitSvg, system.stars, system.bodies, (b: BodyDetail) => {
        renderBodyPanel(bodyPanel, b);
      });
    } catch (err: any) {
      titleEl.textContent = `Error: ${err.message}`;
    }
  }

  load();
}
