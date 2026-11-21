# Shiomi-chō (汐見町) — Blender 5.2 Procedural Scene Generator

Deterministic, 100% procedural Blender 5.2 Python generator producing the full static town diorama (`public/models/town.glb`), stats (`public/models/town.stats.json`), and headless Eevee inspection renders (`shots/blender/`). Zero external assets (no third-party models or textures; no `CREDITS.md` attributions needed).

## Build & Verify Commands
```bash
# Generate shiomi_town.blend, bake AO vertex colors, export public/models/town.glb & town.stats.json
/home/box/.local/bin/blender -b --factory-startup --python blender/build.py

# Render 6 headless Eevee verification views into shots/blender/
/home/box/.local/bin/blender -b --factory-startup --python blender/render_check.py
```

## Module Layout
- `blender/build.py` — Master deterministic entry point (`SEED = 4207`).
- `blender/lib/materials.py` — All 65 exact `ART_BIBLE.md` named materials (sRGB → linear conversion, Principled BSDF).
- `blender/lib/geo.py` — Watertight `bmesh` `MeshBuilder` (beveled boxes, cylinders, prisms, tubes, catenary wires, flush/intersecting recessed windows & doors, 30° auto-smooth).
- `blender/lib/roofs.py` — Authentic Japanese `kirizuma` (gable) and `irimoya` (hip-and-gable) roofs with ≥ 0.58 m eaves, kawara tile ribs, bargeboards, ridge beams, onigawara finials, rain gutters, AC units, and balconies.
- `blender/terrain.py` — Shared elevation field `get_height(x, y)`, higher-density town-warped watertight seabed/beach/cliff/terraced hill mesh with smooth noise & path/terrace dirt/stone mid-tones, and multi-tier stone retaining walls (`ishigaki`).
- `blender/roads_rail.py` — Coastal road with markings/guardrails, hillside switchback lanes with downhill railings & 6 Onomichi side-alley stone stair flights, grand stone shrine stairway, single-track railway with ballast/sleepers/rails/catenary, level crossing (`遮断機`), upgraded Shiomi Station (`しおみ` / `汐見駅` with gabled clock portico), and vintage Enoden-style coastal tram.
- `blender/harbor.py` — Concrete quay wall, water stairs, bollards every 6 m, fenders, stacked fish crates, draped nets with floats, oil drum clusters, yellow jib crane, west davit hoist, mooring & coiled ropes, 3 piers, curved east & west breakwaters with seaward tetrapods, 14 m red lighthouse (`lighthouse_lamp`), west white beacon, 8 fishing boats (`anim_boat_*` + `anim_flag_boat_*`), 3 rowboats, and 6 buoys.
- `blender/house_archetypes.py`, `blender/landmarks.py` & `blender/houses.py` — 6 hand-crafted Japanese architectural archetypes (with rain chains, window boxes, wall battens, doorsteps & batched animated laundry) plus prominent town landmarks (enlarged Fish Market Hall `汐見魚市場`, 2F Elementary Clock School `汐見小学校`, elevated coastal Water Tower) deterministically packed shoulder-to-shoulder across **134** buildings with 100% hillside residential garden walls/fences, side boundaries, stepping stones, and yard planters.
- `blender/shrine.py` — Hilltop Shiomi Shrine (`汐見神社`) at `(-30, 145)`: 2 curved Myojin vermilion torii gates, haiden/honden with katsuogi & chigi, chozuya pavilion, ema rack, 6 glowing stone lanterns (`lamp_shrine_lanterns`), and shrine flags.
- `blender/nature.py` — Dense overlapping forest groves (4–6 lumpy canopy lobes per tree, smooth-shaded canopies separated into `anim_tree_zone0..4` & `anim_tree_shrubs`), sakura blossoms, coastal black pines, giant sacred shrine camphor tree, terrace hedgerows, bamboo clumps, terraced vegetable plots, hydrangea bushes, and coastal boulders.
- `blender/props.py` — Wooden utility poles, crossarms, transformers, sagging catenary power & telecom wires, vending machines, bicycles, red cylindrical postboxes, retro curved-neck street lamps (`lamp_streetlights`) along quay, road & mid-slope lanes, benches, convex mirrors, street & switchback potted plants/planters, and 6 low-poly cats.
- `blender/background.py` — 3 matte layered northern coastal mountain silhouettes + 2 distant sea islands + east sea stack.
- `blender/bake_ao.py` — Cycles CPU vertex-color Ambient Occlusion baker (`AO` → glTF `COLOR_0`).
- `blender/export.py` — Zone-based static joining, planar UVs for `sign_*` canvas textures, local pivot preservation for `anim_*`, glTF 2.0 binary export with `EXT_meshopt_compression`, and `town.stats.json` reporting.
- `blender/render_check.py` — Headless Eevee summer-afternoon review renderer (6 camera presets).

## Lighting Bake Rationale (Vertex AO vs Lightmaps)
We chose **Cycles CPU vertex-color Ambient Occlusion** baked into a `CORNER` `BYTE_COLOR` attribute (`AO`, exported as `COLOR_0` in glTF) over UV lightmap atlases:
1. **Zero UV seams / zero texture memory**: The scene uses 64 pure palette materials with procedural/cel shading in Three.js; baking AO directly to vertices avoids megabytes of PNG/WebP lightmap atlases and keeps total `town.glb` size compact (**21.40 MB** with meshopt across **134 buildings**).

## Current Export Stats (`public/models/town.stats.json`)
- **Buildings**: 134 (5 harbor quay buildings incl. enlarged Fish Market Hall, 21 continuous coastal shopping street/apartment buildings, 2 hillside landmarks — Clock School & Water Tower — plus 106 densely packed hillside residences)
- **File size**: `21.40 MB` (`EXT_meshopt_compression`, ≤ 25 MB budget)
- **Triangles**: `749,400` (≤ 1.2M budget)
- **Draw calls**: `375` across `99` mesh objects (≤ 400 budget)
- **Materials**: `64` named `ART_BIBLE.md` materials (≤ 70 budget)
- **Signs (`extras.text`)**: `29`
- **Vertex AO (`COLOR_0`)**: `true` (`cycles_cpu_vertex_ao_16spp`, ~13 s bake)
2. **Fast deterministic CPU baking**: Modestly subdivided ground, roads, retaining walls, and building walls provide ample vertex density for grounded contact shadows under eaves, alleys, stairwells, and harbor piers while baking 16 samples across the full scene in ~10 seconds on 8 CPU cores.
3. **Anime-safe value remapping**: Raw Cycles AO is remapped with a lifted floor (`0.44` static, `0.52` terrain, `0.60` foliage) and subtle cool crevice tint so the web cel shader's multiply (`baseColor * COLOR_0`) adds gentle depth without muddy black shadows. Emissive lamps (`lamp_*`, `lighthouse_lamp`), signs (`sign_*`), and distant background mountains (`bg_*`) are kept at unoccluded `1.0`.

## Export & Naming Contract
- **Coordinate system**: glTF `+Y` up (converted from Blender `+Z` up).
- **Separated objects**: `anim_boat_*` (individual local pivots for bobbing), `anim_flag_*` (noren/laundry/boat & shrine flags with local pivots), `anim_tree_zone0..4` & `anim_tree_shrubs`, `lamp_*`, `lighthouse_lamp`, and `sign_*` (each with planar `[0,1]` UVs and custom property `extras.text` in Japanese).
- **Compression**: `EXT_meshopt_compression` (matched to Three.js `GLTFLoader` + `MeshoptDecoder` in `vendor/three/addons/libs/meshopt_decoder.module.js`).
