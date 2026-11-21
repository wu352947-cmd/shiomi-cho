"""Ambient Occlusion vertex-color baker for Shiomi-cho.

Bakes Cycles CPU Ambient Occlusion into a `CORNER` `BYTE_COLOR` attribute named
`AO` (exported as `COLOR_0` in glTF 2.0, 1.0 = unoccluded) so the web toon
shader can multiply vertex AO cleanly for grounded crevices, eaves, and alleys.
"""

import time
import bpy
import numpy as np


SKIP_BAKE_PREFIXES = ("lamp_", "lighthouse_lamp", "sign_", "bg_")


def _ensure_ao_attr(mesh: bpy.types.Mesh, name: str = "AO", fill: float = 1.0) -> bpy.types.Attribute:
    attr = mesh.color_attributes.get(name)
    if attr is None:
        attr = mesh.color_attributes.new(name=name, type="BYTE_COLOR", domain="CORNER")
    idx = mesh.color_attributes.find(name)
    mesh.color_attributes.active_color_index = idx
    mesh.color_attributes.render_color_index = idx

    n_loops = len(mesh.loops)
    if n_loops > 0:
        buf = np.full(n_loops * 4, fill, dtype=np.float32)
        attr.data.foreach_set("color", buf)
    return attr


def _remap_ao_attr(mesh: bpy.types.Mesh, name: str, floor_val: float, gamma: float = 0.85) -> None:
    """Remap raw Cycles AO [0, 1] into pleasing anime toon range [floor_val, 1.0]."""
    attr = mesh.color_attributes.get(name)
    if attr is None or len(mesh.loops) == 0:
        return
    n = len(mesh.loops)
    buf = np.empty(n * 4, dtype=np.float32)
    attr.data.foreach_get("color", buf)
    rgba = buf.reshape((n, 4))
    # Use luminance (R channel) and apply gentle curve + anime floor lift
    ao = np.clip(rgba[:, 0], 0.0, 1.0)
    ao = np.power(ao, gamma)
    ao = floor_val + (1.0 - floor_val) * ao
    # Subtle warm-cool nuance: slightly cooler tint in crevices (B slightly higher than R)
    rgba[:, 0] = np.clip(ao * 0.985 + 0.015, floor_val, 1.0)
    rgba[:, 1] = np.clip(ao * 0.992 + 0.008, floor_val, 1.0)
    rgba[:, 2] = np.clip(ao * 0.94 + 0.06, floor_val, 1.0)
    rgba[:, 3] = 1.0
    attr.data.foreach_set("color", rgba.ravel())


def bake_scene_ao(samples: int = 16, attr_name: str = "AO") -> float:
    """Bake AO vertex colors across all town meshes in one Cycles CPU pass.
    Returns elapsed seconds.
    """
    t0 = time.time()
    scene = bpy.context.scene
    prev_engine = scene.render.engine

    mesh_objs = [o for o in bpy.data.objects if o.type == "MESH" and o.data is not None]
    bake_targets: list[bpy.types.Object] = []
    seen_meshes: set[int] = set()

    # Create active AO attribute on every mesh so glTF COLOR_0 is uniform across scene
    for obj in mesh_objs:
        mesh = obj.data
        mid = mesh.as_pointer()
        if mid not in seen_meshes:
            _ensure_ao_attr(mesh, attr_name, fill=1.0)
            seen_meshes.add(mid)
        if obj.name.startswith(SKIP_BAKE_PREFIXES):
            continue
        if len(mesh.polygons) == 0:
            continue
        # Only bake one representative if mesh is shared across instances
        if mesh.users > 1 and any(b.data == mesh for b in bake_targets):
            continue
        bake_targets.append(obj)

    if not bake_targets:
        return 0.0

    # Configure fast multi-threaded Cycles CPU AO vertex bake
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = False
    scene.cycles.use_denoising = False
    scene.cycles.max_bounces = 1
    scene.cycles.diffuse_bounces = 1
    scene.cycles.glossy_bounces = 0
    scene.cycles.transmission_bounces = 0
    scene.cycles.transparent_max_bounces = 0
    scene.render.bake.target = "VERTEX_COLORS"
    scene.render.bake.use_selected_to_active = False

    # Set clean white AO world with modest ray distance (~6m) for crisp architectural crevices
    if scene.world is None:
        scene.world = bpy.data.worlds.new("AO_World")
    if hasattr(scene.world, "light_settings") and hasattr(scene.world.light_settings, "distance"):
        scene.world.light_settings.distance = 6.5
    if hasattr(scene.cycles, "fast_gi_distance"):
        scene.cycles.fast_gi_distance = 6.5

    bpy.ops.object.select_all(action="DESELECT")
    for obj in bake_targets:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = bake_targets[0]

    print(f"[bake_ao] Baking Cycles CPU AO ({samples} samples) across {len(bake_targets)} objects...")
    bpy.ops.object.bake(type="AO")

    # Remap raw AO so shadows never go black in the web toon shader
    remapped: set[int] = set()
    for obj in bake_targets:
        mid = obj.data.as_pointer()
        if mid in remapped:
            continue
        remapped.add(mid)
        if obj.name.startswith("anim_tree_"):
            _remap_ao_attr(obj.data, attr_name, floor_val=0.60, gamma=0.75)
        elif obj.name.startswith("anim_"):
            _remap_ao_attr(obj.data, attr_name, floor_val=0.58, gamma=0.80)
        elif obj.name == "terrain_main":
            _remap_ao_attr(obj.data, attr_name, floor_val=0.52, gamma=0.82)
        else:
            _remap_ao_attr(obj.data, attr_name, floor_val=0.44, gamma=0.82)

    scene.render.engine = prev_engine
    elapsed = time.time() - t0
    print(f"[bake_ao] Completed AO vertex bake in {elapsed:.1f}s")
    return elapsed
