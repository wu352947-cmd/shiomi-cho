import * as THREE from 'three';
import { ATMOSPHERE, SUN_DIR } from './config.js';

const CLOUD_VERT = /* glsl */ `
attribute vec3 aOffset;
attribute vec3 aScale; // width, height, flip
attribute vec4 aMeta;  // seed, towerStyle (0=shelf, 1=tower), tintBias, driftSpeed

uniform float uTime;
uniform vec3 uSunDir;

varying vec2 vUv;
varying vec4 vMeta;
varying vec2 vJitter;
varying vec3 vSunLocal;
varying float vDist;
varying float vWorldY;
varying float vEdgeAA;

void main() {
  vUv = uv;
  vMeta = aMeta;
  // Deterministic lobe offsets per-vertex (exact across quad, zero barycentric noise)
  float sd = floor(aMeta.x + 0.5);
  vJitter = vec2(
    fract(sin(sd * 12.9898) * 43758.5453) - 0.5,
    fract(sin(sd * 78.233) * 19341.234) - 0.5
  );

  vec3 center = aOffset;
  float drift = uTime * aMeta.w;
  center.x = mod(center.x + drift + 1600.0, 3200.0) - 1600.0;
  vWorldY = center.y;

  // Upright camera-facing billboard so flat summer cloud bases stay cleanly horizontal
  vec3 toCam = normalize(cameraPosition - center);
  vec3 upAxis = vec3(0.0, 1.0, 0.0);
  vec3 rightAxis = normalize(cross(upAxis, toCam));
  upAxis = normalize(cross(toCam, rightAxis));

  vec2 local = vec2(position.x * aScale.z, position.y);
  vec3 worldPos = center + rightAxis * (local.x * aScale.x) + upAxis * (local.y * aScale.y);

  vDist = length(cameraPosition - worldPos);
  vSunLocal = normalize(vec3(dot(uSunDir, rightAxis), dot(uSunDir, upAxis), dot(uSunDir, toCam)));
  // Smooth analytical screen-space anti-alias width (zero 2x2 quad fwidth banding!)
  vEdgeAA = clamp(vDist / (min(aScale.x, aScale.y) * 260.0), 0.010, 0.032);

  gl_Position = projectionMatrix * viewMatrix * vec4(worldPos, 1.0);
}
`;

