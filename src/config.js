import * as THREE from 'three';

export function parseParams() {
  const sp = new URLSearchParams(window.location.search);
  const qParam = (sp.get('q') || '').toLowerCase();
  const isMobile = /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent) ||
    Math.min(window.innerWidth, window.innerHeight) <= 520;
  let quality = isMobile ? 'low' : 'high';
  if (qParam === 'low' || qParam === 'med' || qParam === 'high') {
    quality = qParam;
  }
  return {
    quality,
    isMobile,
    cam: (sp.get('cam') || 'overview').toLowerCase(),
    ui: sp.get('ui') !== '0',
    auto: sp.get('auto') !== '0',
    model: sp.get('model') || '',
  };
}

export const QUALITY_TIERS = {
  low: {
    name: 'low',
    maxDpr: 1.25,
    shadowMapSize: 1024,
    cloudCount: 18,
    petalCount: 0,
    seagullCount: 5,
    bloomScale: 0.5,
    oceanSegs: 96,
    useOutline: true,
    useFXAA: true,
  },
  med: {
    name: 'med',
    maxDpr: 1.5,
    shadowMapSize: 2048,
    cloudCount: 26,
    petalCount: 40,
    seagullCount: 7,
    bloomScale: 0.5,
    oceanSegs: 128,
    useOutline: true,
    useFXAA: true,
  },
  high: {
    name: 'high',
    maxDpr: 2.0,
    shadowMapSize: 2048,
    cloudCount: 36,
    petalCount: 65,
    seagullCount: 9,
    bloomScale: 0.75,
    oceanSegs: 160,
    useOutline: true,
    useFXAA: true,
  },
};

// Summer afternoon ~15:30, elevation ~35 deg, azimuth SW (over sea, front-left of town)
// Three.js coords: +X East, +Y Up, +Z South (sea)
export const SUN_DIR = new THREE.Vector3(-0.56, 0.575, 0.596).normalize();

export const ATMOSPHERE = {
  sunColor: new THREE.Color('#FFF0CE'),
  skyZenith: new THREE.Color('#0E4AB8'),
  skyMid: new THREE.Color('#2E82E2'),
  skyHorizon: new THREE.Color('#B4E2FC'),
  sunHaze: new THREE.Color('#FFEDC2'),
  shadowTint: new THREE.Color('#5A6DA8'),
  skyFill: new THREE.Color('#96C3FF'),
  fogColor: new THREE.Color('#9DC4EC'),
  fogNear: 175,
  fogFar: 920,
};

// Blender (x, y, z) -> Three.js (x, z, -y)
export const CAMERA_PRESETS = {
  overview: {
    label: '全景',
    pos: [-96, 46, 174],
    target: [12, 20, -24],
    fov: 44,
  },
  harbor: {
    label: '港口',
    pos: [-46, 16, 72],
    target: [16, 5.5, 2],
    fov: 44,
  },
  street: {
    label: '商店街',
    pos: [-36, 4.0, -3.5],
    target: [24, 4.4, -7.2],
    fov: 46,
  },
  shrine: {
    label: '神社',
    pos: [-14, 56.5, -120],
    target: [-31, 54.5, -148],
    fov: 48,
  },
  lighthouse: {
    label: '灯塔',
    pos: [106, 18, 136],
    target: [48, 8.0, 82],
    fov: 44,
  },
  crossing: {
    label: '踏切',
    pos: [-25.0, 6.4, -23.5],
    target: [-24.5, 3.1, 8.0],
    fov: 46,
  },
};

export const PRESET_KEYS = Object.keys(CAMERA_PRESETS);
