import * as THREE from 'three';

const GULL_VERT = /* glsl */ `
attribute vec3 aOrbit; // radiusX, radiusZ, speed
attribute vec3 aCenter; // cx, cy, cz
attribute float aPhase;

uniform float uTime;
varying float vShade;

void main() {
  float ang = uTime * aOrbit.z + aPhase;
  vec3 pos = vec3(
    aCenter.x + cos(ang) * aOrbit.x,
    aCenter.y + sin(ang * 2.0 + aPhase) * 2.4,
    aCenter.z + sin(ang) * aOrbit.y
  );
  // Tangent flight direction
  vec3 vel = normalize(vec3(
    -sin(ang) * aOrbit.x * aOrbit.z,
    0.0,
    cos(ang) * aOrbit.y * aOrbit.z
  ));
  vec3 right = normalize(cross(vel, vec3(0.0, 1.0, 0.0)));
  vec3 up = vec3(0.0, 1.0, 0.0);

  // Wing flap animation (glides periodically, then flaps)
  float flapCycle = sin(uTime * 5.8 + aPhase * 3.1);
  float glideMask = smoothstep(-0.35, 0.45, sin(uTime * 0.75 + aPhase * 2.3));
  float wingY = abs(position.x) * (flapCycle * 0.42 * glideMask + 0.14);

  vec3 local = vec3(position.x, position.y + wingY, position.z);
  vec3 worldPos = pos + right * local.x + up * local.y + vel * local.z;
  vShade = 0.86 + clamp(local.y * 0.45, -0.12, 0.16);
  gl_Position = projectionMatrix * viewMatrix * vec4(worldPos, 1.0);
}
`;

const GULL_FRAG = /* glsl */ `
varying float vShade;
void main() {
  vec3 col = vec3(0.98, 0.99, 1.0) * vShade;
  gl_FragColor = vec4(col, 1.0);
}
`;

const PETAL_VERT = /* glsl */ `
attribute vec3 aOrigin;
attribute vec3 aParams; // phase, driftSpeed, size

uniform float uTime;
varying float vAlpha;
varying vec2 vUv;

void main() {
  vUv = uv;
  float t = uTime * aParams.y + aParams.x;
  vec3 center = aOrigin;
  center.x += mod(t * 2.1, 64.0) - 32.0 + sin(t * 1.4) * 2.0;
  center.y -= mod(t * 0.95, 18.0);
  if (center.y < 3.5) center.y += 18.0;
  center.z += cos(t * 1.1 + aParams.x) * 2.4;

  // Tumbling petal rotation
  float rx = t * 2.1;
  float ry = t * 1.7 + aParams.x;
  vec3 p = position * aParams.z;
  float cx = cos(rx), sx = sin(rx);
  float cy = cos(ry), sy = sin(ry);
  p = vec3(p.x, p.y * cx - p.z * sx, p.y * sx + p.z * cx);
  p = vec3(p.x * cy + p.z * sy, p.y, -p.x * sy + p.z * cy);

  vec3 worldPos = center + p;
  float dist = length(cameraPosition - worldPos);
  // Fade out when very close to lens or far away
  float nearFade = smoothstep(5.0, 14.0, dist);
  float farFade = 1.0 - smoothstep(95.0, 210.0, dist);
  vAlpha = nearFade * farFade * 0.88;
  gl_Position = projectionMatrix * viewMatrix * vec4(worldPos, 1.0);
}
`;

const PETAL_FRAG = /* glsl */ `
varying float vAlpha;
varying vec2 vUv;

void main() {
  // Delicate notched sakura petal silhouette
  vec2 p = vUv * 2.0 - 1.0;
  p.x *= 1.15;
  float r = length(p - vec2(0.0, -0.05));
  float notch = smoothstep(0.0, 0.35, abs(p.x)) * 0.18;
  float shape = 1.0 - smoothstep(0.62 - notch, 0.86 - notch, r);
  float a = shape * vAlpha;
  if (a < 0.05) discard;
  vec3 col = mix(vec3(0.99, 0.66, 0.77), vec3(1.0, 0.88, 0.92), clamp(vUv.y, 0.0, 1.0));
  gl_FragColor = vec4(col, a);
}
`;