const CLOUD_FRAG = /* glsl */ `
uniform vec3 uSkyHorizon;
uniform vec3 uSunColor;
uniform float uTime;

varying vec2 vUv;
varying vec4 vMeta;
varying vec2 vJitter;
varying vec3 vSunLocal;
varying float vDist;
varying float vWorldY;
varying float vEdgeAA;

float hash21(vec2 p) {
  p = fract(p * vec2(127.1, 311.7));
  p += dot(p, p + 34.53);
  return fract(p.x * p.y);
}

// Quintic smooth value noise (C2 continuous, zero blocky/speckled artifacts)
float snoise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  vec2 u = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);
  return mix(
    mix(hash21(i), hash21(i + vec2(1.0, 0.0)), u.x),
    mix(hash21(i + vec2(0.0, 1.0)), hash21(i + vec2(1.0, 1.0)), u.x),
    u.y
  );
}

// Ultra-clean 2-octave painterly billow noise (smooth organic curve, zero pixel stipple)
float smoothBillow(vec2 p) {
  mat2 m = mat2(0.80, -0.60, 0.60, 0.80);
  float v = 0.68 * snoise(p);
  v += 0.32 * snoise(m * p * 1.85 + vec2(4.7, 8.3));
  return v;
}

// Smooth maximum (polynomial smax) so cumulus puffs merge into silky cauliflower domes
float smax(float a, float b, float k) {
  float h = max(k - abs(a - b), 0.0) / k;
  return max(a, b) + h * h * k * 0.25;
}

float puff(vec2 p, vec2 c, vec2 r) {
  vec2 q = (p - c) / r;
  return 1.0 - length(q);
}

// Sculpted asymmetric Makoto Shinkai cumulus / cumulonimbus cauliflower silhouette
float cloudSilhouette(vec2 p, float seed, float tower, vec2 jit) {
  float s1 = jit.x;
  float s2 = jit.y;

  // Flat-bottomed cohesive cloud base made of overlapping scalloped lobes
  float baseY = tower > 1.05 ? -0.46 : -0.36;
  float d = puff(p, vec2(0.0, baseY), vec2(0.76, 0.28));
  d = smax(d, puff(p, vec2(-0.50 + s1 * 0.12, baseY + 0.08), vec2(0.32, 0.26)), 0.08);
  d = smax(d, puff(p, vec2(0.48 + s2 * 0.12, baseY + 0.09), vec2(0.34, 0.27)), 0.08);
  d = smax(d, puff(p, vec2(-0.26 + s2 * 0.10, baseY + 0.28), vec2(0.32, 0.31)), 0.07);
  d = smax(d, puff(p, vec2(0.24 + s1 * 0.10, baseY + 0.30), vec2(0.33, 0.30)), 0.07);
  d = smax(d, puff(p, vec2(s1 * 0.16, baseY + 0.44), vec2(0.30, 0.29)), 0.06);

  if (tower > 0.35) {
    float th = mix(0.20, 0.44, clamp(tower, 0.0, 1.0));
    // Rising cauliflower lobes with distinct left/right asymmetry
    d = smax(d, puff(p, vec2(-0.24 + s2 * 0.10, th * 0.55), vec2(0.24, 0.25)), 0.055);
    d = smax(d, puff(p, vec2(0.26 - s1 * 0.10, th * 0.48), vec2(0.23, 0.24)), 0.055);
    d = smax(d, puff(p, vec2(0.04 + s1 * 0.18, th * 0.88), vec2(0.27, 0.29)), 0.055);
    d = smax(d, puff(p, vec2(-0.12 - s2 * 0.10, th * 1.05), vec2(0.19, 0.20)), 0.045);
  }

  // Towering summer cumulonimbus (入道雲) vertical cauliflower spire!
  if (tower > 1.05) {
    d = smax(d, puff(p, vec2(-0.30, 0.08), vec2(0.24, 0.25)), 0.05);
    d = smax(d, puff(p, vec2(0.30, 0.04), vec2(0.25, 0.24)), 0.05);
    d = smax(d, puff(p, vec2(-0.14, 0.34), vec2(0.24, 0.24)), 0.05);
    d = smax(d, puff(p, vec2(0.18, 0.30), vec2(0.23, 0.23)), 0.05);
    d = smax(d, puff(p, vec2(-0.02 + s1 * 0.08, 0.54), vec2(0.25, 0.24)), 0.045);
    d = smax(d, puff(p, vec2(-0.18, 0.62), vec2(0.18, 0.17)), 0.04);
    d = smax(d, puff(p, vec2(0.16, 0.58), vec2(0.19, 0.18)), 0.04);
    d = smax(d, puff(p, vec2(0.02, 0.72), vec2(0.17, 0.15)), 0.04);
  }

  // Gentle sculptural cauliflower scallop (clean low-freq curve, zero noisy edge fringes)
  vec2 warpUv = p * 2.0 + vec2(seed * 2.3 + uTime * 0.003, seed * 1.7);
  float edgeWarp = (smoothBillow(warpUv) - 0.5) * 0.14;
  d += edgeWarp;

  // Clean horizontal summer condensation level flat base
  float flatLow = tower > 1.05 ? -0.64 : -0.54;
  float flatHigh = tower > 1.05 ? -0.44 : -0.34;
  float flatCut = smoothstep(flatLow, flatHigh, p.y + edgeWarp * 0.18);
  d = mix(-0.45, d, flatCut);

  // Soft quad-boundary safety guard so clouds never clip their billboard rectangle
  float edgeDist = max(abs(p.x), abs(p.y));
  d -= smoothstep(0.84, 0.98, edgeDist) * 0.55;
  return d;
}

void main() {
  vec2 p = vUv * 2.0 - 1.0;
  float seed = floor(vMeta.x + 0.5);
  float tower = vMeta.y;

  float dens = cloudSilhouette(p, seed, tower, vJitter);
  // Crisp silky anti-aliased anime silhouette (pure analytical AA -> zero dithering!)
  float alpha = smoothstep(0.025 - vEdgeAA, 0.055 + vEdgeAA, dens);
  if (alpha < 0.008) discard;

  // Directional sun self-shadowing across the billowing cloud volume
  vec2 sun2D = normalize(vSunLocal.xy + vec2(0.001, 0.28));
  float dSun1 = cloudSilhouette(p + sun2D * 0.11, seed, tower, vJitter);
  float dSun2 = cloudSilhouette(p + sun2D * 0.25, seed, tower, vJitter);

  // Smooth interior painterly puff shading (never affects alpha!)
  vec2 detailUv = p * 3.1 + vec2(seed * 3.1, seed * 2.7);
  float puffDetail = smoothBillow(detailUv) * 0.65 + smoothBillow(detailUv * 1.75) * 0.35;

  float heightGrad = smoothstep(-0.54, 0.72, p.y);
  float selfShadow = clamp(1.0 - (max(dSun1, 0.0) * 0.88 + max(dSun2, 0.0) * 0.52), 0.0, 1.0);
  float billowLight = (puffDetail - 0.48) * 0.30;
  float baseDark = (1.0 - smoothstep(-0.56, -0.18, p.y)) * 0.46;

  float lit = clamp(selfShadow * 0.58 + heightGrad * 0.46 + billowLight - baseDark + 0.07, 0.0, 1.0);

  // Iconic Makoto Shinkai 4-tone summer cumulus ramp (lavender-blue belly -> golden-cream crown)
  float bandMid    = smoothstep(0.24, 0.42, lit);
  float bandBright = smoothstep(0.50, 0.68, lit);
  float bandCrown  = smoothstep(0.74, 0.90, lit);

  vec3 deepUnder  = vec3(0.42, 0.54, 0.84);   // cool lavender-periwinkle shadow underside
  vec3 coolMid    = vec3(0.70, 0.81, 0.96);   // airy sky-bounce mid-cloud shadow
  vec3 sunlitBody = vec3(0.97, 0.985, 1.00);  // crisp sunlit summer white
  vec3 warmCrest  = mix(vec3(1.05, 1.01, 0.94), uSunColor * 1.15, 0.46); // radiant warm-cream crest

  vec3 col = mix(deepUnder, coolMid, bandMid);
  col = mix(col, sunlitBody, bandBright);
  col = mix(col, warmCrest, bandCrown);

  // Luminous sunlit silver lining right on upper-sunward silhouette rim
  float rimBand = (1.0 - smoothstep(0.05, 0.24, dens)) * smoothstep(0.44, 0.88, lit);
  col += vec3(0.26, 0.22, 0.14) * rimBand;

  // Soft horizon aerial blend on low distant cloud shelves
  float horFade = smoothstep(820.0, 1850.0, vDist) * (1.0 - smoothstep(140.0, 420.0, vWorldY));
  col = mix(col, uSkyHorizon * 1.04, horFade * 0.32);

  gl_FragColor = vec4(col, alpha * 0.985);
}
`;

