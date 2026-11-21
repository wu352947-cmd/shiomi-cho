import * as THREE from 'three';

const ANIM_CHUNK = /* glsl */ `
vec3 applyAnimeMotion(vec3 pos, vec3 worldBase, float time, float mode) {
  if (mode < 0.5) return pos;
  vec3 p = pos;
  if (mode < 1.5) {
    // anim_tree_*: gentle summer breeze sway anchored toward base
    float phase = worldBase.x * 0.23 + worldBase.z * 0.19;
    float h = max(0.0, pos.y * 0.22);
    float gust = sin(time * 1.45 + phase) + 0.45 * sin(time * 2.7 + phase * 1.7 + pos.x * 0.8);
    float bend = clamp(h, 0.0, 1.4) * 0.16;
    p.x += gust * bend;
    p.z += cos(time * 1.2 + phase * 1.3) * bend * 0.65;
  } else {
    // anim_flag_*: noren / banner / laundry cloth flutter
    float phase = worldBase.x * 0.7 + worldBase.z * 0.5;
    float w = sin(time * 3.6 + phase + pos.x * 1.9 + pos.y * 1.6);
    float w2 = cos(time * 5.2 + phase * 1.4 + pos.y * 2.5);
    float weight = clamp(1.0 - smoothstep(0.0, 1.5, pos.y), 0.18, 1.0);
    p.z += (w * 0.09 + w2 * 0.035) * weight;
    p.x += w2 * 0.03 * weight;
  }
  return p;
}
`;

export const TOON_VERT = /* glsl */ `
#include <common>
#include <shadowmap_pars_vertex>

uniform float uTime;
uniform float uAnimMode;

varying vec3 vWorldPos;
varying vec3 vWorldNormal;
varying vec2 vUv;
varying float vAO;

${ANIM_CHUNK}

void main() {
  vUv = uv;
  #if defined(USE_COLOR_ALPHA)
    vAO = clamp(color.r * 0.3 + color.g * 0.59 + color.b * 0.11, 0.25, 1.0);
  #elif defined(USE_COLOR)
    vAO = clamp(color.r * 0.3 + color.g * 0.59 + color.b * 0.11, 0.25, 1.0);
  #else
    vAO = 1.0;
  #endif

  vec3 objectNormal = normalize(normal);
  vec3 worldBase = (modelMatrix * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
  vec3 transformed = applyAnimeMotion(position, worldBase, uTime, uAnimMode);

  vec4 worldPosition = modelMatrix * vec4(transformed, 1.0);
  vWorldPos = worldPosition.xyz;
  vWorldNormal = normalize(mat3(modelMatrix) * objectNormal);
  vec3 transformedNormal = normalize(normalMatrix * objectNormal);

  #include <shadowmap_vertex>
  gl_Position = projectionMatrix * viewMatrix * worldPosition;
}
`;

