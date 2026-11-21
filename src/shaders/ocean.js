import * as THREE from 'three';
import { ATMOSPHERE, SUN_DIR } from '../config.js';

const OCEAN_VERT = /* glsl */ `
uniform float uTime;

varying vec3 vWorldPos;
varying vec3 vWaveNormal;
varying float vWaveCrest;

// Sum of directional swells (gentler inside harbor basin)
void computeWave(vec2 xz, float t, out float h, out vec2 grad) {
  // Calm waves slightly inside sheltered harbor basin (x in -65..95, z in -5..90)
  float bx = smoothstep(55.0, 125.0, abs(xz.x - 15.0));
  float bz = smoothstep(55.0, 120.0, abs(xz.y - 42.0));
  float calm = mix(0.32, 1.0, max(bx, bz));
  // Attenuate far displacement to avoid distant horizon aliasing
  float farFade = 1.0 - smoothstep(420.0, 1400.0, length(xz));
  float ampMul = calm * farFade;

  h = 0.0;
  grad = vec2(0.0);

  vec2 d1 = normalize(vec2(0.45, -0.89));
  float p1 = dot(xz, d1) * 0.085 + t * 1.15;
  float a1 = 0.24 * ampMul;
  h += sin(p1) * a1;
  grad += d1 * cos(p1) * a1 * 0.085;

  vec2 d2 = normalize(vec2(-0.62, -0.78));
  float p2 = dot(xz, d2) * 0.135 + t * 1.48;
  float a2 = 0.15 * ampMul;
  h += sin(p2) * a2;
  grad += d2 * cos(p2) * a2 * 0.135;

  vec2 d3 = normalize(vec2(0.86, -0.51));
  float p3 = dot(xz, d3) * 0.22 + t * 1.92;
  float a3 = 0.075 * ampMul;
  h += sin(p3) * a3;
  grad += d3 * cos(p3) * a3 * 0.22;
}

void main() {
  // Non-linear radial expansion: high density near town & harbor, reaching 2100m horizon
  vec2 p = position.xz;
  float r = length(p);
  vec2 dir = r > 1e-5 ? p / r : vec2(0.0);
  float expandedR = r * 260.0 + pow(r, 3.2) * 1880.0;
  vec3 worldPos = vec3(dir.x * expandedR, 0.0, dir.y * expandedR);

  float h;
  vec2 grad;
  computeWave(worldPos.xz, uTime, h, grad);
  worldPos.y += h;

  vWorldPos = worldPos;
  vWaveNormal = normalize(vec3(-grad.x, 1.0, -grad.y));
  vWaveCrest = clamp(h * 2.2 + 0.5, 0.0, 1.0);

  gl_Position = projectionMatrix * viewMatrix * vec4(worldPos, 1.0);
}
`;

