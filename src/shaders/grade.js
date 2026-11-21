export const GradeShader = {
  uniforms: {
    tDiffuse: { value: null },
    uExposure: { value: 1.06 },
    uSaturation: { value: 1.12 },
    uWarmLift: { value: 0.072 },
    uTealShadow: { value: 0.056 },
    uVignette: { value: 0.15 },
  },

  vertexShader: /* glsl */ `
    varying vec2 vUv;
    void main() {
      vUv = uv;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,

  fragmentShader: /* glsl */ `
    uniform sampler2D tDiffuse;
    uniform float uExposure;
    uniform float uSaturation;
    uniform float uWarmLift;
    uniform float uTealShadow;
    uniform float uVignette;

    varying vec2 vUv;

    // Soft ACES filmic tonemapper tuned to preserve pastel anime chroma
    vec3 acesToneMap(vec3 x) {
      const float a = 2.51;
      const float b = 0.03;
      const float c = 2.43;
      const float d = 0.59;
      const float e = 0.14;
      return clamp((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0);
    }

    vec3 linearToSrgb(vec3 c) {
      return mix(
        c * 12.92,
        1.055 * pow(max(c, vec3(0.0)), vec3(1.0 / 2.4)) - 0.055,
        step(vec3(0.0031308), c)
      );
    }

    void main() {
      vec4 tex = texture2D(tDiffuse, vUv);
      vec3 col = max(tex.rgb, vec3(0.0)) * uExposure;

      // Filmic tonemapping in linear HDR space
      col = acesToneMap(col);

      // Gentle summer anime color grade (warm sunlit lift + cool teal-blue shadows)
      float luma = dot(col, vec3(0.2126, 0.7152, 0.0722));
      float shadowW = pow(clamp(1.0 - luma, 0.0, 1.0), 2.1);
      float highW = smoothstep(0.42, 0.96, luma);

      col += vec3(-0.015, 0.020, 0.045) * shadowW * uTealShadow * 3.0;
      col += vec3(0.042, 0.024, -0.014) * highW * uWarmLift * 2.4;

      // Vibrance-aware saturation boost (lifts muted tones without clipping vivid colors)
      float maxC = max(col.r, max(col.g, col.b));
      float minC = min(col.r, min(col.g, col.b));
      float curSat = maxC - minC;
      float satFactor = mix(uSaturation, 1.0 + (uSaturation - 1.0) * 0.45, clamp(curSat * 1.4, 0.0, 1.0));
      float luma2 = dot(col, vec3(0.2126, 0.7152, 0.0722));
      col = mix(vec3(luma2), col, satFactor);

      // Gentle healing-film vignette (light sky-tinted fade, never dark murky corners)
      vec2 d = (vUv - 0.5) * vec2(1.18, 1.0);
      float vig = smoothstep(0.42, 0.96, length(d));
      col *= mix(1.0, 1.0 - uVignette, vig);

      // Output sRGB for crisp FXAA luma edge detection
      col = linearToSrgb(clamp(col, 0.0, 1.0));
      gl_FragColor = vec4(col, 1.0);
    }
  `,
};