function createSeagulls(count) {
  // Crisp stylized V-wing gull mesh (4 triangles)
  const verts = new Float32Array([
    0, 0, 0.48,     -1.25, 0.12, -0.18,   0, 0, -0.25,
    0, 0, 0.48,      0, 0, -0.25,          1.25, 0.12, -0.18,
    -1.25, 0.12, -0.18,  -1.85, -0.04, -0.45,  -0.55, 0.05, -0.26,
    1.25, 0.12, -0.18,   0.55, 0.05, -0.26,   1.85, -0.04, -0.45,
  ]);
  const baseGeo = new THREE.BufferGeometry();
  baseGeo.setAttribute('position', new THREE.BufferAttribute(verts, 3));

  const instGeo = new THREE.InstancedBufferGeometry();
  instGeo.attributes.position = baseGeo.attributes.position;

  const orbits = new Float32Array(count * 3);
  const centers = new Float32Array(count * 3);
  const phases = new Float32Array(count);

  for (let i = 0; i < count; i++) {
    const f = i / Math.max(1, count);
    orbits[i * 3 + 0] = 28 + (i % 4) * 16;
    orbits[i * 3 + 1] = 22 + ((i + 1) % 3) * 15;
    orbits[i * 3 + 2] = (i % 2 === 0 ? 1 : -1) * (0.24 + (i % 3) * 0.05);
    centers[i * 3 + 0] = -25 + f * 95;
    centers[i * 3 + 1] = 20 + (i % 4) * 7.5;
    centers[i * 3 + 2] = 35 + ((i * 29) % 55);
    phases[i] = i * 1.47;
  }

  instGeo.setAttribute('aOrbit', new THREE.InstancedBufferAttribute(orbits, 3));
  instGeo.setAttribute('aCenter', new THREE.InstancedBufferAttribute(centers, 3));
  instGeo.setAttribute('aPhase', new THREE.InstancedBufferAttribute(phases, 1));
  instGeo.instanceCount = count;

  const uniforms = { uTime: { value: 0 } };
  const mat = new THREE.ShaderMaterial({
    vertexShader: GULL_VERT,
    fragmentShader: GULL_FRAG,
    uniforms,
    side: THREE.DoubleSide,
  });
  const mesh = new THREE.Mesh(instGeo, mat);
  mesh.name = 'AnimeSeagulls';
  mesh.frustumCulled = false;
  return { mesh, uniforms };
}

function createSakuraPetals(count) {
  if (count <= 0) return null;
  const baseGeo = new THREE.PlaneGeometry(0.24, 0.20);
  const instGeo = new THREE.InstancedBufferGeometry();
  instGeo.index = baseGeo.index;
  instGeo.attributes.position = baseGeo.attributes.position;
  instGeo.attributes.uv = baseGeo.attributes.uv;

  const origins = new Float32Array(count * 3);
  const params = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    const s1 = Math.sin(i * 12.9898) * 43758.5453;
    const s2 = Math.sin(i * 78.233) * 19341.234;
    const s3 = Math.sin(i * 39.425) * 61234.123;
    const r1 = s1 - Math.floor(s1);
    const r2 = s2 - Math.floor(s2);
    const r3 = s3 - Math.floor(s3);
    // Concentrate petals near the hillside town & shrine sakura groves
    const nearShrine = i % 3 === 0;
    origins[i * 3 + 0] = nearShrine ? -48 + r1 * 38 : -68 + r1 * 130;
    origins[i * 3 + 1] = nearShrine ? 48 + r2 * 24 : 10 + r2 * 30;
    origins[i * 3 + 2] = nearShrine ? -155 + r3 * 36 : -45 + r3 * 45;
    params[i * 3 + 0] = r1 * 40.0;
    params[i * 3 + 1] = 0.55 + r2 * 0.55;
    params[i * 3 + 2] = 0.75 + r3 * 0.75;
  }

  instGeo.setAttribute('aOrigin', new THREE.InstancedBufferAttribute(origins, 3));
  instGeo.setAttribute('aParams', new THREE.InstancedBufferAttribute(params, 3));
  instGeo.instanceCount = count;

  const uniforms = { uTime: { value: 0 } };
  const mat = new THREE.ShaderMaterial({
    vertexShader: PETAL_VERT,
    fragmentShader: PETAL_FRAG,
    uniforms,
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
  });
  const mesh = new THREE.Mesh(instGeo, mat);
  mesh.name = 'AnimeSakuraPetals';
  mesh.frustumCulled = false;
  baseGeo.dispose();
  return { mesh, uniforms };
}