const OCEAN_FRAG = /* glsl */ `
#include <packing>

uniform sampler2D tDepth;
uniform vec2 uResolution;
uniform float uCameraNear;
uniform float uCameraFar;
uniform float uTime;
uniform vec3 uSunDir;
uniform vec3 uSunColor;
uniform vec3 uSkyZenith;
uniform vec3 uSkyHorizon;
uniform vec3 uFogColor;

varying vec3 vWorldPos;
varying vec3 vWaveNormal;
varying float vWaveCrest;

float hash21(vec2 p) {
  p = fract(p * vec2(127.1, 311.7));
  p += dot(p, p + 34.5);
  return fract(p.x * p.y);
}

float vnoise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  f = f * f * (3.0 - 2.0 * f);
  return mix(
    mix(hash21(i), hash21(i + vec2(1.0, 0.0)), f.x),
    mix(hash21(i + vec2(0.0, 1.0)), hash21(i + vec2(1.0, 1.0)), f.x),
    f.y
  );
}

float readLinearDepth(float fragCoordZ) {
  float viewZ = perspectiveDepthToViewZ(fragCoordZ, uCameraNear, uCameraFar);
  return -viewZ;
}

void main() {
  vec2 screenUv = gl_FragCoord.xy / uResolution;
  float sceneRawZ = texture2D(tDepth, screenUv).x;
  float sceneDist = readLinearDepth(sceneRawZ);
  float waterDist = readLinearDepth(gl_FragCoord.z);
  float depthDiff = max(0.0, sceneDist - waterDist);
  // Treat far background (no seabed geometry beyond town) as deep open ocean
  if (sceneRawZ > 0.9994) depthDiff = 55.0;

  vec3 V = normalize(cameraPosition - vWorldPos);
  vec3 L = normalize(uSunDir);
  float dist = length(cameraPosition - vWorldPos);

  // Smooth shelter mask: 0.0 inside calm harbor basin, 1.0 in open sea
  float hx = smoothstep(48.0, 94.0, abs(vWorldPos.x - 12.0));
  float hz = smoothstep(40.0, 92.0, abs(vWorldPos.z - 42.0));
  float openSea = max(hx, hz);
  float offshore = smoothstep(55.0, 175.0, vWorldPos.z);
  float waveActivity = mix(0.16, 1.0, max(openSea * 0.9, offshore));

  // Organic anime sea ripple lines: stretched primarily along coastal swell (no cross-hatch grid, no camo blobs!)
  // Two slightly angled swell orientations (~12 deg apart) so crests weave organically without plaid diamonds
  mat2 rot1 = mat2(0.985, -0.174, 0.174, 0.985);
  mat2 rot2 = mat2(0.996,  0.087, -0.087, 0.996);
  vec2 w1 = rot1 * vWorldPos.xz;
  vec2 w2 = rot2 * vWorldPos.xz;

  // Fine elongated anisotropic value-noise ripples (ratio ~5:1 along crest vs across wave)
  vec2 ripUv1 = vec2(w1.x * 0.16, w1.y * 0.78) + vec2(uTime * 0.14, -uTime * 0.42);
  vec2 ripUv2 = vec2(w2.x * 0.24, w2.y * 1.18) + vec2(-uTime * 0.18, -uTime * 0.56);
  vec2 ripUv3 = vec2(w1.x * 0.42, w1.y * 1.95) + vec2(uTime * 0.26, -uTime * 0.74);

  // Subtle organic lateral meander so wave lines curve like painterly brush strokes
  float meander = (vnoise(vec2(w1.x * 0.07, w1.y * 0.22) + vec2(0.0, -uTime * 0.15)) - 0.5) * 1.25;
  ripUv1.y += meander * 0.55;
  ripUv2.y -= meander * 0.42;

  float n1 = vnoise(ripUv1);
  float n2 = vnoise(ripUv2);
  float n3 = vnoise(ripUv3);

  // Sharp thin wave-crest ridges (1 - |2n - 1| creates crisp narrow anime ripple strokes, never round blobs!)
  float ridge1 = 1.0 - abs(n1 * 2.0 - 1.0);
  float ridge2 = 1.0 - abs(n2 * 2.0 - 1.0);
  float ridge3 = 1.0 - abs(n3 * 2.0 - 1.0);
  float fineLine = pow(ridge1, 3.6) * 0.52 + pow(ridge2, 4.2) * 0.40 + pow(ridge3, 4.5) * 0.26;

  float rippleFade = 1.0 - smoothstep(180.0, 980.0, dist);
  float fineFade = 1.0 - smoothstep(85.0, 440.0, dist);

  // Directional normal perturbation via finite differences of stretched ripples (silky calm inside harbor!)
  float d1 = vnoise(ripUv1 + vec2(0.0, 0.12)) - n1;
  float d2 = vnoise(ripUv2 + vec2(0.0, 0.14)) - n2;
  float dx1 = vnoise(ripUv1 + vec2(0.12, 0.0)) - n1;
  float nAmp = (0.14 + 0.42 * waveActivity) * rippleFade;
  vec3 ripplePerturb = vec3(
    dx1 * 0.35 + (n3 - 0.5) * 0.10 * fineFade,
    0.0,
    (d1 * 1.35 + d2 * 1.05 + (n3 - 0.5) * 0.14 * fineFade)
  ) * nAmp;
  vec3 N = normalize(vWaveNormal + ripplePerturb);

  // Smooth depth gradient: luminous turquoise shallows -> clear azure harbor -> rich deep cobalt offshore
  float vertDepth = depthDiff * clamp(V.y * 0.85 + 0.28, 0.35, 1.0);
  float effectiveDepth = vertDepth + offshore * 14.0 + openSea * 5.2;

  vec3 shallowCol = vec3(0.14, 0.78, 0.76); // crystal emerald-turquoise shallows near sand/quay
  vec3 midSeaCol  = vec3(0.05, 0.40, 0.74); // clear serene cerulean harbor water
  vec3 deepSeaCol = vec3(0.022, 0.16, 0.50); // rich deep cobalt Pacific offshore

  float tShallow = 1.0 - exp(-effectiveDepth * 0.52);
  float tDeep = 1.0 - exp(-effectiveDepth * 0.145);
  vec3 waterCol = mix(shallowCol, midSeaCol, smoothstep(0.03, 0.86, tShallow));
  waterCol = mix(waterCol, deepSeaCol, smoothstep(0.12, 0.94, tDeep));

  // Delicate shallow-water caustic net strictly in crystal shallows (< 2m)
  float shallowMask = (1.0 - tShallow) * fineFade;
  float causticNet = pow(ridge2 * ridge3, 2.2);
  waterCol += vec3(0.15, 0.38, 0.36) * causticNet * shallowMask * 0.48;

  // Fine anime directional ripple highlights (crisp thin strokes, calmer in harbor, zero camo blotches)
  float strokeMask = smoothstep(0.36, 0.78, fineLine) * rippleFade;
  float strokeStrength = mix(0.07, 0.24, waveActivity);
  vec3 strokeCol = mix(vec3(0.34, 0.76, 0.95), vec3(0.56, 0.86, 0.99), offshore * 0.45);
  waterCol = mix(waterCol, strokeCol, strokeMask * strokeStrength);

  // Very subtle cool depth ripple line variation (never blotchy patches)
  float coolTrough = smoothstep(0.62, 0.90, pow(1.0 - ridge1, 2.2)) * rippleFade * mix(0.03, 0.11, waveActivity);
  waterCol *= mix(vec3(1.0), vec3(0.84, 0.90, 0.98), coolTrough);

  // Fresnel sky reflection (clean overhead cobalt, glassy calm in harbor, luminous at horizon)
  float ndv = max(dot(N, V), 0.0);
  float fresnel = pow(1.0 - ndv, 4.0);
  vec3 R = reflect(-V, N);
  vec3 skyRefl = mix(uSkyHorizon * 0.88, uSkyZenith * 1.10, clamp(R.y * 1.35 + 0.12, 0.0, 1.0));
  float reflMix = clamp(mix(0.05, 0.13, 1.0 - openSea) + fresnel * 0.54, 0.0, 0.68);
  vec3 col = mix(waterCol, skyRefl, reflMix);

  // Sparkling sun-glint band toward the sun (crisp Shinkai diamond sparkles, HDR > 1.0 blooms!)
  vec3 H = normalize(L + V);
  float ndh = max(dot(N, H), 0.0);
  vec3 flatRefl = reflect(-L, vec3(0.0, 1.0, 0.0));
  float sunBand = pow(max(dot(flatRefl, V), 0.0), 8.5);
  float sunBandTight = pow(max(dot(flatRefl, V), 0.0), 28.0);

  // Fine high-frequency glitter facets aligned along wave crests
  vec2 spUv1 = vec2(w1.x * 0.88, w1.y * 2.25) + vec2(uTime * 0.52, -uTime * 0.86);
  vec2 spUv2 = vec2(w2.x * 1.32, w2.y * 3.10) + vec2(-uTime * 0.64, -uTime * 0.72);
  float spCell = vnoise(spUv1) * vnoise(spUv2);
  float glintLine = smoothstep(0.28, 0.54, spCell) * (0.45 + 0.55 * strokeMask);
  float diamondGlint = smoothstep(0.42, 0.62, spCell);

  float broadSheen = (pow(ndh, 58.0) * 0.36 + sunBandTight * 0.28) * (0.55 + 0.45 * waveActivity);
  float sharpSparkle = pow(ndh, 155.0) * (1.6 + diamondGlint * 5.6);
  float pathGlitter = (glintLine * sunBand * 3.1 + diamondGlint * sunBandTight * 4.8) * (0.35 + 0.65 * rippleFade);
  // Delicate sunlit crest sparkles catching afternoon rays across mid/foreground sea
  float crestSparkle = smoothstep(0.56, 0.74, spCell) * smoothstep(0.58, 0.94, ndh) * fineFade * 1.35;
  col += uSunColor * (broadSheen + sharpSparkle + pathGlitter + crestSparkle);

  // Clean white shoreline, breakwater, quay & boat hull foam lines
  float foamNoise = vnoise(vWorldPos.xz * 0.76 + vec2(uTime * 0.28, -uTime * 0.22));
  float fineFoamNoise = vnoise(vWorldPos.xz * 1.95 - vec2(uTime * 0.42, uTime * 0.31));
  float fNoise = foamNoise * 0.65 + fineFoamNoise * 0.35;
  float edgeFoam = 1.0 - smoothstep(0.06, 0.48 + fNoise * 0.38, vertDepth);
  float waveRing = sin(vertDepth * 7.2 - uTime * 2.4 + foamNoise * 3.2);
  float outerRipple = smoothstep(0.66, 0.90, waveRing)
    * (1.0 - smoothstep(0.35, 2.15, vertDepth))
    * (0.42 + 0.58 * fNoise)
    * mix(0.48, 1.0, openSea);
  float foam = clamp(smoothstep(0.30, 0.50, edgeFoam + outerRipple * 0.80), 0.0, 1.0);
  vec3 foamCol = mix(vec3(0.96, 0.99, 1.0), vec3(1.0, 0.99, 0.95), 0.45);
  col = mix(col, foamCol, foam * 0.94);

  // Seamless blend into light anime sky horizon
  float horBlend = smoothstep(460.0, 1850.0, dist);
  vec3 horTarget = mix(uFogColor * 1.06, uSkyHorizon * 1.03, 0.72);
  col = mix(col, horTarget, clamp(horBlend, 0.0, 0.98));

  // Soft shoreline alpha feather right at water's edge for clean anti-aliased contact
  float alpha = smoothstep(0.0, 0.12, depthDiff);
  gl_FragColor = vec4(col, clamp(max(alpha, foam * 0.92), 0.0, 1.0));
}
`;

