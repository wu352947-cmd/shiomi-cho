You are the lead graphics engineer for this project. Read ./ART_BIBLE.md first — it is binding.

USER'S ORIGINAL REQUEST (Chinese): 「选用合适的技术栈构建一个超级精美、还原度超高的可自由旋转的高精度3d日系动漫画风唯美海港小镇景观模型。只在意视觉的精美与还原度，不在意token预算，可以尽情尝试显著提升视觉美感的测试包括子代理。给我一个叹为观止的产品。小镇美观，元素好看齐全，动漫日系的治愈风格。」

YOUR JOB (batch B): build the web viewer that makes the Blender-made town (public/models/town.glb, being built IN PARALLEL by another agent —
do not edit blender/) look like a Makoto Shinkai / Ghibli summer-afternoon anime frame, freely rotatable with mouse and touch.
Stack: plain ES modules, Three.js 0.170 vendored at vendor/three (three.module.js + addons/), import map in index.html, no bundler, static
hosting on GitHub Pages under a sub-path (use only RELATIVE URLs). Files: index.html, src/*.js, src/shaders/*.

Until town.glb exists, generate a small stand-in yourself: write blender/stub_test.py (that filename only) producing public/models/stub.glb with a
few houses/trees/boat using ART_BIBLE material names & object naming, and load town.glb if present else stub.glb.

Must have:
1. Material system: on load, replace every glTF material by a custom toon ShaderMaterial (or onBeforeCompile on MeshToonMaterial) keyed by material
   name: 3-band cel shading with soft edges, warm key / cool blue-violet shadow tint (never black), sky-tinted fill, rim light, multiply by the AO in
   COLOR_0 if present, real-time sun shadow map (one directional light, PCF soft, tightly fitted frustum; quality tiers), atmospheric distance fog
   toward sky color, subtle specular on roofs/glass/water-wet surfaces, window_glass reflecting sky gradient, lamp_glow emissive.
2. Outlines: screen-space edge detection post pass (depth + normal Sobel) with thin, color-tinted lines fading with distance; skip sky/sea.
3. Sky: painterly gradient sky shader (deep azure zenith → pale cyan horizon, warm haze near the sun), sun disk with soft glow, and big,
   gorgeous anime cumulus clouds — layered billboards or volumetric-looking shaded sprites with crisp lit tops, soft blue undersides, slowly drifting.
   High cirrus streaks. Clouds are a key element of the Shinkai look — iterate until they are beautiful.
4. Ocean: large animated stylized sea shader (Gerstner/sum-of-sines), depth-based color (turquoise shallows near shore/harbor → deep blue),
   shoreline/foam bands around objects intersecting the water (depth-diff foam), sun glitter sparkles that bloom, horizon blend into sky.
   Boats bob (`anim_boat_*`), small wakes optional.
5. Motion: wind sway vertex shader for `anim_tree_*` and cloth for `anim_flag_*`, drifting clouds, a few seagulls (simple flapping V shapes),
   lighthouse lamp glow, optional sakura petals drifting, optional slow-moving tram on the rail line if geometry exists.
6. Post: UnrealBloomPass (subtle threshold), color grading (warm lift, teal shadows, slight saturation boost), vignette, FXAA/SMAA, tonemapping
   ACES or AgX. Order: render → outline → bloom → grade → AA.
7. Camera: OrbitControls with damping, touch rotate/pinch/pan, limits (no going under sea/ground, sensible min/max distance), gentle auto-rotate
   after 8 s idle (stops on interaction), 6 preset views (全景 Overview, 港口 Harbor, 商店街 Street, 神社 Shrine, 灯塔 Lighthouse, 踏切 Crossing) chosen
   from the Blender layout contract coordinates (Blender (x,y,z) → three (x, z, -y)). Smooth fly-to transitions.
8. UI: minimal elegant Japanese-style overlay — title 「汐見町 Shiomi-chō」 small, preset buttons, a "hide UI" toggle, loading screen with progress.
   Must look good on phone portrait 390x844 (buttons not overlapping, thumb-friendly) and desktop. Chinese/Japanese labels fine.
9. Quality tiers auto-detected (mobile → lower pixel ratio ≤1.5, smaller shadow map, fewer clouds; desktop → high). URL params ?q=low|med|high,
   ?cam=<preset>, ?ui=0, ?auto=0. Expose window.__READY=true once the first full frame after load rendered, and window.__INFO() returning
   {tris, calls, fps, quality}. Also window.__setCam(name) for screenshots.
10. Sign text: meshes named `sign_*` with extras.text get a canvas-drawn texture (vertical or horizontal Japanese text, hand-painted look).

Testing: tools/shot.mjs is a headless Chrome screenshot harness (SwiftShader software WebGL, slow; low FPS is expected).
`node tools/shot.mjs --out shots/web/x.png --w 1280 --h 720 --params "cam=overview&ui=0"`. It waits for window.__READY.
SELF-CRITIQUE LOOP (mandatory, ≥3 iterations): screenshot overview, harbor, street, phone portrait (--w 390 --h 844), compare against the art
bible mood (Shinkai/Ghibli summer), fix ugliness (banding, harsh black, aliasing, plastic look, boring sky), re-shoot. Zero console errors.
Keep it fast on an M1 Air / mid phone: avoid per-frame allocations, cap DPR.

When finished, print a concise summary: files, features, screenshots path, known weak spots. Do not git push.