export const TOON_FRAG = /* glsl */ `
#include <common>
#include <packing>
#include <lights_pars_begin>
#include <shadowmap_pars_fragment>
#include <shadowmask_pars_fragment>

uniform vec3 uBaseColor;
uniform vec3 uSunDir;
uniform vec3 uSunColor;
uniform vec3 uShadowTint;
uniform vec3 uSkyFill;
uniform vec3 uSkyZenith;
uniform vec3 uSkyHorizon;
uniform vec3 uFogColor;
uniform float uFogNear;
uniform float uFogFar;
uniform float uSpecStrength;
uniform float uShininess;
uniform float uRimStrength;
uniform float uMatType; // 0=std, 1=glass, 2=foliage, 3=emissive, 4=wet, 5=shoji, 6=wire
uniform float uHasMap;
uniform sampler2D uMap;

varying vec3 vWorldPos;
varying vec3 vWorldNormal;
varying vec2 vUv;
varying float vAO;

void main() {
  vec3 N = normalize(vWorldNormal);
  vec3 V = normalize(cameraPosition - vWorldPos);
  vec3 L = normalize(uSunDir);

  vec3 baseCol = uBaseColor;
  if (uHasMap > 0.5) {
    vec4 tex = texture2D(uMap, vUv);
    baseCol = mix(baseCol, tex.rgb, tex.a);
  }

  // Real-time directional shadow map (soft PCF)
  float shadow = getShadowMask();

  // Emissive lamps (warm HDR for subtle bloom)
  if (uMatType > 2.5 && uMatType < 3.5) {
    vec3 glow = baseCol * 1.65;
    float distE = length(cameraPosition - vWorldPos);
    float fogE = smoothstep(uFogNear * 1.4, uFogFar * 1.3, distE) * 0.65;
    gl_FragColor = vec4(mix(glow, uFogColor, fogE), 1.0);
    return;
  }

  // Slight normal softness on foliage so clustered trees feel lush & painterly
  float ndlRaw = dot(N, L);
  float ndl = (uMatType > 1.5 && uMatType < 2.5)
    ? clamp(ndlRaw * 0.72 + 0.30, -1.0, 1.0)
    : ndlRaw;

  // Power lines: crisp dark indigo against bright sky
  if (uMatType > 5.5 && uMatType < 6.5) {
    vec3 wireCol = mix(vec3(0.14, 0.18, 0.28), uFogColor, smoothstep(80.0, 320.0, length(cameraPosition - vWorldPos)) * 0.7);
    gl_FragColor = vec4(wireCol, 1.0);
    return;
  }

  // Real-time directional shadow cleanly drops sunlit surfaces into cool blue-violet shadow band
  float shadowBand = mix(-0.34, 1.0, shadow);
  float litSignal = min(ndl, shadowBand);
  float ao = mix(0.48, 1.0, vAO);

  // 3-band cel shading with soft 1-2px screen-space transition
  float fw = clamp(fwidth(litSignal) * 1.15, 0.022, 0.075);
  float bandMid = smoothstep(-0.08 - fw, -0.08 + fw, litSignal);
  float bandLit = smoothstep(0.24 - fw, 0.24 + fw, litSignal);

  // Cool blue-violet shadow tint (never black) -> soft sky-lit mid -> warm golden sunlit key
  vec3 shadowTint = mix(vec3(0.35, 0.44, 0.74), uShadowTint * 1.02, 0.65);
  vec3 shadowCol = baseCol * shadowTint + vec3(0.032, 0.052, 0.125) * (1.0 - baseCol * 0.35);
  vec3 midCol = baseCol * mix(uSkyFill * 0.92, uSunColor, 0.44) * 0.89;
  vec3 litCol = baseCol * mix(vec3(1.0), uSunColor * 1.16, 0.86);

  vec3 col = mix(shadowCol, midCol, bandMid);
  col = mix(col, litCol, bandLit);

  // Hemisphere sky fill & subtle warm ground bounce
  float skyUp = N.y * 0.5 + 0.5;
  vec3 hemiFill = mix(vec3(0.95, 0.86, 0.74) * 0.07, uSkyFill * 0.13, skyUp);
  col += baseCol * hemiFill;

  // Foliage warm translucent glow when backlit by summer sun
  if (uMatType > 1.5 && uMatType < 2.5) {
    float sss = pow(clamp(dot(V, -L), 0.0, 1.0), 3.0) * 0.26;
    col += baseCol * uSunColor * sss * (0.4 + 0.6 * shadow);
  }

  // Shoji gentle warm backlit paper feel
  if (uMatType > 4.5 && uMatType < 5.5) {
    col += vec3(0.14, 0.10, 0.05);
  }

  // Stylized specular on roofs, boats, metal, glass, wet coastal stone/concrete
  float specMul = uSpecStrength;
  if (uMatType > 3.5 && uMatType < 4.5) {
    float wetZone = 1.0 - smoothstep(0.05, 2.3, vWorldPos.y);
    specMul += wetZone * 0.36;
    col *= mix(1.0, 0.84, wetZone * 0.55);
  }
  if (specMul > 0.01) {
    vec3 H = normalize(L + V);
    float ndh = max(dot(N, H), 0.0);
    float sp = pow(ndh, uShininess);
    float celSpec = smoothstep(0.26, 0.48, sp) * 0.78 + sp * 0.32;
    col += uSunColor * celSpec * specMul * (0.12 + 0.88 * shadow);
  }

  // Window glass: vivid anime sky gradient reflection + crisp sun glint
  if (uMatType > 0.5 && uMatType < 1.5) {
    vec3 R = reflect(-V, N);
    float rUp = clamp(R.y * 0.5 + 0.5, 0.0, 1.0);
    vec3 skyRefl = mix(uSkyHorizon * 1.05, uSkyZenith * 1.25, pow(rUp, 0.68));
    float band = smoothstep(0.46, 0.60, rUp) * (1.0 - smoothstep(0.60, 0.76, rUp));
    skyRefl = mix(skyRefl, vec3(1.0, 0.99, 0.95), band * 0.45);
    float fres = pow(1.0 - max(dot(N, V), 0.0), 2.0);
    col = mix(col * 0.55, skyRefl, clamp(0.52 + fres * 0.42, 0.0, 0.94));
    float sunGlint = smoothstep(0.95, 0.99, dot(R, L));
    col += uSunColor * sunGlint * 1.25;
  }

  // Thin sky-tinted rim light on silhouettes
  if (uRimStrength > 0.01) {
    float fres = pow(1.0 - max(dot(N, V), 0.0), 3.0);
    float rimMask = smoothstep(0.28, 0.74, fres) * (0.35 + 0.65 * clamp(N.y * 0.5 + 0.6, 0.0, 1.0));
    vec3 rimTint = mix(uSkyFill * 1.18, uSunColor * 1.20, smoothstep(-0.1, 0.6, ndl));
    col += rimTint * rimMask * uRimStrength * 0.42;
  }

  // Multiply vertex AO with cool blue-violet crevice tint (never murky black)
  vec3 aoTint = mix(uShadowTint * 0.68 + vec3(0.20), vec3(1.0), ao);
  col *= aoTint;

  // Layered atmospheric distance perspective: near forested blue-green ridges -> mid cerulean -> far sky mist
  float dist = length(cameraPosition - vWorldPos);
  float heightEase = 1.0 - clamp(vWorldPos.y / 320.0, 0.0, 0.34);
  float nearFog = smoothstep(uFogNear, uFogFar, dist) * heightEase;
  // Separate 3 mountain distance bands (~450m near, ~680m mid, ~900m+ far)
  float layerNear = smoothstep(320.0, 560.0, dist);
  float layerMid  = smoothstep(560.0, 790.0, dist);
  float layerFar  = smoothstep(790.0, 1080.0, dist);

  // Subtle sunlit ridgeline tint so near/mid mountains keep crisp layered silhouettes
  float ridgeLit = smoothstep(-0.15, 0.55, ndlRaw);
  vec3 nearTint = mix(vec3(0.24, 0.48, 0.56), vec3(0.36, 0.62, 0.66), ridgeLit);
  vec3 midTint  = mix(vec3(0.38, 0.57, 0.79), vec3(0.50, 0.69, 0.88), ridgeLit);
  vec3 farTint  = mix(uFogColor * 1.06, uSkyHorizon * 1.02, 0.52);

  vec3 fogTarget = mix(uFogColor, nearTint, layerNear * (1.0 - layerMid));
  fogTarget = mix(fogTarget, midTint, layerMid * (1.0 - layerFar * 0.75));
  fogTarget = mix(fogTarget, farTint, layerFar);

  float fogMix = clamp(max(nearFog * 0.58, layerNear * 0.56 + layerMid * 0.24 + layerFar * 0.14), 0.0, 0.90);
  // Keep horizon haze bright & airy right along low distant bases
  float baseMist = smoothstep(360.0, 820.0, dist) * (1.0 - smoothstep(0.0, 68.0, vWorldPos.y));
  col = mix(col, fogTarget, fogMix);
  col = mix(col, uSkyHorizon * 1.03, baseMist * 0.34);

  gl_FragColor = vec4(col, 1.0);
}
`;

export const NORMAL_MASK_VERT = /* glsl */ `
uniform float uTime;
uniform float uAnimMode;

varying vec3 vViewNormal;

${ANIM_CHUNK}

void main() {
  vec3 worldBase = (modelMatrix * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
  vec3 transformed = applyAnimeMotion(position, worldBase, uTime, uAnimMode);
  vViewNormal = normalize(normalMatrix * normal);
  gl_Position = projectionMatrix * modelViewMatrix * vec4(transformed, 1.0);
}
`;

export const NORMAL_MASK_FRAG = /* glsl */ `
uniform float uOutlineWeight;
varying vec3 vViewNormal;

void main() {
  vec3 n = normalize(vViewNormal) * 0.5 + 0.5;
  gl_FragColor = vec4(n, uOutlineWeight);
}
`;