export function createOcean(qualityTier) {
  const segs = qualityTier.oceanSegs || 128;
  // Unit disk-like plane [-1, 1] expanded radially in vertex shader
  const geo = new THREE.PlaneGeometry(2, 2, segs, segs);
  geo.rotateX(-Math.PI / 2);

  const uniforms = {
    tDepth: { value: null },
    uResolution: { value: new THREE.Vector2(1280, 720) },
    uCameraNear: { value: 0.5 },
    uCameraFar: { value: 3200 },
    uTime: { value: 0 },
    uSunDir: { value: SUN_DIR.clone() },
    uSunColor: { value: ATMOSPHERE.sunColor.clone() },
    uSkyZenith: { value: ATMOSPHERE.skyZenith.clone() },
    uSkyHorizon: { value: ATMOSPHERE.skyHorizon.clone() },
    uFogColor: { value: ATMOSPHERE.fogColor.clone() },
  };

  const mat = new THREE.ShaderMaterial({
    vertexShader: OCEAN_VERT,
    fragmentShader: OCEAN_FRAG,
    uniforms,
    transparent: true,
    depthWrite: true,
    depthTest: true,
  });

  const mesh = new THREE.Mesh(geo, mat);
  mesh.name = 'AnimeOcean';
  mesh.frustumCulled = false;
  mesh.renderOrder = 5;
  return { mesh, uniforms };
}
