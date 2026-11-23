// Three.js scene: city block + road + character + soft light + slow push-in.
// Open index.html in Chrome (mobile OK). Uses three r170 from CDN.
import * as THREE from 'https://unpkg.com/three@0.170.0/build/three.module.js';

const W = 1080, H = 1920;
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(W / 2, H / 2, false);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
document.body.style.margin = 0;
document.body.appendChild(renderer.domElement);
renderer.domElement.style.width = '100vw';

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xf4e6d4);
scene.fog = new THREE.Fog(0xf4e6d4, 40, 120);

const cam = new THREE.PerspectiveCamera(35, W / H, 0.1, 300);
const camStart = new THREE.Vector3(0, 2.2, 14), camEnd = new THREE.Vector3(0, 2.0, 7.5);
const look = new THREE.Vector3(0, 1.4, 0);

scene.add(new THREE.HemisphereLight(0xfff4e6, 0x5a4a3a, 1.1));
const sun = new THREE.DirectionalLight(0xffe2b8, 2.4);
sun.position.set(-10, 14, 8); sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -15, right: 15, top: 15, bottom: -15, near: 1, far: 60 });
scene.add(sun);

const ground = new THREE.Mesh(new THREE.PlaneGeometry(200, 200), new THREE.MeshStandardMaterial({ color: 0x8a8a84, roughness: 0.95 }));
ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);

const road = new THREE.Mesh(new THREE.PlaneGeometry(6, 200), new THREE.MeshStandardMaterial({ color: 0x3a3a3a, roughness: 0.8 }));
road.rotation.x = -Math.PI / 2; road.position.y = 0.01; road.receiveShadow = true; scene.add(road);

// simple buildings
const bMat = [0xd9c7a8, 0xbfb29a, 0xe8ddc8, 0xa89a84].map(c => new THREE.MeshStandardMaterial({ color: c, roughness: 0.7 }));
for (let i = 0; i < 10; i++) {
  const h = 4 + (i * 37 % 9);
  const b = new THREE.Mesh(new THREE.BoxGeometry(3, h, 3), bMat[i % 4]);
  b.position.set(i % 2 ? 6 : -6, h / 2, -i * 4 + 2);
  b.castShadow = b.receiveShadow = true; scene.add(b);
}

// character: red helmet, green visor, red T-shirt, blue jeans, red shoes
const M = (c, r = 0.6) => new THREE.MeshStandardMaterial({ color: c, roughness: r });
const char = new THREE.Group(); char.position.set(1.8, 0, 0); scene.add(char);
const part = (geo, mat, x, y, z) => { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.castShadow = true; char.add(m); return m; };
part(new THREE.CylinderGeometry(0.22, 0.2, 0.9, 16), M(0x1f3d8f), -0.13, 0.45, 0);   // left leg
part(new THREE.CylinderGeometry(0.22, 0.2, 0.9, 16), M(0x1f3d8f), 0.13, 0.45, 0);    // right leg
part(new THREE.BoxGeometry(0.1, 0.07, 0.22), M(0xc81414), -0.13, 0.03, 0.05);         // shoes
part(new THREE.BoxGeometry(0.1, 0.07, 0.22), M(0xc81414), 0.13, 0.03, 0.05);
part(new THREE.BoxGeometry(0.55, 0.62, 0.3), M(0xd01010), 0, 1.2, 0);                  // red T-shirt
part(new THREE.SphereGeometry(0.2, 24, 20), M(0xc69070), 0, 1.78, 0);                  // head
part(new THREE.SphereGeometry(0.24, 24, 20, 0, Math.PI * 2, 0, Math.PI / 2), M(0xd81818, 0.35), 0, 1.84, 0); // red helmet
part(new THREE.BoxGeometry(0.34, 0.09, 0.05), M(0x18d060, 0.1), 0, 1.78, -0.2);       // green visor
const arm = (x) => part(new THREE.CylinderGeometry(0.07, 0.07, 0.6, 12), M(0xd01010), x, 1.15, 0);
arm(-0.36); arm(0.36);

// slow push-in: ease in-out, no shake
const clock = new THREE.Clock();
const ease = t => t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
function frame() {
  const t = ease(Math.min(clock.getElapsedTime() / 8, 1));
  cam.position.lerpVectors(camStart, camEnd, t);
  cam.lookAt(look);
  renderer.render(scene, cam);
  requestAnimationFrame(frame);
}
frame();
window.addEventListener('resize', () => renderer.setSize(W / 2, H / 2, false));
