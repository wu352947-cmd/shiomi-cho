import * as THREE from 'three';

export const OutlineShader = {
  uniforms: {
    tDiffuse: { value: null },
    tNormalMask: { value: null },
    tDepth: { value: null },
    uResolution: { value: new THREE.Vector2(1280, 720) },
    uCameraNear: { value: 0.5 },
    uCameraFar: { value: 3200.0 },
    uCamPos: { value: new THREE.Vector3() },
    uInvProj: { value: new THREE.Matrix4() },
    uCamWorld: { value: new THREE.Matrix4() },
    uOutlineTint: { value: new THREE.Color('#2B395B') },
    uThickness: { value: 1.05 },
    uStrength: { value: 0.62 },
  },

  vertexShader: /* glsl */ `
    varying vec2 vUv;
    void main() {
      vUv = uv;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,

  fragmentShader: /* glsl */ `
    #include <packing>

    uniform sampler2D tDiffuse;
    uniform sampler2D tNormalMask;
    uniform sampler2D tDepth;
    uniform vec2 uResolution;
    uniform float uCameraNear;
    uniform float uCameraFar;
    uniform vec3 uCamPos;
    uniform mat4 uInvProj;
    uniform mat4 uCamWorld;
    uniform vec3 uOutlineTint;
    uniform float uThickness;
    uniform float uStrength;

    varying vec2 vUv;

    float getViewDist(vec2 uv) {
      float z = texture2D(tDepth, uv).x;
      if (z >= 0.9995) return uCameraFar;
      return -perspectiveDepthToViewZ(z, uCameraNear, uCameraFar);
    }

    vec4 getNM(vec2 uv) {
      vec4 nm = texture2D(tNormalMask, uv);
      nm.xyz = nm.xyz * 2.0 - 1.0;
      return nm;
    }

    void main() {
      vec4 sceneCol = texture2D(tDiffuse, vUv);
      float rawZ = texture2D(tDepth, vUv).x;

      // Skip sky pixels
      if (rawZ >= 0.9995) {
        gl_FragColor = sceneCol;
        return;
      }

      // Compute exact ray to detect if ocean plane (y = 0) occludes seabed here
      vec4 clip = vec4(vUv * 2.0 - 1.0, -1.0, 1.0);
      vec4 viewP = uInvProj * clip;
      vec3 viewDir = normalize(viewP.xyz / viewP.w);
      vec3 worldDir = normalize((uCamWorld * vec4(viewDir, 0.0)).xyz);

      float centerViewZ = getViewDist(vUv);
      float solidRayDist = centerViewZ / max(0.001, -viewDir.z);

      if (worldDir.y < -0.0005 && uCamPos.y > 0.0) {
        float tOcean = -uCamPos.y / worldDir.y;
        // Skip ocean pixels cleanly (allow small tolerance so boat/pier waterline edges stay crisp)
        if (tOcean > 0.0 && tOcean < solidRayDist - 0.18) {
          gl_FragColor = sceneCol;
          return;
        }
      }

      vec2 texel = (uThickness / uResolution);
      // 3x3 Sobel taps
      vec2 oTL = vUv + vec2(-texel.x,  texel.y);
      vec2 oT  = vUv + vec2( 0.0,      texel.y);
      vec2 oTR = vUv + vec2( texel.x,  texel.y);
      vec2 oL  = vUv + vec2(-texel.x,  0.0);
      vec2 oR  = vUv + vec2( texel.x,  0.0);
      vec2 oBL = vUv + vec2(-texel.x, -texel.y);
      vec2 oB  = vUv + vec2( 0.0,     -texel.y);
      vec2 oBR = vUv + vec2( texel.x, -texel.y);

      float dTL = getViewDist(oTL); float dT = getViewDist(oT); float dTR = getViewDist(oTR);
      float dL  = getViewDist(oL);                              float dR  = getViewDist(oR);
      float dBL = getViewDist(oBL); float dB = getViewDist(oB); float dBR = getViewDist(oBR);

      // Relative depth Sobel (scale-invariant with distance)
      float gxD = -dTL - 2.0 * dL - dBL + dTR + 2.0 * dR + dBR;
      float gyD = -dTL - 2.0 * dT - dTR + dBL + 2.0 * dB + dBR;
      float depthGrad = sqrt(gxD * gxD + gyD * gyD) / max(1.0, centerViewZ * 0.24);
      float depthEdge = smoothstep(0.18, 0.56, depthGrad);

      // Normal Sobel (weighted by per-material outline mask so foliage/terrain stay clean)
      vec4 nmC  = getNM(vUv);
      vec3 nTL = getNM(oTL).xyz; vec3 nT = getNM(oT).xyz; vec3 nTR = getNM(oTR).xyz;
      vec3 nL  = getNM(oL).xyz;                           vec3 nR  = getNM(oR).xyz;
      vec3 nBL = getNM(oBL).xyz; vec3 nB = getNM(oB).xyz; vec3 nBR = getNM(oBR).xyz;

      vec3 gxN = -nTL - 2.0 * nL - nBL + nTR + 2.0 * nR + nBR;
      vec3 gyN = -nTL - 2.0 * nT - nTR + nBL + 2.0 * nB + nBR;
      float normGrad = sqrt(dot(gxN, gxN) + dot(gyN, gyN));
      float normEdge = smoothstep(0.55, 1.35, normGrad) * nmC.a;

      // Combine: crisp depth silhouettes (even light silhouette on trees), normal creases only where mask > 0
      float silMask = smoothstep(0.02, 0.22, nmC.a);
      float edge = max(depthEdge * mix(0.45, 1.0, silMask), normEdge * 0.85);

      // Smooth fade with distance so distant mountains/hills stay painterly & airy
      float distFade = 1.0 - smoothstep(115.0, 390.0, centerViewZ);
      float lineAmt = edge * distFade * uStrength;

      // Color-tinted anime ink: darkened local color blended with cool slate-indigo (never harsh black)
      vec3 localDark = sceneCol.rgb * vec3(0.36, 0.40, 0.50);
      vec3 inkCol = mix(localDark, uOutlineTint, 0.34);
      vec3 outCol = mix(sceneCol.rgb, inkCol, clamp(lineAmt, 0.0, 0.78));

      gl_FragColor = vec4(outCol, sceneCol.a);
    }
  `,
};