export function createClouds(qualityTier) {
  const BANKS = [
    // Signature giant towering入道雲 (cumulonimbus) on the north-east horizon behind mountains!
    { x: 420,  y: 270, z: -1080, w: 640, h: 520, tower: 1.30, speed: 0.75, seed: 11 },
    // Companion north/west horizon cumulus banks (integer seeds -> exact constant per quad!)
    { x: 840,  y: 235, z: -640,  w: 500, h: 325, tower: 0.92, speed: 1.1, seed: 23 },
    { x: 40,   y: 315, z: -1080, w: 590, h: 390, tower: 0.95, speed: 0.9, seed: 37 },
    { x: -410, y: 330, z: -1020, w: 550, h: 365, tower: 0.88, speed: 1.0, seed: 49 },
    { x: -800, y: 250, z: -660,  w: 510, h: 320, tower: 0.84, speed: 1.2, seed: 61 },

    // East & West coastal flanks
    { x: 960,  y: 220, z: -120, w: 480, h: 280, tower: 0.78, speed: 1.4, seed: 73 },
    { x: 920,  y: 205, z: 420,  w: 460, h: 265, tower: 0.75, speed: 1.3, seed: 84 },
    { x: -940, y: 225, z: -100, w: 480, h: 275, tower: 0.76, speed: 1.3, seed: 95 },
    { x: -880, y: 210, z: 480,  w: 450, h: 260, tower: 0.72, speed: 1.5, seed: 107 },

    // Giant Pacific horizon cumulus towers (visible from Shrine & Crossing looking south!)
    { x: -240, y: 245, z: 980,  w: 610, h: 440, tower: 1.25, speed: 1.0, seed: 119 },
    { x: 270,  y: 240, z: 1040, w: 600, h: 390, tower: 1.0,  speed: 1.0, seed: 131 },
    { x: -460, y: 125, z: 1060, w: 500, h: 255, tower: 0.72, speed: 1.3, seed: 143 },
    { x: 380,  y: 120, z: 1080, w: 520, h: 260, tower: 0.76, speed: 1.2, seed: 155 },
    { x: -680, y: 225, z: 820,  w: 460, h: 270, tower: 0.74, speed: 1.4, seed: 161 },
    { x: 680,  y: 220, z: 800,  w: 450, h: 265, tower: 0.72, speed: 1.3, seed: 165 },

    // Low distant coastal cloud shelves
    { x: 690,  y: 140, z: -980, w: 540, h: 165, tower: 0.14, speed: 0.9, seed: 167 },
    { x: 890,  y: 130, z: -420, w: 500, h: 155, tower: 0.12, speed: 1.0, seed: 179 },
    { x: -20,  y: 165, z: 1120, w: 620, h: 190, tower: 0.22, speed: 0.9, seed: 191 },
    { x: -580, y: 155, z: -1040, w: 560, h: 170, tower: 0.16, speed: 1.0, seed: 203 },

    // Secondary high fair-weather clouds
    { x: -160, y: 405, z: -860, w: 380, h: 225, tower: 0.52, speed: 1.5, seed: 227 },
    { x: 20,   y: 340, z: 860,  w: 380, h: 225, tower: 0.60, speed: 1.5, seed: 239 },
  ];

  const maxBanks = qualityTier.name === 'low' ? 14 : BANKS.length;
  const active = BANKS.slice(0, maxBanks);

  const offsets = new Float32Array(active.length * 3);
  const scales = new Float32Array(active.length * 3);
  const metas = new Float32Array(active.length * 4);

  active.forEach((b, i) => {
    offsets[i * 3 + 0] = b.x;
    offsets[i * 3 + 1] = b.y;
    offsets[i * 3 + 2] = b.z;
    scales[i * 3 + 0] = b.w;
    scales[i * 3 + 1] = b.h;
    scales[i * 3 + 2] = i % 2 === 0 ? 1.0 : -1.0;
    metas[i * 4 + 0] = b.seed;
    metas[i * 4 + 1] = b.tower;
    metas[i * 4 + 2] = 0.5;
    metas[i * 4 + 3] = b.speed;
  });

  const baseGeo = new THREE.PlaneGeometry(1, 1);
  const instGeo = new THREE.InstancedBufferGeometry();
  instGeo.index = baseGeo.index;
  instGeo.attributes.position = baseGeo.attributes.position;
  instGeo.attributes.uv = baseGeo.attributes.uv;
  instGeo.setAttribute('aOffset', new THREE.InstancedBufferAttribute(offsets, 3));
  instGeo.setAttribute('aScale', new THREE.InstancedBufferAttribute(scales, 3));
  instGeo.setAttribute('aMeta', new THREE.InstancedBufferAttribute(metas, 4));
  instGeo.instanceCount = active.length;

  const uniforms = {
    uTime: { value: 0 },
    uSunDir: { value: SUN_DIR.clone() },
    uSkyHorizon: { value: ATMOSPHERE.skyHorizon.clone() },
    uSunColor: { value: ATMOSPHERE.sunColor.clone() },
  };

  const mat = new THREE.ShaderMaterial({
    vertexShader: CLOUD_VERT,
    fragmentShader: CLOUD_FRAG,
    uniforms,
    transparent: true,
    depthWrite: false,
    depthTest: true,
    side: THREE.DoubleSide,
  });

  const mesh = new THREE.Mesh(instGeo, mat);
  mesh.name = 'AnimeCumulusClouds';
  mesh.frustumCulled = false;
  mesh.renderOrder = -40;
  baseGeo.dispose();

  return { mesh, uniforms, count: active.length };
}
