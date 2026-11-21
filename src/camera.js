import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CAMERA_PRESETS } from './config.js';

const IDLE_MS = 8000;
const FLY_DURATION = 1.35;

export function createCameraController(camera, domElement, opts = {}) {
  const autoEnabled = opts.auto !== false;
  const controls = new OrbitControls(camera, domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.068;
  controls.rotateSpeed = 0.65;
  controls.zoomSpeed = 0.85;
  controls.panSpeed = 0.72;
  controls.screenSpacePanning = false;
  controls.minDistance = 10;
  controls.maxDistance = 410;
  controls.minPolarAngle = 0.14;
  controls.maxPolarAngle = Math.PI * 0.484;
  controls.autoRotate = false;
  controls.autoRotateSpeed = 0.34;
  controls.touches = {
    ONE: THREE.TOUCH.ROTATE,
    TWO: THREE.TOUCH.DOLLY_PAN,
  };

  let lastInteract = performance.now();
  let currentPreset = 'overview';
  let onPresetChange = null;

  // Fly-to transition state (reused vectors -> zero per-frame allocations)
  const fly = {
    active: false,
    elapsed: 0,
    startPos: new THREE.Vector3(),
    endPos: new THREE.Vector3(),
    startTarget: new THREE.Vector3(),
    endTarget: new THREE.Vector3(),
    startFov: 42,
    endFov: 42,
  };

  function markInteract() {
    lastInteract = performance.now();
    controls.autoRotate = false;
    fly.active = false;
  }

  controls.addEventListener('start', markInteract);
  domElement.addEventListener('pointerdown', markInteract, { passive: true });
  domElement.addEventListener('wheel', markInteract, { passive: true });
  domElement.addEventListener('touchstart', markInteract, { passive: true });

  function setCam(name, instant = false) {
    const key = (name || 'overview').toLowerCase();
    const preset = CAMERA_PRESETS[key] || CAMERA_PRESETS.overview;
    currentPreset = CAMERA_PRESETS[key] ? key : 'overview';

    controls.autoRotate = false;
    lastInteract = performance.now();

    if (instant) {
      fly.active = false;
      camera.position.set(preset.pos[0], preset.pos[1], preset.pos[2]);
      controls.target.set(preset.target[0], preset.target[1], preset.target[2]);
      if (Math.abs(camera.fov - preset.fov) > 0.05) {
        camera.fov = preset.fov;
        camera.updateProjectionMatrix();
      }
      controls.update();
    } else {
      fly.active = true;
      fly.elapsed = 0;
      fly.startPos.copy(camera.position);
      fly.endPos.set(preset.pos[0], preset.pos[1], preset.pos[2]);
      fly.startTarget.copy(controls.target);
      fly.endTarget.set(preset.target[0], preset.target[1], preset.target[2]);
      fly.startFov = camera.fov;
      fly.endFov = preset.fov;
    }

    if (onPresetChange) onPresetChange(currentPreset);
  }

  // Approximate terrain height floor so camera never dives under sea or hillside
  function minGroundY(x, z) {
    if (z > 8) return 2.2;
    if (z > -18) return 3.0;
    const t = Math.min(1, (-z - 18) / 135);
    const dx = (x + 30) / 150;
    const ridge = Math.exp(-dx * dx * 1.4);
    return 3.2 + Math.pow(t, 1.25) * 50.0 * (0.55 + 0.45 * ridge);
  }

  function update(dt) {
    if (fly.active) {
      fly.elapsed += dt;
      const rawT = Math.min(1, fly.elapsed / FLY_DURATION);
      // Smooth quintic ease-in-out
      const t = rawT < 0.5
        ? 4 * rawT * rawT * rawT
        : 1 - Math.pow(-2 * rawT + 2, 3) / 2;
      camera.position.lerpVectors(fly.startPos, fly.endPos, t);
      controls.target.lerpVectors(fly.startTarget, fly.endTarget, t);
      const nextFov = fly.startFov + (fly.endFov - fly.startFov) * t;
      if (Math.abs(camera.fov - nextFov) > 0.02) {
        camera.fov = nextFov;
        camera.updateProjectionMatrix();
      }
      if (rawT >= 1) fly.active = false;
    } else if (autoEnabled && !controls.autoRotate) {
      if (performance.now() - lastInteract >= IDLE_MS) {
        controls.autoRotate = true;
      }
    }

    controls.update();

    // Clamp target within coastal town basin & camera safely above sea/terrain
    controls.target.x = THREE.MathUtils.clamp(controls.target.x, -165, 165);
    controls.target.z = THREE.MathUtils.clamp(controls.target.z, -190, 145);
    controls.target.y = THREE.MathUtils.clamp(controls.target.y, 0.5, 85);

    const floorY = minGroundY(camera.position.x, camera.position.z);
    if (camera.position.y < floorY) {
      camera.position.y = floorY;
    }
  }

  function setOnPresetChange(cb) {
    onPresetChange = cb;
  }

  return {
    controls,
    setCam,
    update,
    setOnPresetChange,
    getPreset: () => currentPreset,
  };
}
