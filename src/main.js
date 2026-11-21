import * as THREE from 'three';
import { ATMOSPHERE, QUALITY_TIERS, SUN_DIR, parseParams } from './config.js';
import { createMaterialSystem } from './materials.js';
import { createSky } from './shaders/sky.js';
import { createClouds } from './clouds.js';
import { createOcean } from './shaders/ocean.js';
import { createAtmosphere } from './atmosphere.js';
import { loadTownModel } from './loader.js';
import { createPipeline } from './pipeline.js';
import { createCameraController } from './camera.js';
import { createUI } from './ui.js';

window.__READY = false;

async function init() {
  const params = parseParams();
  const tier = QUALITY_TIERS[params.quality] || QUALITY_TIERS.high;
  const wrap = document.getElementById('canvas-wrap');

  const renderer = new THREE.WebGLRenderer({
    antialias: false,
    powerPreference: 'high-performance',
    stencil: false,
  });
  const getDpr = () => Math.min(window.devicePixelRatio || 1, tier.maxDpr);
  renderer.setPixelRatio(getDpr());
  renderer.setSize(window.innerWidth, window.innerHeight, false);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.NoToneMapping;
  renderer.info.autoReset = false;
  wrap.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = ATMOSPHERE.skyHorizon.clone();

  const camera = new THREE.PerspectiveCamera(42, window.innerWidth / window.innerHeight, 0.5, 3200);
  const cameraCtrl = createCameraController(camera, renderer.domElement, { auto: params.auto });
  const ui = createUI(cameraCtrl, { ui: params.ui });
  cameraCtrl.setCam(params.cam, true);

  // Single warm directional sunlight with tightly fitted soft PCF frustum
  const sunLight = new THREE.DirectionalLight(ATMOSPHERE.sunColor, 1.0);
  const shadowTarget = new THREE.Object3D();
  shadowTarget.position.set(0, 12, -26);
  scene.add(shadowTarget);
  sunLight.target = shadowTarget;
  sunLight.position.copy(shadowTarget.position).addScaledVector(SUN_DIR, 265);
  sunLight.castShadow = true;
  sunLight.shadow.mapSize.set(tier.shadowMapSize, tier.shadowMapSize);
  sunLight.shadow.camera.left = -170;
  sunLight.shadow.camera.right = 175;
  sunLight.shadow.camera.top = 165;
  sunLight.shadow.camera.bottom = -145;
  sunLight.shadow.camera.near = 35;
  sunLight.shadow.camera.far = 540;
  sunLight.shadow.bias = -0.00045;
  sunLight.shadow.normalBias = 0.085;
  scene.add(sunLight);

  // Non-solid environmental layer (hidden during solid-world normal/depth prepass)
  const envGroup = new THREE.Group();
  envGroup.name = 'EnvVisuals';
  scene.add(envGroup);

  const sky = createSky();
  envGroup.add(sky.mesh);

  const clouds = createClouds(tier);
  envGroup.add(clouds.mesh);

  const ocean = createOcean(tier);
  envGroup.add(ocean.mesh);

  const atmosphere = createAtmosphere(envGroup, tier);
  const materialSystem = createMaterialSystem();

  const pipeline = createPipeline(renderer, scene, camera, tier, {
    skipInPrepass: [envGroup],
    oceanUniforms: ocean.uniforms,
  });

  // Expose camera helper early so scripts can switch view cleanly
  window.__setCam = (name, instant = true) => {
    cameraCtrl.setCam(name, instant);
  };

  let modelMeta = null;
  let lastCalls = 0;
  let lastTris = 0;
  let fpsAvg = 60;

  window.__INFO = () => ({
    tris: modelMeta ? modelMeta.totalTris : lastTris,
    renderTris: lastTris,
    calls: lastCalls,
    fps: Math.round(fpsAvg * 10) / 10,
    quality: tier.name,
    model: modelMeta ? modelMeta.url : '',
  });

  // Handle viewport resize cleanly
  const onResize = () => {
    const w = window.innerWidth;
    const h = window.innerHeight;
    camera.aspect = w / Math.max(1, h);
    camera.updateProjectionMatrix();
    pipeline.resize(w, h, getDpr());
  };
  window.addEventListener('resize', onResize);

  // Load town.glb (or fallback stub.glb)
  ui.setProgress(0.08, '町並みを読み込み中…');
  try {
    modelMeta = await loadTownModel(
      materialSystem,
      (frac) => ui.setProgress(0.08 + frac * 0.86),
      params.model
    );
    scene.add(modelMeta.root);
    pipeline.setSolidMeshes(modelMeta.solidMeshes);
    atmosphere.attachModelObjects(modelMeta);
    ui.setProgress(1.0, '汐見町へようこそ');
  } catch (err) {
    console.error('Model load failed:', err);
    ui.setProgress(1.0, 'モデルの読み込みに失敗しました');
  }

  let prevTime = performance.now();
  let startTime = prevTime;
  let firstFrameDone = false;

  function tick(now) {
    requestAnimationFrame(tick);
    const dt = Math.min(0.1, Math.max(0.001, (now - prevTime) / 1000));
    prevTime = now;
    const elapsed = (now - startTime) / 1000;
    fpsAvg = fpsAvg * 0.9 + (1 / dt) * 0.1;

    sky.uniforms.uTime.value = elapsed;
    clouds.uniforms.uTime.value = elapsed;
    ocean.uniforms.uTime.value = elapsed;
    materialSystem.update(elapsed);
    atmosphere.update(elapsed);
    cameraCtrl.update(dt);

    renderer.info.reset();
    pipeline.render();
    lastCalls = renderer.info.render.calls;
    lastTris = renderer.info.render.triangles;

    if (!firstFrameDone) {
      firstFrameDone = true;
      ui.hideLoader();
      window.__READY = true;
    }
  }

  requestAnimationFrame(tick);
}

init();