function createBeaconGlow() {
  const c = document.createElement('canvas');
  c.width = 128;
  c.height = 128;
  const ctx = c.getContext('2d');
  const g = ctx.createRadialGradient(64, 64, 2, 64, 64, 62);
  g.addColorStop(0.0, 'rgba(255, 250, 224, 1.0)');
  g.addColorStop(0.28, 'rgba(255, 234, 170, 0.62)');
  g.addColorStop(0.65, 'rgba(255, 206, 130, 0.16)');
  g.addColorStop(1.0, 'rgba(255, 206, 130, 0.0)');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, 128, 128);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  const mat = new THREE.SpriteMaterial({
    map: tex,
    color: new THREE.Color('#FFF3C4'),
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    opacity: 0.72,
  });
  const sprite = new THREE.Sprite(mat);
  sprite.name = 'LighthouseBeaconFlare';
  sprite.scale.set(6.5, 6.5, 1);
  sprite.position.set(58, 13.5, 98);
  return sprite;
}

export function createAtmosphere(scene, qualityTier) {
  const gulls = createSeagulls(qualityTier.seagullCount || 7);
  scene.add(gulls.mesh);

  const petals = createSakuraPetals(qualityTier.petalCount || 0);
  if (petals) scene.add(petals.mesh);

  const beacon = createBeaconGlow();
  scene.add(beacon);

  const boats = [];
  const trams = [];
  const tmpBox = new THREE.Box3();
  const tmpCenter = new THREE.Vector3();

  function attachModelObjects(meta) {
    boats.length = 0;
    for (const obj of meta.boats) {
      boats.push({
        obj,
        baseY: obj.position.y,
        baseRx: obj.rotation.x,
        baseRz: obj.rotation.z,
        phase: obj.position.x * 0.17 + obj.position.z * 0.13,
      });
    }
    trams.length = 0;
    for (const obj of meta.trams || []) {
      trams.push({ obj, baseX: obj.position.x });
    }
    if (meta.lighthouseLamp) {
      meta.lighthouseLamp.updateWorldMatrix(true, false);
      tmpBox.setFromObject(meta.lighthouseLamp);
      tmpBox.getCenter(tmpCenter);
      if (isFinite(tmpCenter.x)) {
        beacon.position.copy(tmpCenter);
      }
    }
  }

  function update(elapsed) {
    gulls.uniforms.uTime.value = elapsed;
    if (petals) petals.uniforms.uTime.value = elapsed;

    // Gentle lighthouse lamp pulse
    const pulse = 0.62 + 0.38 * (0.5 + 0.5 * Math.sin(elapsed * 2.2));
    const s = 5.4 + pulse * 2.6;
    beacon.scale.set(s, s, 1);
    beacon.material.opacity = 0.45 + pulse * 0.4;

    // Harbor boat bobbing & rolling
    for (let i = 0; i < boats.length; i++) {
      const b = boats[i];
      const p = b.phase;
      b.obj.position.y = b.baseY + Math.sin(elapsed * 1.45 + p) * 0.13 + Math.cos(elapsed * 2.1 + p * 1.3) * 0.05;
      b.obj.rotation.x = b.baseRx + Math.sin(elapsed * 1.15 + p * 0.8) * 0.028;
      b.obj.rotation.z = b.baseRz + Math.cos(elapsed * 1.35 + p * 1.2) * 0.036;
    }

    // Slow seaside tram along railway if tram geometry exists
    for (let i = 0; i < trams.length; i++) {
      const tr = trams[i];
      tr.obj.position.x = ((elapsed * 6.5 + tr.baseX + 110) % 220) - 110;
    }
  }

  return { attachModelObjects, update };
}
