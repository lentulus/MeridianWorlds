import * as THREE from 'three';
import type { StarListRow } from '@worlds/shared';


export class StarMap {
  private renderer: THREE.WebGLRenderer;
  private scene: THREE.Scene;
  private camera: THREE.PerspectiveCamera;
  private points: THREE.Points | null = null;
  private animId = 0;
  private isDragging = false;
  private lastMouse = { x: 0, y: 0 };
  private spherical = new THREE.Spherical(200, Math.PI / 3, 0);

  constructor(private container: HTMLElement) {
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setPixelRatio(devicePixelRatio);
    this.renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(this.renderer.domElement);

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x040408);

    this.camera = new THREE.PerspectiveCamera(
      60, container.clientWidth / container.clientHeight, 0.1, 5000
    );

    // Sol crosshair
    const crossGeo = new THREE.BufferGeometry();
    crossGeo.setFromPoints([
      new THREE.Vector3(-4, 0, 0), new THREE.Vector3(4, 0, 0),
      new THREE.Vector3(0, -4, 0), new THREE.Vector3(0, 4, 0),
      new THREE.Vector3(0, 0, -4), new THREE.Vector3(0, 0, 4),
    ]);
    this.scene.add(new THREE.LineSegments(crossGeo, new THREE.LineBasicMaterial({ color: 0xffdd88 })));

    this.bindEvents();
    this.animate();
  }

  setStars(rows: StarListRow[]) {
    if (this.points) { this.scene.remove(this.points); this.points.geometry.dispose(); }

    const positions = new Float32Array(rows.length * 3);
    const colors    = new Float32Array(rows.length * 3);

    for (let i = 0; i < rows.length; i++) {
      const r = rows[i];
      positions[i * 3]     = r.x_pc;
      positions[i * 3 + 1] = r.y_pc;
      positions[i * 3 + 2] = r.z_pc;

      const col = spectralColour(r.primary_spectral);
      colors[i * 3]     = col.r;
      colors[i * 3 + 1] = col.g;
      colors[i * 3 + 2] = col.b;
    }

    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geo.setAttribute('color',    new THREE.BufferAttribute(colors,    3));

    const mat = new THREE.PointsMaterial({ size: 2, vertexColors: true, sizeAttenuation: false });
    this.points = new THREE.Points(geo, mat);
    this.scene.add(this.points);
  }

  resize() {
    const w = this.container.clientWidth, h = this.container.clientHeight;
    this.renderer.setSize(w, h);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
  }

  destroy() {
    cancelAnimationFrame(this.animId);
    this.renderer.dispose();
    this.container.removeChild(this.renderer.domElement);
  }

  private animate() {
    this.animId = requestAnimationFrame(() => this.animate());
    const pos = new THREE.Vector3().setFromSpherical(this.spherical);
    this.camera.position.copy(pos);
    this.camera.lookAt(0, 0, 0);
    this.renderer.render(this.scene, this.camera);
  }

  private bindEvents() {
    const el = this.renderer.domElement;
    el.addEventListener('mousedown', (e) => {
      this.isDragging = true;
      this.lastMouse = { x: e.clientX, y: e.clientY };
    });
    window.addEventListener('mouseup', () => { this.isDragging = false; });
    el.addEventListener('mousemove', (e) => {
      if (!this.isDragging) return;
      const dx = e.clientX - this.lastMouse.x;
      const dy = e.clientY - this.lastMouse.y;
      this.spherical.theta -= dx * 0.005;
      this.spherical.phi   = Math.max(0.1, Math.min(Math.PI - 0.1, this.spherical.phi + dy * 0.005));
      this.lastMouse = { x: e.clientX, y: e.clientY };
    });
    el.addEventListener('wheel', (e) => {
      this.spherical.radius = Math.max(10, Math.min(2000, this.spherical.radius + e.deltaY * 0.5));
    });
  }
}

export function spectralColour(spectral: string): { r: number; g: number; b: number } {
  const s = spectral[0]?.toUpperCase() ?? '?';
  switch (s) {
    case 'O': return { r: 0.6, g: 0.7,  b: 1.0  };
    case 'B': return { r: 0.7, g: 0.8,  b: 1.0  };
    case 'A': return { r: 0.9, g: 0.95, b: 1.0  };
    case 'F': return { r: 1.0, g: 1.0,  b: 0.9  };
    case 'G': return { r: 1.0, g: 0.95, b: 0.7  };
    case 'K': return { r: 1.0, g: 0.75, b: 0.4  };
    case 'M': return { r: 1.0, g: 0.4,  b: 0.2  };
    default:  return { r: 0.5, g: 0.5,  b: 0.5  };
  }
}
