You are the lead 3D environment artist + technical artist for this project. Read ./ART_BIBLE.md first — it is binding.

USER'S ORIGINAL REQUEST (Chinese, keep its spirit): 「选用合适的技术栈构建一个超级精美、还原度超高的可自由旋转的高精度3d日系动漫画风唯美海港小镇景观模型。只在意视觉的精美与还原度，不在意token预算，可以尽情尝试显著提升视觉美感的测试包括子代理。给我一个叹为观止的产品。小镇美观，元素好看齐全，动漫日系的治愈风格。」

YOUR JOB (batch A): write a deterministic Blender 5.2 Python generator that builds the ENTIRE static town scene and exports it to
`public/models/town.glb`. Blender binary: /home/box/.local/bin/blender (run headless: `blender -b --factory-startup --python blender/build.py`).
Machine: 8 CPU, 16 GB RAM, NO GPU. Eevee & Workbench do render headless (software GL, slowish); Cycles CPU works too. Keep each build under ~10 min.

Structure the code as modules under blender/ (e.g. build.py entry, lib/materials.py, lib/geo.py helpers (bevelled boxes, extrude, roof builders,
windows, stairs, railings, catenary wires), terrain.py, roads_rail.py, harbor.py (quay, piers, breakwaters+tetrapods, lighthouse, boats, buoys),
houses.py (several archetypes: 2-storey wooden minka with kirizuma roof, stucco house with irimoya roof & balcony, shop-house with noren/awning/sign,
small apartment 3F with outdoor stairs & laundry, warehouse/fish market with tin roof, station building), shrine.py, nature.py (lumpy clustered trees,
sakura, pines, hydrangea, flowers, grass tufts), props.py (utility poles+wires, vending machines, bicycles, mailbox, guardrails, crossing gate & signal,
street lamps, benches, potted plants, cats, laundry, flags), background.py (mountain layers + islands), export.py.

Quality bar: this must look hand-crafted and rich. Each house archetype needs the details listed in ART_BIBLE "Geometry rules". Study real Japanese
seaside towns (Onomichi, Kamakura/Enoshima, Ine-no-Funaya, Manazuru): dense houses on slopes, narrow stairs, retaining walls, poles & wires everywhere.

Lighting bake: bake ambient occlusion (and optionally soft sun shadow) into a vertex color attribute so the web toon shader can multiply it
(COLOR_0 in glTF, value 1 = unoccluded). Make sure geometry has enough vertices where AO matters (subdivide large ground/walls modestly), or bake to a
small lightmap — your choice, but justify. If baking is too slow, bake at low samples. Document the choice in blender/README.md.

Export: glTF binary, +Y up, apply modifiers, export vertex colors, export custom properties (extras) for sign text, keep object names per ART_BIBLE
naming. Join static geometry per material per zone to keep draw calls < 400; keep animated categories as separate objects (they may be joined per
category per zone, e.g. all tree canopies in one zone = one object `anim_tree_zone3`). Use linked duplicates / instancing for repeated props where
the glTF exporter supports GPU instancing (EXT_mesh_gpu_instancing option) — else join. Compress with meshopt if available in the exporter,
otherwise leave uncompressed; report final size and triangle count (write public/models/town.stats.json with tris, objects, materials, size).

SELF-CRITIQUE LOOP (mandatory, at least 3 iterations): write blender/render_check.py that loads the built scene and renders with Eevee
(simple sun + sky world, Filmic/AgX) to shots/blender/: a wide overview from the south-west over the sea, a harbor close-up, a street-level
view of the shopping street, a close-up of 2 houses (check windows flush, roofs proper), the shrine, the level crossing. Look at every image
critically against the art bible and the "failure modes": box-like buildings, floating windows, hollow/shattered geometry, empty areas,
repetitive clones, wrong scale. Fix and re-render. Keep the final review images.

Budgets: ≤ 25 MB glb, ≤ 1.2M triangles. Open-license only: if you use any external asset (CC0 from Poly Haven / Kenney / ambientCG), record it in
CREDITS.md with URL and license; prefer fully procedural. No real brands. No people.

When finished, print a concise summary: files created, build time, glb size, tris, draw calls, what you checked in the renders, known weak spots.
Do not touch index.html / src/ (another agent builds the web viewer in parallel). Do not git push.
