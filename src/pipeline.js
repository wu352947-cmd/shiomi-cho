import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { ShaderPass } from 'three/addons/postprocessing/ShaderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { FXAAShader } from 'three/addons/shaders/FXAAShader.js';
import { OutlineShader } from './shaders/outline.js';
import { GradeShader } from './shaders/grade.js';

export function createPipeline(renderer, scene, camera, qualityTier, hooks = {}) {
  const size = new THREE.Vector2();
  renderer.getDrawingBufferSize(size);
  const w = Math.max(1, size.x);
  const h = Math.max(1, size.y);

  // Shared solid-world prepass target: RGB = view normal, A = outline mask, DepthTexture = solid depth
  const depthTexture = new THREE.DepthTexture(w, h);
  depthTexture.format = THREE.DepthFormat;
  depthTexture.type = THREE.UnsignedIntType;
  depthTexture.minFilter = THREE.NearestFilter;
  depthTexture.magFilter = THREE.NearestFilter;

  const normalDepthRT = new THREE.WebGLRenderTarget(w, h, {
    minFilter: THREE.LinearFilter,
    magFilter: THREE.LinearFilter,
    format: THREE.RGBAFormat,
    type: THREE.UnsignedByteType,
    depthBuffer: true,
    depthTexture,
  });

  // HDR composer buffer (HalfFloatType so bloom sees true >1.0 glints & emissives)
  const composerRT = new THREE.WebGLRenderTarget(w, h, {
    minFilter: THREE.LinearFilter,
    magFilter: THREE.LinearFilter,
    format: THREE.RGBAFormat,
    type: THREE.HalfFloatType,
    depthBuffer: true,
  });

  const composer = new EffectComposer(renderer, composerRT);
  composer.setPixelRatio(renderer.getPixelRatio());
  composer.setSize(window.innerWidth, window.innerHeight);

  // 1. Main scene pass
  const renderPass = new RenderPass(scene, camera);
  composer.addPass(renderPass);

  // 2. Screen-space depth + normal Sobel outline pass
  const outlinePass = new ShaderPass(OutlineShader);
  outlinePass.enabled = qualityTier.useOutline !== false;
  outlinePass.uniforms.tNormalMask.value = normalDepthRT.texture;
  outlinePass.uniforms.tDepth.value = depthTexture;
  outlinePass.uniforms.uResolution.value.set(w, h);
  outlinePass.uniforms.uCameraNear.value = camera.near;
  outlinePass.uniforms.uCameraFar.value = camera.far;
  composer.addPass(outlinePass);

  // 3. Subtle HDR bloom pass (sun glints, sea sparkles, lamps)
  const bloomScale = qualityTier.bloomScale || 0.5;
  const bloomPass = new UnrealBloomPass(
    new THREE.Vector2(Math.max(1, Math.floor(w * bloomScale)), Math.max(1, Math.floor(h * bloomScale))),
    0.26, // subtle strength
    0.58, // soft dreamy radius
    0.94  // threshold: only HDR glints/corona/lamps
  );
  composer.addPass(bloomPass);

  // 4. Filmic ACES tonemapping + summer warm/teal grade + soft vignette + sRGB encode
  const gradePass = new ShaderPass(GradeShader);
  composer.addPass(gradePass);

  // 5. FXAA anti-aliasing (operates on sRGB output)
  const fxaaPass = new ShaderPass(FXAAShader);
  fxaaPass.enabled = qualityTier.useFXAA !== false;
  fxaaPass.uniforms.resolution.value.set(1 / w, 1 / h);
  composer.addPass(fxaaPass);

  let solidMeshes = [];
  const skipObjects = hooks.skipInPrepass || [];
  const oceanUniforms = hooks.oceanUniforms || null;
  if (oceanUniforms) {
    oceanUniforms.tDepth.value = depthTexture;
    oceanUniforms.uResolution.value.set(w, h);
    oceanUniforms.uCameraNear.value = camera.near;
    oceanUniforms.uCameraFar.value = camera.far;
  }

  const prevClearColor = new THREE.Color();
  const clearNormalColor = new THREE.Color(0.5, 0.5, 1.0);

  function setSolidMeshes(list) {
    solidMeshes = list || [];
  }

  function resize(cssW, cssH, dpr) {
    renderer.setPixelRatio(dpr);
    renderer.setSize(cssW, cssH, false);
    const pw = Math.max(1, Math.floor(cssW * dpr));
    const ph = Math.max(1, Math.floor(cssH * dpr));

    normalDepthRT.setSize(pw, ph);
    composer.setPixelRatio(dpr);
    composer.setSize(cssW, cssH);

    outlinePass.uniforms.uResolution.value.set(pw, ph);
    fxaaPass.uniforms.resolution.value.set(1 / pw, 1 / ph);
    bloomPass.resolution.set(
      Math.max(1, Math.floor(pw * bloomScale)),
      Math.max(1, Math.floor(ph * bloomScale))
    );
    if (oceanUniforms) {
      oceanUniforms.uResolution.value.set(pw, ph);
    }
  }

  function render() {
    // --- Prepass: solid world view-normals + outline mask + exact depth ---
    const prevAutoClear = renderer.autoClear;
    const prevShadowEnabled = renderer.shadowMap.enabled;
    const prevClearAlpha = renderer.getClearAlpha();
    renderer.getClearColor(prevClearColor);

    const prevVis = [];
    for (let i = 0; i < skipObjects.length; i++) {
      prevVis[i] = skipObjects[i].visible;
      skipObjects[i].visible = false;
    }
    for (let i = 0; i < solidMeshes.length; i++) {
      const m = solidMeshes[i];
      if (m.userData.normalMaskMaterial) {
        m.material = m.userData.normalMaskMaterial;
      }
    }

    renderer.shadowMap.enabled = false;
    renderer.setRenderTarget(normalDepthRT);
    renderer.setClearColor(clearNormalColor, 0.0);
    renderer.clear(true, true, false);
    renderer.render(scene, camera);
    renderer.setRenderTarget(null);

    // Restore materials, shadow map, clear state, and non-solid visuals
    for (let i = 0; i < solidMeshes.length; i++) {
      const m = solidMeshes[i];
      if (m.userData.toonMaterial) {
        m.material = m.userData.toonMaterial;
      }
    }
    for (let i = 0; i < skipObjects.length; i++) {
      skipObjects[i].visible = prevVis[i];
    }
    renderer.setClearColor(prevClearColor, prevClearAlpha);
    renderer.shadowMap.enabled = prevShadowEnabled;
    renderer.autoClear = prevAutoClear;

    // Update outline camera uniforms (zero allocations)
    outlinePass.uniforms.uCamPos.value.copy(camera.position);
    outlinePass.uniforms.uInvProj.value.copy(camera.projectionMatrixInverse);
    outlinePass.uniforms.uCamWorld.value.copy(camera.matrixWorld);
    outlinePass.uniforms.uCameraNear.value = camera.near;
    outlinePass.uniforms.uCameraFar.value = camera.far;

    // --- Main HDR Composer: Render -> Outline -> Bloom -> Grade -> FXAA ---
    composer.render();
  }

  return {
    setSolidMeshes,
    resize,
    render,
    passes: { renderPass, outlinePass, bloomPass, gradePass, fxaaPass },
  };
}
