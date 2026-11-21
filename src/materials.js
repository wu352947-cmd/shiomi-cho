import * as THREE from 'three';
import { ATMOSPHERE, SUN_DIR } from './config.js';
import { lookupMaterialSpec } from './palette.js';
import { TOON_VERT, TOON_FRAG, NORMAL_MASK_VERT, NORMAL_MASK_FRAG } from './shaders/toon.js';

const KIND_TO_TYPE = {
  wall: 0,
  roof: 0,
  ground: 0,
  metal: 0,
  boat: 0,
  cloth: 0,
  accent: 0,
  glass: 1,
  foliage: 2,
  emissive: 3,
  wet: 4,
  shoji: 5,
  wire: 6,
};

export function createMaterialSystem() {
  const sharedTime = { value: 0 };
  const toonCache = new Map();
  const normalCache = new Map();

  // Shared 1x1 white dummy texture so sampler2D uMap is always valid
  const dummyTex = new THREE.DataTexture(new Uint8Array([255, 255, 255, 255]), 1, 1);
  dummyTex.needsUpdate = true;

  function makeToonMaterial(matName, fallbackColor, opts = {}) {
    const animMode = opts.animMode || 0;
    const hasAO = Boolean(opts.hasAO);
    const doubleSided = Boolean(opts.doubleSided);
    const signMap = opts.signMap || null;

    const fallbackHex = fallbackColor ? '#' + fallbackColor.getHexString() : null;
    const spec = lookupMaterialSpec(matName, fallbackHex);
    const isDouble = doubleSided || spec.kind === 'cloth';

    const cacheKey = signMap
      ? null
      : `${spec.key}|a${animMode}|ao${hasAO ? 1 : 0}|ds${isDouble ? 1 : 0}|f${fallbackHex || ''}`;

    if (cacheKey && toonCache.has(cacheKey)) {
      return toonCache.get(cacheKey);
    }

    const baseCol = new THREE.Color(spec.color);
    const matType = KIND_TO_TYPE[spec.kind] ?? 0;

    const uniforms = THREE.UniformsUtils.merge([
      THREE.UniformsLib.lights,
      {
        uTime: sharedTime,
        uAnimMode: { value: animMode },
        uBaseColor: { value: baseCol },
        uSunDir: { value: SUN_DIR.clone() },
        uSunColor: { value: ATMOSPHERE.sunColor.clone() },
        uShadowTint: { value: ATMOSPHERE.shadowTint.clone() },
        uSkyFill: { value: ATMOSPHERE.skyFill.clone() },
        uSkyZenith: { value: ATMOSPHERE.skyZenith.clone() },
        uSkyHorizon: { value: ATMOSPHERE.skyHorizon.clone() },
        uFogColor: { value: ATMOSPHERE.fogColor.clone() },
        uFogNear: { value: ATMOSPHERE.fogNear },
        uFogFar: { value: ATMOSPHERE.fogFar },
        uSpecStrength: { value: spec.spec },
        uShininess: { value: spec.shininess },
        uRimStrength: { value: spec.rim },
        uMatType: { value: matType },
        uHasMap: { value: signMap ? 1.0 : 0.0 },
        uMap: { value: signMap || dummyTex },
      },
    ]);
    // Ensure uTime shares the exact same reference after UniformsUtils.merge clones objects
    uniforms.uTime = sharedTime;

    const mat = new THREE.ShaderMaterial({
      name: `toon_${spec.key}`,
      vertexShader: TOON_VERT,
      fragmentShader: TOON_FRAG,
      uniforms,
      lights: true,
      fog: false,
      vertexColors: hasAO,
      side: isDouble ? THREE.DoubleSide : THREE.FrontSide,
    });
    mat.userData.spec = spec;
    mat.userData.animMode = animMode;
    mat.userData.outlineWeight = spec.outline;

    if (cacheKey) toonCache.set(cacheKey, mat);
    return mat;
  }

  function makeNormalMaskMaterial(outlineWeight, animMode = 0, doubleSided = false) {
    const wKey = Math.round(outlineWeight * 100);
    const key = `nm|w${wKey}|a${animMode}|ds${doubleSided ? 1 : 0}`;
    if (normalCache.has(key)) return normalCache.get(key);

    const mat = new THREE.ShaderMaterial({
      vertexShader: NORMAL_MASK_VERT,
      fragmentShader: NORMAL_MASK_FRAG,
      uniforms: {
        uTime: sharedTime,
        uAnimMode: { value: animMode },
        uOutlineWeight: { value: outlineWeight },
      },
      side: doubleSided ? THREE.DoubleSide : THREE.FrontSide,
    });
    normalCache.set(key, mat);
    return mat;
  }

  function update(elapsed) {
    sharedTime.value = elapsed;
  }

  return {
    makeToonMaterial,
    makeNormalMaskMaterial,
    update,
    sharedTime,
  };
}
