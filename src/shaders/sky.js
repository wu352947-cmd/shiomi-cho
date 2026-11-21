import * as THREE from 'three';
import { ATMOSPHERE, SUN_DIR } from '../config.js';

const SKY_VERT = /* glsl */ `
varying vec3 vWorldDir;
void main() {
  vec4 wp = modelMatrix * vec4(position, 1.0);
  vWorldDir = wp.xyz;
  gl_Position = projectionMatrix * viewMatrix * wp;
}
`;

const SKY_FRAG = /* glsl */ `
uniform vec3 uSunDir;
uniform vec3 uZenith;
uniform vec3 uMid;
uniform vec3 uHorizon;
uniform vec3 uSunHaze;
uniform float uTime;

varying vec3 vWorldDir;

float hash21(vec2 p) {
  p = fract(p * vec2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return fract(p.x * p.y);
}

float vnoise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  f = f * f * (3.0 - 2.0 * f);
  float a = hash21(i);
  float b = hash21(i + vec2(1.0, 0.0));
  float c = hash21(i + vec2(0.0, 1.0));
  float d = hash21(i + vec2(1.0, 1.0));
  return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {
  float v = 0.0;
  float a = 0.5;
  mat2 rot = mat2(0.82, -0.57, 0.57, 0.82);
  for (int i = 0; i < 4; i++) {
    v += a * vnoise(p);
    p = rot * p * 2.04 + vec2(13.1, 7.7);
    a *= 0.5;
  }
  return v;
}

void main() {
  vec3 dir = normalize(vWorldDir);
  float h = clamp(dir.y, -0.15, 1.0);
  float hPos = max(h, 0.0);

  // Shinkai 3-stop painterly sky gradient
  vec3 col = mix(uHorizon, uMid, smoothstep(0.0, 0.34, pow(hPos, 0.82)));
  col = mix(col, uZenith, smoothstep(0.24, 0.92, hPos));

  // Crisp luminous horizon band right above the sea
  float horizonBand = exp(-abs(h) * 14.0);
  col = mix(col, vec3(0.89, 0.96, 1.0), horizonBand * 0.45);

  // Warm solar Mie haze + golden horizon bloom on sun side
  float sunDot = max(dot(dir, normalize(uSunDir)), 0.0);
  float mieWide = pow(sunDot, 5.0) * 0.28;
  float mieTight = pow(sunDot, 36.0) * 0.55;
  col += uSunHaze * (mieWide * (1.15 - 0.55 * hPos) + mieTight);

  // High-altitude anime cirrus streaks (wispy stretched veil in upper dome)
  if (hPos > 0.05) {
    vec2 skyUv = dir.xz / (hPos + 0.24);
    vec2 drift = vec2(uTime * 0.0045, uTime * 0.0018);
    // Stretch along wind axis for painterly brush-stroke cirrus
    vec2 p1 = vec2(skyUv.x * 1.15 + skyUv.y * 0.55, skyUv.y * 0.32 - skyUv.x * 0.22) * 1.35 + drift;
    float w1 = fbm(p1);
    float w2 = fbm(p1 * 2.3 + vec2(w1 * 1.4, -w1 * 0.6));
    float streak = smoothstep(0.56, 0.86, w1 * 0.55 + w2 * 0.55);
    float altFade = smoothstep(0.06, 0.22, hPos) * (1.0 - smoothstep(0.72, 0.98, hPos));
    vec3 cirrusCol = mix(vec3(0.95, 0.98, 1.0), vec3(1.0, 0.97, 0.90), pow(sunDot, 3.0));
    col = mix(col, cirrusCol, streak * altFade * 0.42);
  }

  // Sun disk + soft HDR corona (triggers subtle UnrealBloom)
  float sunDisk = smoothstep(0.9982, 0.9994, sunDot);
  float sunCorona = pow(sunDot, 220.0) * 0.95;
  col += vec3(1.55, 1.44, 1.16) * (sunDisk * 1.85 + sunCorona);

  // Below horizon softly reflects sea-sky mist
  if (h < 0.0) {
    col = mix(col, vec3(0.55, 0.78, 0.94), smoothstep(0.0, -0.14, h));
  }

  gl_FragColor = vec4(col, 1.0);
}
`;

export function createSky() {
  const geo = new THREE.SphereGeometry(2200, 32, 20);
  const uniforms = {
    uSunDir: { value: SUN_DIR.clone() },
    uZenith: { value: ATMOSPHERE.skyZenith.clone() },
    uMid: { value: ATMOSPHERE.skyMid.clone() },
    uHorizon: { value: ATMOSPHERE.skyHorizon.clone() },
    uSunHaze: { value: ATMOSPHERE.sunHaze.clone() },
    uTime: { value: 0 },
  };
  const mat = new THREE.ShaderMaterial({
    vertexShader: SKY_VERT,
    fragmentShader: SKY_FRAG,
    uniforms,
    side: THREE.BackSide,
    depthWrite: false,
    depthTest: true,
    fog: false,
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.name = 'AnimeSkyDome';
  mesh.renderOrder = -100;
  mesh.frustumCulled = false;
  return { mesh, uniforms };
}
