import { StarListView } from './views/StarList.js';
import { SystemView }   from './views/SystemView.js';
import { ShipDesignView } from './views/ShipDesign.js';

const app = document.getElementById('app')!;

const NAV = `
  <nav class="main-nav">
    <a href="#stars">Stars</a>
    <a href="#system">System</a>
    <a href="#ships">Ships</a>
  </nav>`;

const views: Record<string, (el: HTMLElement) => unknown> = {
  stars:  StarListView,
  system: SystemView,
  ships:  ShipDesignView,
};

let currentDestroy: (() => void) | null = null;

function route() {
  const hash = location.hash.slice(1) || 'stars';
  const viewFn = views[hash] ?? views.stars;

  currentDestroy?.();
  currentDestroy = null;

  app.innerHTML = NAV + '<div id="view" class="view-container"></div>';

  // Highlight active nav link
  app.querySelectorAll('.main-nav a').forEach(a => {
    a.classList.toggle('active', a.getAttribute('href') === `#${hash}`);
  });

  const viewEl = app.querySelector<HTMLElement>('#view')!;
  const result = viewFn(viewEl);
  if (result && typeof (result as any).destroy === 'function') {
    currentDestroy = (result as any).destroy.bind(result);
  }
}

window.addEventListener('hashchange', route);
route();

// Global styles
const style = document.createElement('style');
style.textContent = `
  .main-nav { padding: 6px 12px; background: #111; display: flex; gap: 16px; border-bottom: 1px solid #222; }
  .main-nav a { color: #888; text-decoration: none; padding: 2px 0; }
  .main-nav a.active { color: #e0e0e0; border-bottom: 2px solid #4488cc; }
  .main-nav a:hover { color: #ccc; }

  .view-container { flex: 1; display: flex; flex-direction: column; overflow: hidden; }

  .toolbar { padding: 6px 10px; background: #111; display: flex; gap: 10px; align-items: center;
             flex-wrap: wrap; border-bottom: 1px solid #1e1e1e; }
  .toolbar input, .toolbar select { background: #1a1a1a; border: 1px solid #333; color: #ccc;
                                     padding: 2px 6px; border-radius: 3px; }
  .toolbar button { background: #1e2a3a; border: 1px solid #336; color: #88aacc;
                    padding: 3px 10px; border-radius: 3px; cursor: pointer; }
  .toolbar button:hover { background: #243040; }
  .toolbar button:disabled { opacity: 0.4; cursor: default; }
  .toolbar label { display: flex; gap: 5px; align-items: center; }
  .sep { color: #333; }

  .dim { color: #555; }
  .view-title { font-size: 14px; color: #aaa; }

  .list-body { flex: 1; overflow: auto; }
  .data-table { width: 100%; border-collapse: collapse; }
  .data-table th { background: #111; color: #666; font-weight: normal; text-align: left;
                   padding: 4px 8px; position: sticky; top: 0; border-bottom: 1px solid #222; }
  .data-table td { padding: 3px 8px; border-bottom: 1px solid #111; }
  .data-table tr:hover td { background: #141a24; }

  .system-layout { flex: 1; display: flex; overflow: hidden; min-height: 0; }
  .orbit-svg { flex: 1; min-width: 0; min-height: 0; display: block; }
  .body-panel { width: 220px; flex-shrink: 0; padding: 10px; overflow-y: auto; border-left: 1px solid #1a1a1a; }

  .kv-table { width: 100%; border-collapse: collapse; }
  .kv-table th { color: #666; font-weight: normal; text-align: right; padding: 2px 8px 2px 0; width: 45%; }
  .kv-table td { color: #ccc; padding: 2px 0; overflow-wrap: break-word; }

  .sd-layout { flex: 1; display: flex; overflow: hidden; }
  .sd-left { flex: 1; display: flex; flex-direction: column; overflow-y: auto; padding: 8px; gap: 8px; }
  .catalog-panel { width: 260px; overflow-y: auto; padding: 8px; border-left: 1px solid #1a1a1a; }

  .stats-box { background: #0d0d0d; border: 1px solid #1a1a1a; padding: 8px; border-radius: 4px; }

  .slot-section { margin-bottom: 14px; }
  .slot-section-label { color: #888; font-size: 10px; font-weight: 700; letter-spacing: 0.1em;
                        text-transform: uppercase; padding: 0 4px 4px; border-bottom: 1px solid #222;
                        margin-bottom: 2px; }

  .slot-row { display: flex; align-items: baseline; gap: 8px; padding: 3px 6px; border-radius: 2px;
              cursor: pointer; }
  .slot-row:hover { background: #141414; }
  .slot-row.drag-over { background: #111a11; outline: 1px dashed #3a5a3a; }
  .slot-row.slot-core { opacity: 0.85; }

  .slot-num { color: #999; font-size: 11px; width: 32px; flex-shrink: 0; text-align: right; }
  .slot-core .slot-num { color: #7a8aaa; }
  .slot-name { flex: 1; color: #ccc; }
  .slot-empty .slot-name { color: #aaa; font-style: italic; }
  .slot-he-marker { color: #b88a4a; font-size: 10px; }
  .slot-detail { color: #999; font-size: 11px; }

  .catalog-list { list-style: none; padding: 0; }
  .catalog-item { display: flex; justify-content: space-between; padding: 3px 4px; cursor: grab;
                  border-bottom: 1px solid #111; }
  .catalog-item:hover { background: #141414; }
  .catalog-clear { justify-content: center; color: #444; font-style: italic; font-size: 11px;
                   border-bottom: 1px solid #1a1a1a; margin-bottom: 6px; }
  .ci-name { color: #bbb; }
  .ci-stats { color: #556; font-size: 11px; }
  details > summary { cursor: pointer; color: #667; padding: 4px 0; font-size: 11px;
                      text-transform: uppercase; letter-spacing: 0.05em; }
`;
document.head.appendChild(style);
