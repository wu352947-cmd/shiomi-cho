# 汐見町 Shiomi-chō — Art Bible (binding for every batch)

Goal: a breathtaking, freely-rotatable 3D diorama of a Japanese seaside harbor town in a healing (治愈)
anime style — think Makoto Shinkai skies + Ghibli warmth: summer afternoon ~15:30, deep clear blue sky,
huge soft cumulus, warm sunlight, cool blue-violet shadows, sparkling sea. Viewed in the browser (Three.js).

## Mood & lighting
- Time: summer afternoon, sun elevation ~35°, azimuth from south-west (sun over the sea, town lit from front-left).
- Key light warm (#FFF1D6, strong). Fill/sky light cool (#9CC7FF). Shadows are never black: tinted blue-violet (#5C6FA8 at ~45%).
- Cel shading: 3 bands (shadow / mid / lit) with soft 1–2px transition, plus a thin rim light on silhouettes facing the sky.
- Outlines: thin, dark-tinted (not black) — e.g. darkened local color, ~1.0–1.5px at 1080p, fading with distance. No outlines on sea/sky/clouds/foliage interiors.
- Atmospheric perspective: distant objects desaturate & shift to sky blue (#A9C9EE). Mountains/islands are flat blue silhouettes in 2–3 layers.
- Post: gentle bloom only on sun glints/sea sparkles/lamps, slight warm grade, mild vignette, no heavy film grain.

## Palette (sRGB) — use these named materials ONLY (material name = key)
Walls:  `wall_cream` #F3E6CC, `wall_white` #F6F2EA, `wall_peach` #F2CBB0, `wall_mint` #CFE6D6, `wall_sky` #C9DDF0, `wood_dark` #6B4A36, `wood_light` #B88A5E, `wood_weathered` #8E8173
Roofs (kawara tiles, slightly glossy): `roof_blue` #3F5F8C, `roof_teal` #3E7D7A, `roof_terracotta` #B5583F, `roof_charcoal` #4A4E58, `roof_tin_red` #A8453C (corrugated)
Trim: `trim_white` #FAFAF5, `window_glass` #8FB8D9 (slightly emissive/specular sky reflection), `window_frame` #E9E3D6, `shoji` #F4EBD8, `door_wood` #7A5233
Ground: `grass` #8CC56A, `grass_dark` #5E9E55, `dirt_path` #D8C39A, `stone` #BDB6A8, `stone_dark` #8C877E, `asphalt` #7C8088, `road_line` #F5F2E8, `concrete` #CFCAC0, `sand` #EADBB2, `cliff_rock` #A99C88
Nature: `leaf_green` #6FB04F, `leaf_light` #A6D46A, `leaf_dark` #3F7E43, `sakura` #F7C6D4, `sakura_deep` #EE9DB5, `bark` #6E5444, `hydrangea_blue` #8DA8E8, `hydrangea_pink` #E7A3C6, `sunflower` #F5C542
Accent: `torii_red` #D8443A, `lighthouse_white` #F7F7F2, `lighthouse_red` #D84B3E, `boat_white` #F4F4EF, `boat_blue` #3C76B8, `boat_red` #C9503F, `metal_grey` #9AA1AA, `metal_dark` #4F555E, `rail_steel` #6E737A, `pole_wood` #7D6A55, `wire_black` #2E3036, `vending_red` #D94A44, `vending_blue` #3E79C7, `vending_white` #F2F2F2, `noren_indigo` #2F4A7A, `noren_red` #B8443C, `awning_stripe` #E46F5F, `sign_yellow` #F2C84B, `crossing_yellow` #F2C230, `crossing_black` #2B2B2B, `laundry_white` #FBFBF7, `laundry_blue` #9FC3E8, `laundry_pink` #F3B9C5, `tram_cream` #F1E7CF, `tram_green` #4F8F6B, `lamp_glow` (emissive warm), `flower_red` #E85D5D, `flower_yellow` #F6D365
- Max ~70 materials total. Colors are BASE colors; the web shader does the lighting. Keep saturation pleasant, not neon.

## Geometry rules (learned from a failed previous project — MUST follow)
1. NO "box buildings". Every house has: a stone/concrete base course, walls with visible structure (wood board bands or plaster with wood trim),
   proper Japanese roof (kirizuma gable or irimoya hip-and-gable) with real overhang (≥0.5 m), visible ridge, slight eave thickness,
   tile rows suggested by geometry (ridged strips) — not a flat plane. Add engawa/balcony, rain gutters, AC units, small chimneys/vent pipes, potted plants.
2. Windows/doors are NOT floating quads. Build them as a frame (4 thin bars) that INTERSECTS or sits flush against the wall plus a glass pane recessed 3–5 cm.
   Window must never stand off the wall with a gap. Verify by rendering close-ups.
3. All meshes closed & solid. NEVER use the Decimate modifier. No hollow walls, no flipped normals (recalc normals outside), apply all transforms before export.
4. Bevel important edges slightly (0.02–0.05 m) so cel shading catches highlights; keep shading flat/smooth sensibly (auto smooth 30°).
5. Variation: seeded randomness (fixed seed) on width/depth/floors(1–3)/roof type/colors so no two neighbours are identical, but a coherent palette.
6. Scale is real: door 2 m, floor height 2.8 m, street 4–6 m wide, stairs 0.18 m rise.
7. People: none (the scene is about place). Optionally a few cats on walls (simple, cute, low-poly).
8. Signage: only fictional Japanese shop names (e.g. 「汐見食堂」「かもめ書店」「潮風珈琲」「たばこ」-style generic words are fine, NO real brands).
   Text may be done in the web viewer as canvas textures on sign planes named `sign_<n>` with a custom property `text`.

## Layout contract (Blender coords: X east, Y north, Z up, meters; glTF export converts to Y-up)
- Sea level z = 0. Open sea to the south (y < -20) and stretching to the horizon (viewer renders the ocean; Blender only provides seabed/shore up to y=-120).
- Harbor basin: y ∈ [-90, -5], x ∈ [-60, 90]. Concrete quay along y ≈ -5 from x=-60..90, height z=1.2.
- Breakwater (tetrapods + concrete wall) curving from (95,-5) to (60,-95); red lighthouse at its tip (~(58,-98)), 14 m tall.
  Second short breakwater from (-70,-10) to (-45,-70) with a small white light tower.
- Piers: 2–3 wooden/concrete piers extending south from the quay; 6–10 fishing boats (varied sizes, wheelhouses, masts, flags, buoys), small rowboats.
- Coastal road along y ≈ 4, z≈1.5 with guardrails; railway (single track, ballast, sleepers) along y ≈ 12, z ≈ 2.5, with a small station platform
  (roof, bench, name board 「しおみ」) around x=10 and a level crossing (遮断機 with yellow/black arm, crossing signal) at x ≈ -25.
- Town hill: rises north from y=18 to a summit ~z=55 at around (−30, 150). Terrain = smooth sculpted hill with terraces (stone retaining walls), not a cone.
  Winding lanes switchback up the hill; long stone stairway from the station area up to the shrine.
- Shrine at hilltop (~(−30,145)): stone stairs, 2 vermilion torii, small honden with roof, stone lanterns, big camphor tree, sakura trees around.
- 45–70 houses/shops on terraces between y=20 and y=130; shopping street (商店街) along the coastal road with shops: noren, awnings, vending machines, signs, bicycles, potted plants.
- Utility poles (wooden, crossarms, transformers) along roads with catenary wires (thin sagging tubes) — wires are important for the anime look.
- Trees: rounded clustered canopies (multiple blobby spheres, sculpted lumpy look, not single spheres), sakura blossoms, a few pines near the coast.
  Hydrangea bushes, flower boxes, sunflowers in gardens, laundry lines on balconies.
- East headland: rocky cliff (x 100..160) with the lighthouse path; West: small sandy beach (x −120..−70) with a few rocks.
- Background: 2–3 layers of mountains to the north/north-east (y 250–600) and 2 islands in the sea (south-west, ~(−400,−600) and (300,−800)) — low-poly smooth silhouettes.
- Total scene extent roughly x −200..200, y −120..250 for detailed area.

## Object naming (so the web viewer can animate)
- Prefix `anim_flag_*` for flags/noren/laundry (cloth sway), `anim_tree_*` for foliage meshes (wind sway), `anim_boat_*` for boats (bob on water),
  `lamp_*` for lights that may glow at dusk, `sign_*` for sign planes (custom prop `text`), `lighthouse_lamp` for the lamp head.
- Store foliage, boats, flags as SEPARATE objects (do not join them with buildings). Static buildings/terrain may be joined per-material per-zone to reduce draw calls.

## Performance budget (must run on phones and an M1 MacBook Air)
- Final town.glb ≤ 25 MB (target 12–18 MB), ≤ 1.2 M triangles total, ≤ 400 draw calls after joining. Use instancing-friendly duplication (linked meshes) for props.
- Use meshopt or Draco compression only if the viewer supports it (vendor/three/addons/libs has draco + meshopt decoders).
